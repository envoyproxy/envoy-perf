"""
Test the base benchmark class
"""
import os
import copy
import pytest

import api.control_pb2 as proto_control
import src.lib.benchmark.base_benchmark as base_benchmark

def test_environment_variables():
  """Test that the specified environment variables are set for a
      benchmark.

      We copy the environment variables for verification and clear
      the variables that we set so that we do not pollute other
      tests.
  """
  job_control = proto_control.JobControl()
  environ = job_control.environment
  environ.variables["TMP_DIR"] = "/home/user/nighthawk_output"
  environ.variables["TEST_VAR1"] = "TEST_VALUE1"
  environ.variables["TEST_VAR2"] = "TEST_VALUE2"
  environ.variables["TEST_VAR3"] = "TEST_VALUE3"
  environ.test_version = job_control.environment.IPV_V4ONLY
  environ.envoy_path = "a_proxy_called_envoy"

  benchmark = base_benchmark.BaseBenchmark(job_control, "test_benchmark")
  benchmark._set_environment_vars()

  expected_vars = {
      'TMP_DIR': '/home/user/nighthawk_output',
      'TEST_VAR1': 'TEST_VALUE1',
      'TEST_VAR2': 'TEST_VALUE2',
      'TEST_VAR3': 'TEST_VALUE3',
      'ENVOY_IP_TEST_VERSIONS': 'v4only',
      'ENVOY_PATH': 'a_proxy_called_envoy'
  }

  environment_variables = copy.deepcopy(os.environ)
  benchmark._clear_environment_vars()

  for (key, value) in expected_vars.items():
    assert environment_variables[key] == value

def test_no_environment_variables_exception():
  """Test that we raise an exception if the environment is not configured."""
  job_control = proto_control.JobControl()

  benchmark = base_benchmark.BaseBenchmark(job_control, "test_benchmark")
  with pytest.raises(Exception) as environment_exception:
    benchmark._set_environment_vars()

  assert str(environment_exception.value) == \
      "No IP version is specified for the benchmark"

def test_minimal_environment_variables():
  """Test that setting the required variables works and no extra variables are
     set.
  """
  job_control = proto_control.JobControl()
  environ = job_control.environment
  environ.test_version = job_control.environment.IPV_V4ONLY

  benchmark = base_benchmark.BaseBenchmark(job_control, "test_benchmark")
  benchmark._set_environment_vars()

  not_expected_vars = {
      'TMP_DIR': '/home/user/nighthawk_output',
      'TEST_VAR1': 'TEST_VALUE1',
      'TEST_VAR2': 'TEST_VALUE2',
      'TEST_VAR3': 'TEST_VALUE3',
      'ENVOY_PATH': 'a_proxy_called_envoy'
  }

  expected_vars = {
      'ENVOY_IP_TEST_VERSIONS': 'v4only',
  }

  for (key, value) in expected_vars.items():
    assert os.environ[key] == value

  for (key, _) in not_expected_vars.items():
    assert key not in os.environ


if __name__ == '__main__':
  raise SystemExit(pytest.main(['-s', '-v', __file__]))
