"""
Perform a Scavenging benchmark

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
    pass

  def _prepare_nighthawk(self) -> None:
    """Prepare the nighthawk source for the benchmark.

    Checks out the nighthawk source if necessary, builds the nighthawk client
    and server binaries

    """
    pass

  def execute_benchmark(self) -> None:
    """Execute the scavenging benchmark."""
    pass
