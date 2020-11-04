#!/usr/bin/env python3
"""
This module builds the volume mapping structure passed to a docker image 
"""

import json
import logging

# Ref: https://docker-py.readthedocs.io/en/stable/index.html
import docker

from google.protobuf.json_format import (Error, MessageToJson)

from api.docker_volume_pb2 import Volume, VolumeProperties

log = logging.getLogger(__name__)


class DockerVolume():

  @staticmethod
  def generate_volume_config(output_dir, test_dir=None):
    """
    Generates the volumes config necessary for a container to run.
    The docker path is hardcoded at the moment.  The output directory
    is mounted read-write and the test directory if specified is mounted
    read-only
    """
    volume_cfg = Volume()

    # Setup the docker socket
    properties = VolumeProperties()
    properties.bind = '/var/run/docker.sock'
    properties.mode = 'rw'
    volume_cfg.volumes['/var/run/docker.sock'].CopyFrom(properties)

    # Setup the output directory
    properties = VolumeProperties()
    properties.bind = output_dir
    properties.mode = 'rw'
    volume_cfg.volumes[output_dir].CopyFrom(properties)

    # Setup the test directory
    if test_dir:
      properties = VolumeProperties()
      properties.bind = '/usr/local/bin/benchmarks/benchmarks.runfiles/nighthawk/benchmarks/external_tests/'
      properties.mode = 'ro'
      volume_cfg.volumes[test_dir].CopyFrom(properties)

    volume_json = {}
    try:
      volume_json = json.loads(MessageToJson(volume_cfg))
    except Error as serialize_error:
      log.exception(f"Could not build volume json object: {serialize_error}")
      raise

    return volume_json["volumes"]
