"""
This module builds the volume mapping structure passed to a docker image 
"""

import json
import logging

import google.protobuf.json_format as json_format
import src.lib.constants as constants
import api.docker_volume_pb2 as proto_docker_volume

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

  Raises:
    json.decoder.JSONDecodeError: if we are unable to convert the object
      to json
    an Error for any other exceptions caught when generating json from the
      VolumeProperties object
  """
  volume_cfg = proto_docker_volume.Volume()

  # Setup the docker socket
  properties = proto_docker_volume.VolumeProperties()
  properties.bind = constants.DOCKER_SOCKET_PATH
  properties.mode = 'rw'
  volume_cfg.volumes[constants.DOCKER_SOCKET_PATH].CopyFrom(properties)

  # Setup the output directory
  properties = proto_docker_volume.VolumeProperties()
  properties.bind = output_dir
  properties.mode = 'rw'
  volume_cfg.volumes[output_dir].CopyFrom(properties)

  # Setup the test directory
  if test_dir:
    properties = proto_docker_volume.VolumeProperties()
    properties.bind = constants.NIGHTHAWK_EXTERNAL_TEST_DIR
    properties.mode = 'ro'
    volume_cfg.volumes[test_dir].CopyFrom(properties)

  volume_json = {}
  try:
    volume_json = json.loads(json_format.MessageToJson(volume_cfg))
  except json.decoder.JSONDecodeError as decode_error:
    log.error(f"Could not build volume json object: {decode_error}")
    raise
  except json_format.Error as general_error:
    log.error(f"Unable to convert message to JSON: {general_error}")
    raise

  return volume_json["volumes"]
