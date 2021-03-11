"""
Test the scavenging benchmark class
"""
import pytest
from unittest import mock

from src.lib.benchmark import (base_benchmark, scavenging_benchmark)
from src.lib.builder import nighthawk_builder
from src.lib import (source_manager, generate_test_objects)

def test_execute_benchmark_no_images_or_sources():
  """Verify the benchmark fails if no images or sources are present """

  job_control = generate_test_objects.generate_default_job_control()
  benchmark = scavenging_benchmark.Benchmark(job_control, 'scavenging')

  with pytest.raises(base_benchmark.BenchmarkError) as benchmark_error:
    benchmark.execute_benchmark()

  assert str(benchmark_error.value) == "No source configuration specified"

def test_execute_benchmark_nighthawk_source_only():
  """Verify that we detect missing Envoy sources """

  job_control = generate_test_objects.generate_default_job_control()
  generate_test_objects.generate_nighthawk_source(job_control)
  benchmark = scavenging_benchmark.Benchmark(job_control, 'scavenging')

  with pytest.raises(base_benchmark.BenchmarkError) as benchmark_error:
    benchmark.execute_benchmark()

  assert str(benchmark_error.value) == \
      "No source specified to build Envoy image"

def test_execute_benchmark_envoy_source_only():
  """Verify that we detect missing NightHawk sources """

  job_control = generate_test_objects.generate_default_job_control()
  generate_test_objects.generate_envoy_source(job_control)
  benchmark = scavenging_benchmark.Benchmark(job_control, 'scavenging')

  with pytest.raises(base_benchmark.BenchmarkError) as benchmark_error:
    benchmark.execute_benchmark()

  assert str(benchmark_error.value) == \
      "No source specified to build NightHawk image"

@mock.patch.object(source_manager.SourceManager, 'get_source_tree')
@mock.patch.object(nighthawk_builder.NightHawkBuilder, 'build_nighthawk_benchmarks')
def test_execute_benchmark_no_environment(mock_benchmarks, mock_get_source_tree):
  """Verify that we fail a benchmark if no environment is set """

  job_control = generate_test_objects.generate_default_job_control()

  # Add nighthawk and envoy sources
  generate_test_objects.generate_envoy_source(job_control)
  generate_test_objects.generate_nighthawk_source(job_control)

  benchmark = scavenging_benchmark.Benchmark(job_control, 'scavenging')

  with pytest.raises(base_benchmark.BenchmarkEnvironmentError) as \
      benchmark_error:
    benchmark.execute_benchmark()

  assert str(benchmark_error.value) == \
      "No IP version is specified for the benchmark"

  mock_benchmarks.assert_called()
  mock_get_source_tree.assert_called()

@mock.patch('src.lib.cmd_exec.run_command')
@mock.patch.object(source_manager.SourceManager, 'get_source_tree')
@mock.patch.object(nighthawk_builder.NightHawkBuilder, 'build_nighthawk_benchmarks')
def test_execute_benchmark(mock_benchmarks, mock_get_source_tree, mock_run_command):
  """Verify that we fail a benchmark if no environment is set """

  job_control = generate_test_objects.generate_default_job_control()

  # Add nighthawk and envoy sources
  generate_test_objects.generate_envoy_source(job_control)
  generate_test_objects.generate_nighthawk_source(job_control)
  generate_test_objects.generate_environment(job_control)

  calls = [
      mock.call("bazel-bin/benchmarks/benchmarks "
                "--log-cli-level=info -vvvv -k test_http_h1_small "
                "benchmarks/", mock.ANY)
  ]
  benchmark = scavenging_benchmark.Benchmark(job_control, 'scavenging')

  benchmark.execute_benchmark()

  mock_benchmarks.assert_called()
  mock_get_source_tree.assert_called()
  mock_run_command.assert_has_calls(calls)

if __name__ == '__main__':
  raise SystemExit(pytest.main(['-s', '-v', __file__]))
