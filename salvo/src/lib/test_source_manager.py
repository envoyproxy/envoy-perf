"""
Test source management operations needed for executing benchmarks
"""
import logging
import pytest
from unittest import mock

from src.lib import (source_manager, source_tree)
import api.control_pb2 as proto_control
import api.source_pb2 as proto_source

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
  """Generate a default image configuration for the job control object.

  Args:
    job_control:  The control object in which we insert the image definitions.
  """
  image_config = job_control.images
  image_config.reuse_nh_images = True
  image_config.nighthawk_benchmark_image = \
    "envoyproxy/nighthawk-benchmark-dev:latest"
  image_config.nighthawk_binary_image = \
    "envoyproxy/nighthawk-dev:latest"

  return image_config

def _generate_default_envoy_source(job_control):
  """Add a source repository for Envoy

  Args:
    job_control:  The control object in which we insert the source repository.
  """
  source_repo = job_control.source.add()
  source_repo.identity = source_repo.SRCID_ENVOY
  source_repo.source_path = '/some/random/path/on/disk/envoy'
  source_repo.commit_hash = 'expected_baseline_hash'

@mock.patch("src.lib.cmd_exec.run_command")
def test_get_envoy_hashes_for_benchmark(mock_run_command):
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

  manager = source_manager.SourceManager(job_control)
  hashes = manager.get_envoy_hashes_for_benchmark()

  assert hashes == ['mocked_hash_the_sequel', 'latest']

@mock.patch("src.lib.cmd_exec.run_command")
def test_get_image_hashes_from_disk_source(mock_run_command):
  """
  Verify that we can determine Envoy hashes from source locations
  """
  job_control = proto_control.JobControl(
      remote=False,
      scavenging_benchmark=True
  )

  _generate_default_benchmark_images(job_control)
  _generate_default_envoy_source(job_control)

  mock_run_command.side_effect = _run_command_side_effect

  manager = source_manager.SourceManager(job_control)
  source_repo = manager.get_source_repository(
    proto_source.SourceRepository.SourceIdentity.SRCID_ENVOY
  )
  envoy_source_tree = source_tree.SourceTree(source_repo)

  expected_hashes = [
      'expected_previous_commit_hash',
      'expected_baseline_hash'
  ]

  origin = envoy_source_tree.get_origin()
  assert origin

  previous_hash = manager.get_image_hashes_from_disk_source(
      envoy_source_tree, source_repo.commit_hash
  )

  assert previous_hash == expected_hashes

@mock.patch("src.lib.cmd_exec.run_command")
@mock.patch.object(source_tree.SourceTree, 'copy_source_directory')
def test_determine_envoy_hashes_from_source(mock_copy_source_directory,
                                            mock_run_command):
  """
  Verify that we can determine Envoy hashes from a source repository
  """
  job_control = proto_control.JobControl(
      remote=False,
      scavenging_benchmark=True
  )

  _generate_default_benchmark_images(job_control)
  _generate_default_envoy_source(job_control)

  # Setup mocks
  mock_copy_source_directory.return_value = True
  mock_run_command.side_effect = _run_command_side_effect

  manager = source_manager.SourceManager(job_control)

  hashes = manager.determine_envoy_hashes_from_source()
  expected_hashes = ['mocked_hash_the_sequel', 'mocked_hash']

  assert hashes == expected_hashes

def test_find_all_images_from_specified_tags():
  """Verify that we can parse an image tag and deterimine the previous
  image tag.
  """
  job_control = proto_control.JobControl(
      remote=False,
      scavenging_benchmark=True
  )
  _generate_default_benchmark_images(job_control)

  # Add an envoy image and specify additional versions to test
  job_control.images.envoy_image="envoyproxy/envoy:v1.16.0"

  for index in range(1,4):
    job_control.images.additional_envoy_images.append(
        "envoyproxy/envoy:tag{i}".format(i=index)
    )

  manager = source_manager.SourceManager(job_control)

  tags = manager.find_all_images_from_specified_tags()

  # We test all extra tags first and the specified image tags is always last
  expected_tags = [
      'tag1',
      'tag2',
      'tag3',
      'v1.16.0'
  ]
  assert tags == expected_tags

@mock.patch("src.lib.cmd_exec.run_command")
@mock.patch.object(source_tree.SourceTree, 'copy_source_directory')
def test_find_all_images_from_specified_sources(mock_copy_source_directory,
                                                mock_run_command):
  """Verify that we can deterimine the previous commit hash from a source tree.
  """
  job_control = proto_control.JobControl(
      remote=False,
      scavenging_benchmark=True
  )

  _generate_default_benchmark_images(job_control)
  _generate_default_envoy_source(job_control)

  # Setup mocks
  mock_copy_source_directory.return_value = True
  mock_run_command.side_effect = _run_command_side_effect

  manager = source_manager.SourceManager(job_control)

  hashes = manager.find_all_images_from_specified_sources()
  expected_hashes = [
      'expected_previous_commit_hash',
      'expected_baseline_hash'
  ]
  assert hashes == expected_hashes

@mock.patch("src.lib.cmd_exec.run_command")
@mock.patch.object(source_tree.SourceTree, 'copy_source_directory')
def test_get_envoy_hashes_for_benchmark(mock_copy_source_directory,
                                        mock_run_command):
  """Verify that we can determine the hashes for the baseline and previous
  Envoy Image.
  """
  job_control = proto_control.JobControl(
      remote=False,
      scavenging_benchmark=True
  )

  _generate_default_benchmark_images(job_control)
  _generate_default_envoy_source(job_control)

  # Add an envoy image and specify additional versions to test
  job_control.images.envoy_image="envoyproxy/envoy:v1.16.0"

  for index in range(1,4):
    job_control.images.additional_envoy_images.append(
        "envoyproxy/envoy:tag{i}".format(i=index)
    )

  # Setup mocks
  mock_copy_source_directory.return_value = True
  mock_run_command.side_effect = _run_command_side_effect

  manager = source_manager.SourceManager(job_control)

  hashes = manager.get_envoy_hashes_for_benchmark()

  # Since both a source and image was specified, we benchmark
  # the source at its current and previous commit, as well as
  # the other specified image tags.
  expected_hashes = [
      'tag1',
      'tag2',
      'tag3',
      'v1.16.0',
      'expected_previous_commit_hash',
      'expected_baseline_hash'
  ]
  assert hashes == expected_hashes

@mock.patch("src.lib.cmd_exec.run_command")
@mock.patch.object(source_tree.SourceTree, 'copy_source_directory')
def test_get_image_hashes_from_disk_source(mock_copy_source_directory,
                                           mock_run_command):
  """Verify that we can determine previous hash for a specified commit."""

  job_control = proto_control.JobControl(
      remote=False,
      scavenging_benchmark=True
  )

  _generate_default_benchmark_images(job_control)
  _generate_default_envoy_source(job_control)

  # Setup mocks
  mock_copy_source_directory.return_value = True
  mock_run_command.side_effect = _run_command_side_effect

  manager = source_manager.SourceManager(job_control)
  source_tree = manager.get_source_tree(
      proto_source.SourceRepository.SourceIdentity.SRCID_ENVOY
  )
  hashes = manager.get_image_hashes_from_disk_source(
    source_tree, 'expected_baseline_hash'
  )

  expected_hashes = [
      'expected_previous_commit_hash',
      'expected_baseline_hash'
  ]
  assert hashes == expected_hashes

def test_get_source_tree():
  """Verify that we can return a source otree object.  If no sources
  are specified, we use the known default location from which to get
  the source code.
  """

  job_control = proto_control.JobControl(
      remote=False,
      scavenging_benchmark=True
  )

  manager = source_manager.SourceManager(job_control)

  for source_id in [
       proto_source.SourceRepository.SourceIdentity.SRCID_ENVOY,
       proto_source.SourceRepository.SourceIdentity.SRCID_NIGHTHAWK
  ]:
    source_tree = manager.get_source_tree(source_id)
    assert source_tree.get_identity() == source_id

def test_get_build_options():
  """Verify that we can retrieve specified build options"""
  job_control = proto_control.JobControl(
      remote=False,
      scavenging_benchmark=True
  )

  _generate_default_envoy_source(job_control)
  envoy_source = job_control.source[0]

  expected_options = [ "-c opt", "--jobs 4"]
  for option in expected_options:
    envoy_source.bazel_options.add(parameter=option)

  manager = source_manager.SourceManager(job_control)
  bazel_options = manager.get_build_options(
      proto_source.SourceRepository.SourceIdentity.SRCID_ENVOY
  )
  assert bazel_options
  assert all([option.parameter in expected_options for option in bazel_options])

def test_have_build_options():
  """Verify that we can determine if build options exist"""
  job_control = proto_control.JobControl(
      remote=False,
      scavenging_benchmark=True
  )

  _generate_default_envoy_source(job_control)
  envoy_source = job_control.source[0]

  expected_options = [ "-c opt", "--jobs 4"]
  for option in expected_options:
    envoy_source.bazel_options.add(parameter=option)

  # We construct build options for Envoy.  NightHawk sources
  # will not have any options specified
  manager = source_manager.SourceManager(job_control)
  bazel_options = manager.have_build_options(
      proto_source.SourceRepository.SourceIdentity.SRCID_NIGHTHAWK
  )
  assert not bazel_options

if __name__ == '__main__':
  raise SystemExit(pytest.main(['-s', '-v', __file__]))
