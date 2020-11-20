"""
This module builds the volume mapping structure passed to a docker image 
"""

import json
import logging

# Ref: https://docker-py.readthedocs.io/en/stable/index.html
import docker

from google.protobuf.json_format import (Error, MessageToJson)
from src.lib.constants import (DOCKER_SOCKET_PATH, NIGHTHAWK_EXTERNAL_TEST_DIR)

from api.docker_volume_pb2 import Volume, VolumeProperties

log = logging.getLogger(__name__)


def generate_volume_config(output_dir: str, test_dir: str='') -> dict:
  """Generates the volumes config necessary for a container to run.

  The docker path is hardcoded at the moment.  The output directory
  is mounted read-write and the test directory if specified is mounted
  read-only

  Args:
    output_dir: The directory where the benchmark artifacts are placed
    test_dir: If specified, identifies the location of user supplied tests

  Returns:
    A map specifying the local and remote mount paths, and whether each
    mount path is read-only, or read-write
  """
  volume_cfg = Volume()

  # Setup the docker socket
  properties = VolumeProperties()
  properties.bind = DOCKER_SOCKET_PATH
  properties.mode = 'rw'
  volume_cfg.volumes[DOCKER_SOCKET_PATH].CopyFrom(properties)

  # Setup the output directory
  properties = VolumeProperties()
  properties.bind = output_dir
  properties.mode = 'rw'
  volume_cfg.volumes[output_dir].CopyFrom(properties)

  # Setup the test directory
  if test_dir:
    properties = VolumeProperties()
    properties.bind = NIGHTHAWK_EXTERNAL_TEST_DIR
    properties.mode = 'ro'
    volume_cfg.volumes[test_dir].CopyFrom(properties)

  volume_json = {}
  try:
    volume_json = json.loads(MessageToJson(volume_cfg))
  except json.decoder.JSONDecodeError as decode_error:
    log.exception(f"Could not build volume json object: {decode_error}")
    raise
  except Error as general_error:
    log.exception(f"Unable to convert message to JSON: {general_error}")
    raise

  return volume_json["volumes"]
