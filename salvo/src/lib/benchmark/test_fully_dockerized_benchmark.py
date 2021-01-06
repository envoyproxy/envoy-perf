"""
Test the fully dockerized benchmark class
"""

import os
import pytest
from unittest import mock

import api.control_pb2 as proto_control
import api.image_pb2 as proto_image
import api.env_pb2 as proto_environ
import api.source_pb2 as proto_source

from src.lib.benchmark import fully_dockerized_benchmark as full_docker
from src.lib.benchmark import base_benchmark
from src.lib.docker import docker_image

def _generate_images(
    job_control: proto_control.JobControl) -> proto_image.DockerImages:
  """Generate a default images specification for a control object.

  Returns:
    a DockerImages object populated with a default set of data
  """
  generated_images = job_control.images
  generated_images.reuse_nh_images = True
  generated_images.nighthawk_benchmark_image = \
      "envoyproxy/nighthawk-benchmark-dev:random_benchmark_image_tag"
  generated_images.nighthawk_binary_image = \
      "envoyproxy/nighthawk-dev:random-binary_image_tag"
  generated_images.envoy_image = \
      "envoyproxy/envoy-dev:f61b096f6a2dd3a9c74b9a9369a6ea398dbe1f0f"

  return generated_images

def _generate_environment(
    job_control: proto_control.JobControl) -> proto_environ.EnvironmentVars:
  """Generate a default set of environment variables for a control object.

  Returns:
    an EnvironmentVars object containing varibles used by benchmarks.
  """
  generated_environment = job_control.environment
  generated_environment.variables["TMP_DIR"] = "/home/ubuntu/nighthawk_output"
  generated_environment.test_version = generated_environment.IPV_V4ONLY
  generated_environment.envoy_path = "envoy"

  return generated_environment

def _generate_envoy_source(
    job_control: proto_control.JobControl) -> proto_source.SourceRepository:
  """Generate a default Envoy SourceRepository in the control object.

  Returns:
    a SourceRepository object defining the location of the Envoy source.
  """
  envoy_source = job_control.source.add()
  envoy_source.identity = envoy_source.SRCID_ENVOY
  envoy_source.source_path = "/home/ubuntu/envoy"
  envoy_source.source_url = "https://github.com/envoyproxy/envoy.git"
  envoy_source.branch = "master"
  envoy_source.commit_hash = "hash_doesnt_really_matter_here"

  return envoy_source

def _generate_default_job_control() -> proto_control.JobControl:
  """Generate a default job control object used in tests."""
  job_control = proto_control.JobControl(
      remote=False,
      scavenging_benchmark=True
  )
  return job_control

def test_images_only_config():
  """Test benchmark validation logic."""

  # create a valid configuration defining images only for benchmark
  job_control = _generate_default_job_control()

  _generate_images(job_control)
  _generate_environment(job_control)

  benchmark = full_docker.Benchmark(job_control, "test_benchmark")

  run_parameters = docker_image.DockerRunParameters(
      command=['./benchmarks', '--log-cli-level=info', '-vvvv'],
      environment=mock.ANY,
      volumes=mock.ANY,
      network_mode='host',
      tty=True
  )

  # Calling execute_benchmark shoud not throw an exception
  # Mock the container invocation so that we don't try to pull an image
  with mock.patch('src.lib.benchmark.base_benchmark.BaseBenchmark.run_image') \
      as docker_mock:
    benchmark.execute_benchmark()
    docker_mock.assert_called_once_with(
        'envoyproxy/nighthawk-benchmark-dev:random_benchmark_image_tag',
        run_parameters)

def test_no_envoy_image_no_sources():
  """Test benchmark validation logic.

  No Envoy image is specified, we expect the validation logic to
  throw an exception since no sources are present
  """
  # create a valid configuration with a missing Envoy image
  job_control = _generate_default_job_control()

  images = _generate_images(job_control)
  images.envoy_image = ""

  _generate_environment(job_control)

  benchmark = full_docker.Benchmark(job_control, "test_benchmark")

  # Calling execute_benchmark shoud not throw an exception
  with pytest.raises(full_docker.FullyDockerizedBenchmarkError) \
      as validation_error:
    benchmark.execute_benchmark()

  assert str(validation_error.value) == "No source configuration specified"

def test_source_to_build_envoy():
  """Validate we can build images from source.

  Validate that sources are defined that enable us to build the Envoy image
  We do not expect the validation logic to throw an exception
  """
  # create a valid configuration with a missing Envoy image
  job_control = _generate_default_job_control()

  images = _generate_images(job_control)
  images.envoy_image = ""

  _generate_envoy_source(job_control)

  env = job_control.environment
  env.test_version = env.IPV_V4ONLY
  env.envoy_path = 'envoy'
  env.output_dir = 'some_output_dir'
  env.test_dir = 'some_test_dir'

  benchmark = full_docker.Benchmark(job_control, "test_benchmark")

  run_parameters = docker_image.DockerRunParameters(
      command=['./benchmarks', '--log-cli-level=info', '-vvvv'],
      environment=mock.ANY,
      volumes=mock.ANY,
      network_mode='host',
      tty=True
  )

  # Mock the container invocation so that we don't try to pull an image
  with mock.patch('src.lib.benchmark.base_benchmark.BaseBenchmark.run_image') \
      as docker_mock:
    benchmark.execute_benchmark()
    docker_mock.assert_called_once_with(
        'envoyproxy/nighthawk-benchmark-dev:random_benchmark_image_tag',
        run_parameters)

def test_no_source_to_build_envoy():
  """Validate that we fail to build images without sources.

  Validate that no sources are present that enable us to build the missing
  Envoy image

  We expect the validation logic to throw an exception
  """
  # create a configuration with a missing Envoy image
  job_control = proto_control.JobControl(
      remote=False,
      scavenging_benchmark=True
  )

  images = _generate_images(job_control)
  images.envoy_image = ""

  # Denote that the soure is for nighthawk.  Values aren't really checked at
  # this stage since we have a missing Envoy image and a nighthawk source
  # validation should fail.
  envoy_source = _generate_envoy_source(job_control)
  envoy_source.identity = envoy_source.SRCID_NIGHTHAWK

  benchmark = full_docker.Benchmark(job_control, "test_benchmark")

  # Calling execute_benchmark shoud not throw an exception
  with pytest.raises(Exception) as validation_exception:
    benchmark.execute_benchmark()

  assert str(validation_exception.value) == \
      "No source specified to build unspecified Envoy image"

def test_no_source_to_build_nh():
  """Validate that we fail to build nighthawk without sources.

  Validate that no sources are defined that enable us to build the missing
  NightHawk benchmark image.

  We expect the validation logic to throw an exception
  """
  # create a valid configuration with a missing NightHawk container image
  job_control = proto_control.JobControl(
      remote=False,
      scavenging_benchmark=True
  )

  images = _generate_images(job_control)
  images.nighthawk_binary_image = ""

  # Generate a default Envoy source object.  Values aren't really checked at
  # this stage since we have a missing Envoy image, nighthawk source validation
  # should fail.
  _generate_envoy_source(job_control)

  benchmark = full_docker.Benchmark(job_control, "test_benchmark")

  # Calling execute_benchmark shoud not throw an exception
  with pytest.raises(Exception) as validation_exception:
    benchmark.execute_benchmark()

  assert str(validation_exception.value) == \
      "No source specified to build unspecified NightHawk image"

def test_no_source_to_build_nh2():
  """Validate that we fail to build nighthawk without sources.

  Validate that no sources are defined that enable us to build the missing
  NightHawk binary image.

  We expect the validation logic to throw an exception
  """
  # create a valid configuration with a missing both NightHawk container images
  job_control = proto_control.JobControl(
      remote=False,
      scavenging_benchmark=True
  )

  images = _generate_images(job_control)
  images.nighthawk_binary_image = ""
  images.nighthawk_benchmark_image = ""

  # Generate a default Envoy source object.  Values aren't really checked at
  # this stage since we have a missing Envoy image, nighthawk source validation
  # should fail.
  _generate_envoy_source(job_control)

  benchmark = full_docker.Benchmark(job_control, "test_benchmark")

  # Calling execute_benchmark shoud not throw an exception
  with pytest.raises(Exception) as validation_exception:
    benchmark.execute_benchmark()

  assert str(validation_exception.value) == \
      "No source specified to build unspecified NightHawk image"


if __name__ == '__main__':
  raise SystemExit(pytest.main(['-s', '-v', __file__]))
