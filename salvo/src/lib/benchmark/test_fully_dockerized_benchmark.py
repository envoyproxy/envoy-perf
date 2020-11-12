#!/usr/bin/env python3
"""
Test the fully dockerized benchmark class
"""

import site
import pytest

from api.control_pb2 import JobControl
from src.lib.benchmark.fully_dockerized_benchmark import Benchmark


def test_images_only_config():
  """
  Test benchmark validation logic
  """
  pass


def test_no_envoy_image_no_sources():
  """
  Test benchmark validation logic.  No Envoy image is specified, we
  expect the validation logic to throw an exception since no sources are present
  """
  pass

def test_source_to_build_envoy():
  """
  Validate that sources are defined that enable us to build the Envoy image
  We do not expect the validation logic to throw an exception
  """
  pass

def test_no_source_to_build_envoy():
  """
  Validate that no sources are present that enable us to build the missing Envoy image
  We expect the validation logic to throw an exception
  """
  pass

def test_no_source_to_build_nh():
  """
  Validate that no sources are defined that enable us to build the missing NightHawk
  benchmark image
  We expect the validation logic to throw an exception
  """
  pass

def test_no_source_to_build_nh2():
  """
  Validate that no sources are defined that enable us to build the missing NightHawk
  binary image
  We expect the validation logic to throw an exception
  """
  pass

if __name__ == '__main__':
  raise SystemExit(pytest.main(['-s', '-v', __file__]))
