"""
This module contains the methods to perform a Binary benchmark using
containers for the scripts, nighthawk binaries, and envoy

https://github.com/envoyproxy/nighthawk/blob/master/benchmarks/README.md
"""

import subprocess
import logging
import os

import api.control_pb2 as proto_control
import api.source_pb2 as proto_source

from src.lib.benchmark import base_benchmark
from src.lib.builder import (envoy_builder, nighthawk_builder)
from src.lib import (cmd_exec, source_manager)

log = logging.getLogger(__name__)


class BinaryBenchmarkError(Exception):
  """Error raised when running a binary benchmark in cases
     where we cannot make progress due to abnormal conditions.
  """

class Benchmark(base_benchmark.BaseBenchmark):
  """This benchmark class is the binary benchmark. We use a path to an Envoy
     binary to execute the Nighthawk benchmarks using that specific build.
  """

  def __init__(
    self, job_control: proto_control.JobControl, benchmark_name: str) -> None:
    """ Initializes the benchmark class

    Args:
        job_control: The protobuf object containing the parameters and locations
          of benchmark artifacts
        benchmark_name: The name of the benchmark to execute

    Raises:
        BaseBenchmarkError: if no job control object is specified
    """

    super(Benchmark, self).__init__(job_control, benchmark_name)
    self._benchmark_dir = None
    self._envoy_binary_path = job_control.environment.variables['ENVOY_PATH']
    self._envoy_builder = None
    self._nighthawk_builder = None
    self._source_manager = source_manager.SourceManager(job_control)

  def _validate(self) -> None:
    """Validate that all data required for running a benchmark exists.

    Verify that a source has been specified with which to build Nighthawk,
    warns the user if no valid Envoy binary is specified.

    Returns:
        None

    Raises:
        BinaryBenchmarkError: Source configuration is missing, invalid, or incomplete
    """

    source = self.get_source()
    if not source:
      raise BinaryBenchmarkError("No source configuration specified")

    can_build_envoy = False
    can_build_nighthawk = False

    for source_def in source:
      if source_def.identity == source_def.SRCID_UNSPECIFIED:
        raise BinaryBenchmarkError("No source identity specified")

      if source_def.identity == source_def.SRCID_ENVOY and \
        (source_def.source_path or source_def.source_url):
        can_build_envoy = True

      if source_def.identity == source_def.SRCID_NIGHTHAWK and \
        (source_def.source_path or source_def.source_url):
        can_build_nighthawk = True

    if not can_build_nighthawk:
      raise BinaryBenchmarkError("No source specified to build Nighthawk")

    if not (can_build_envoy or self._envoy_binary_path):
      raise BinaryBenchmarkError("No Envoy source or binary was specified")


  def _prepare_nighthawk(self) -> None:
    """Prepare the nighthawk source for the benchmark.

    Checks out the nighthawk source if necessary, builds the client
    and server binaries

    """

    self._nighthawk_builder = nighthawk_builder.NightHawkBuilder(self._source_manager)
    self._nighthawk_builder.build_nighthawk_binaries()
    self._nighthawk_builder.build_nighthawk_benchmarks()

    nighthawk_source = self._source_manager.get_source_tree(
        proto_source.SourceRepository.SourceIdentity.SRCID_NIGHTHAWK
    )
    self._benchmark_dir = nighthawk_source.get_source_directory()

  def _prepare_envoy(self) -> None:
    """Prepare the envoy source for the benchmark.

    Raises:
      BinaryBenchmarkError: an invalid envoy binary is specified via ENVOY_PATH
    """
    if self._envoy_binary_path:
      if not (os.path.exists(self._envoy_binary_path) \
          and os.access(self._envoy_binary_path, os.X_OK)):
        raise BinaryBenchmarkError("ENVOY_PATH environment variable specified, but invalid")
      # We already have a binary, no need to build
      log.info("Using Envoy binary specified in ENVOY_PATH environment variable")
      return

    self._envoy_builder = envoy_builder.EnvoyBuilder(self._source_manager)
    self._envoy_binary_path = self._envoy_builder.build_envoy_binary_from_source()


  def execute_benchmark(self) -> None:
    """Execute the binary benchmark

    Uses either the Envoy specified in ENVOY_PATH, or one built from a
    specified source.
    """

    self._validate()
    self._prepare_nighthawk()
    self._prepare_envoy()

    #todo: refactor args, have frontend specify them via protobuf
    cmd = ("bazel test "
           "--test_summary=detailed "
           "--test_output=all "
           "--test_arg=--log-cli-level=info "
           "--test_env=ENVOY_IP_TEST_VERSIONS=v4only "
           "--test_env=HEAPPROFILE= "
           "--test_env=HEAPCHECK= "
           "--cache_test_results=no "
           "--compilation_mode=opt "
           "--cxxopt=-g "
           "--cxxopt=-ggdb3 "
           "--define tcmalloc=gperftools "
           "//benchmarks:* ")

    cmd_params = cmd_exec.CommandParameters(cwd=self._benchmark_dir)

    # pull in environment and set values
    env = self._control.environment

    # 'TMPDIR' is required for successful operation.  This is the output
    # directory for all produced NightHawk artifacts
    binary_benchmark_vars = {
      'TMPDIR': env.output_dir
    }
    if self._envoy_binary_path:
      binary_benchmark_vars['ENVOY_PATH'] = self._envoy_binary_path

    log.debug(f"Using environment: {binary_benchmark_vars}")

    for (key, value) in binary_benchmark_vars.items():
      if key not in env.variables:
        log.debug(f"Building control environment variables: {key}={value}")
        env.variables[key] = value

    environment_controller = base_benchmark.BenchmarkEnvController(env)

    with environment_controller:
      try:
        cmd_exec.run_command(cmd, cmd_params)
      except subprocess.CalledProcessError as cpe:
        log.error(f"Unable to execute the benchmark: {cpe}")
