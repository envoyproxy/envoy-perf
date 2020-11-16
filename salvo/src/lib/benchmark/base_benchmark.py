"""
Base Benchmark object module that contains
options common to all execution methods
"""
import os
import logging

import src.lib.docker_image as docker_image
import src.lib.docker_volume as docker_volume

log = logging.getLogger(__name__)


def get_docker_volumes(output_dir, test_dir=None):
  """
  Build the json specifying the volume configuration needed for running the container
  """
  return docker_volume.generate_volume_config(output_dir, test_dir)

class BaseBenchmark(object):
  """
  Base Benchmark class with common functions for all invocations
  """

  def __init__(self, job_control, benchmark_name, **kwargs):
    """
    Initialize the Base Benchmark class.
    """
    pass

  def is_remote(self):
    """
    Return a boolean indicating whether the test is to
    be executed locally or remotely
    """
    pass

  def get_images(self):
    """
    Return the images object from the control object
    """
    pass

  def get_source(self):
    """
    Return the source object defining locations from where either NightHawk or Envoy
    can be built
    """
    pass

  def run_image(self, image_name, **kwargs):
    """
    Run the specified docker image witht he supplied keyword arguments
    """
    pass

  def pull_images(self):
    """
    Retrieve the NightHawk and Envoy images defined in the control object. 
    """
    pass

  def set_environment_vars(self):
    """
    Set the Envoy IP test versions and any other environment variables needed by the test
    """
    pass

