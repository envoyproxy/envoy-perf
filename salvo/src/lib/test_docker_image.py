#!/usr/bin/env python3
"""
Test Docker interactions
"""

import os
import re
import site
import pytest

site.addsitedir("src")

from lib.docker_image import DockerImage


def test_pull_image():
  """Test retrieving an image"""

  if not os.path.exists("/var/run/docker.sock"):
    pytest.skip("Skipping docker test since no socket is available")

  docker_image = DockerImage()
  container = docker_image.pull_image("oschaaf/benchmark-dev:latest")
  assert container is not None


def test_run_image():
  """Test executing a command in an image"""

  if not os.path.exists("/var/run/docker.sock"):
    pytest.skip("Skipping docker test since no socket is available")

  env = ['key1=val1', 'key2=val2']
  cmd = ['uname', '-r']
  image_name = 'oschaaf/benchmark-dev:latest'

  docker_image = DockerImage()
  kwargs = {}
  kwargs['environment'] = env
  kwargs['command'] = cmd
  result = docker_image.run_image(image_name, **kwargs)

  assert result is not None
  assert re.match(r'[0-9\-a-z]', result.decode('utf-8')) is not None


def test_list_images():
  """Test listing available images"""

  if not os.path.exists("/var/run/docker.sock"):
    pytest.skip("Skipping docker test since no socket is available")

  docker_image = DockerImage()
  images = docker_image.list_images()
  assert images != []


if __name__ == '__main__':
  raise SystemExit(pytest.main(['-s', '-v', __file__]))
