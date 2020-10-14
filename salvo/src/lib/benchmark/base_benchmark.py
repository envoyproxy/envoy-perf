"""
Base Benchmark object module that contains
options common to all execution methods
"""
import os
import logging

import lib.docker_helper as docker_helper

log = logging.getLogger(__name__)
"""
Base Benchmark class with common functions for all invocations
"""


class BaseBenchmark(object):

  def __init__(self, **kwargs):
    """
    Initialize the Base Benchmark class.
    """

    self._docker_helper = docker_helper.DockerHelper()
    self._control = kwargs.get('control', None)
    if self._control is None:
      raise Exception("No control object received")

    self._benchmark_name = kwargs.get('name', None)

    self._mode_remote = self._control.remote

    log.debug("Running benchmark: %s %s", "Remote" if self._mode_remote else "Local",
              self._benchmark_name)

  def is_remote(self):
    """
    Return a boolean indicating whether the test is to
    be executed locally or remotely
    """
    return self._mode_remote

  def get_images(self):
    """
    Return the images object from the control object
    """
    return self._control.images

  def get_source(self):
    """
    Return the source object from the control object
    """
    return self._control.source

  def run_image(self, image_name, **kwargs):
    """
    Run the specified docker image
    """
    return self._docker_helper.run_image(image_name, **kwargs)

  def pull_images(self):
    """
    Retrieve all images defined in the control object.  The validation
    logic should be run before this method.  The images object should be
    populated with non-zero length strings.
    """
    retrieved_images = []
    images = self.get_images()

    for image in [
        images.nighthawk_benchmark_image, images.nighthawk_binary_image, images.envoy_image
    ]:
      # If the image name is not defined, we will have an empty string.  For unit
      # testing we'll keep this behavior. For true usage, we should raise an exception
      # when the benchmark class performs its validation
      if image:
        i = self._docker_helper.pull_image(image)
        log.debug(f"Retrieved image: {i} for {image}")
        if i is None:
          return []
        retrieved_images.append(i)

    return retrieved_images

  def set_environment_vars(self):
    """
    Set the Envoy IP test versions and any other variables controlling the test
    """
    environment = self._control.environment
    if environment.v4only:
      os.environ['ENVOY_IP_TEST_VERSIONS'] = 'v4only'
    elif environment.v6only:
      os.environ['ENVOY_IP_TEST_VERSIONS'] = 'v6only'

    for key, value in environment.variables.items():
      os.environ[key] = value

  @staticmethod
  def get_docker_volumes(output_dir, test_dir=None):
    """
    Build the json specifying the volume configuration needed for running the container
    """
    return docker_helper.DockerHelper.generate_volume_config(output_dir, test_dir)
