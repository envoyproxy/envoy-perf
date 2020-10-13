#!/usr/bin/env python3
"""
This module contains helper functions abstracting the interaction
with docker.
"""

import json
import logging

#Ref: https://docker-py.readthedocs.io/en/stable/index.html
import docker

from google.protobuf.json_format import (Error, MessageToJson)

from lib.api.docker_volume_pb2 import Volume, VolumeProperties

log = logging.getLogger(__name__)


class DockerHelper():
  """
    This class is a wrapper to encapsulate docker operations

    It uses an available docker python module which handles the
    heavy lifting for manipulating images.
    """

  def __init__(self):
    self._client = docker.from_env()

  def pull_image(self, image_name):
    """Pull the identified docker image"""
    return self._client.images.pull(image_name)

  def list_images(self):
    """List all available docker images"""
    return self._client.images.list()

  def run_image(self, image_name, **kwargs):
    """Execute the identified docker image

        The user must specify the command to run and any environment
        variables required
        """
    return self._client.containers.run(image_name, stdout=True, stderr=True, detach=False, **kwargs)

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

