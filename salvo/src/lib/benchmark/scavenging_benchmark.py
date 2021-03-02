"""
This module contains the methods to perform a Scavenging benchmark using
containers for the scripts, nighthawk binaries, and envoy

https://github.com/envoyproxy/nighthawk/blob/master/benchmarks/README.md
"""

import subprocess
import logging

import api.control_pb2 as proto_control
import api.source_pb2 as proto_source

from src.lib.benchmark import base_benchmark
from src.lib.builder import nighthawk_builder
from src.lib import (cmd_exec, source_manager)

log = logging.getLogger(__name__)

class ScavengingBenchmarkError(Exception):
  """Error rasied when running a scavenging benchmark in cases
     where we cannot make progress due to abnormal conditions.
  """

class Benchmark(base_benchmark.BaseBenchmark):
  """This benchmark class is the scavenging benchmark. We build the nighthawk
     binaries and scripts, then execute "bazel test" to run all tests in the
     benchmarks directory
  """

  def __init__(
      self, job_control: proto_control.JobControl, benchmark_name: str) -> None:
    """Initialize the benchmark class."""

    self._benchmark_dir = None
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

  def _prepare_nighthawk(self) -> None:
    """Prepare the nighthawk source for the benchmark.

    Checks out the nighthawk source if necessary, builds the client
    and server binaries

    """
    manager = source_manager.SourceManager(self._control)

    # This builder needs to be a self object so that the temporary cache
    # directory is not prematurely cleaned up
    self._nighthawk_builder = nighthawk_builder.NightHawkBuilder(manager)

    # FIXME: We build this for each envoy image that we test.
    self._nighthawk_builder.build_nighthawk_benchmarks()

    nighthawk_source = manager.get_source_tree(
        proto_source.SourceRepository.SourceIdentity.SRCID_NIGHTHAWK
    )
    self._benchmark_dir = nighthawk_source.get_source_directory()
    log.debug(f"NightHawk benchmark dir {self._benchmark_dir}")

  def execute_benchmark(self) -> None:
    """Execute the scavenging benchmark."""

    self._validate()
    self._prepare_nighthawk()

    # pull in environment and set values
    env = self._control.environment
    output_dir = env.output_dir
    images = self.get_images()
    log.debug(f"Images: {images.nighthawk_benchmark_image}")

    # 'TMPDIR' is required for successful operation.  This is the output
    # directory for all produced NightHawk artifacts
    image_vars = {
        'NH_DOCKER_IMAGE': images.nighthawk_binary_image,
        'ENVOY_DOCKER_IMAGE_TO_TEST': images.envoy_image,
        'TMPDIR': output_dir
    }
    log.debug(f"Using environment: {image_vars}")

    for (key, value) in image_vars.items():
      if key not in env.variables:
        log.debug(f"Building control environment variables: {key}={value}")
        env.variables[key] = value

    environment_controller = base_benchmark.BenchmarkEnvController(env)

    cmd = ("bazel-bin/benchmarks/benchmarks "
           "--log-cli-level=info -vvvv -k test_http_h1_small "
           "benchmarks/")
    cmd_params = cmd_exec.CommandParameters(cwd=self._benchmark_dir)

    with environment_controller:
      try:
        cmd_exec.run_command(cmd, cmd_params)
      except subprocess.CalledProcessError as cpe:
        log.error(f"Unable to execute the benchmark: {cpe}")
