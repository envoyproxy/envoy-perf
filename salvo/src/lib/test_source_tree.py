"""
Test source_tree operations needed for executing benchmarks
"""
from unittest import mock
import pytest
import logging
import subprocess

from src.lib import (cmd_exec, source_tree)
import api.source_pb2 as proto_source

log = logging.getLogger(__name__)

def test_source_tree_object():
  """Verify that we throw an exception if not all required data is present."""
  pass

def test_git_with_origin():
  """Verify that at a minimum, we can work with a remote origin url
     specified.
  """
  pass

def test_source_tree_with_local_workdir():
  """Verify that we can work with a source location on disk."""
  pass

def test_get_origin_ssh():
  """Verify that we can determine the origin for a local repository.

  In this instance the repo was cloned via ssh.
  """
  pass

def test_get_origin_https():
  """Verify that we can determine the origin for a local repository.

  In this instance the repo was cloned via https
  """
  pass

def _generate_source_tree_from_origin(origin):
  """Build a source tree from a remote url."""
  pass

def mock_run_command_side_effect(*args):
  """Mock run_command side effect for checkout operation."""
  pass

@mock.patch("src.lib.cmd_exec.run_command")
def test_source_tree_pull(mock_run_command):
  """Verify that we can clone a repository ensuring that the process completed
     without errors.
  """
  pass

def mock_run_command_side_effect_failure(*args):
  """Mock run_command side effect for checkout operation."""
  pass

@mock.patch("src.lib.cmd_exec.run_command")
def test_source_tree_pull_failure(mock_run_command):
  """Verify that we can clone a repository and detect an incomplete
     operation.
  """
  pass

def test_retrieve_head_hash():
  """Verify that we can determine the hash for the head commit."""
  pass

def _check_output_side_effect(*args):
  """Respond to the mocked function call with the correct output.

  Args:
    args: the arguments supplied to the mock.  The first argument is the
      command being executed.

    kwargs: the keyword arguments supplied to the mock. In this case
      the 'cwd' (working directory) is the one keyword that should always
      be present
  """
  pass

@mock.patch('src.lib.cmd_exec.run_command')
def test_get_previous_commit(mock_check_output):
  """Verify that we can identify one commit prior to a specified hash. """
  pass

def _check_output_side_effect_fail(*args):
  """Respond to the mocked function call with the correct output.

  Args:
    args: the arguments supplied to the mock.  The first argument is the
      command being executed.
  """
  pass

@mock.patch('src.lib.cmd_exec.run_command')
def test_get_previous_commit_fail(mock_check_output):
  """Verify that we can identify a failure when attempting to manage commit
     hashes.
  """
  pass

def test_parent_branch_ahead():
  """Verify that we can determine how many commits beind the local source tree
     lags behind the remote repository.
  """
  pass

def test_parent_branch_up_to_date():
  """Verify that we can determine how many commits beind the local source tree
     lags behind the remote repository.
  """
  pass

def test_branch_up_to_date():
  """Verify that we can determine a source tree is up to date."""
  pass

def test_list_tags():
  """Verify that we can list tags from a repository."""
  pass

def test_is_tag():
  """Verify that we can detect a hash and a git tag."""
  pass

def test_get_previous_tag():
  """Verify that we can identify the previous tag for a given release."""
  pass

def test_get_previous_n_tag():
  """Verify that we can identify the previous tag for a given release."""
  pass

def test_source_tree_with_disk_files():
  """Verify that we can get hash data from a source tree on disk."""
  pass

if __name__ == '__main__':
  raise SystemExit(pytest.main(['-s', '-v', __file__]))
