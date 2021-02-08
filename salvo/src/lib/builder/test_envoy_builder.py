"""
Test envoy building operations
"""
import logging
import pytest
from unittest import mock

import api.source_pb2 as proto_source
import api.control_pb2 as proto_control
from src.lib.builder import envoy_builder
from src.lib import (constants, source_tree, source_manager)

logging.basicConfig(level=logging.DEBUG)

def test_build_envoy_image_from_source():
  """Verify the calls made to build an envoy image from a source tree."""
  pass

def test_build_envoy_image_from_source_fail():
  """Verify an exception is raised if the source identity is invalid"""
  pass

def test_stage_envoy():
  """Verify the commands used to stage the envoy binary for docker image
  construction.
  """
  pass

def test_create_docker_image():
  """Verify that we issue the correct commands to build an envoy docker
  image.
  """
  pass

def _generate_default_source_manager():
  """Build a default SourceRepository object."""

  control = proto_control.JobControl(remote=False, scavenging_benchmark=True)
  control.source.add(
      identity=proto_source.SourceRepository.SourceIdentity.SRCID_ENVOY,
      source_path='/some_random_envoy_directory',
      commit_hash='v1.16.0'
  )
  return source_manager.SourceManager(control)

if __name__ == '__main__':
  raise SystemExit(pytest.main(['-s', '-v', __file__]))
