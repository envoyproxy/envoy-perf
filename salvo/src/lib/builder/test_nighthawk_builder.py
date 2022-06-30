"""Test envoy building operations."""
import pytest
from unittest import mock

import api.source_pb2 as proto_source
import api.control_pb2 as proto_control
from src.lib.builder import nighthawk_builder
from src.lib import (cmd_exec, constants, source_tree, source_manager)

_BAZEL_CLEAN_CMD = "bazel clean"


@mock.patch.object(source_manager.SourceManager, 'get_source_repository')
def test_prepare_nighthawk_source_fail(mock_get_source_tree):
  """Verify an exception is raised if the source identity is invalid."""
  envoy_source_repo = proto_source.SourceRepository(
      identity=proto_source.SourceRepository.SourceIdentity.SRCID_ENVOY,
      source_path='/some_random_envoy_directory',
      commit_hash='doesnt_matter')

  mock_get_source_tree.return_value = envoy_source_repo
  manager = _generate_default_source_manager()
  builder = nighthawk_builder.NightHawkBuilder(manager)

  with pytest.raises(nighthawk_builder.NightHawkBuilderError) as builder_error:
    builder.prepare_nighthawk_source()

  assert str(builder_error.value) == \
      "This module supports building NightHawk Only"


@mock.patch.object(source_tree.SourceTree, 'get_source_directory')
@mock.patch.object(source_tree.SourceTree, 'copy_source_directory')
@mock.patch.object(source_tree.SourceTree, 'pull')
def test_prepare_nighthawk_source(mock_pull, mock_copy_source, mock_get_source_dir):
  """Verify that we are able to get a source tree on disk to build NightHawk."""
  mock_pull.return_value = False
  mock_copy_source.return_value = None
  mock_get_source_dir.return_value = '/tmp/nighthawk_source_dir'

  manager = _generate_default_source_manager()
  builder = nighthawk_builder.NightHawkBuilder(manager)

  with mock.patch("src.lib.cmd_exec.run_command",
                  mock.MagicMock(return_value="Cleaned...")) as mock_cmd:
    builder.prepare_nighthawk_source()

  params = cmd_exec.CommandParameters(cwd='/tmp/nighthawk_source_dir')
  mock_cmd.assert_called_once_with(_BAZEL_CLEAN_CMD, params, False)
  mock_pull.assert_called_once()
  mock_copy_source.assert_called_once()


@mock.patch('src.lib.cmd_exec.run_command')
@mock.patch.object(source_tree.SourceTree, 'copy_source_directory')
@mock.patch.object(source_tree.SourceTree, 'pull')
def test_build_nighthawk_benchmarks(mock_pull, mock_copy_source, mock_run_command):
  """Verify the calls made to build the nighthawk benchmarks target."""
  mock_pull.return_value = True
  mock_copy_source.return_value = None
  mock_run_command.side_effect = ['bazel clean output ...', 'bazel build output ...']
  calls = [
      mock.call(_BAZEL_CLEAN_CMD, mock.ANY, mock.ANY),
      mock.call("bazel build --jobs 4 -c opt //benchmarks:benchmarks", mock.ANY, mock.ANY)
  ]

  manager = _generate_default_source_manager()
  builder = nighthawk_builder.NightHawkBuilder(manager)

  source_repo = manager.get_source_repository(
      proto_source.SourceRepository.SourceIdentity.SRCID_NIGHTHAWK)
  source_repo.bazel_options.add(parameter="--jobs 4")

  builder.build_nighthawk_benchmarks()
  mock_run_command.assert_has_calls(calls)
  mock_pull.assert_called_once()
  mock_copy_source.assert_not_called()


@mock.patch('src.lib.cmd_exec.run_command')
@mock.patch.object(source_tree.SourceTree, 'copy_source_directory')
@mock.patch.object(source_tree.SourceTree, 'pull')
def test_build_nighthawk_binaries(mock_pull, mock_copy_source, mock_run_command):
  """Verify the calls made to build nighthawk binaries."""
  mock_pull.return_value = True
  mock_copy_source.return_value = None
  mock_run_command.side_effect = ['bazel clean output', 'bazel nighthawk build output ...']
  calls = [
      mock.call(_BAZEL_CLEAN_CMD, mock.ANY, mock.ANY),
      mock.call("bazel build --jobs 4 -c dbg //:nighthawk", mock.ANY, mock.ANY)
  ]
  manager = _generate_default_source_manager()

  source_repo = manager.get_source_repository(
      proto_source.SourceRepository.SourceIdentity.SRCID_NIGHTHAWK)
  source_repo.bazel_options.add(parameter="--jobs 4")
  source_repo.bazel_options.add(parameter="-c dbg")

  builder = nighthawk_builder.NightHawkBuilder(manager)
  builder.build_nighthawk_binaries()

  mock_run_command.assert_has_calls(calls)


@mock.patch('src.lib.cmd_exec.run_command')
@mock.patch.object(source_tree.SourceTree, 'pull')
def test_build_nighthawk_benchmark_image(mock_pull, mock_run_command):
  """Verify that we can build the nighthawk benchmark image."""
  mock_pull.return_value = True
  mock_run_command.side_effect = [
      'bazel clean output ...', 'bazel build benchmarks output ...',
      'bazel benchmark image build output ...'
  ]
  calls = [
      mock.call(_BAZEL_CLEAN_CMD, mock.ANY, mock.ANY),
      mock.call("bazel build -c opt //benchmarks:benchmarks", mock.ANY, mock.ANY),
      mock.call(constants.NH_BENCHMARK_IMAGE_SCRIPT, mock.ANY, mock.ANY)
  ]

  manager = _generate_default_source_manager()
  builder = nighthawk_builder.NightHawkBuilder(manager)
  builder.build_nighthawk_benchmark_image()

  mock_run_command.assert_has_calls(calls)
  mock_pull.assert_called_once()


@mock.patch('src.lib.cmd_exec.run_command')
@mock.patch.object(source_tree.SourceTree, 'pull')
def test_build_nighthawk_binary_image(mock_pull, mock_run_command):
  """Verify that we can build the nighthawk benchmark image."""
  mock_pull.return_value = True
  mock_run_command.side_effect = [
      'bazel clean output ...', 'bazel build benchmarks output ...',
      'bazel benchmark image build output ...'
  ]
  calls = [
      mock.call(_BAZEL_CLEAN_CMD, mock.ANY, mock.ANY),
      mock.call("bazel build -c opt //:nighthawk", mock.ANY, mock.ANY),
      mock.call(constants.NH_BINARY_IMAGE_SCRIPT, mock.ANY, mock.ANY)
  ]

  manager = _generate_default_source_manager()
  builder = nighthawk_builder.NightHawkBuilder(manager)
  builder.build_nighthawk_binary_image()

  mock_run_command.assert_has_calls(calls)
  mock_pull.assert_called_once()


def _generate_default_source_manager():
  """Build a default SourceRepository object."""
  control = proto_control.JobControl(remote=False, scavenging_benchmark=True)
  control.source.add(
      identity=proto_source.SourceRepository.SourceIdentity.SRCID_NIGHTHAWK,
      source_path='/where_nighthawk_code_lives',
  )
  return source_manager.SourceManager(control)


if __name__ == '__main__':
  raise SystemExit(pytest.main(['-s', '-v', __file__]))
