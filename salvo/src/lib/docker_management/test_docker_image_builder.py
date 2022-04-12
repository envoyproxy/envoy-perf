"""
Test Docker image build logic.  Most of these test are shallow and do not
verify the git operations being automated.
"""
import pytest
from unittest import mock

from src.lib import source_manager
from src.lib.docker_management import docker_image_builder as image_builder
from src.lib.docker_management import docker_image
from src.lib.builder import (envoy_builder, nighthawk_builder)

import api.source_pb2 as proto_source
import api.control_pb2 as proto_control

_DEFAULT_ENVOY_IMAGE_TAG = "envoy/envoy-dev:envoy_tag"

_generate_image_name_from_tag_mock_name = \
    'src.lib.docker_management.docker_image_builder.generate_envoy_image_name_from_tag'
_build_envoy_docker_image_mock_name = \
    'src.lib.docker_management.docker_image_builder.build_envoy_docker_image'


def generate_image_manager_with_source_url():
  """Generate a source manager with a job control specifying remote repos
  for images.
  """

  job_control = proto_control.JobControl()
  job_control.source.add(identity=proto_source.SourceRepository.SRCID_ENVOY,
                         source_url='https://www.github.com/_some_random_repo_')
  job_control.source.add(identity=proto_source.SourceRepository.SRCID_NIGHTHAWK,
                         source_url='https://www.github.com/_nighthawk_repo_')
  return source_manager.SourceManager(job_control)


@mock.patch.object(envoy_builder.EnvoyBuilder, 'build_envoy_image_from_source')
def test_build_envoy_docker_image(mock_envoy_builder):
  """Verify that we can build an envoy docker image"""

  mock_envoy_builder.return_value = None

  manager = generate_image_manager_with_source_url()
  image_builder.build_envoy_docker_image(manager, 'random_hash_or_tag')

  mock_envoy_builder.assert_called_once()


@mock.patch(_generate_image_name_from_tag_mock_name)
@mock.patch.object(docker_image.DockerImage, 'list_images')
def test_build_missing_envoy_docker_image(mock_list_images, mock_generate_image_from_tag):
  """Verify we build an image only if it is not present and no build options
  are present"""

  mock_list_images.return_value = []
  mock_generate_image_from_tag.return_value = _DEFAULT_ENVOY_IMAGE_TAG

  manager = generate_image_manager_with_source_url()
  with mock.patch(_build_envoy_docker_image_mock_name, mock.MagicMock()) as mock_build_image:
    image_builder.build_missing_envoy_docker_image(manager, 'envoy_tag')
    mock_build_image.assert_called_once_with(manager, 'envoy_tag')

  mock_list_images.assert_called_once()
  mock_generate_image_from_tag.assert_called_once_with('envoy_tag')


@mock.patch(_generate_image_name_from_tag_mock_name)
@mock.patch.object(docker_image.DockerImage, 'list_images')
def test_build_missing_envoy_docker_image_image_present(mock_list_images,
                                                        mock_generate_image_from_tag):
  """Verify we do not build an image if it is present and no build options
  are present"""

  image_tag = 'envoy/envoy-dev:envoy_tag'
  mock_list_images.return_value = [image_tag]
  mock_generate_image_from_tag.return_value = image_tag

  manager = generate_image_manager_with_source_url()
  with mock.patch(_build_envoy_docker_image_mock_name, mock.MagicMock()) as mock_build_image:
    image_builder.build_missing_envoy_docker_image(manager, 'envoy_tag')

    # If the image name exists, we should not call the build_envoy_docker_image
    # method
    mock_build_image.assert_not_called()

  mock_list_images.assert_called_once()
  mock_generate_image_from_tag.assert_called_once_with('envoy_tag')


@mock.patch.object(source_manager.SourceManager, 'have_build_options')
@mock.patch(_generate_image_name_from_tag_mock_name)
def test_build_missing_envoy_docker_image_options_present(mock_generate_image_from_tag,
                                                          mock_build_options):
  """Verify we build an image if build options are present"""

  image_tag = 'envoy/envoy-dev:envoy_tag'
  mock_generate_image_from_tag.return_value = image_tag
  mock_build_options.return_vaue = True

  manager = generate_image_manager_with_source_url()
  with mock.patch(_build_envoy_docker_image_mock_name, mock.MagicMock()) as mock_build_image:
    image_builder.build_missing_envoy_docker_image(manager, 'envoy_tag')
    mock_build_image.assert_called_once_with(manager, 'envoy_tag')

  mock_build_options.assert_called_once()
  mock_generate_image_from_tag.assert_called_once_with('envoy_tag')


@mock.patch(_generate_image_name_from_tag_mock_name)
@mock.patch('src.lib.docker_management.docker_image_builder.build_missing_envoy_docker_image')
def test_build_envoy_image_from_source(mock_build_missing_image, mock_generate_image_from_tag):
  """Verify that we return the tag of a constructed image.  This is a shallow
  test and does not invoke any git operations to manipulate the source.
  """

  mock_build_missing_image.return_value = None
  mock_generate_image_from_tag.return_value = _DEFAULT_ENVOY_IMAGE_TAG

  manager = generate_image_manager_with_source_url()
  image_tag = image_builder.build_envoy_image_from_source(manager, 'envoy_tag')

  assert image_tag == _DEFAULT_ENVOY_IMAGE_TAG
  mock_generate_image_from_tag.assert_called_once()
  mock_build_missing_image.assert_called_once_with(manager, 'envoy_tag')


def test_generate_envoy_image_name_from_tag():
  """Verify we create the correct image name from its tag.  For images built
  from a release tag, we use 'envoyproxy/envoy', anything else uses
  'envoyproxy/envoy-dev'
  """
  image_name = image_builder.generate_envoy_image_name_from_tag('definitely_not_a_tag')
  assert image_name == "envoyproxy/envoy-dev:definitely_not_a_tag"

  image_name = image_builder.generate_envoy_image_name_from_tag('v1.1.1')
  assert image_name == "envoyproxy/envoy:v1.1.1"


def test_get_image_prefix():
  """Verify we return the correct image prefix given a tag or hash"""
  expected_values = {'not_a_tag': 'envoyproxy/envoy-dev', 'v1.1.1': 'envoyproxy/envoy'}

  for key, value in expected_values.items():
    assert value == image_builder.get_envoy_image_prefix(key)


@mock.patch.object(nighthawk_builder.NightHawkBuilder, 'build_nighthawk_benchmark_image')
def test_build_nighthawk_benchmark_image_from_source(mock_benchmark_image):
  """Verify that we build the nighthawk benchmark container from a source
  tree.
  """
  mock_benchmark_image.return_value = None
  manager = generate_image_manager_with_source_url()
  image_builder.build_nighthawk_benchmark_image_from_source(manager)
  mock_benchmark_image.assert_called_once()


@mock.patch.object(nighthawk_builder.NightHawkBuilder, 'build_nighthawk_binary_image')
def test_build_nighthawk_binary_image_from_source(mock_binary_image):
  """Verify that we build the nighthawk binary container from a source
  tree.
  """
  mock_binary_image.return_value = None
  manager = generate_image_manager_with_source_url()
  image_builder.build_nighthawk_binary_image_from_source(manager)
  mock_binary_image.assert_called_once()


if __name__ == '__main__':
  raise SystemExit(pytest.main(['-s', '-v', __file__]))
