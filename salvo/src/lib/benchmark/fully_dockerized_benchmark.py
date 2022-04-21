"""This module contains the methods to perform a nighthawk benchmark using containers for the
scripts, nighthawk binaries, and envoy

https://github.com/envoyproxy/nighthawk/blob/master/benchmarks/README.md
"""
import logging

import api.control_pb2 as proto_control
from src.lib.benchmark import base_benchmark
from src.lib.docker_management import docker_image

log = logging.getLogger(__name__)


class FullyDockerizedBenchmarkError(Exception):
  """Error rasied when running a fully dockerized benchmark in cases where we cannot make progress due to abnormal conditions."""


class Benchmark(base_benchmark.BaseBenchmark):
  """This benchmark class is the fully dockerized benchmark. Docker images containing the benchmark scripts, binaries, and envoy are used to execute the tests."""

  def __init__(self, job_control: proto_control.JobControl, benchmark_name: str) -> None:
    """Initialize the benchmark class."""
    super(Benchmark, self).__init__(job_control, benchmark_name)

  def _validate(self) -> None:
    """Validate that all data required for running a benchmark exists.

    Verify that all required images are present in the control object.
    If not, verify that sources exist from which we can build the
    required docker images.

    Returns:
        None
    """
    verify_source = False
    images = self.get_images()

    # Determine whether we need to build the images from source
    # If so, verify that the required source data is defined
    verify_source = images is None or \
        not images.nighthawk_benchmark_image or \
        not images.nighthawk_binary_image or \
        not images.envoy_image

    log.debug(f"Source verification needed: {verify_source}")
    if verify_source:
      self._verify_sources(images)

  def execute_benchmark(self) -> None:
    """Prepare input artifacts and run the benchmark.

    Construct the volume, environment variables, and command line
    arguments needed to execute the benchmark image.

    Returns:
        None

    Raises:
      NotImplementedError: if the benchmark is configured to execute
        remotely.
      BenchmarkError: if the benchmark fails to execute successfully
    """
    self._validate()

    if self.is_remote():
      raise NotImplementedError("Local benchmarks only for the moment")

    # pull in environment and set values
    output_dir = self._control.environment.output_dir
    test_dir = self._control.environment.test_dir
    images = self.get_images()
    log.debug(f"Images: {images.nighthawk_benchmark_image}")

    # 'TMPDIR' is required for successful operation.
    image_vars = {
        'NH_DOCKER_IMAGE': images.nighthawk_binary_image,
        'ENVOY_DOCKER_IMAGE_TO_TEST': images.envoy_image,
        'TMPDIR': output_dir
    }
    log.debug(f"Using environment: {image_vars}")

    volumes = base_benchmark.get_docker_volumes(output_dir, test_dir)
    log.debug(f"Using Volumes: {volumes}")

    environment_controller = base_benchmark.BenchmarkEnvController(self._control.environment)

    run_parameters = docker_image.DockerRunParameters(
        command=['./benchmarks', '--log-cli-level=info', '-vvvv'],
        environment=image_vars,
        volumes=volumes,
        network_mode='host',
        tty=True)

    # TODO: We need to capture stdout and stderr to a file to catch docker
    # invocation issues. This may help with the escaping that we see happening
    # on an successful invocation

    with environment_controller:
      result = self.run_image(images.nighthawk_benchmark_image, run_parameters)

    # FIXME: result needs to be unescaped. We don't use this data and the same
    # content is available in the nighthawk-human.txt file.
    log.debug(f"Output: {len(result)} bytes")

    log.info(f"Benchmark output: {output_dir}")

    # Establishing success here requires that we examine the output produced by
    # NightHawk. If the latency output exists we can be relatively certain that
    # all containers were able to run and execute the specified tests
    if "benchmark_http_client" not in result.decode('utf-8'):
      raise base_benchmark.BenchmarkError(
          "Unable to assert that the benchmark executed successfully")
