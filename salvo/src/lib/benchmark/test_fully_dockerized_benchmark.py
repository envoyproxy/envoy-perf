"""
Test the fully dockerized benchmark class
"""

import pytest
from unittest import mock

import api.control_pb2 as proto_control
import api.image_pb2 as proto_image
import api.env_pb2 as proto_environ
import api.source_pb2 as proto_source
import src.lib.benchmark.fully_dockerized_benchmark as full_docker

def _generate_images(job_control: proto_control.JobControl) -> proto_image.DockerImages:
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

def test_images_only_config():
  """Test benchmark validation logic.

  Validate that we attempt to run the specified docker image
  when all parameters are present.
  """
  # create a valid configuration defining images only for benchmark
  job_control = proto_control.JobControl(
      remote=False,
      scavenging_benchmark=True
  )

  _generate_images(job_control)
  _generate_environment(job_control)

  benchmark = full_docker.Benchmark(job_control, "test_benchmark")

  # Calling execute_benchmark shoud not throw an exception
  # Mock the container invocation so that we don't try to pull an image
  with mock.patch(
      'docker.models.containers.ContainerCollection.run') as docker_mock:
    benchmark.execute_benchmark()
    docker_mock.assert_called_once_with(
        'envoyproxy/nighthawk-benchmark-dev:random_benchmark_image_tag',
        command=mock.ANY,
        detach=False,
        environment=mock.ANY,
        network_mode='host',
        stderr=True,
        stdout=True,
        tty=True,
        volumes=mock.ANY)

def test_no_envoy_image_no_sources():
  """Test benchmark validation logic.

  No Envoy image is specified, we expect the validation logic to
  throw an exception since no sources are present
  """
  # create a valid configuration with a missing Envoy image
  job_control = proto_control.JobControl(
      remote=False,
      scavenging_benchmark=True
  )

  images = _generate_images(job_control)
  images.envoy_image = ""

  _generate_environment(job_control)

  benchmark = full_docker.Benchmark(job_control, "test_benchmark")

  # Calling execute_benchmark shoud not throw an exception
  with pytest.raises(Exception) as validation_exception:
    benchmark.execute_benchmark()

  assert str(validation_exception.value) == "No source configuration specified"

def test_source_to_build_envoy():
  """Validate we can build images from source.

  Validate that sources are defined that enable us to build the Envoy image
  We do not expect the validation logic to throw an exception
  """
  # create a valid configuration with a missing Envoy image
  job_control = proto_control.JobControl(
      remote=False,
      scavenging_benchmark=True
  )

  images = _generate_images(job_control)
  images.envoy_image = ""

  _generate_envoy_source(job_control)

  env = job_control.environment
  env.test_version = env.IPV_V4ONLY
  env.envoy_path = 'envoy'
  env.output_dir = 'some_output_dir'
  env.test_dir = 'some_test_dir'

  benchmark = full_docker.Benchmark(job_control, "test_benchmark")

  # Mock the container invocation so that we don't try to pull an image
  with mock.patch('docker.models.containers.ContainerCollection.run') as docker_mock:
    benchmark.execute_benchmark()
    docker_mock.assert_called_once_with(
        'envoyproxy/nighthawk-benchmark-dev:random_benchmark_image_tag',
        command=mock.ANY,
        detach=False,
        environment=mock.ANY,
        network_mode='host',
        stderr=True,
        stdout=True,
        tty=True,
        volumes=mock.ANY)

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
