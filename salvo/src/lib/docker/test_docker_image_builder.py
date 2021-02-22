"""
Test Docker image build logic.  Most of these test are shallow and do not
verify the git operations being automated.
"""
import logging
import pytest
from unittest import mock

from src.lib import source_manager
from src.lib.docker import docker_image_builder as image_builder
from src.lib.docker import docker_image
from src.lib.builder import (envoy_builder, nighthawk_builder)

import api.source_pb2 as proto_source
import api.control_pb2 as proto_control

logging.basicConfig(level=logging.DEBUG)
log = logging.getLogger(__name__)

def generate_image_manager_with_source_url():
  """Generate a source manager with a job control specifying remote repos
  for images.
  """
  pass


def test_build_envoy_docker_image():
  """Verify that we can build an envoy docker image"""
  pass


def test_build_missing_envoy_docker_image():
  """Verify we build an image only if it is not present and no build options
  are present"""
  pass


def test_build_missing_envoy_docker_image_image_present():
  """Verify we do not build an image if it is present and no build options
  are present"""
  pass

def test_build_missing_envoy_docker_image_options_present():
  """Verify we build an image if build options are present"""
  pass

def test_build_envoy_image_from_source():
  """Verify that we return the tag of a constructed image.  This is a shallow
  test and does not invoke any git operations to manipulate the source.
  """
  pass

def test_generate_envoy_image_name_from_tag():
  """Verify we create the correct image name from its tag.  For images built
  from a release tag, we use 'envoyproxy/envoy', anything else uses
  'envoyproxy/envoy-dev'
  """
  pass

def test_get_image_prefix():
  """Verify we return the correct image prefix given a tag or hash"""
  pass

def test_build_nighthawk_benchmark_image_from_source():
  """Verify that we build the nighthawk benchmark container from a source
  tree.
  """
  pass

def test_build_nighthawk_binary_image_from_source():
  """Verify that we build the nighthawk binary container from a source
  tree.
  """
  pass

if __name__ == '__main__':
  raise SystemExit(pytest.main(['-s', '-v', __file__]))
