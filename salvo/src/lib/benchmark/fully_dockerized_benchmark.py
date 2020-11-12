"""
This module contains the methods to perform a nighthawk benchmark using
containers for the scripts, nighthawk binaries, and envoy

https://github.com/envoyproxy/nighthawk/blob/master/benchmarks/README.md
"""

import logging

from src.lib.benchmark.base_benchmark import BaseBenchmark

log = logging.getLogger(__name__)


class Benchmark(BaseBenchmark):

  def __init__(self, **kwargs):
    super(Benchmark, self).__init__(**kwargs)

  def validate(self):
    """
    Validate that all data required for running the dockerized
    benchmark is defined and or accessible
    """
    pass

  def _verify_sources(self, images):
    """
    Validate that sources are available from which we can build a missing image
    """
    pass

  def execute_benchmark(self):
    """
    Prepare input artifacts and run the benchmark
    """
    pass
