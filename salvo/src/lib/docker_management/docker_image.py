"""
This module contains abstracts running a docker image.
"""

import collections
import logging
import requests

# Ref: https://docker-py.readthedocs.io/en/stable/index.html
import docker
from typing import List

log = logging.getLogger(__name__)

# TODO(abaptiste): consider using pytype annotations in the NamedTuple

# Provides parameters required for executing a docker container
DockerRunParameters = collections.namedtuple(
    "DockerRunParameters",
    [
        'environment',  # a dict with environment variables to set in the container
        'command',  # a lexical split string containing the command to execute
        'volumes',  # a dict with the volumes mounted in the container
        'network_mode',  # a string that specifies the network stack used
        'tty'  # a boolean indicating if a pseudo-tty is allocated
    ])


class DockerImagePullError(Exception):
  """This error is raised if an image pull is unsuccessful"""


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
        dockerhub or another repository. If the image exists locally, we return
        the corresponding docker image object from the image name

    Returns:
        The Image that was pulled

    Raises:
      DockerImagePullError: if the image pull is not successful
    """

    image = None
    existing_images = self.list_images()
    if image_name not in existing_images:
      log.debug(f"Pulling image: {image_name}")
      try:
        image = self._client.images.pull(image_name)
      except docker.errors.ImageNotFound as image_not_found_error:
        log.error(f"Unable to pull image {image_name}: {image_not_found_error}")
        raise DockerImagePullError(image_not_found_error)
      except requests.exceptions.HTTPError as http_error:
        log.error(f"HTTP Error pulling image: {image_name}: {http_error}")
        raise DockerImagePullError(http_error)
    else:
      image = self._client.images.get(image_name)

    return image

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

  def get_docker_client(self) -> docker.client:
    """Return an instance of the docker client for use by the controller.

    Returns:
      the instantiated docker client.
    """
    return self._client

  def run_image(self, image_name: str, run_parameters: DockerRunParameters) -> bytearray:
    """Execute the identified docker image using the docker controller.

    This method runs the specified image using the arguments specified in
    run_parameters. DockerRunParameters contains the volume mapping,
    environment variables, and command to be executed.

    Args:
        image_name: The image that is to be executed
        run_parameters: argumments to pass to the invocation of the docker
          image.

    Returns:
        A bytearray containing the output produced from executing the specified
          container
    """

    output = ''
    with DockerImageController(self) as docker_controller:
      output = docker_controller.run(image_name, run_parameters)

    return output

  def list_processes(self) -> List[str]:
    """List running containers."""
    image_filter = {'status': 'running'}
    return [container.name for container in self._client.containers.list(filters=image_filter)]

  def stop_image(self, image_name: str) -> None:
    """Stops a running container."""
    container = self._client.containers.get(image_name)
    container.stop()


class DockerImageController():
  """Manage docker images and stop lingering processes that we spawn."""

  def __init__(self, docker_image: DockerImage) -> None:
    """Initialize the controller with the DockerImage object.

    Internally this uses the docker image object to enumerage running containers
    and stop identified containers.
    """
    self._running_procs = []
    self._image = docker_image

  def __enter__(self):
    """Enumerate any docker images that are running prior to invoking the
       benchmark container.
    """
    running_images = self._image.list_processes()
    log.debug(f"Currently Running images: {running_images}")
    self._running_procs = running_images

    return self

  def __exit__(self, type_param, value, traceback) -> None:
    """Stop any new docker processes that were started.

    Note that this will catch any docker images that were started after
    the benchmark begins running.
    """
    running_images = self._image.list_processes()

    images_to_stop = filter(lambda img: img not in self._running_procs, running_images)

    for image_name in images_to_stop:
      log.debug(f"Stopping image: {image_name}")
      self._image.stop_image(image_name)

  def run(self, image_name: str, run_parameters: DockerRunParameters) -> bytearray:
    """Use the docker client to execute the specified container.

    Args:
      image_name: The image that is to be executed
      run_parameters: argumments to pass to the invocation of the docker
        image. The list of supported options is quite long and they are
        documented here https://docker-py.readthedocs.io/en/stable/index.html

    Returns:
      A bytearray containing the output produced from executing the specified
        container
    """

    client = self._image.get_docker_client()
    try:
      return client.containers.run(image_name,
                                   stdout=True,
                                   stderr=True,
                                   detach=False,
                                   **run_parameters._asdict())
    except docker.errors.ContainerError as e:
      error_logs = e.container.logs()
      log.error(
          f"Failed to run benchmarking test in image: {image_name}, error message: {e}, container logs: {error_logs}"
      )
      exit()
