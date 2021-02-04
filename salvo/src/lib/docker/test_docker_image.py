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

@mock.patch.object(docker_image.DockerImage, 'list_images')
@mock.patch.object(docker.models.images.ImageCollection, 'pull')
def test_pull_image(mock_pull, mock_list_images):
  """Test retrieving an image.

  Verify that we can pull a docker image specifying only
  its name and tag
  """
  mock_list_images.return_value = []
  mock_pull.return_value = mock.MagicMock()

  new_docker_image = docker_image.DockerImage()
  container = new_docker_image.pull_image("amazonlinux:2")
  assert container is not None

@mock.patch.object(docker_image.DockerImage, 'list_images')
@mock.patch.object(docker.models.images.ImageCollection, 'get')
def test_pull_image_return_existing(mock_pull, mock_list_images):
  """Verify that we return an existing image if it is already local instead
  of re-pulling it.
  """
  mock_list_images.return_value = ['amazonlinux:2']
  mock_pull.return_value = mock.MagicMock()

  new_docker_image = docker_image.DockerImage()
  container = new_docker_image.pull_image("amazonlinux:2")
  assert container is not None

@mock.patch.object(docker.models.images.ImageCollection, 'list')
def test_list_images(mock_list_images):
  """Verify that we can list all existing cached docker images."""

  expected_image_tags = ['image:1', 'image:2', 'image:3']
  mock_list_images.return_value = \
    map(lambda tag: mock.Mock(tags=[tag]), expected_image_tags)

  new_docker_image = docker_image.DockerImage()
  images = new_docker_image.list_images()
  assert images == expected_image_tags

@mock.patch('docker.from_env')
def test_get_client(mock_docker):
  """Verify that we can return a reference to the instantiated
  docker client.
  """
  mock_docker.return_value = mock.Mock()

  new_docker_image = docker_image.DockerImage()
  docker_client = new_docker_image.get_docker_client()
  assert docker_client


@mock.patch.object(docker_image.DockerImage, 'stop_image')
@mock.patch.object(docker_image.DockerImage, 'list_processes')
@mock.patch.object(docker.models.containers.ContainerCollection, 'run')
def test_run_image(mock_docker_run, mock_docker_list, mock_docker_stop):
  """Verify that we execute the specified docker image"""

  # Mock the actual docker client invocation to return output from the container
  mock_docker_run.return_value = "docker output"
  mock_docker_list.return_value = ['dummy_image']
  mock_docker_stop.return_value = None

  new_docker_image = docker_image.DockerImage()
  run_parameters = docker_image.DockerRunParameters(
    environment={},
    command='bash',
    volumes={},
    network_mode='host',
    tty=False,
  )
  output = new_docker_image.run_image('test_image', run_parameters)

  assert output == 'docker output'
  mock_docker_run.assert_called_once_with('test_image', stdout=True,
      stderr=True, detach=False, **run_parameters._asdict())

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
