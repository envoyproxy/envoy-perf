"""Test source_tree operations needed for executing benchmarks."""
import pytest

import os
import json
import tempfile

from src.lib.common import file_ops

from unittest import mock

_TEST_JSON = """
{
  "key" : "this is my json file",
  "key2" : "there are many like it",
  "key3" : [
    "but", "this", "one", "is", "mine"
  ]
}
"""

_TEST_YAML = """
key: this is my json file
key2: there are many like it
key3:
  - but
  - this
  - one
  - is
  - mine
"""


def _validate_test_data(file_data):
  """Validate test data."""
  assert file_data
  assert all(map(lambda key: key in file_data, ["key", "key2", "key3"]))
  assert file_data['key3'] == ['but', 'this', 'one', 'is', 'mine']


def test_open_json():
  """Verify we can open json file."""
  with tempfile.NamedTemporaryFile() as temp_json:
    with open(temp_json.name, 'w') as temp_data:
      temp_data.write(_TEST_JSON)

    json_data = file_ops.open_json(temp_json.name)
    _validate_test_data(json_data)


def test_open_yaml():
  """Verify we can open yaml file."""
  with tempfile.NamedTemporaryFile() as temp_yaml:
    with open(temp_yaml.name, 'w') as temp_data:
      temp_data.write(_TEST_YAML)

    yaml_data = file_ops.open_yaml(temp_yaml.name)
    _validate_test_data(yaml_data)


def test_open_yaml_as_json():
  """Verify it will raise an error when decoding yaml file as json format."""
  with tempfile.NamedTemporaryFile() as temp_json:
    with open(temp_json.name, 'w') as temp_data:
      temp_data.write(_TEST_YAML)

    with pytest.raises(json.decoder.JSONDecodeError) as decode_error:
      _ = file_ops.open_json(temp_json.name)

    assert 'Expecting value' in str(decode_error.value)


def test_open_json_as_yaml():
  """Verify it will raise an error when decoding json file as yaml format."""
  with tempfile.NamedTemporaryFile() as temp_yaml:
    with open(temp_yaml.name, 'w') as temp_data:
      temp_data.write(_TEST_JSON)

    yaml_data = file_ops.open_yaml(temp_yaml.name)
    _validate_test_data(yaml_data)


def test_delete_directory():
  """Verify we can delete directory."""
  with mock.patch('shutil.rmtree') as magic_mock:
    file_ops.delete_directory('this_is_my_directory')

  magic_mock.assert_called_once_with('this_is_my_directory')


def test_get_random_dir():
  """Verify we can get random directory."""
  temp_path = file_ops.get_random_dir('my_test_path')
  assert temp_path
  parent_dir = os.path.dirname(temp_path.name)
  assert parent_dir == 'my_test_path'


if __name__ == '__main__':
  raise SystemExit(pytest.main(['-s', '-v', __file__]))
