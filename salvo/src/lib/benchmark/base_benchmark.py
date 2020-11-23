"""
Base Benchmark object module that contains
options common to all execution methods
"""
import os
import logging
from typing import List

import src.lib.docker_image as docker_image
import src.lib.docker_volume as docker_volume
from api.control_pb2 import JobControl
from api.image_pb2 import DockerImages
from api.source_pb2 import SourceRepository

log = logging.getLogger(__name__)


def get_docker_volumes(output_dir: str, test_dir: str='') -> dict:
  """Build the volume structure needed to run a container.

  Build the json specifying the volume configuration needed for running the container

  Args:
      output_dir: The directory containing the artifacts of the benchmark
      test_dir: If specified, points to the location of user supplied tests
        If the test_dir is not specified, the volume map will not include an
        entry for the external test directory
  """
  return docker_volume.generate_volume_config(output_dir, test_dir)


class BaseBenchmark(object):
  """Base Benchmark class with common functions for all invocations."""

  def __init__(self, job_control: JobControl, benchmark_name: str) -> None:
    """Initialize the Base Benchmark class.

    Args:
        job_control: The protobuf object containing the parameters and locations
          of benchmark artifacts
        benchmark_name: The name of the benchmark to execute
    """
    pass

  def is_remote(self) -> bool:
    """Return a boolean indicating whether the test is to be executed
       locally or remotely.

    Returns:
        Whether or not the benchmark runs locally or in a remote service
    """
    pass

  def get_images(self) -> DockerImages:
    """Return the images object from the control object.

    Returns:
        The images objects specified in the control object
    """
    pass

  def get_source(self) -> List[SourceRepository]:
    """Return the source object defining locations from where
       NightHawk or Envoy can be built.

    Returns:
        The source objects specified in the control object
    """
    pass

  def run_image(self, image_name : str, **kwargs) -> bytearray:
    """Run the specified docker image with the supplied keyword arguments.

    Args:
        image_name: The docker image to be executed
        kwargs: Additional (optional) arguments passed to the docker
          image for execution. The full list of arguments can be referenced
          here https://docker-py.readthedocs.io/en/stable/containers.html#docker.models.containers.ContainerCollection.run

    Returns:
        A bytearray containing the output produced from executing the specified container
    """
    pass

  def pull_images(self) -> List[str]:
    """Retrieve all images necessary for the benchmark.

    Retrieve the NightHawk and Envoy images defined in the control object. 
    """
    pass

  def set_environment_vars(self) -> None:
    """Build the environment variable map used to launch an image.

    Set the Envoy IP test versions and any other environment variables needed by the test
    """
    pass
