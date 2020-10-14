"""
General benchmark wrapper that validates that the
job control contains all dat required for each known
benchmark
"""
import copy
import logging
import os

import lib.benchmark.fully_dockerized_benchmark as fulldocker
import lib.source_manager as source_manager
from lib.source_manager import (CURRENT, PREVIOUS)

log = logging.getLogger(__name__)


class Benchmark(object):

  def __init__(self, control):
    """
    Initialize the benchmark object and instantiate the underlying
    object actually performing the test
    """
    self._control = control
    self._test = {}
    self._setup_test()

  def _setup_test(self):
    """
    Instantiate the object performing the actual test invocation
    """
    # Get the two points that we are benchmarking.  Source Manager will ultimately
    # determine the commit hashes for the images used for benchmarks
    kwargs = {'control': self._control}
    sm = source_manager.SourceManager(**kwargs)
    envoy_images = sm.get_envoy_images_for_benchmark()
    # TODO: We need to determine whether the docker image exists for a given hash

    # Deep copy self_control into current and previous
    # Adjust the envoy images and output paths for these containers
    (current_job, previous_job) = self.create_job_control_for_images(envoy_images)

    current_kwargs = {'control': current_job}
    previous_kwargs = {'control': previous_job}

    # We will need to instantiate two of these tests.  One for the current
    # commit and one for the previous commit
    if self._control.scavenging_benchmark:
      current_kwargs['name'] = "Scavenging Benchmark"
      previous_kwargs['name'] = "Scavenging Benchmark (Previous image)"
    elif self._control.binary_benchmark:
      current_kwargs['name'] = "Binary Benchmark"
      previous_kwargs['name'] = "Binary Benchmark (Previous image)"
    elif self._control.dockerized_benchmark:
      current_kwargs['name'] = "Fully Dockerized Benchmark"
      previous_kwargs['name'] = "Fully Dockerized Benchmark (Previous image)"
      self._test[CURRENT] = fulldocker.Benchmark(**current_kwargs)
      self._test[PREVIOUS] = fulldocker.Benchmark(**previous_kwargs)

    if CURRENT not in self._test:
      raise NotImplementedError("No %s defined yet" % current_kwargs['name'])

    if PREVIOUS not in self._test:
      raise NotImplementedError("No %s defined yet" % previous_kwargs['name'])

  def _create_new_job_control(self, envoy_image, image_hash, hashid):
    """
    Copy the job control object and set the image name to the hash specified

    Create a symlink to identify the output directory for the test
    """
    new_job_control = copy.deepcopy(self._control)
    new_job_control.images.envoy_image = \
        '{base_image}:{tag}'.format(base_image=envoy_image, tag=image_hash[hashid])
    new_job_control.environment.output_dir = \
        os.path.join(self._control.environment.output_dir, image_hash[hashid])

    link_name = os.path.join(self._control.environment.output_dir, hashid)
    if os.path.exists(link_name):
      os.unlink(link_name)
    os.symlink(new_job_control.environment.output_dir, link_name)

    return new_job_control

  def create_job_control_for_images(self, image_hashes):
    """
    Deep copy the original job control document and reset the envoy images
    with the tags for the previous and current image.
    """
    if not all([CURRENT in image_hashes, PREVIOUS in image_hashes]):
      raise Exception(f"Missing an image definition for benchmark: {image_hashes}")

    base_envoy = None
    images = self._control.images
    if images:
      envoy_image = images.envoy_image
      base_envoy = envoy_image.split(':')[0]

      # Create a new Job Control object for the current image being tested
      current_jc = self._create_new_job_control(base_envoy, image_hashes, CURRENT)
      log.debug(f"Current image: {current_jc.images.envoy_image}")

      # Create a new Job Control object for the previous image being tested
      previous_jc = self._create_new_job_control(base_envoy, image_hashes, PREVIOUS)
      log.debug(f"Previous image: {previous_jc.images.envoy_image}")

      return current_jc, previous_jc

    else:
      # TODO: Build images from source since none are specified
      raise NotImplementedError("We need to build images since none exist")

    return (None, None)

  def validate(self):
    """
    Determine if the configured benchmark has all needed
    data defined and present
    """
    if self._test is None:
      raise Exception("No test object was defined")

    return all in [self._test[version].validate() for version in [CURRENT, PREVIOUS]]

  def execute(self):
    """
    Run the instantiated benchmark
    """
    if self._control.remote:
      # Kick things off in parallel
      raise NotImplementedError("Remote benchmarks have not been implemented yet")

    horizontal_bar = '=' * 20
    log.info(f"{horizontal_bar} Running benchmark for prior Envoy version {horizontal_bar}")
    self._test[PREVIOUS].execute_benchmark()

    log.info(
        f"{horizontal_bar} Running benchmark for current (baseline) Envoy version {horizontal_bar}")
    self._test[CURRENT].execute_benchmark()
