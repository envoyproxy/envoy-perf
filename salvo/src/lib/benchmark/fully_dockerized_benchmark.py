"""
This module contains the methods to perform a nighthawk benchmark using
containers for the scripts, nighthawk binaries, and envoy

https://github.com/envoyproxy/nighthawk/blob/master/benchmarks/README.md
"""

import logging

from src.lib.benchmark.base_benchmark import BaseBenchmark
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
    """Validate that all data required for running a benchmark exist.

    Returns:
        None
    """
    pass

  def _verify_sources(self, images: DockerImages) -> None:
    """Validate that sources are available to build a missing image.

    Returns:
        None
    """
    pass

  def execute_benchmark(self) -> None:
    """Prepare input artifacts and run the benchmark.

    Returns:
        None
    """
    self._validate()
