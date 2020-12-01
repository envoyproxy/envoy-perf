"""
Test the fully dockerized benchmark class
"""

import pytest
from unittest import mock

from api.control_pb2 import JobControl
from src.lib.benchmark.fully_dockerized_benchmark import Benchmark


def test_images_only_config():
  """Test benchmark validation logic.

  Validate that we attempt to run the specified docker image
  when all parameters are present.
  """
  # create a valid configuration defining images only for benchmark
  job_control = JobControl()
  job_control.remote = False
  job_control.scavenging_benchmark = True

  docker_images = job_control.images
  docker_images.reuse_nh_images = True
  docker_images.nighthawk_benchmark_image = \
      "envoyproxy/nighthawk-benchmark-dev:test_images_only_config"
  docker_images.nighthawk_binary_image = \
      "envoyproxy/nighthawk-dev:test_images_only_config"
  docker_images.envoy_image = \
      "envoyproxy/envoy-dev:f61b096f6a2dd3a9c74b9a9369a6ea398dbe1f0f"

  env = job_control.environment
  env.variables["TMP_DIR"] = "/home/ubuntu/nighthawk_output"
  env.test_version = env.IPV_V4ONLY
  env.envoy_path = "envoy"

  benchmark = Benchmark(job_control, "test_benchmark")

  # Calling execute_benchmark shoud not throw an exception
  # Mock the container invocation so that we don't try to pull an image
  with mock.patch('docker.models.containers.ContainerCollection.run') as docker_mock:
    benchmark.execute_benchmark()
    docker_mock.assert_called_once_with(
        'envoyproxy/nighthawk-benchmark-dev:test_images_only_config',
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
  job_control = JobControl()
  job_control.remote = False
  job_control.scavenging_benchmark = True

  docker_images = job_control.images
  docker_images.reuse_nh_images = True
  docker_images.reuse_nh_images = True
  docker_images.nighthawk_benchmark_image = \
      "envoyproxy/nighthawk-benchmark-dev:test_missing_envoy_image"
  docker_images.nighthawk_binary_image = \
      "envoyproxy/nighthawk-dev:test_missing_envoy_image"

  benchmark = Benchmark(job_control, "test_benchmark")

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
  job_control = JobControl()
  job_control.remote = False
  job_control.scavenging_benchmark = True

  docker_images = job_control.images
  docker_images.reuse_nh_images = True
  docker_images.nighthawk_benchmark_image = \
      "envoyproxy/nighthawk-benchmark-dev:test_source_present_to_build_envoy"
  docker_images.nighthawk_binary_image = \
      "envoyproxy/nighthawk-dev:test_source_present_to_build_envoy"

  envoy_source = job_control.source.add()
  envoy_source.identity = envoy_source.SRCID_ENVOY
  envoy_source.source_path = "/home/ubuntu/envoy"
  envoy_source.source_url = "https://github.com/envoyproxy/envoy.git"
  envoy_source.branch = "master"
  envoy_source.commit_hash = "hash_doesnt_really_matter_here"

  env = job_control.environment
  env.test_version = env.IPV_V4ONLY
  env.envoy_path = 'envoy'
  env.output_dir = 'some_output_dir'
  env.test_dir = 'some_test_dir'

  benchmark = Benchmark(job_control, "test_benchmark")

  # Mock the container invocation so that we don't try to pull an image
  with mock.patch('docker.models.containers.ContainerCollection.run') as docker_mock:
    benchmark.execute_benchmark()
    docker_mock.assert_called_once_with(
        'envoyproxy/nighthawk-benchmark-dev:test_source_present_to_build_envoy',
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
  job_control = JobControl()
  job_control.remote = False
  job_control.scavenging_benchmark = True

  docker_images = job_control.images
  docker_images.reuse_nh_images = True
  docker_images.nighthawk_benchmark_image = \
      "envoyproxy/nighthawk-benchmark-dev:test_no_source_present_to_build_envoy"
  docker_images.nighthawk_binary_image = \
      "envoyproxy/nighthawk-dev:test_no_source_present_to_build_envoy"

  envoy_source = job_control.source.add()

  # Denote that the soure is for nighthawk.  Values aren't really checked at
  # this stage since we have a missing Envoy image and a nighthawk source
  # validation should fail.
  envoy_source.identity = envoy_source.SRCID_NIGHTHAWK
  envoy_source.source_path = "/home/ubuntu/envoy"
  envoy_source.source_url = "https://github.com/envoyproxy/envoy.git"
  envoy_source.branch = "master"
  envoy_source.commit_hash = "hash_doesnt_really_matter_here"

  benchmark = Benchmark(job_control, "test_benchmark")

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
  job_control = JobControl()
  job_control.remote = False
  job_control.scavenging_benchmark = True

  docker_images = job_control.images
  docker_images.reuse_nh_images = True
  docker_images.nighthawk_benchmark_image = \
      "envoyproxy/nighthawk-benchmark-dev:test_no_source_to_build_nh"
  docker_images.envoy_image = \
      "envoyproxy/envoy-dev:test_no_source_to_build_nh"

  envoy_source = job_control.source.add()

  # Denote that the soure is for envoy.  Values aren't really checked at this
  # stage since we have a missing Envoy image and a nighthawk source validation
  # should fail.
  envoy_source.identity = envoy_source.SRCID_ENVOY
  envoy_source.source_path = "/home/ubuntu/envoy"
  envoy_source.source_url = "https://github.com/envoyproxy/envoy.git"
  envoy_source.branch = "master"
  envoy_source.commit_hash = "hash_doesnt_really_matter_here"

  benchmark = Benchmark(job_control, "test_benchmark")

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
  job_control = JobControl()
  job_control.remote = False
  job_control.scavenging_benchmark = True

  docker_images = job_control.images
  docker_images.envoy_image = \
      "envoyproxy/envoy-dev:test_no_source_present_to_build_both_nighthawk_images"

  envoy_source = job_control.source.add()

  # Denote that the soure is for envoy.  Values aren't really checked at this
  # stage since we have a missing Envoy image and a nighthawk source validation
  # should fail.
  envoy_source.identity = envoy_source.SRCID_ENVOY
  envoy_source.source_path = "/home/ubuntu/envoy"
  envoy_source.source_url = "https://github.com/envoyproxy/envoy.git"
  envoy_source.branch = "master"
  envoy_source.commit_hash = "hash_doesnt_really_matter_here"

  benchmark = Benchmark(job_control, "test_benchmark")

  # Calling execute_benchmark shoud not throw an exception
  with pytest.raises(Exception) as validation_exception:
    benchmark.execute_benchmark()

  assert str(validation_exception.value) == \
      "No source specified to build unspecified NightHawk image"


if __name__ == '__main__':
  raise SystemExit(pytest.main(['-s', '-v', __file__]))
