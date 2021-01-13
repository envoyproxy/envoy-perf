"""
Module to abstract a few common file operations used in the framework
"""
import json
import random
import shutil
import yaml
import glob
import os
import tempfile


def open_json(path: str, mode: str = 'r') -> dict:
  """Open a json file and return its contents as a dictionary

  Args:
    path: the full path to the JSON file
    mode: the mode with which we open the file.  The mode defaults
      to read only and is an optional argument.
  """
  data = {}
  with open(path, mode) as json_file:
    data = json.loads(json_file.read())
  return data


def open_yaml(path: str, mode: str = 'r') -> dict:
  """Open a yaml file and return its contents as a dictionary 
  Args:
    path: the full path to the YAML file
    mode: the mode with which we open the file.  The mode defaults
      to read only and is an optional argument.
  """
  data = {}
  with open(path, mode) as yaml_file:
    data = yaml.load(yaml_file)
  return data


def delete_directory(path: str) -> None:
  """Delete a directory and its contents.

  Args:
    path: The directory to be deleted
  """
  shutil.rmtree(path)


def get_random_dir(path: str) -> str:
  """Get a random named directory.

  The caller must re-create the path received if the value
  is used as-is.

  Args:
    path: The location where the temporary directory is to be
     created

  Returns:
    The full pathname of the temporary directory.
  """

  if not os.path.exists(path):
    os.mkdir(path)

  temp_dir = tempfile.TemporaryDirectory(dir=path)
  return temp_dir.name
