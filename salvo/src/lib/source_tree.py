import re
import logging
import os
import tempfile

import lib.cmd_exec as cmd_exec

log = logging.getLogger(__name__)


class SourceTree(object):

  def __init__(self, **kwargs):
    self._tempdir = tempfile.TemporaryDirectory()

    self._origin = kwargs.get('origin', None)
    self._branch = kwargs.get('branch', None)
    self._hash = kwargs.get('hash', None)
    self._working_dir = kwargs.get('workdir', None)

  def validate(self):
    if self._working_dir is None and self._origin is None:
      raise Exception("No origin is defined or can be deduced from the path")

    # We must have either a path or an origin url defined
    if not self._working_dir and self._origin:
      self._working_dir = self._tempdir.name
      return True

    # We have a working directory on disk and can deduce the origin from it
    if self._working_dir and not self._origin:
      return True

    return False

  def get_origin(self):
    """
        Detect the origin url from where the code is fetched
        """
    self.validate()
    origin_url = self._origin

    cmd = "git remote -v | grep ^origin | grep fetch"
    if origin_url is None:
      kwargs = {'cwd': self._working_dir}
      output = cmd_exec.run_command(cmd, **kwargs)
      match = re.match(r'^origin\s*([\w:@\.\/-]+)\s\(fetch\)$', output)
      if match:
        origin_url = match.group(1)

    return origin_url

  def get_directory(self):
    """
        Return the full path to where the code has been checked out
        """
    self.validate()

    return self._working_dir

  def pull(self):
    """
        Retrieve the code from the repository and indicate whether the operation
        succeeded
        """
    self.validate()

    # Clone into the working directory
    cmd = "git clone {origin} .".format(origin=self._origin)
    kwargs = {'cwd': self._working_dir}

    if not os.path.exists(self._working_dir):
      os.mkdir(self._tempdir.name)

    output = cmd_exec.run_command(cmd, **kwargs)

    expected = 'Cloning into \'.\''
    return expected in output

  def get_head_hash(self):
    """
        Retrieve the hash for the HEAD commit
        """
    self.validate()

    cmd = "git rev-list --no-merges --committer='GitHub <noreply@github.com>' --max-count=1 HEAD"

    kwargs = {'cwd': self._working_dir}
    return cmd_exec.run_command(cmd, **kwargs)

  def get_previous_commit_hash(self, current_commit):
    """
        Return one commit hash before the identified commit
        """
    if current_commit == 'latest':
      current_commit = self.get_head_hash()

    cmd = "git rev-list --no-merges --committer='GitHub <noreply@github.com>'  --max-count=2 {commit}".format(
        commit=current_commit)
    kwargs = {'cwd': self._working_dir}
    hash_list = cmd_exec.run_command(cmd, **kwargs)

    # Check whether we got an error from git
    if 'unknown revision or path not in the working tree.' in hash_list:
      return None

    # Reverse iterate throught the list of hashes, skipping any blank
    # lines that may have trailed the original git output
    for commit_hash in hash_list.split('\n')[::-1]:
      if commit_hash:
        return commit_hash

    return None

  def get_revs_behind_parent_branch(self):
    """
        Determine how many commits the current branch on disk is behind the
        parent branch.  If we are up to date, return zero
        """
    cmd = "git status"
    kwargs = {'cwd': self._working_dir}
    status_output = cmd_exec.run_command(cmd, **kwargs)

    commit_count = 0
    ahead = re.compile(r'.*ahead of \'(.*)\' by (\d+) commit[s]')
    uptodate = re.compile(r'Your branch is up to date with \'(.*)\'')

    for line in status_output.split('\n'):
      match = ahead.match(line)
      if match:
        commit_count = int(match.group(2))
        log.debug(f"Branch is {commit_count} ahead of branch {match.group(1)}")
        break

      match = uptodate.match(line)
      if match:
        log.debug(f"Branch {match.group(1)} is up to date")
        break

    return commit_count

  def is_up_to_date(self):
    """
        Convenience function that returns a boolean indicating whether the tree is up to date.
        """
    return self.get_revs_behind_parent_branch() == 0
