"""This module contains methods for managing a source tree"""

import logging
import os
import re
from subprocess import CalledProcessError

import src.lib.cmd_exec as cmd_exec
import src.lib.constants as constants

import api.source_pb2 as proto_source

log = logging.getLogger(__name__)


TAG_REGEX = r'^v\d\.\d+\.\d+'

class SourceTreeException(Exception):
  """Raised if we encounter a condition from which we cannot recover, when
     manipulating SourceTree objects.
  """

def is_tag(image_tag: str) -> bool:
  """Determine whether a an image tag is a commit hash or a version tag."""
  match = re.match(TAG_REGEX, image_tag)
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
    self._tempdir = fileops.get_random_dir(constants.SALVO_TMP)

    self._source_repo = source_repo
    self._source_url = source_repo.source_url
    self._branch = source_repo.branch
    self._commit_hash = source_repo.commit_hash
    self._source_path = source_repo.source_path

  def __repr__(self) -> str:
    """Return a string representation of this class."""
    return '{name}: Origin: [{origin}] Branch: [{branch}] Hash: [{hash}] \
      Workdir [{dir}]'.format(
          name=type(self).__name__,
          origin=self._source_url,
          branch=self._branch,
          hash=self._commit_hash,
          dir=self._source_path)

  def _validate(self) -> bool:
    """Verify that we have enough data to work with the source tree.

    Returns:
      a bool indicating that we have a source path on disk or a url from
        which to pull the source.

    Raises:
      SourceTreeException: if no path or url is specified for the class to
        operate.
    """

    if all([not self._source_path, not self._source_url]):
      raise SourceTreeException(
          "No origin is defined or can be deduced from the path")

    # We must have either a path or an origin url defined
    if not self._source_path and self._source_url:
      log.debug(f"No source path.  Using {self._tempdir} for future clone")

      if not os.path.exists(self._tempdir):
        os.mkdir(self._tempdir)

      self._source_path = self._tempdir
      return True

    # We have a working directory on disk and can deduce the origin from it
    if self._source_path and not self._source_url:
      return True

    return False

  def get_source_identity(self) -> \
      proto_source.SourceRepository.SourceIdentity.SRCID_NIGHTHAWK:
    """Returns the identity of the source tree being managed."""
    return self._source_repo.identity

  def get_origin(self) -> str:
    """Detect the origin url from where the code is fetched.

    Returns:
      A string showing the origin url for the source tree.  This needed most
        for remote execution where we do not ship the entire source tree
        remotely.  We will attempt to generate a patch between the origin
        HEAD and the local HEAD.  This diff is applied to the source in the
        remote context.
    """
    pass

  def get_directory(self) -> str:
    """Return the full path where the code has been checked out.

    Returns:
      a string containing the disk path to the source.
    """
    pass

  def pull(self) -> bool:
    """Retrieve the code from the repository.

    Uses git to clone the source into a working directory that has read/write
    permissions by salvo

    Returns:
      a boolean indicating whether the operation was successful
    """
    pass

  def checkout_commit_hash(self) -> bool:
    """Checks out the specified commit hash in the source tree

    Returns:
      a boolean indicating whether the operation was successful
    """
    pass

  def get_head_hash(self) -> str:
    """Retrieve the hash for the HEAD commit.

    Returns:
      a string containing the hash corresponding to commit at the HEAD of the
        tree.
    """
    pass

  def get_previous_commit_hash(self, current_commit: str,
                               revisions: int = 2) -> str:
    """Return the specified number of commits behind the current commit hash.

    Args:
      current_commit: The current hash from which we are starting the search
      revisions: The number of commits in the tree that we skip over, starting
        from the current_commit

    Returns:
      a string with the discovered commit hash
    """
    pass

  def get_revs_behind_parent_branch(self) -> int:
    """Get the number of commits behind the parent branch.

    Determine how many commits the current branch on disk is behind the
    parent branch.  If we are up to date, return zero

    Returns:
      an integer with the number of commits the local source lags
       behind the parent branch
    """
    pass

  def is_up_to_date(self) -> bool:
    """Determine whether the source tree is up to date.

    Returns:
      a boolean indicating whether the tree is up to date.
    """
    pass

  def list_tags(self) -> list:
    """Enumerate the repository tags and return them in a list.

    Returns:
      a list of tags from the commits
    """
    pass

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
      SourceTreeException: if the specified tag does not match the tag format
        we expect

    """
    pass
