"""
Test the fully dockerized benchmark class
"""

import pytest
import subprocess
from unittest.mock import patch

import api.control_pb2 as proto_control

from src.lib.benchmark import binary_benchmark
from src.lib import generate_test_objects

_BUILD_NIGHTHAWK_BENCHMARKS = \
    ('src.lib.builder.nighthawk_builder.NightHawkBuilder'
     '.build_nighthawk_benchmarks')
_BUILD_NIGHTHAWK_BINARIES = \
    ('src.lib.builder.nighthawk_builder.NightHawkBuilder'
     '.build_nighthawk_binaries')
_BUILD_ENVOY_BINARY = \
    ('src.lib.builder.envoy_builder.EnvoyBuilder'
     '.build_envoy_binary_from_source')

def test_no_sources():
  """Test benchmark validation logic.

  We expect the validation logic to throw an exception,
  since no sources are present
  """
  # create a valid configuration with no images
  job_control = generate_test_objects.generate_default_job_control()

  generate_test_objects.generate_environment(job_control)

  benchmark = binary_benchmark.Benchmark(job_control, "test_benchmark")

  # Calling execute_benchmark should throw an exception
  with pytest.raises(binary_benchmark.BinaryBenchmarkError) \
      as validation_error:
    benchmark.execute_benchmark()

  assert str(validation_error.value) == "No source configuration specified"

# Mock the build invocations so we don't actually try to build this big chungus
@patch(_BUILD_NIGHTHAWK_BENCHMARKS)
@patch(_BUILD_NIGHTHAWK_BINARIES)
@patch(_BUILD_ENVOY_BINARY)
@patch('src.lib.cmd_exec.run_command')
def test_source_to_build_binaries(mock_cmd, mock_envoy_build, mock_nh_bin_build, mock_nh_bench_build):
  """Validate we can build binaries from source.

  Validate that sources are defined that enable us to build Envoy/Nighthawk
  We do not expect the validation logic to throw an exception
  """
  # create a valid configuration with a missing Envoy image
  job_control = generate_test_objects.generate_default_job_control()

  generate_test_objects.generate_envoy_source(job_control)
  generate_test_objects.generate_nighthawk_source(job_control)
  generate_test_objects.generate_environment(job_control)

  # Setup mock values
  mock_envoy_path = "/home/ubuntu/envoy/bazel-bin/source/exe/envoy-static"
  mock_envoy_build.return_value = mock_envoy_path

  benchmark = binary_benchmark.Benchmark(job_control, "test_benchmark")

  benchmark.execute_benchmark()
  assert benchmark.envoy_binary_path == mock_envoy_path
  mock_envoy_build.assert_called_once()
  mock_nh_bench_build.assert_called_once()
  mock_nh_bin_build.assert_called_once()

def test_no_source_to_build_nh():
  """Validate that we fail the entire process in the absence of NH sources

  Validate that even if Envoy sources are specified, the absence of Nighthawk
  sources will cause the program to fail.

  We expect the validation logic to throw an exception
  """
  # create a valid configuration with a missing NightHawk container image
  job_control = proto_control.JobControl(
      remote=False,
      binary_benchmark=True
  )

  generate_test_objects.generate_envoy_source(job_control)
  generate_test_objects.generate_environment(job_control)

  benchmark = binary_benchmark.Benchmark(job_control, "test_benchmark")

  # Calling execute_benchmark should throw an exception
  with pytest.raises(Exception) as validation_exception:
    benchmark.execute_benchmark()

  assert str(validation_exception.value) == \
      "No source specified to build Nighthawk"

# Mock the build invocations so we don't actually try to build this big chungus
@patch(_BUILD_NIGHTHAWK_BENCHMARKS)
@patch(_BUILD_NIGHTHAWK_BINARIES)
@patch(_BUILD_ENVOY_BINARY)
@patch('src.lib.cmd_exec.run_command')
def test_fallback_envoy(mock_cmd, mock_envoy_build, mock_nh_bin_build, mock_nh_bench_build):
  """Validate that we proceed when Envoy sources are not present

  Validate that a fallback to the Nighthawk test server is triggered
  when no Envoy sources or binaries are specified.

  We do not expect the validation logic to throw an exception
  """
  # create a valid configuration with a missing both NightHawk container images
  job_control = proto_control.JobControl(
      remote=False,
      binary_benchmark=True
  )

  generate_test_objects.generate_nighthawk_source(job_control)
  generate_test_objects.generate_environment(job_control)
  benchmark = binary_benchmark.Benchmark(job_control, "test_benchmark")

  benchmark.execute_benchmark()
  assert benchmark.use_fallback
  mock_envoy_build.assert_not_called()
  mock_nh_bench_build.assert_called_once()
  mock_nh_bin_build.assert_called_once()

@patch(_BUILD_NIGHTHAWK_BENCHMARKS)
@patch(_BUILD_NIGHTHAWK_BINARIES)
@patch(_BUILD_ENVOY_BINARY)
@patch('src.lib.cmd_exec.run_command')
def test_envoy_build_failure(mock_cmd, mock_envoy_build, mock_nh_bin_build, mock_nh_bench_build):
  """Validate that an exception is raised which halts the benchmark execution
  when the Envoy build fails

  We expect an unhandled exception to surface from _prepare_envoy
  """
  # Setup mock values
  mock_envoy_build.side_effect = subprocess.CalledProcessError(1, "foo")

  job_control = generate_test_objects.generate_default_job_control()

  generate_test_objects.generate_envoy_source(job_control)
  generate_test_objects.generate_nighthawk_source(job_control)
  generate_test_objects.generate_environment(job_control)

  benchmark = binary_benchmark.Benchmark(job_control, "test_benchmark")
  with pytest.raises(Exception) as build_exception:
    benchmark.execute_benchmark()

  assert str(build_exception.value) == "Command 'foo' returned non-zero exit status 1."
  assert not benchmark.envoy_binary_path
  # We expect the nighthawk build to occur before the Envoy build fails
  mock_nh_bench_build.assert_called_once()
  mock_nh_bin_build.assert_called_once()

@patch(_BUILD_NIGHTHAWK_BENCHMARKS)
@patch(_BUILD_NIGHTHAWK_BINARIES)
@patch(_BUILD_ENVOY_BINARY)
@patch('src.lib.cmd_exec.run_command')
def test_nh_build_failure(mock_cmd, mock_envoy_build, mock_nh_bin_build, mock_nh_bench_build):
  """Validate that an exception is raised which halts the benchmark execution
  when the Nighthawk build fails

  We expect an unhandled exception to surface from _prepare_nighthawk
  """
  # Setup mock values
  mock_nh_bench_build.side_effect = subprocess.CalledProcessError(1, "bar")
  mock_envoy_path = "/home/ubuntu/envoy/bazel-bin/source/exe/envoy-static"
  mock_envoy_build.return_value = mock_envoy_path

  job_control = generate_test_objects.generate_default_job_control()

  generate_test_objects.generate_envoy_source(job_control)
  generate_test_objects.generate_nighthawk_source(job_control)
  generate_test_objects.generate_environment(job_control)

  benchmark = binary_benchmark.Benchmark(job_control, "test_benchmark")
  with pytest.raises(Exception) as build_exception:
    benchmark.execute_benchmark()

  assert str(build_exception.value) == "Command 'bar' returned non-zero exit status 1."
  assert not benchmark.envoy_binary_path
  # We expect the nighthawk binary build to occur
  # before the benchmark build fails
  mock_nh_bin_build.assert_called_once()
  # Raising an exception during the nighthawk build should prevent control flow
  # from proceeding to build Envoy
  mock_envoy_build.assert_not_called()

if __name__ == '__main__':
  raise SystemExit(pytest.main(['-s', '-v', __file__]))
