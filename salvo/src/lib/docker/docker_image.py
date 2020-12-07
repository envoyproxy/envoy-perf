"""
This module contains abstracts running a docker image.
"""

import collections
import logging

# Ref: https://docker-py.readthedocs.io/en/stable/index.html
import docker
from typing import List

log = logging.getLogger(__name__)

# TODO(abaptiste): consider using pytype annotations in the NamedTuple

# Provides parameters required for executing a docker container
DockerRunParameters = collections.namedtuple("DockerRunParameters", [
    'environment',  # a dict with environment variables to set in the container
    'command',      # a lexical split string containing the command to execute
    'volumes',      # a dict with the volumes mounted in the container
    'network_mode', # a string that specifies the network stack used
    'tty'           # a boolean indicating if a pseudo-tty is allocated
])

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

  def list_images(self) -> List[str]:
    """List all available docker image tags.

    This method returns all the existing image tags from the local host. This
    is used to determine whether the envoy image already exists before we
    attempt to rebuild it

    Returns:
        A list of image tags available on the local host
    """
    for i in self._client.images.list():
      self._existing_tags.extend([tag for tag in i.tags])

    return self._existing_tags

  def run_image(self, image_name: str,
                run_parameters: DockerRunParameters) -> bytearray:
    """Execute the identified docker image.

    This method runs the specified image using the arguments specified in
    run_parameters. DockerRunParameters contains the volume mapping,
    environment variables, and command to be executed.

    Args:
        image_name: The image that is to be executed
        run_parameters: argumments to pass to the invocation of the docker
          image. The list of supported options is quite long and they are
          documented here https://docker-py.readthedocs.io/en/stable/index.html

    Returns:
        A bytearray containing the output produced from executing the specified
          container
    """

    return self._client.containers.run(image_name, stdout=True, stderr=True,
                                       detach=False, **run_parameters._asdict())
