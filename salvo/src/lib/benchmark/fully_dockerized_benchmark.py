"""
This module contains the methods to perform a nighthawk benchmark using
containers for the scripts, nighthawk binaries, and envoy

https://github.com/envoyproxy/nighthawk/blob/master/benchmarks/README.md
"""

import logging

from src.lib.benchmark.base_benchmark import BaseBenchmark

log = logging.getLogger(__name__)


class Benchmark(BaseBenchmark):

  def __init__(self, job_control, benchmark_name):
    """Initialize the benchmark class."""
    super(Benchmark, self).__init__(job_control, benchmark_name)

  def _validate(self):
    """Validate that all data required for running a benchmark exist.

    Returns:
        None
    """
    pass

  def _verify_sources(self, images):
    """Validate that sources are available to build a missing image.

    Returns:
        None
    """
    pass

  def execute_benchmark(self):
    """Prepare input artifacts and run the benchmark.

    Returns:
        None
    """
    self._validate()
