"""
This module contains abstracts running a docker image.
"""

import json
import logging

# Ref: https://docker-py.readthedocs.io/en/stable/index.html
import docker
from typing import List

from google.protobuf.json_format import (Error, MessageToJson)

from api.docker_volume_pb2 import Volume, VolumeProperties

log = logging.getLogger(__name__)


class DockerImage():
  """This class is a wrapper to encapsulate docker operations.

  It uses an available docker python module which handles the
  heavy lifting for manipulating images.
  """

  def __init__(self) -> None:
    """Initialize the docker client context."""
    self._client = docker.from_env()
    self._existing_tags = []

  def pull_image(self, image_name: str) -> docker.models.containers.Image:
    """Pull the identified docker image

    Args:
        image_name: The name of the docker image that we are retrieving from
        dockerhub or another repository

    Returns:
        The Image that was pulled
    """
    return self._client.images.pull(image_name)

  def list_images(self) -> list:
    """List all available docker image tags.

    This method returns all the existing image tags from the local host. This is used
    to determine whether the envoy image already exists before we attempt to rebuild it

    Returns:
        A list of image tags available on the local host
    """
    for i in self._client.images.list():
      self._existing_tags.extend([tag for tag in i.tags])

    return self._existing_tags

  def run_image(self, image_name: str, **kwargs: List[str]) -> bytearray:
    """Execute the identified docker image.

    This method runs the specified image using the arguments specified in kwargs.  kwargs
    is passed through to the docker container and should contain the volume mapping,
    environment variables, and command to be executed.

    Args:
        image_name: The image that is to be executed
        kwargs: Additional optional argumments to pass to the invocation of
          the docker image.  The list of supported options is quite long and they
          are documented here https://docker-py.readthedocs.io/en/stable/index.html

    Returns:
        A bytearray containing the output produced from executing the specified container
    """
    return self._client.containers.run(image_name, stdout=True, stderr=True, detach=False, **kwargs)
