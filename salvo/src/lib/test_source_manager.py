"""
Test source management operations needed for executing benchmarks
"""
import logging
import pytest
from unittest import mock

from src.lib import (source_manager, source_tree)
import api.control_pb2 as proto_control

logging.basicConfig(level=logging.DEBUG)
log = logging.getLogger(__name__)

def _verify_cwd(**kwargs):
  """Verify cwd is defined in kwargs."""

  assert 'cwd' in kwargs
  assert kwargs['cwd']

def _run_command_side_effect(*args):
  """Adjust the check_output output so that we can respond differently to
  input arguments.

  Args:
    args: the list of arguments received by the mocked function
  """
  _verify_cwd(**args[1]._asdict())

  # First call clone the repository
  if args[0] == \
      'git clone https://github.com/envoyproxy/envoy.git .':
    return 'Mocked output: Cloning into \'.\'...'

  # Second call gets the hash for the HEAD commit
  elif args[0] == ("git rev-list --no-merges "
                   "--committer=\'GitHub <noreply@github.com>\' "
                   "--max-count=1 HEAD"):
    return 'mocked_hash'

  # Third call gets the 2 commits in the tree starting with a specific hash
  elif args[0] == ("git rev-list --no-merges "
                   "--committer=\'GitHub <noreply@github.com>\' "
                   "--max-count=2 mocked_hash"):
    return "mocked_hash\nmocked_hash_the_sequel"

  elif args[0] == "git status":
    return "Your branch is up to date with \'some_random_branch\'"

  elif args[0] == 'git remote -v':
    return 'origin  git@github.com:username/reponame.git (fetch)'

  elif args[0] == ("git rev-list --no-merges "
                   "--committer=\'GitHub <noreply@github.com>\' "
                   "--max-count=2 expected_baseline_hash"):
    return ('expected_baseline_hash\n'
            'expected_previous_commit_hash')

  elif args[0] == 'git clone git@github.com:username/reponame.git .':
    return 'Cloning into \'.\''

  raise Exception(f"Unhandled input in side effect: {args}")

def _generate_default_benchmark_images(job_control):
  """Generate a default image configuration for the job control object."""

  image_config = job_control.images
  image_config.reuse_nh_images = True
  image_config.nighthawk_benchmark_image = \
    "envoyproxy/nighthawk-benchmark-dev:latest"
  image_config.nighthawk_binary_image = \
    "envoyproxy/nighthawk-dev:latest"

  return image_config

@mock.patch("src.lib.cmd_exec.run_command")
def test_get_envoy_images_for_benchmark(mock_run_command):
  """Verify that we can determine the current and previous image
     tags from a minimal job control object.
  """

  job_control = proto_control.JobControl(
      remote=False,
      scavenging_benchmark=True
  )

  image_config = _generate_default_benchmark_images(job_control)
  image_config.envoy_image = "envoyproxy/envoy-dev:latest"

  mock_run_command.side_effect = _run_command_side_effect

  src_mgr = source_manager.SourceManager(job_control)
  hashes = src_mgr.get_envoy_hashes_for_benchmark()

  assert hashes == ['mocked_hash_the_sequel', 'latest']

@mock.patch("src.lib.cmd_exec.run_command")
def test_previous_hash_with_disk_files(mock_run_command):
  """
  Verify that we can determine Envoy images from source locations
  """
  job_control = proto_control.JobControl(
      remote=False,
      scavenging_benchmark=True
  )

  _generate_default_benchmark_images(job_control)

  source_repo = job_control.source.add()
  source_repo.identity = source_repo.SRCID_ENVOY
  source_repo.source_path = '/some/random/path/on/disk/envoy'
  source_repo.commit_hash = 'expected_baseline_hash'

  mock_run_command.side_effect = _run_command_side_effect

  src_mgr = source_manager.SourceManager(job_control)
  envoy_source_tree = source_tree.SourceTree(source_repo)

  expected_hashes = [
      'expected_previous_commit_hash',
      'expected_baseline_hash'
  ]

  origin = envoy_source_tree.get_origin()
  assert origin

  previous_hash = src_mgr.get_image_hashes_from_disk_source(
      envoy_source_tree, source_repo.commit_hash
  )

  assert previous_hash == expected_hashes


if __name__ == '__main__':
  raise SystemExit(pytest.main(['-s', '-v', __file__]))
