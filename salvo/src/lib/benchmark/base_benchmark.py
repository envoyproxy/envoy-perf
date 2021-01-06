"""
Base Benchmark object module that contains
options common to all execution methods
"""
import os
import logging
from typing import List

from src.lib.docker import (docker_image, docker_volume)

import api.control_pb2 as proto_control
import api.image_pb2 as proto_image
import api.source_pb2 as proto_source
import api.env_pb2 as proto_env

log = logging.getLogger(__name__)


def get_docker_volumes(output_dir: str, test_dir: str = '') -> dict:
  """Build the volume structure needed to run a container.

  Build the json specifying the volume configuration needed for running the
  container.

  Args:
      output_dir: The directory containing the artifacts of the benchmark
      test_dir: If specified, points to the location of user supplied tests
        If the test_dir is not specified, the volume map will not include an
        entry for the external test directory
  """
  return docker_volume.generate_volume_config(output_dir, test_dir)


class BenchmarkError(Exception):
  """Errror raised in a benchmark for an unresolvable condition."""


class BaseBenchmark(object):
  """Base Benchmark class with common functions for all invocations."""

  def __init__(self, job_control: proto_control.JobControl,
               benchmark_name: str) -> None:
    """Initialize the Base Benchmark class.

    Args:
        job_control: The protobuf object containing the parameters and locations
          of benchmark artifacts
        benchmark_name: The name of the benchmark to execute

    Raises:
        BaseBenchmarkError: if no job control object is specified
    """
    if job_control is None:
      raise BenchmarkError("No control object received")

    self._docker_image = docker_image.DockerImage()
    self._control = job_control
    self._benchmark_name = benchmark_name

    self._mode_remote = self._control.remote
    self._build_envoy = False
    self._build_nighthawk = False

    log.debug("Running benchmark: %s %s", "Remote" if self._mode_remote \
      else "Local", self._benchmark_name)

  def is_remote(self) -> bool:
    """Return a boolean indicating whether the test is to be executed
       locally or remotely.

    Returns:
        Whether or not the benchmark runs locally or in a remote service
    """
    return self._mode_remote

  def get_images(self) -> proto_image.DockerImages:
    """Return the images object from the control object.

    Returns:
        The images objects specified in the control object
    """
    return self._control.images

  def get_source(self) -> List[proto_source.SourceRepository]:
    """Return the source object defining locations from where
       NightHawk or Envoy can be built.

    Returns:
        The source objects specified in the control object
    """
    return self._control.source

  def run_image(self, image_name: str,
                run_parameters: docker_image.DockerRunParameters) -> bytearray:
    """Run the specified docker image with the supplied keyword arguments.

    Args:
        image_name: The docker image to be executed
        run_paramters: a namedtuple of parameters supplied to an image for
          execution

    Returns:
        A bytearray containing the output produced from executing the specified
        container
    """
    return self._docker_image.run_image(image_name, run_parameters)

  def pull_images(self) -> List[str]:
    """Retrieve all images necessary for the benchmark.

    Retrieve the NightHawk and Envoy images defined in the control
    object.

    Returns:
        a List of required image names that are retrievable. If any image is
          unavailable, we return an empty list. The intent is for the caller to
          build the necessary images.

    Raises:
        BenchmarkError: if a requested image is unavailable.
    """
    retrieved_images = []
    images = self.get_images()

    for image in [
        images.nighthawk_benchmark_image,
        images.nighthawk_binary_image,
        images.envoy_image
    ]:
      # If the image name is not defined, we will have an empty string.
      # For unit testing we'll keep this behavior. For true usage, we
      # should raise an exception when the benchmark class performs its
      # validation
      if image:
        retrieved_image = self._docker_image.pull_image(image)
        log.debug(f"Retrieved image: {retrieved_image} for {image}")
        if retrieved_image is None:
          raise BenchmarkError("Unable to retrieve image: %s" % image)
        retrieved_images.append(retrieved_image)

    return retrieved_images

class BenchmarkEnvironmentError(Exception):
  """An Error raised if the environment variables required are not
     able to be set.
  """

class BenchmarkEnvController():
  """Benchmark Environment Controller context class."""

  def __init__(self, environment: proto_env.EnvironmentVars) -> None:
    """Initialize the environment controller with the environment object."""
    self._environment = environment

  def _set_environment_vars(self) -> None:
    """Build the environment variable map used to launch an image.

    Set the Envoy IP test versions and any other environment variables needed
    by the test. This method is called before we execute the docker image so
    that the image has all variables it needs for a given benchmark.

    Raises:
      BenchmarkEnvironmentError: if a required environment variable is
        unspecified
    """
    self._clear_environment_vars()

    environment = self._environment

    if environment.test_version == environment.IPV_UNSPECIFIED:
      raise BenchmarkEnvironmentError(
          "No IP version is specified for the benchmark")
    elif environment.test_version == environment.IPV_V4ONLY:
      os.environ['ENVOY_IP_TEST_VERSIONS'] = 'v4only'
    elif environment.test_version == environment.IPV_V6ONLY:
      os.environ['ENVOY_IP_TEST_VERSIONS'] = 'v6only'

    if environment.envoy_path:
      os.environ['ENVOY_PATH'] = environment.envoy_path

    for key, value in environment.variables.items():
      os.environ[key] = value

  def _clear_environment_vars(self) -> None:
    """Clear any environment variables in the job control document
       so that we do not influence additionally executing tests.
    """
    environment = self._environment

    # Check that the key exists before deleting it to prevent KeyErrors
    if 'ENVOY_IP_TEST_VERSIONS' in os.environ:
      del os.environ['ENVOY_IP_TEST_VERSIONS']

    if 'ENVOY_PATH' in os.environ:
      del os.environ['ENVOY_PATH']

    for key, _ in environment.variables.items():
      if key in os.environ:
        del os.environ[key]

  def execute_benchmark(self) -> None:
    """Interface that must be implemented to execute a given
       benchmark.

    Raises:
      NotImplementedError: if this method is not overridden
    """
    raise NotImplementedError("Execute Benchmark must be implemented")

  def __enter__(self):
    """Sets the environment variables specified in the control document."""
    self._set_environment_vars()

  def __exit__(self, type_param, value, traceback):
    """Clears any environment variables specified in the control document."""
    self._clear_environment_vars()
