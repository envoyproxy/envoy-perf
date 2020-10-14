"""
Test git operations needed for executing benchmarks
"""
import site
import shlex
from unittest import mock
import pytest

site.addsitedir("src")

import lib.source_tree as source_tree


def test_git_object():
  """
  Verify that we throw an exception if not all required data is present
  """
  git = source_tree.SourceTree()

  with pytest.raises(Exception) as pull_exception:
    git.validate()

  assert "No origin is defined or can be" in str(pull_exception.value)


def test_git_with_origin():
  """
  Verify that at a minimum, we can work with a remote origin url specified
  """
  kwargs = {'origin': 'somewhere_in_github'}
  git = source_tree.SourceTree(**kwargs)

  assert git.validate()


def test_git_with_local_workdir():
  """
  Verify that we can work with a source location on disk

  If the directory is not a real repository, then subsequent functions are
  expected to fail.  They will be reported accordingly.
  """
  kwargs = {'workdir': '/tmp'}
  git = source_tree.SourceTree(**kwargs)

  assert git.validate()


def test_get_origin_ssh():
  """
  Verify that we can determine the origin for a local repository.  We will
  use this to clone the repository when running in a remote context

  In this instance the repo was cloned via ssh
  """
  remote_string = 'origin  git@github.com:username/reponame.git (fetch)'
  gitcmd = "git remote -v | grep ^origin | grep fetch"
  kwargs = {'workdir': '/tmp', 'name': "required_directory_name"}
  git = source_tree.SourceTree(**kwargs)

  assert git.validate()
  with mock.patch('subprocess.check_output',
                  mock.MagicMock(return_value=remote_string)) as magic_mock:
    origin_url = git.get_origin()
    magic_mock.assert_called_once_with(shlex.split(gitcmd), cwd=kwargs['workdir'], stderr=mock.ANY)

    assert origin_url == 'git@github.com:username/reponame.git'


def test_get_origin_https():
  """
  Verify that we can determine the origin for a local repository.  We will
  use this to clone the repository when running in a remote context

  In this instance the repo was cloned via https
  """
  remote_string = 'origin	https://github.com/aws/aws-app-mesh-examples.git (fetch)'
  gitcmd = "git remote -v | grep ^origin | grep fetch"

  kwargs = {'workdir': '/tmp'}
  git = source_tree.SourceTree(**kwargs)

  assert git.validate()
  with mock.patch('subprocess.check_output',
                  mock.MagicMock(return_value=remote_string)) as magic_mock:
    origin_url = git.get_origin()
    magic_mock.assert_called_once_with(shlex.split(gitcmd), cwd=kwargs['workdir'], stderr=mock.ANY)

    assert origin_url == 'https://github.com/aws/aws-app-mesh-examples.git'


def test_git_pull():
  """
  Verify that we can clone a repository and ensure that the process completed
  without errors
  """
  origin = 'https://github.com/someawesomeproject/repo.git'
  kwargs = {'origin': origin, 'workdir': '/tmp'}
  git = source_tree.SourceTree(**kwargs)

  gitcmd = 'git clone {source} .'.format(source=origin)
  git_output = b"Cloning into '.'..."

  with mock.patch('subprocess.check_output', mock.MagicMock(return_value=git_output)) as magic_mock:
    result = git.pull()
    magic_mock.assert_called_once_with(shlex.split(gitcmd), cwd=kwargs['workdir'], stderr=mock.ANY)

    origin_url = git.get_origin()
    assert origin_url == origin
    assert result


def test_git_pull_failure():
  """
  Verify that we can clone a repository and detect an incomplete operation
  """
  origin = 'https://github.com/someawesomeproject/repo.git'
  kwargs = {'origin': origin, 'workdir': '/tmp'}
  git = source_tree.SourceTree(**kwargs)

  gitcmd = 'git clone {source} .'.format(source=origin)
  git_output = b"Some unexpected output"

  with mock.patch('subprocess.check_output', mock.MagicMock(return_value=git_output)) as magic_mock:
    result = git.pull()
    magic_mock.assert_called_once_with(shlex.split(gitcmd), cwd=kwargs['workdir'], stderr=mock.ANY)

    origin_url = git.get_origin()
    assert origin_url == origin
    assert not result


def test_retrieve_head_hash():
  """
  Verify that we can determine the hash for the head commit
  """
  origin = 'https://github.com/someawesomeproject/repo.git'
  kwargs = {'origin': origin, 'workdir': '/tmp'}
  git = source_tree.SourceTree(**kwargs)

  gitcmd = "git rev-list --no-merges --committer='GitHub <noreply@github.com>' --max-count=1 HEAD"
  git_output = b"some_long_hex_string_that_is_the_hash"

  with mock.patch('subprocess.check_output', mock.MagicMock(return_value=git_output)) as magic_mock:
    hash_string = git.get_head_hash()
    magic_mock.assert_called_once_with(shlex.split(gitcmd), cwd=kwargs['workdir'], stderr=mock.ANY)

    assert hash_string == git_output.decode('utf-8')


def test_get_previous_commit():
  """
  Verify that we can identify one commit prior to a specified hash.
  """
  origin = 'https://github.com/someawesomeproject/repo.git'
  kwargs = {'origin': origin, 'workdir': '/tmp'}
  git = source_tree.SourceTree(**kwargs)

  commit_hash = '5f6990f981ec89fd4e7ffd6c1fccd3a4f2cbeee1'
  gitcmd = "git rev-list --no-merges --committer='GitHub <noreply@github.com>' --max-count=2 {hash}".format(
      hash=commit_hash)
  git_output = b"""5f6990f981ec89fd4e7ffd6c1fccd3a4f2cbeee1
81b1d4859bc84a656fe72482e923f3a7fcc498fa
"""

  with mock.patch('subprocess.check_output', mock.MagicMock(return_value=git_output)) as magic_mock:
    hash_string = git.get_previous_commit_hash(commit_hash)
    magic_mock.assert_called_once_with(shlex.split(gitcmd), cwd=kwargs['workdir'], stderr=mock.ANY)

    assert hash_string == '81b1d4859bc84a656fe72482e923f3a7fcc498fa'


def test_get_previous_commit_fail():
  """
  Verify that we can identify a failure when attempting to manage commit hashes
  """
  origin = 'https://github.com/someawesomeproject/repo.git'
  kwargs = {'origin': origin, 'workdir': '/tmp'}
  git = source_tree.SourceTree(**kwargs)

  commit_hash = 'invalid_hash_reference'
  gitcmd = "git rev-list --no-merges --committer='GitHub <noreply@github.com>' --max-count=2 {hash}".format(
      hash=commit_hash)
  git_output = b"""fatal: ambiguous argument 'invalid_hash_reference_': unknown revision or path not in the working tree.
Use '--' to separate paths from revisions, like this:
'git <command> [<revision>...] -- [<file>...]'
"""

  with mock.patch('subprocess.check_output', mock.MagicMock(return_value=git_output)) as magic_mock:
    hash_string = git.get_previous_commit_hash(commit_hash)
    magic_mock.assert_called_once_with(shlex.split(gitcmd), cwd=kwargs['workdir'], stderr=mock.ANY)

    assert hash_string is None


def test_parent_branch_ahead():
  """
  Verify that we can determine how many commits beind the local source tree
  lags behind the remote repository
  """

  origin = 'https://github.com/someawesomeproject/repo.git'
  kwargs = {'origin': origin, 'workdir': '/tmp'}
  git = source_tree.SourceTree(**kwargs)

  gitcmd = 'git status'
  git_output = b"""On branch master
Your branch is ahead of 'origin/master' by 99 commits.
  (use "git push" to publish your local commits)

nothing to commit, working tree clean
"""
  with mock.patch('subprocess.check_output', mock.MagicMock(return_value=git_output)) as magic_mock:
    commit_count = git.get_revs_behind_parent_branch()
    magic_mock.assert_called_once_with(shlex.split(gitcmd), cwd=kwargs['workdir'], stderr=mock.ANY)
    assert isinstance(commit_count, int)
    assert commit_count == 99


def test_parent_branch_up_to_date():
  """
  Verify that we can determine how many commits beind the local source tree
  lags behind the remote repository
  """

  origin = 'https://github.com/someawesomeproject/repo.git'
  kwargs = {'origin': origin, 'workdir': '/tmp'}
  git = source_tree.SourceTree(**kwargs)

  gitcmd = 'git status'
  git_output = b"""On branch master
Your branch is up to date with 'origin/master'.

Changes not staged for commit:
  (use "git add <file>..." to update what will be committed)
  (use "git checkout -- <file>..." to discard changes in working directory)
"""
  with mock.patch('subprocess.check_output', mock.MagicMock(return_value=git_output)) as magic_mock:
    commit_count = git.get_revs_behind_parent_branch()
    magic_mock.assert_called_once_with(shlex.split(gitcmd), cwd=kwargs['workdir'], stderr=mock.ANY)
    assert isinstance(commit_count, int)
    assert commit_count == 0


def test_branch_up_to_date():
  """
  Verify that we can determine how many commits beind the local source tree
  lags behind the remote repository
  """

  origin = 'https://github.com/someawesomeproject/repo.git'
  kwargs = {'origin': origin, 'workdir': '/tmp'}
  git = source_tree.SourceTree(**kwargs)

  with mock.patch('lib.source_tree.SourceTree.get_revs_behind_parent_branch',
                  mock.MagicMock(return_value=0)) as magic_mock:
    up_to_date = git.is_up_to_date()
    magic_mock.assert_called_once()
    assert up_to_date


if __name__ == '__main__':
  raise SystemExit(pytest.main(['-s', '-v', __file__]))
