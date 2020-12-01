#!/usr/bin/env python3
"""
Test Docker interactions
"""

import os
import re
import site
import pytest

site.addsitedir("src")

from src.lib.constants import DOCKER_SOCKET_PATH
from src.lib.docker_image import DockerImage


def test_pull_image():
  """Test retrieving an image.

  Verify that we can pull a docker image specifying only
  its name and tag
  """

  if not os.path.exists(DOCKER_SOCKET_PATH):
    pytest.skip("Skipping docker test since no socket is available")

  docker_image = DockerImage()
  container = docker_image.pull_image("amazonlinux:2")
  assert container is not None


def test_run_image():
  """Test executing a command in an image.

  Verify that we can construct the parameters needed to execute
  a given docker image.  We verify that the output contains
  the expected output from the issued command
  """

  if not os.path.exists(DOCKER_SOCKET_PATH):
    pytest.skip("Skipping docker test since no socket is available")

  env = ['key1=val1', 'key2=val2']
  cmd = ['uname', '-r']
  image_name = 'amazonlinux:2'

  docker_image = DockerImage()
  kwargs = {}
  kwargs['environment'] = env
  kwargs['command'] = cmd
  result = docker_image.run_image(image_name, **kwargs)

  assert result is not None
  assert re.match(r'[0-9\-a-z]', result.decode('utf-8')) is not None


def test_list_images():
  """Test listing available images.

  Verify that we can list all existing cached docker images.
  """

  if not os.path.exists(DOCKER_SOCKET_PATH):
    pytest.skip("Skipping docker test since no socket is available")

  docker_image = DockerImage()
  images = docker_image.list_images()
  assert images != []


if __name__ == '__main__':
  raise SystemExit(pytest.main(['-s', '-v', __file__]))
