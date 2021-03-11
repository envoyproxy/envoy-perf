"""
Test Docker volume generation
"""
import json
import pytest
from unittest import mock
from google.protobuf import json_format

from src.lib import constants
from src.lib.docker_management import docker_volume

def test_generate_volume_config():
  """Verify the volume mount map can be created with no test directory
     specified.
  """
  output_dir = '/tmp/random_dir_on_disk'
  volume_map = docker_volume.generate_volume_config(output_dir)

  # Verify the contents of the volume map.  Specified output
  # paths are mounted as read/write with the same external path
  # within the container.
  assert volume_map

  verify_required_paths(volume_map, output_dir)

def test_generate_volume_config_with_test_dir():
  """Verify the volume mount map can be created when a test directory
     is specified.
  """
  output_dir = '/tmp/random_dir_on_disk'
  test_dir = '/home/user/test_directory'
  volume_map = docker_volume.generate_volume_config(output_dir, test_dir)

  # Verify the contents of the volume map.  Specified output
  # paths are mounted as read/write with the same external path
  # within the container.
  assert volume_map

  verify_required_paths(volume_map, output_dir)

  # Verify that the read-only test directory is in the map
  assert test_dir in volume_map
  test_map = volume_map[test_dir]
  assert test_map['bind'] == constants.NIGHTHAWK_EXTERNAL_TEST_DIR
  assert test_map['mode'] == constants.MOUNT_READ_ONLY

def json_loads_side_effect(arg):
  raise json.decoder.JSONDecodeError("json loading failed", arg, 0)

@mock.patch('json.loads')
def test_generate_volume_config_json_error(mock_json_loads):
  """Verify that an exception is raised if the json serialization fails."""

  mock_json_loads.side_effect = json_loads_side_effect
  output_dir = '/tmp/random_dir_on_disk'

  volume_map = None
  with pytest.raises(json.decoder.JSONDecodeError) as decode_error:
    volume_map = docker_volume.generate_volume_config(output_dir)

  assert not volume_map
  assert str(decode_error.value) == \
      'json loading failed: line 1 column 1 (char 0)'

def json_loads_side_effect_format_error(arg):
  raise json_format.Error("Error in json format")

@mock.patch('json.loads')
def test_generate_volume_config_format_error(mock_json_loads):
  """Verify that an exception is raised if the json serialization fails."""

  mock_json_loads.side_effect = json_loads_side_effect_format_error
  output_dir = '/tmp/random_dir_on_disk'

  volume_map = None
  with pytest.raises(json_format.Error) as format_error:
    volume_map = docker_volume.generate_volume_config(output_dir)

  assert not volume_map
  assert str(format_error.value) == 'Error in json format'

def verify_required_paths(volume_map, output_dir):
  """Verify the required mounts in the volume map"""
  assert constants.DOCKER_SOCKET_PATH in volume_map
  docker_map = volume_map[constants.DOCKER_SOCKET_PATH]

  assert 'bind' in docker_map
  assert docker_map['bind'] == constants.DOCKER_SOCKET_PATH
  assert docker_map['mode'] == constants.MOUNT_READ_WRITE

  assert output_dir in volume_map
  output_map = volume_map[output_dir]

  assert output_map['bind'] == output_dir
  assert output_map['mode'] == constants.MOUNT_READ_WRITE


if __name__ == '__main__':
  raise SystemExit(pytest.main(['-s', '-v', __file__]))
