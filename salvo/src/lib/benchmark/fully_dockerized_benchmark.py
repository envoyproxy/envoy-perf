"""
This module contains the methods to perform a nighthawk benchmark using
containers for the scripts, nighthawk binaries, and envoy

https://github.com/envoyproxy/nighthawk/blob/master/benchmarks/README.md
"""

import logging

from src.lib.benchmark.base_benchmark import (BaseBenchmark, get_docker_volumes)
from api.control_pb2 import JobControl
from api.image_pb2 import DockerImages

log = logging.getLogger(__name__)


class Benchmark(BaseBenchmark):
  """This is the base class from which all benchmark objecs are derived.
     All common methods for benchmarks should be defined here.
  """

  def __init__(self, job_control: JobControl, benchmark_name: str) -> None:
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

    return

  def _verify_sources(self, images: DockerImages) -> None:
    """Validate that sources are available to build a missing image.

    Verify that a source definition exists tht can build a missing
    image needed for the benchmark.

    Returns:
        None

    Raises:
        an Exception if no source definitions allow us to build
          missing docker images.
    """
    source = self.get_source()
    if not source:
      raise Exception("No source configuration specified")

    can_build_envoy = False
    can_build_nighthawk = False

    for source_def in source:
      # Cases:
      # Missing envoy image -> Need to see an envoy source definition
      # Missing at least one nighthawk image -> Need to see a nighthawk source

      if source_def.identity == source_def.SRCID_UNSPECIFIED:
        raise Exception("No source identity specified")

      if not images.envoy_image \
          and source_def.identity == source_def.SRCID_ENVOY and \
          (source_def.source_path or source_def.source_url):
        can_build_envoy = True

      if (not images.nighthawk_benchmark_image or not images.nighthawk_binary_image) \
          and source_def.identity == source_def.SRCID_NIGHTHAWK and \
          (source_def.source_path or source_def.source_url):
        can_build_nighthawk = True

      if (not images.envoy_image and not can_build_envoy) or \
          (not images.nighthawk_benchmark_image or not images.nighthawk_binary_image) \
              and not can_build_nighthawk:
        # If the Envoy image is specified, then the validation failed for
        # NightHawk and vice versa
        msg = "No source specified to build unspecified {image} image".format(
            image="NightHawk" if images.envoy_image else "Envoy")
        raise Exception(msg)


  def execute_benchmark(self) -> None:
    """Prepare input artifacts and run the benchmark.

    Construct the volume, environment variables, and command line
    arguments needed to execute the benchmark image.

    Returns:
        None

    Raises:
      NotImplementedError if the benchmark is configured to execute
        remotely.
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

    volumes = get_docker_volumes(output_dir, test_dir)
    log.debug(f"Using Volumes: {volumes}")
    self.set_environment_vars()

    kwargs = {}
    kwargs['environment'] = image_vars
    kwargs['command'] = ['./benchmarks', '--log-cli-level=info', '-vvvv']
    kwargs['volumes'] = volumes
    kwargs['network_mode'] = 'host'
    kwargs['tty'] = True

    # TODO: We need to capture stdout and stderr to a file to catch docker
    # invocation issues. This may help with the escaping that we see happening
    # on an successful invocation
    result = self.run_image(images.nighthawk_benchmark_image, **kwargs)

    # FIXME: result needs to be unescaped. We don't use this data and the same
    # content is available in the nighthawk-human.txt file.
    log.debug(f"Output: {len(result)} bytes")

    log.info(f"Benchmark output: {output_dir}")

    return

