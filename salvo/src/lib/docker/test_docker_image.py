#!/usr/bin/env python3
"""
Test Docker interactions
"""

import os
import re
import pytest

import src.lib.constants as constants
import src.lib.docker.docker_image as docker_image


def test_pull_image():
  """Test retrieving an image.

  Verify that we can pull a docker image specifying only
  its name and tag
  """

  if not os.path.exists(constants.DOCKER_SOCKET_PATH):
    pytest.skip("Skipping docker test since no socket is available")

  new_docker_image = docker_image.DockerImage()
  container = new_docker_image.pull_image("amazonlinux:2")
  assert container is not None


def test_run_image():
  """Test executing a command in an image.

  Verify that we can construct the parameters needed to execute
  a given docker image.  We verify that the output contains
  the expected output from the issued command
  """

  if not os.path.exists(constants.DOCKER_SOCKET_PATH):
    pytest.skip("Skipping docker test since no socket is available")

  env = ['key1=val1', 'key2=val2']
  cmd = ['uname', '-r']
  image_name = 'amazonlinux:2'

  new_docker_image = docker_image.DockerImage()
  run_parameters = docker_image.DockerRunParameters(
      environment=env,
      command=cmd,
      volumes={},
      network_mode='host',
      tty=True
  )
  result = new_docker_image.run_image(image_name, run_parameters)

  assert result is not None
  assert re.match(r'[0-9\-a-z]', result.decode('utf-8')) is not None


def test_list_images():
  """Test listing available images.

  Verify that we can list all existing cached docker images.
  """

  if not os.path.exists(constants.DOCKER_SOCKET_PATH):
    pytest.skip("Skipping docker test since no socket is available")

  new_docker_image = docker_image.DockerImage()
  images = new_docker_image.list_images()
  assert images != []


if __name__ == '__main__':
  raise SystemExit(pytest.main(['-s', '-v', __file__]))
