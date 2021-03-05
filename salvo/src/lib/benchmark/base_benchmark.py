"""
Base Benchmark object module that contains common methods for all benchmarks
"""
import abc
import os
import logging
from typing import List

from src.lib.docker import (docker_image, docker_volume)
import api.control_pb2 as proto_control
import api.image_pb2 as proto_image
import api.source_pb2 as proto_source
import api.env_pb2 as proto_env

log = logging.getLogger(__name__)

_VARIABLES_TO_CLEAR_AND_RESTORE = [
    'RUNFILES_MANIFEST_FILE'  # This variable is set by the outer bazel
                              # invocation and negatively impacts invoking
                              # bazel to run the scavenging benchmark
]

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


class BaseBenchmark(abc.ABC):
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

    log.debug(f"Running benchmark: %s {self._benchmark_name} [{self}]",
              "Remote" if self._mode_remote else "Local")

  def get_name(self) -> str:
    """Return the name of the benchmark being executed."""
    return self._benchmark_name

  def get_image(self) -> str:
    """Return the name of the envoy image being tested."""
    return self._control.images.envoy_image

  def _verify_sources(self, images: proto_image.DockerImages) -> None:
    """Validate that sources are available to build a missing image.

    Verify that a source definition exists that can build a missing
    image needed for the benchmark.

    Args:
      images: The defined images and versions needed to conduct the
        benchmark

    Returns:
        None

    Raises:
        BenchmarkError: if no source definitions allow us to build missing
          docker images.
    """
    source = self.get_source()
    if not source:
      raise BenchmarkError("No source configuration specified")

    can_build_envoy = False
    can_build_nighthawk = False

    for source_def in source:
      # Cases:
      # Missing envoy image -> Need to see an envoy source definition
      # Missing at least one nighthawk image -> Need to see a nighthawk source

      if source_def.identity == source_def.SRCID_UNSPECIFIED:
        raise BenchmarkError("No source identity specified")

      if not images.envoy_image \
          and source_def.identity == source_def.SRCID_ENVOY:
        can_build_envoy = True

      if (not images.nighthawk_benchmark_image or not images.nighthawk_binary_image) \
          and source_def.identity == source_def.SRCID_NIGHTHAWK:
        can_build_nighthawk = True

    if not images.envoy_image and not can_build_envoy:
      raise BenchmarkError("No source specified to build Envoy image")

    if (not images.nighthawk_benchmark_image or not images.nighthawk_binary_image) \
        and not can_build_nighthawk:
      raise BenchmarkError("No source specified to build NightHawk image")

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

  @abc.abstractmethod
  def execute_benchmark(self) -> None:
    """Run a benchmark

    A class derived from BaseBenchmark is responsible for building and staging
    the required binaries, tests, and any other artifacts for running a
    benchmark.

    For example in the scavenging benchmark, that class must prepare
    the NightHawk benchmark and binary docker image, as well as build an Envoy
    docker image for the version being tested, if none of these artifacts are
    already available.

    Once all artifact preparation is done, execute benchmark is called where
    the enviroment variables required to run the benchmark are populated and
    the command to invoke the benchmark is built and executed.

    Classes derived from BaseBenchmark must override execute_benchmark since
    this is a common operation shared by all benchmarks and the individual
    execution steps differ among them.

    The method should raise a BenchmarkError if the test fails to complete.

    All output from the NightHawk invocation is written to the location defined
    by the TMPDIR environment variable which is populated from the "output_dir"
    field in the job control document.
    """

class BenchmarkEnvironmentError(Exception):
  """An Error raised if the environment variables required are not
     able to be set.
  """

class BenchmarkEnvController():
  """Benchmark Environment Controller context class."""

  def __init__(self, environment: proto_env.EnvironmentVars) -> None:
    """Initialize the environment controller with the environment object."""
    self._environment = environment
    self._preserved_vars = {}

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
      log.debug(f"Setting ENVOY_PATH={environment.envoy_path}")
      os.environ['ENVOY_PATH'] = environment.envoy_path

    for key, value in environment.variables.items():
      log.debug(f"Setting environment {key}={value}")
      os.environ[key] = value

  def _preserve_and_clear_special_vars(self) -> None:
    """Store the name and value for any special variables."""
    for variable in _VARIABLES_TO_CLEAR_AND_RESTORE:
      if variable in os.environ:
        self._preserved_vars[variable] = os.environ[variable]
        del os.environ[variable]

  def _restore_special_vars(self):
    """Restore any saved environment variables."""
    for key, value in self._preserved_vars.items():
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

  def __enter__(self):
    """Sets the environment variables specified in the control document."""

    self._preserve_and_clear_special_vars()
    self._set_environment_vars()

  def __exit__(self, type_param, value, traceback):
    """Clears any environment variables specified in the control document."""
    self._clear_environment_vars()
    self._restore_special_vars()
