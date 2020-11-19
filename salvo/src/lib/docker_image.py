"""
This module contains abstracts running a docker image.
"""

import json
import logging

# Ref: https://docker-py.readthedocs.io/en/stable/index.html
import docker

from google.protobuf.json_format import (Error, MessageToJson)

from api.docker_volume_pb2 import Volume, VolumeProperties

log = logging.getLogger(__name__)


class DockerImage():
  """This class is a wrapper to encapsulate docker operations.

  It uses an available docker python module which handles the
  heavy lifting for manipulating images.
  """

  def __init__(self):
    """Initialize the docker client context."""
    self._client = docker.from_env()

  def pull_image(self, image_name):
    """Pull the identified docker image.
    Args:
        image_name: The image that is to be executed

    Returns:
        An Image object for the requested container
    """
    return self._client.images.pull(image_name)

  def list_images(self):
    """List all available docker images.

    Returns:
        A list of image tags available on the local host
    """
    return self._client.images.list()

  def run_image(self, image_name, **kwargs):
    """Execute the identified docker image.

    The user must specify the command to run and any environment
    variables required

    Args:
        image_name: The image that is to be executed
        kwargs:  Additional arguments to pass to the invocation of
          the docker image

    Returns:
        The output produced from executing the specified container
    """
    return self._client.containers.run(image_name, stdout=True, stderr=True, detach=False, **kwargs)
