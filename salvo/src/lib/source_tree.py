"""Manage a source location on disk"""
import re
import logging
import os
import subprocess
from typing import List

from src.lib import (cmd_exec, constants)
from src.lib.common import file_ops

import api.source_pb2 as proto_source

log = logging.getLogger(__name__)

# _TAG_REGEX matches strings of the format "v1.16.0".  We use this to
# determine whether a user specified a commit hash or a release tag
# for a given docker image
_TAG_REGEX = r'^v\d\.\d+\.\d+'

# _GIT_ORIGIN_REGEX matches the fetch urls returned in `git origin -v`
# For example, from
# origin        https://github.com/envoyproxy/envoy.git (fetch)"
# we get https://github.com/envoyproxy/envoy.git in an enumerated group
_GIT_ORIGIN_REGEX = r'^origin\s*([\w:@\.\/-]+)\s\(fetch\)$'

class SourceTreeError(Exception):
  """Raised if we encounter a condition from which we cannot recover, when
     manipulating SourceTree objects.
  """

def is_tag(image_tag: str) -> bool:
  """Determine whether a an image tag is a commit hash or a version tag."""
  match = re.match(_TAG_REGEX, image_tag)
  return match is not None


class SourceTree(object):
  """Abstracts the manipulation of souce locations on disk.

  This class encapsulates the git logic needed to determine the endpoints
  of the benchmark.
  """

  def __init__(self, source_repo: proto_source.SourceRepository) -> None:
    """Create temporary directories for building and working
        with a source tree.
    """

    # TODO: We need one module that centralizes directory management.  This
    #       module will have one $HOME path defined and orchestrate sources
    #       to reduce/eliminate multiple copies of a source tree

    home_dir = '' if not 'HOME' in os.environ else os.environ['HOME']
    if not home_dir.startswith(constants.SALVO_TMP):
      home_dir = constants.SALVO_TMP

    self._tempdir = file_ops.get_random_dir(home_dir)
    self._source_repo = source_repo

  def __repr__(self) -> str:
    """Return a string representation of this class."""

    result = f"{type(self).__name__}: "
    result += f"Origin: [{self._source_repo.source_url}] "
    result += f"Branch: [{self._source_repo.branch}] "
    result += f"Hash: [{self._source_repo.commit_hash}] "
    result += f"Workdir: [{self._source_repo.source_path}]"

    return result

  def get_identity(self) -> proto_source.SourceRepository.SourceIdentity:
    """Return the identity of the source tree being managed."""
    return self._source_repo.identity

  def _validate(self) -> bool:
    """Verify that we have enough data to work with the source tree.

    Returns:
      a bool indicating that we have a source path on disk or a url from
        which to pull the source.

    Raises:
      SourceTreeError: if no path or url is specified for the class to
        operate.
    """

    # We have neither a source url nor source on disk.
    # - This is a non starter and we cannot operate further. We don't know where
    #   to get the source for building anything
    if all([not self._source_repo.source_path,
            not self._source_repo.source_url]):
      raise SourceTreeError(
          "No origin is defined or can be deduced from the path")

    # We have a source url and no source on disk -> good.
    # - We can clone the url to a temporary disk location and work in that
    #   directory
    if not self._source_repo.source_path and self._source_repo.source_url:
      log.debug(f"No source path in control object. Using {self._tempdir}")

      if not os.path.exists(self._tempdir):
        os.mkdir(self._tempdir)

      return True

    # We have a source url and a source on disk -> good.
    # - This means we have pulled/cloned the source, or the source is to be
    #   copied from the specified directory
    if self._source_repo.source_path and self._source_repo.source_url:
      return True

    # We have a source on disk and no source url -> good
    # - We can copy the source tree and determine what we need from it.
    if self._source_repo.source_path and not self._source_repo.source_url:
      return True

    log.debug(f"Validation failed for source tree: {self}")
    raise SourceTreeError(
        "Insufficient information in source definition for it to be usable")

  def get_origin(self) -> str:
    """Detect the origin url from where the code is fetched.

    Returns:
      A string showing the origin url for the source tree.  This needed most
        for remote execution where we do not ship the entire source tree
        remotely.  We will attempt to generate a patch between the origin
        HEAD and the local HEAD.  This diff is applied to the source in the
        remote context.
    """
    valid = self._validate()
    log.debug(f"Valid: {valid} for object: {self}")

    origin_url = self._source_repo.source_url
    output_directory = self.get_source_directory()

    cmd = "git remote -v"
    if not origin_url:
      cmd_params = cmd_exec.CommandParameters(cwd=output_directory)
      output = cmd_exec.run_command(cmd, cmd_params)
      for line in output.split('\n'):
        match = re.match(_GIT_ORIGIN_REGEX, line)
        if match:
          origin_url = match.group(1)
          self._source_repo.source_url = origin_url
          break

    if not origin_url:
      raise SourceTreeError(
          f"Unable to determine the origin url from {output_directory}"
      )

    return origin_url

  def get_source_directory(self) -> str:
    """Return the full path where the code has been checked out.

    Returns:
      a string containing the disk path to the source.
    """
    self._validate()

    return  self._source_repo.source_path \
                 if self._source_repo.source_path else self._tempdir

  def pull(self) -> bool:
    """Retrieve the code from the repository.

    Uses git to clone the source into a working directory that has read/write
    permissions by salvo

    Returns:
      a boolean indicating whether the operation was successful
    """

    self._validate()

    source_name = proto_source.SourceRepository.SourceIdentity.Name(
        self._source_repo.identity)
    log.debug(f"Pulling [{source_name}] from origin: [{self._source_repo.source_url}]")

    try:
      if self.is_up_to_date():
        return True
    except subprocess.CalledProcessError:
      log.info("Source likely does not exist on disk")

    if not self._source_repo.source_url:
      self._source_repo.source_url = self.get_origin()

    output_dir = self.get_source_directory()

    # Clone into the working directory
    cmd = "git clone {origin} .".format(origin=self._source_repo.source_url)
    cmd_params = cmd_exec.CommandParameters(cwd=output_dir)
    output = cmd_exec.run_command(cmd, cmd_params)
    expected = 'Cloning into \'.\''

    return expected in output


  def checkout_commit_hash(self) -> bool:
    """Checks out the specified commit hash in the source tree

    Returns:
      a boolean indicating whether the operation was successful
    """
    self._validate()

    # Assume the checkout is successful.  It is possible that it is a no-op
    # if no commit hashes are specified
    checkout_success = True

    # Clone the repo if it doesn't exist on disk
    if not self._source_repo.source_path and self._source_repo.source_url:
      log.debug("No local source path exists.  Cloning repo for hash discovery")
      self.pull()

    if self._source_repo.commit_hash:
      output_directory = self.get_source_directory()
      cmd = "git checkout {hash}".format(hash=self._source_repo.commit_hash)
      cmd_params = cmd_exec.CommandParameters(cwd=output_directory)
      output = cmd_exec.run_command(cmd, cmd_params)

      # HEAD is now at <8 chars of hash>
      expected = "HEAD is now at {commit_hash}".format(
          commit_hash=self._source_repo.commit_hash[:8])
      log.debug(f"Checkout output: {output}")

      checkout_success = expected in output

    return checkout_success

  def get_head_hash(self) -> str:
    """Retrieve the hash for the HEAD commit.

    Returns:
      a string containing the hash corresponding to commit at the HEAD of the
        tree.
    """
    self._validate()

    cmd = ("git rev-list --no-merges --committer='GitHub <noreply@github.com>' "
           "--max-count=1 HEAD")

    output_directory = self.get_source_directory()
    cmd_params = cmd_exec.CommandParameters(cwd=output_directory)
    return cmd_exec.run_command(cmd, cmd_params)

  def get_previous_commit_hash(self, current_commit: str,
                               revisions: int = 2) -> str:
    """Return the specified number of commits behind the current commit hash.

    Args:
      current_commit: The current hash from which we are starting the search
      revisions: The number of commits in the tree that we skip over, starting
        from the current_commit

    Returns:
      a string with the discovered commit hash

    Raises:
      SourceTreeError if we are not able to deduce the previous commit
    """

    assert current_commit

    self.pull()

    log.debug(f"Finding previous commit to current commit: [{current_commit}]")
    if is_tag(current_commit):
      log.info(f"Current commit \"{current_commit}\" is a tag.")
      return self.get_previous_tag(current_commit)

    if current_commit == 'latest':
      current_commit = self.get_head_hash()

    cmd = "git rev-list --no-merges --committer='GitHub <noreply@github.com>' "
    cmd += "--max-count={revisions} {commit}".format(
        revisions=revisions, commit=current_commit
    )

    output_directory = self.get_source_directory()
    cmd_params = cmd_exec.CommandParameters(cwd=output_directory)
    hash_list = cmd_exec.run_command(cmd, cmd_params)

    # Check whether we got an error from git
    if 'unknown revision or path not in the working tree.' in hash_list:
      raise SourceTreeError(hash_list)

    # Reverse iterate throught the list of hashes, skipping any blank
    # lines that may have trailed the original git output
    for commit_hash in hash_list.split('\n')[::-1]:
      if commit_hash:
        log.debug(f"Returning {commit_hash} as the previous commit to {current_commit}")
        return commit_hash

    raise SourceTreeError(f"No commit found prior to {current_commit}")

  def get_revs_behind_parent_branch(self) -> int:
    """Get the number of commits behind the parent branch.

    Determine how many commits the current branch on disk is behind the
    parent branch.  If we are up to date, return zero

    Returns:
      an integer with the number of commits the local source lags
       behind the parent branch
    """
    self._validate()

    cmd = "git status"
    output_directory = self.get_source_directory()
    cmd_params = cmd_exec.CommandParameters(cwd=output_directory)
    status_output = cmd_exec.run_command(cmd, cmd_params)

    commit_count = 0

    # Extract the commit count from lines such as:
    #
    # Your branch is ahead of 'origin/master' by 99 commits.
    #
    # or determine whether git believes we are up to date:
    #
    # Your branch is up to date with 'origin/master'.
    ahead = re.compile(r'.*ahead of \'(.*)\' by (\d+) commit[s]')
    up_to_date = re.compile(r'Your branch is up to date with \'(.*)\'')

    for line in status_output.split('\n'):
      match = ahead.match(line)
      if match:
        commit_count = int(match.group(2))
        log.debug(f"Branch is {commit_count} ahead of branch {match.group(1)}")
        break

      match = up_to_date.match(line)
      if match:
        log.debug(f"Branch {match.group(1)} is up to date")
        break

    return commit_count

  def is_up_to_date(self) -> bool:
    """Determine whether the source tree is up to date.

    Returns:
      a boolean indicating whether the tree is up to date.
    """
    return self.get_revs_behind_parent_branch() == 0

  def list_tags(self) -> List[str]:
    """Enumerate the repository tags and return them in a list.

    Returns:
      a list of tags from the commits
    """
    self._validate()

    cmd = "git tag --list --sort v:refname"
    output_directory = self.get_source_directory()
    cmd_params = cmd_exec.CommandParameters(cwd=output_directory)
    tag_output = cmd_exec.run_command(cmd, cmd_params)

    tag_list = [tag.strip() for tag in tag_output.split('\n') if tag]
    log.debug(f"Repository tags {tag_list}")

    return tag_list

  def get_previous_tag(self, current_tag: str, revisions: int = 1) -> str:
    """Identify a tag a number of revisions behind the current tag.

    Find the current tag among the ones retrieed from the repository and return
    the previous tag

    Args:
      current_tag: the tag for the baseline revision of the source
      revisions: The number of tags in the tree that we skip over, starting from
        the current_tag

    Returns:
      the sought after tag

    Raises:
      SourceTreeError: if the specified tag does not match the tag format
        we expect

    """
    self._validate()

    if not is_tag(current_tag):
      raise SourceTreeError("The tag specified is not the expected format")

    tag_list = self.list_tags()[::-1]

    count_previous_revisions = False
    for tag in tag_list:
      if count_previous_revisions:
        log.debug(f"Walking {revisions} back from {current_tag}")
        revisions -= 1

      if revisions == 0:
        return tag

      if tag == current_tag:
        log.debug(f"Found {tag} in revision list")
        count_previous_revisions = True

    return ''
