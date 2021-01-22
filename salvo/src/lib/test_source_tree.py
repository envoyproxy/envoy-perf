"""
Test source_tree operations needed for executing benchmarks
"""
from unittest import mock
import pytest
import logging
import subprocess

from src.lib import (cmd_exec, source_tree)
import api.source_pb2 as proto_source

logging.basicConfig(level=logging.DEBUG)
log = logging.getLogger(__name__)

def test_source_tree_object():
  """Verify that we throw an exception if not all required data is present."""
  source = source_tree.SourceTree(proto_source.SourceRepository())

  with pytest.raises(source_tree.SourceTreeError) as pull_exception:
    source.get_head_hash()

  assert "No origin is defined or can be" in str(pull_exception.value)


def test_git_with_origin():
  """Verify that at a minimum, we can work with a remote origin url
     specified.
  """
  source_repository = proto_source.SourceRepository(
      source_url='somewhere_in_github'
  )
  source = source_tree.SourceTree(source_repository)

  assert source.get_origin()


def test_source_tree_with_local_workdir():
  """Verify that we can work with a source location on disk."""
  source_repository = proto_source.SourceRepository(
      source_path='/some_source_path'
  )
  source = source_tree.SourceTree(source_repository)

  remote_string = 'origin  git@github.com:username/reponame.git (fetch)'

  with mock.patch('src.lib.cmd_exec.run_command',
                  mock.MagicMock(return_value=remote_string)) as magic_mock:
    origin = source.get_origin()
    assert origin == "git@github.com:username/reponame.git"

    cmd_params = cmd_exec.CommandParameters(cwd='/some_source_path')
    magic_mock.assert_called_once_with("git remote -v", cmd_params)

def test_get_origin_ssh():
  """Verify that we can determine the origin for a local repository.

  In this instance the repo was cloned via ssh.
  """
  remote_string = 'origin  git@github.com:username/reponame.git (fetch)'
  git_cmd = "git remote -v"

  source_repository = proto_source.SourceRepository(
      source_path='/tmp'
  )
  source = source_tree.SourceTree(source_repository)

  with mock.patch('src.lib.cmd_exec.run_command',
                  mock.MagicMock(return_value=remote_string)) as magic_mock:
    origin_url = source.get_origin()

    cmd_params = cmd_exec.CommandParameters(cwd='/tmp')
    magic_mock.assert_called_once_with(git_cmd, cmd_params)

    assert origin_url == 'git@github.com:username/reponame.git'

def test_get_origin_https():
  """Verify that we can determine the origin for a local repository.

  In this instance the repo was cloned via https
  """
  remote_string = \
      'origin	https://github.com/aws/aws-app-mesh-examples.git (fetch)'
  git_cmd = "git remote -v"

  source_repository = proto_source.SourceRepository(
      source_path='/tmp'
  )
  source = source_tree.SourceTree(source_repository)

  with mock.patch('src.lib.cmd_exec.run_command',
                  mock.MagicMock(return_value=remote_string)) as magic_mock:
    origin_url = source.get_origin()
    cmd_params = cmd_exec.CommandParameters(cwd='/tmp')
    magic_mock.assert_called_once_with(git_cmd, cmd_params)

    assert origin_url == 'https://github.com/aws/aws-app-mesh-examples.git'

def _generate_source_tree_from_origin(origin):
  """Build a source tree from a remote url."""
  source_repository = proto_source.SourceRepository(
      source_path='/tmp',
      source_url=origin
  )
  return source_tree.SourceTree(source_repository)

def mock_run_command_side_effect(*function_args):
  """Mock run_command side effect for checkout operation.

  Args:
    function_args:  This is a list of arguments passed to the mocked
      function.  In this case the first entry is the shell command being
      executed and the second parameter is the cmd_exec.CommandParameters
      tuple containing the working directory.

      We are most interested in the contents of the first entry.
  """
  if function_args[0] == 'git status':
    raise subprocess.CalledProcessError(1, "msg")
  elif function_args[0] == 'git remote -v':
    return \
        ("origin  https://www.github.com/_some_random_repo_/repo.git (fetch)\n"
         "origin  https://www.github.com/_some_random_repo_/repo.git (push)")
  elif function_args[0] == \
      'git clone https://www.github.com/_some_random_repo_/repo.git .':
    return "Cloning into \'.\'"

  elif function_args[0] == \
      "git clone https://github.com/_some_random_repo_/repo.git .":
    return "Cloning into \'.\'"

  elif function_args[0] == (
      "git rev-list --no-merges "
      "--committer=\'GitHub <noreply@github.com>\' "
      "--max-count=2 fake_commit_hash_1"):
    return ("fake_commit_hash_1\n"
            "fake_commit_hash_2\n")

  elif function_args[0] == (
      "git rev-list --no-merges "
      "--committer=\'GitHub <noreply@github.com>\' "
      "--max-count=2 invalid_hash_reference"):
    git_output = """fatal: ambiguous argument 'invalid_hash_reference': unknown revision or path not in the working tree.
Use '--' to separate paths from revisions, like this:
'git <command> [<revision>...] -- [<file>...]'
"""
    return git_output

  elif function_args[0] == "git status":
    return "Your branch is up to date with \'some_random_branch\'"

  raise NotImplementedError(f"Unhandled arguments: {function_args}")

@mock.patch("src.lib.cmd_exec.run_command")
def test_source_tree_pull(mock_run_command):
  """Verify that we can clone a repository ensuring that the process completed
     without errors.
  """
  origin = 'https://www.github.com/_some_random_repo_/repo.git'

  source = _generate_source_tree_from_origin(origin)
  mock_run_command.side_effect = mock_run_command_side_effect

  result = source.pull()
  assert result

  git_status = 'git status'
  git_clone = 'git clone https://www.github.com/_some_random_repo_/repo.git .'
  cmd_params = cmd_exec.CommandParameters(cwd=mock.ANY)

  calls = [
      mock.call(git_status, cmd_params),
      mock.call(git_clone, cmd_params)
  ]
  mock_run_command.assert_has_calls(calls)

  origin_url = source.get_origin()
  assert origin_url == origin

def mock_run_command_side_effect_failure(*function_args):
  """Mock run_command side effect for a failed checkout operation.

  Args:
    function_args:  This is a list of arguments passed to the mocked
      function.  In this case the first entry is the shell command being
      executed and the second parameter is the cmd_exec.CommandParameters
      tuple containing the working directory.

      We are most interested in the contents of the first entry.
  """

  if function_args[0] == 'git status':
    raise subprocess.CalledProcessError(1, "msg")
  elif function_args[0] == 'git remote -v':
    return \
        ("origin  https://github.com/someawesomeproject/repo.git (fetch)\n"
         "origin  https://github.com/someawesomeproject/repo.git (push)")
  elif function_args[0] == \
      'git clone https://github.com/someawesomeproject/repo.git .':
    return "Something failed during a clone...'"

  raise NotImplementedError(f"Unhandled arguments: {function_args}")

@mock.patch("src.lib.cmd_exec.run_command")
def test_source_tree_pull_failure(mock_run_command):
  """Verify that we can clone a repository and detect an incomplete
     operation.
  """
  origin = 'https://github.com/someawesomeproject/repo.git'
  source = _generate_source_tree_from_origin(origin)

  mock_run_command.side_effect = mock_run_command_side_effect_failure

  git_status = 'git status'
  git_clone = 'git clone https://github.com/someawesomeproject/repo.git .'
  cmd_params = cmd_exec.CommandParameters(cwd=mock.ANY)

  result = source.pull()
  assert not result

  calls = [
      mock.call(git_status, cmd_params),
      mock.call(git_clone, cmd_params)
  ]
  mock_run_command.assert_has_calls(calls)

  assert source.get_origin() == origin

def test_retrieve_head_hash():
  """Verify that we can determine the hash for the head commit."""

  origin = 'https://github.com/someawesomeproject/repo.git'
  source = _generate_source_tree_from_origin(origin)

  git_cmd = ("git rev-list --no-merges --committer='GitHub <noreply@github.com>'"
            " --max-count=1 HEAD")
  git_output = "some_long_hex_string_that_is_the_hash"

  with mock.patch('src.lib.cmd_exec.run_command',
                  mock.MagicMock(return_value=git_output)) as magic_mock:
    hash_string = source.get_head_hash()
    cmd_params = cmd_exec.CommandParameters(cwd=mock.ANY)
    magic_mock.assert_called_once_with(git_cmd, cmd_params)

    assert hash_string == git_output

@mock.patch('src.lib.cmd_exec.run_command')
def test_get_previous_commit(mock_check_output):
  """
    Verify that we can identify one commit prior to a specified hash.
    """
  origin = 'https://github.com/_some_random_repo_/repo.git'
  source = _generate_source_tree_from_origin(origin)

  commit_hash = 'fake_commit_hash_1'

  mock_check_output.return_value = 'fake_commit_hash_2'
  hash_string = source.get_previous_commit_hash(commit_hash)
  assert hash_string == 'fake_commit_hash_2'

@mock.patch('src.lib.cmd_exec.run_command')
def test_get_previous_commit_fail(mock_check_output):
  """Verify that we can identify a failure when attempting to manage commit
     hashes.
  """
  origin = 'https://github.com/_some_random_repo_/repo.git'
  source = _generate_source_tree_from_origin(origin)

  commit_hash = 'invalid_hash_reference'

  mock_check_output.side_effect = mock_run_command_side_effect

  with pytest.raises(source_tree.SourceTreeError) as source_error:
    source.get_previous_commit_hash(commit_hash)

  assert "fatal: ambiguous argument \'invalid_hash_reference\'" in \
      str(source_error.value)

def test_parent_branch_ahead():
  """Verify that we can determine how many commits beind the local source tree
     lags behind the remote repository.
  """
  origin = 'https://github.com/someawesomeproject/repo.git'
  st = _generate_source_tree_from_origin(origin)

  git_cmd = 'git status'
  git_output = """On branch master
Your branch is ahead of 'origin/master' by 99 commits.
  (use "git push" to publish your local commits)

nothing to commit, working tree clean
"""
  with mock.patch('src.lib.cmd_exec.run_command',
                  mock.MagicMock(return_value=git_output)) as magic_mock:
    commit_count = st.get_revs_behind_parent_branch()
    cmd_params = cmd_exec.CommandParameters(cwd=mock.ANY)
    magic_mock.assert_called_once_with(git_cmd, cmd_params)

    assert isinstance(commit_count, int)
    assert commit_count == 99

def test_parent_branch_up_to_date():
  """Verify that we can determine how many commits beind the local source tree
     lags behind the remote repository.
  """
  origin = 'https://github.com/someawesomeproject/repo.git'
  source = _generate_source_tree_from_origin(origin)

  git_cmd = 'git status'
  git_output = """On branch master
Your branch is up to date with 'origin/master'.

Changes not staged for commit:
  (use "git add <file>..." to update what will be committed)
  (use "git checkout -- <file>..." to discard changes in working directory)
"""
  with mock.patch('src.lib.cmd_exec.run_command',
                  mock.MagicMock(return_value=git_output)) as magic_mock:
    commit_count = source.get_revs_behind_parent_branch()
    cmd_params = cmd_exec.CommandParameters(cwd=mock.ANY)
    magic_mock.assert_called_once_with(git_cmd, cmd_params)

    assert isinstance(commit_count, int)
    assert commit_count == 0

def test_branch_up_to_date():
  """Verify that we can determine a source tree is up to date."""

  origin = 'https://github.com/someawesomeproject/repo.git'
  source = _generate_source_tree_from_origin(origin)

  with mock.patch(
      'src.lib.source_tree.SourceTree.get_revs_behind_parent_branch',
      mock.MagicMock(return_value=0)) as magic_mock:
    up_to_date = source.is_up_to_date()
    magic_mock.assert_called_once()
    assert up_to_date

def test_list_tags():
  """Verify that we can list tags from a repository."""

  GIT_TAG_LIST = """
v1.15.2
v1.16.0
"""

  origin = 'https://github.com/someawesomeproject/repo.git'
  source = _generate_source_tree_from_origin(origin)

  git_cmd = "git tag --list --sort v:refname"
  with mock.patch('src.lib.cmd_exec.run_command',
                  mock.MagicMock(return_value=GIT_TAG_LIST)) as magic_mock:

    tags_list = source.list_tags()
    expected_tags_list = [
        tag for tag in GIT_TAG_LIST.split('\n') if tag
    ]

    cmd_params = cmd_exec.CommandParameters(cwd=mock.ANY)
    magic_mock.assert_called_once_with(git_cmd, cmd_params)

    assert tags_list
    assert tags_list == expected_tags_list

def test_is_tag():
  """Verify that we can detect a hash and a git tag."""
  commit_hash = 'obviously_not_a_tag'
  tag_string = 'v1.15.1'

  assert not source_tree.is_tag(commit_hash)
  assert source_tree.is_tag(tag_string)

def test_get_previous_tag():
  """Verify that we can identify the previous tag for a given release."""

  GIT_TAG_LIST = """
v1.15.2
v1.16.0
"""

  origin = 'https://github.com/someawesomeproject/repo.git'
  source = _generate_source_tree_from_origin(origin)

  current_tag = 'v1.16.0'
  previous_tag = 'v1.15.2'

  git_cmd = "git tag --list --sort v:refname"

  with mock.patch('src.lib.cmd_exec.run_command',
                  mock.MagicMock(return_value=GIT_TAG_LIST)) as magic_mock:

    previous_tag = source.get_previous_tag(current_tag)
    cmd_params = cmd_exec.CommandParameters(cwd=mock.ANY)
    magic_mock.assert_called_once_with(git_cmd, cmd_params)

    assert previous_tag == previous_tag

def test_get_previous_n_tag():
  """Verify that we can identify the previous tag for a given release."""

  GIT_TAG_LIST = """
v1.14.5
v1.15.0
v1.15.1
v1.15.2
v1.16.0
"""
  origin = 'https://github.com/someawesomeproject/repo.git'
  source = _generate_source_tree_from_origin(origin)

  current_tag = 'v1.16.0'
  previous_tag = 'v1.14.5'

  git_cmd = "git tag --list --sort v:refname"

  with mock.patch('src.lib.cmd_exec.run_command',
                  mock.MagicMock(return_value=GIT_TAG_LIST)) as magic_mock:

    previous_tag = source.get_previous_tag(current_tag, revisions=4)

    cmd_params = cmd_exec.CommandParameters(cwd=mock.ANY)
    magic_mock.assert_called_once_with(git_cmd, cmd_params)

    assert previous_tag == previous_tag

def test_source_tree_with_disk_files():
  """Verify that we can get hash data from a source tree on disk."""

  source = source_tree.SourceTree(proto_source.SourceRepository(
      identity=proto_source.SourceRepository.SRCID_ENVOY,
      source_path='/tmp',
      commit_hash='fake_commit_hash'
  ))
  git_output = 'origin  git@github.com:username/reponame.git (fetch)'
  git_cmd = "git remote -v"

  with mock.patch('src.lib.cmd_exec.run_command',
                  mock.MagicMock(return_value=git_output)) as magic_mock:

    origin = source.get_origin()
    assert origin

    cmd_params = cmd_exec.CommandParameters(cwd='/tmp')
    magic_mock.assert_called_once_with(git_cmd, cmd_params)


if __name__ == '__main__':
  raise SystemExit(pytest.main(['-s', '-v', __file__]))
