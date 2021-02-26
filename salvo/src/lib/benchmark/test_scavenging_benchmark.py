"""
Test the scavenging benchmark class
"""
import pytest
from unittest import mock

from src.lib.benchmark import (base_benchmark, scavenging_benchmark,
                               test_common)
from src.lib.builder import nighthawk_builder
from src.lib import source_manager

def test_execute_benchmark_no_images_or_sources():
  """Verify the benchmark fails if no images or sources are present."""
  pass

def test_execute_benchmark_nighthawk_source_only():
  """Verify that we detect missing Envoy sources."""
  pass

def test_execute_benchmark_envoy_source_only():
  """Verify that we detect missing NightHawk sources."""
  pass

def test_execute_benchmark_no_environment():
  """Verify that we fail a benchmark if no environment is set."""
  pass

def test_execute_benchmark():
  """Verify that we can successfully execute a benchmark."""
  pass

if __name__ == '__main__':
  raise SystemExit(pytest.main(['-s', '-v', __file__]))
