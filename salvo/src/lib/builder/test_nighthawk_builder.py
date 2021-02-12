"""
Test envoy building operations
"""
import pytest
from unittest import mock

import api.source_pb2 as proto_source
import api.control_pb2 as proto_control
from src.lib.builder import nighthawk_builder
from src.lib import (cmd_exec, constants, source_tree, source_manager)

def test_prepare_nighthawk_source_fail():
  """Verify an exception is raised if the source identity is invalid"""
  pass

def test_prepare_nighthawk_source():
  """Verify that we are able to get a source tree on disk to build NightHawk"""
  pass

def test_build_nighthawk_benchmarks():
  """Verify the calls made to build the nighthawk benchmarks target"""
  pass

def test_build_nighthawk_binaries():
  """Verify the calls made to build nighthawk binaries"""
  pass

def test_build_nighthawk_benchmark_image():
  """Verify that we can build the nighthawk benchmark image"""
  pass

def test_build_nighthawk_binary_image():
  """Verify that we can build the nighthawk benchmark image"""
  pass

if __name__ == '__main__':
  raise SystemExit(pytest.main(['-s', '-v', __file__]))
