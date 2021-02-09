"""
Test envoy building operations
"""
import logging
import pytest
from unittest import mock

import api.source_pb2 as proto_source
import api.control_pb2 as proto_control
from src.lib.builder import envoy_builder
from src.lib import (constants, source_tree, source_manager)

logging.basicConfig(level=logging.DEBUG)

def _check_call_side_effect(args, parameters):
  """Examine the incoming arguments for command execution and return the
  expected or unexpected output.

  Args:
    args: The arguments supplied to the mocked function
    parameter: The CommandParameters passed to the cmd_exec method
  Return:
    usually this returns a string containing the command output.  In
      some cases we may raise an exception.
  """

  assert 'cwd' in parameters._asdict()

  if args == "bazel clean":
    return "INFO: Starting clean"
  elif args == "bazel build -c opt " + constants.ENVOY_BINARY_BUILD_TARGET:
    return "foo"
  elif args == ("cp -fv bazel-bin/source/exe/envoy-static "
                "build_release_stripped/envoy"):
    return "copied..."
  elif args == (("objcopy --strip-debug bazel-bin/source/exe/envoy-static "
                 "build_release_stripped/envoy")):
    return "stripped..."
  elif args == (("docker build -f ci/Dockerfile-envoy -t "
                 "envoyproxy/envoy-dev:v1.16.0 --build-arg "
                 "TARGETPLATFORM='.' .")):
    return "docker build output..."

  raise NotImplementedError(f"Unhandled arguments in call: {args}")

@mock.patch.object(envoy_builder.EnvoyBuilder, 'create_docker_image')
@mock.patch.object(envoy_builder.EnvoyBuilder, 'stage_envoy')
@mock.patch('src.lib.cmd_exec.run_check_command')
@mock.patch('src.lib.cmd_exec.run_command')
@mock.patch.object(source_tree.SourceTree, 'checkout_commit_hash')
@mock.patch.object(source_tree.SourceTree, 'copy_source_directory')
def test_build_envoy_image_from_source(mock_copy_source,
                                       mock_checkout_hash,
                                       mock_run_command,
                                       mock_run_check_command,
                                       mock_stage_envoy,
                                       mock_create_docker_image):
  """Verify the calls made to build an envoy image from a source tree."""
  mock_copy_source.return_value = None
  mock_checkout_hash.return_value = None
  mock_run_command.side_effect = _check_call_side_effect
  mock_run_check_command.side_effect = _check_call_side_effect
  mock_stage_envoy.return_value = None
  mock_create_docker_image.return_value = None

  manager = _generate_default_source_manager()
  builder = envoy_builder.EnvoyBuilder(manager)
  builder.build_envoy_image_from_source()

  mock_copy_source.assert_called_once()
  mock_checkout_hash.assert_called_once()
  mock_stage_envoy.assert_called_once_with(False)
  mock_create_docker_image.assert_called_once()

@mock.patch.object(source_manager.SourceManager, 'get_source_repository')
def test_build_envoy_image_from_source_fail(mock_get_source_tree):
  """Verify an exception is raised if the source identity is invalid"""

  nighthawk_source_repo = proto_source.SourceRepository(
      identity=proto_source.SourceRepository.SourceIdentity.SRCID_NIGHTHAWK,
      source_path='/some_random_not_envoy_directory'
  )

  mock_get_source_tree.return_value = nighthawk_source_repo
  manager = _generate_default_source_manager()
  builder = envoy_builder.EnvoyBuilder(manager)

  with pytest.raises(envoy_builder.EnvoyBuilderError) as builder_error:
    builder.build_envoy_image_from_source()

  assert str(builder_error.value) == "This class builds Envoy only."

@mock.patch('src.lib.cmd_exec.run_command')
def test_stage_envoy(mock_run_command):
  """Verify the commands used to stage the envoy binary for docker image
  construction.
  """
  mock_run_command.side_effect = _check_call_side_effect

  calls = [
    mock.call(("cp -fv bazel-bin/source/exe/envoy-static "
              "build_release_stripped/envoy"),
              mock.ANY),
    mock.call(("objcopy --strip-debug bazel-bin/source/exe/envoy-static "
              "build_release_stripped/envoy"),
              mock.ANY)
  ]
  manager = _generate_default_source_manager()
  builder = envoy_builder.EnvoyBuilder(manager)
  builder.stage_envoy(False)
  builder.stage_envoy(True)

  mock_run_command.assert_has_calls(calls)

@mock.patch('glob.glob')
@mock.patch('src.lib.cmd_exec.run_command')
def test_create_docker_image(mock_run_command, mock_glob):
  """Verify that we issue the correct commands to build an envoy docker
  image.
  """
  mock_run_command.side_effect = _check_call_side_effect
  mock_glob.return_value = ['file1', 'file2']

  manager = _generate_default_source_manager()
  builder = envoy_builder.EnvoyBuilder(manager)
  builder.create_docker_image()

  mock_run_command.assert_called_once()

def _generate_default_source_manager():
  """Build a default SourceRepository object."""

  control = proto_control.JobControl(remote=False, scavenging_benchmark=True)
  control.source.add(
      identity=proto_source.SourceRepository.SourceIdentity.SRCID_ENVOY,
      source_path='/some_random_envoy_directory',
      commit_hash='v1.16.0'
  )
  return source_manager.SourceManager(control)

if __name__ == '__main__':
  raise SystemExit(pytest.main(['-s', '-v', __file__]))
