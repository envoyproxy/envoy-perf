"""
Test the fully dockerized benchmark class
"""

import pytest
from unittest import mock

import api.control_pb2 as proto_control

from src.lib.benchmark import fully_dockerized_benchmark as full_docker
from src.lib.benchmark import (generate_benchmark_test_objects, base_benchmark)
from src.lib.docker import docker_image


@mock.patch.object(base_benchmark.BaseBenchmark, 'run_image')
def test_execute_benchmark_using_images_only(mock_run_image):
  """Validate we execute the benchmark with only images specified."""

  mock_run_image.return_value = b'benchmark_http_client output'

  # create a valid configuration defining images only for benchmark
  job_control = generate_benchmark_test_objects.generate_default_job_control()

  generate_benchmark_test_objects.generate_images(job_control)
  generate_benchmark_test_objects.generate_environment(job_control)

  benchmark = full_docker.Benchmark(job_control, "test_benchmark")

  run_parameters = docker_image.DockerRunParameters(
      command=['./benchmarks', '--log-cli-level=info', '-vvvv'],
      environment=mock.ANY,
      volumes=mock.ANY,
      network_mode='host',
      tty=True
  )

  # Calling execute_benchmark shoud not throw an exception
  benchmark.execute_benchmark()
  mock_run_image.assert_called_once_with(
      'envoyproxy/nighthawk-benchmark-dev:random_benchmark_image_tag',
      run_parameters)

def test_execute_benchmark_no_image_or_sources():
  """Verify that the validation logic raises an exception since we are unable to
  build a required Envoy image.
  """
  # create a valid configuration with a missing Envoy image
  job_control = generate_benchmark_test_objects.generate_default_job_control()

  images = generate_benchmark_test_objects.generate_images(job_control)
  images.envoy_image = ""

  generate_benchmark_test_objects.generate_environment(job_control)

  benchmark = full_docker.Benchmark(job_control, "test_benchmark")

  # Calling execute_benchmark shoud not throw an exception
  with pytest.raises(base_benchmark.BenchmarkError) \
      as validation_error:
    benchmark.execute_benchmark()

  assert str(validation_error.value) == "No source configuration specified"

@mock.patch.object(base_benchmark.BaseBenchmark, 'run_image')
def test_execute_benchmark_with_envoy_source(mock_run_image):
  """Validate that if sources are defined that enable us to build the Envoy
  image we do not throw an exception.
  """

  mock_run_image.return_value = b'benchmark_http_client output'

  # create a valid configuration with a missing Envoy image
  job_control = generate_benchmark_test_objects.generate_default_job_control()

  images = generate_benchmark_test_objects.generate_images(job_control)
  images.envoy_image = ""

  generate_benchmark_test_objects.generate_envoy_source(job_control)
  generate_benchmark_test_objects.generate_environment(job_control)

  benchmark = full_docker.Benchmark(job_control, "test_benchmark")

  run_parameters = docker_image.DockerRunParameters(
      command=['./benchmarks', '--log-cli-level=info', '-vvvv'],
      environment=mock.ANY,
      volumes=mock.ANY,
      network_mode='host',
      tty=True
  )

  benchmark.execute_benchmark()
  mock_run_image.assert_called_once_with(
      'envoyproxy/nighthawk-benchmark-dev:random_benchmark_image_tag',
      run_parameters)

def test_execute_benchmark_missing_envoy_source():
  """Validate that although sources are defined for NightHawk we raise an
  exception due to the inability to build Envoy.
  """
  # create a configuration with a missing Envoy image
  job_control = proto_control.JobControl(
      remote=False,
      scavenging_benchmark=True
  )

  images = generate_benchmark_test_objects.generate_images(job_control)
  images.envoy_image = ""

  # Change the source identity to NightHawk
  envoy_source = generate_benchmark_test_objects.generate_envoy_source(
      job_control)
  envoy_source.identity = envoy_source.SRCID_NIGHTHAWK

  benchmark = full_docker.Benchmark(job_control, "test_benchmark")

  # Calling execute_benchmark should raise an exception from validate()
  with pytest.raises(Exception) as validation_exception:
    benchmark.execute_benchmark()

  assert str(validation_exception.value) == \
      "No source specified to build Envoy image"

def test_execute_benchmark_missing_nighthawk_binary_image():
  """Validate that no sources are defined that enable us to build the missing
  NightHawk benchmark image resulting in a raised exception.
  """
  # create a valid configuration with a missing NightHawk container image
  job_control = proto_control.JobControl(
      remote=False,
      scavenging_benchmark=True
  )

  images = generate_benchmark_test_objects.generate_images(job_control)
  images.nighthawk_binary_image = ""

  # Generate a default Envoy source object.
  generate_benchmark_test_objects.generate_envoy_source(job_control)
  benchmark = full_docker.Benchmark(job_control, "test_benchmark")

  # Calling execute_benchmark raise an exception from validate()
  with pytest.raises(Exception) as validation_exception:
    benchmark.execute_benchmark()

  assert str(validation_exception.value) == \
      "No source specified to build NightHawk image"

def test_execute_benchmark_missing_nighthawk_benchmark_image():
  """Validate an exception is raised if we cannot build the unspecified
  NightHawk benchmark image.
  """
  # create a valid configuration with a missing both NightHawk container images
  job_control = proto_control.JobControl(
      remote=False,
      scavenging_benchmark=True
  )

  images = generate_benchmark_test_objects.generate_images(job_control)
  images.nighthawk_benchmark_image = ""

  # Generate a default Envoy source object
  generate_benchmark_test_objects.generate_envoy_source(job_control)

  benchmark = full_docker.Benchmark(job_control, "test_benchmark")

  # Calling execute_benchmark shoud not throw an exception
  with pytest.raises(Exception) as validation_exception:
    benchmark.execute_benchmark()

  assert str(validation_exception.value) == \
      "No source specified to build NightHawk image"

if __name__ == '__main__':
  raise SystemExit(pytest.main(['-s', '-v', __file__]))
