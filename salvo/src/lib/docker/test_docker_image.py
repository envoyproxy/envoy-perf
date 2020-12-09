"""
Test Docker interactions
"""

import os
import re
import pytest
import docker
from unittest import mock

from src.lib import constants
from src.lib.docker import docker_image


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

def test_list_processes():
  """Verify that we can list running images."""

  expected_name_list = [
      "prefix/image_1",
      "prefix/image_2",
      "prefix/image_3"
  ]

  expected_image_list = []
  for image_name in expected_name_list:
    mock_container = mock.Mock()
    mock_container.name = image_name
    expected_image_list.append(mock_container)

  image_filter = {'status': 'running'}

  new_docker_image = docker_image.DockerImage()
  with mock.patch('docker.models.containers.ContainerCollection.list',
                  mock.MagicMock(return_value=expected_image_list)) \
      as image_list_mock:
    image_list = new_docker_image.list_processes()
    image_list_mock.assert_called_once_with(filters=image_filter)
    assert image_list == expected_name_list

def test_stop_image():
  """Verify that we invoke the proper call to stop a docker image."""

  test_image_name = "some_random_running_docker_image"

  mock_container = docker.models.containers.Container()
  mock_container.stop = mock.MagicMock(return_value=None)

  new_docker_image = docker_image.DockerImage()
  with mock.patch('docker.models.containers.ContainerCollection.get',
                  mock.MagicMock(return_value=mock_container)) \
      as image_get_mock:

    new_docker_image.stop_image(test_image_name)

    image_get_mock.assert_called_once_with(test_image_name)
    mock_container.stop.assert_called_once()

if __name__ == '__main__':
  raise SystemExit(pytest.main(['-s', '-v', __file__]))
