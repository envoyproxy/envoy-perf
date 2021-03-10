"""
General benchmark wrapper that validates that the
job control contains all dat required for each known
benchmark
"""
import logging
import os
from typing import (List, Set)

from src.lib.benchmark import fully_dockerized_benchmark as fulldocker
from src.lib.benchmark import scavenging_benchmark as scavenging
from src.lib.benchmark import base_benchmark
from src.lib.docker import (docker_image, docker_image_builder)
from src.lib import source_manager

import api.control_pb2 as proto_control
import api.source_pb2 as proto_source
import api.image_pb2 as proto_image

log = logging.getLogger(__name__)


class BenchmarkRunnerError(Exception):
  """An error raised if if an unrecoverable condition arises when executing
     a benchmark.
  """

class BenchmarkRunner(object):
  """This class contains the logic to validate input artifacts and
     perform a benchmark.
  """

  def __init__(self, control: proto_control.JobControl) -> None:
    """Initialize the benchmark object.

    Perform class member initialization and instantiate the underlying
    object actually performing the test.

    Args:
      control: The Job Control object dictating the parameters governing the
      benchmark

    Returns:
      None
    """
    self._control = control
    self._source_manager = source_manager.SourceManager(self._control)

    self._test = []
    self._setup_test()

  def _setup_test(self) -> None:
    """Create the object performing the desired benchmark.

    Instantiate the object performing the actual test and setup the control
    objects for each test invocation.

    Raises:
      NotImplementedError: for tests and/or modes that are not yet implemented.
    """

    current_benchmark_name = "Unspecified Benchmark"

    if self._control.scavenging_benchmark:
      current_benchmark_name = "Scavenging Benchmark"
      job_control_list = self.generate_job_control_for_envoy_images()

      for job_control in job_control_list:
        benchmark = scavenging.Benchmark(job_control, current_benchmark_name)
        self._test.append(benchmark)

    elif self._control.dockerized_benchmark:
      current_benchmark_name = "Fully Dockerized Benchmark"
      job_control_list = self.generate_job_control_for_envoy_images()

      for job_control in job_control_list:
        benchmark = fulldocker.Benchmark(job_control, current_benchmark_name)
        self._test.append(benchmark)

    elif self._control.binary_benchmark:
      current_benchmark_name = "Binary Benchmark"
      job_control_list = []

    if not self._test:
      raise NotImplementedError(f"No [{current_benchmark_name}] defined yet")

  def generate_job_control_for_envoy_images(self) \
      -> List[proto_control.JobControl]:
    """Determine the required envoy images needed for the benchmark.

    Find the commit hashes or tags for all envoy images, build images if
    necessary.
    """

    # Get the images that we are benchmarking. Source Manager will
    # determine the commit hashes for the images used for benchmarks
    image_hashes = self._source_manager.get_envoy_hashes_for_benchmark()

    envoy_images = self._pull_or_build_envoy_images_for_benchmark(image_hashes)
    if not envoy_images:
      raise Exception("Unable to find or build images for benchmark")

    self._pull_or_build_nighthawk_images_for_benchmark()

    log.debug(f"Using {envoy_images} for benchmark")
    job_control_list = self.create_job_control_for_images(envoy_images)

    return job_control_list

  def _pull_or_build_nh_benchmark_image(self, \
                                        images: proto_image.DockerImages) \
                                        -> None:
    """Attempt to pull the NightHawk Benchmark Image.  Build the image if
       unavailable.

       Args:
        images: the DockerImages appearing in the control object
    """
    di = docker_image.DockerImage()
    pull_result = False
    try:
      pull_result = di.pull_image(images.nighthawk_benchmark_image)
    except docker_image.DockerImagePullError:
      log.error(f"Image pull failed for {images.nighthawk_benchmark_image}")

    if not pull_result:
      log.debug(f"Attempting to build {images.nighthawk_benchmark_image}")
      docker_image_builder.build_nighthawk_benchmark_image_from_source(
          self._source_manager
      )

  def _pull_or_build_nh_binary_image(self,
                                     images: proto_image.DockerImages) -> None:
    """Attempt to pull the NightHawk Binary Image.  Build it if it is
       unavailable.

      Args:
        images: the DockerImages appearing in the control object
    """
    di = docker_image.DockerImage()
    pull_result = False
    try:
      pull_result = di.pull_image(images.nighthawk_binary_image)
    except docker_image.DockerImagePullError:
      log.error(f"Image pull failed for {images.nighthawk_binary_image}")

    if not pull_result:
      log.debug(f"Attempting to build {images.nighthawk_binary_image}")
      docker_image_builder.build_nighthawk_binary_image_from_source(
          self._source_manager
      )

  def _pull_or_build_nighthawk_images_for_benchmark(self):
    """Pull the nighthawk docker iamges needed for benchmarks.  If an image
       remains unavailable, raise an Exception.

    Raises:
      BenchmarkRunnerError: if no nighthawk images appear in the control object
    """
    images = self._control.images

    if not images.nighthawk_benchmark_image:
      raise BenchmarkRunnerError("No NightHawk Benchmark Image specified")

    if not images.nighthawk_binary_image:
      raise BenchmarkRunnerError("No NightHawk Binary Image specified")

    # TODO: If bazel options are specified, we need to build the images.
    # Specific case is if we enable CpuProfiling, this is not available in
    # the stock image.

    self._pull_or_build_nh_benchmark_image(images)
    self._pull_or_build_nh_binary_image(images)

  def _pull_or_build_envoy_images_for_benchmark(
      self, image_hashes: Set[str]) -> Set[str]:
    """Pull the docker images needed for the benchmarks. If an image is not
       available build it.

    Args:
      image_hashes: The envoy image hashes that we are locating images

    Returns:
      a Set of envoy image tags required for the benchmark:
        eg ["envoyproxy/envoy:v1.X.X", ...]
    """

    have_build_options = self._source_manager.have_build_options(
        proto_source.SourceRepository.SourceIdentity.SRCID_ENVOY)

    envoy_images = set()
    di = docker_image.DockerImage()

    log.debug(f"Finding matching images for hashes: {image_hashes}")

    for image_hash in image_hashes:
      assert image_hash
      image_prefix = docker_image_builder.get_envoy_image_prefix(image_hash)
      envoy_image = "{prefix}:{hash}".format(prefix=image_prefix,
                                             hash=image_hash)

      image_object = None
      try:
        image_object = di.pull_image(envoy_image)
      except docker_image.DockerImagePullError:
        log.error(f"Image pull failed for {envoy_image}")

      if have_build_options or not image_object:
        log.debug(f"Attempting to build {envoy_image}")
        docker_image_builder.build_envoy_image_from_source(
            self._source_manager, image_hash
        )

      envoy_images.add(envoy_image)

    return envoy_images

  def _create_new_job_control(self, envoy_image) -> proto_control.JobControl:
    """Duplicate the job control for a specific benchmark run.

    This method creates a new job control object and sets the commit hash for
    the envoy revision being tested

    Args:
      envoy_image: The envoy image name being tested. This is expected to be
        in the format "envoyproxy/envoy-dev:tag".

    Returns:
      A job control document containing the hash and image name being tested
    """

    image_hash = envoy_image.split(':')[-1]
    output_dir = os.path.join(self._control.environment.output_dir, image_hash)

    new_job_control = proto_control.JobControl()
    new_job_control.CopyFrom(self._control)
    new_job_control.images.envoy_image = envoy_image
    new_job_control.environment.output_dir = output_dir

    self._create_symlink_for_test_artifacts(output_dir, image_hash)

    return new_job_control

  def _create_symlink_for_test_artifacts(self, output_dir: str,
                                         image_tag: str) -> None:
    """Create a symlink linking the artifacts for easy identification.

    Creates a symlink named with the value of 'image_tag' which points to the
    output directory containing the artifacts for the image beign tested.  The
    target of the link is the tag or commit hash from which the docker image
    was created.  This is analogous to the set of bazel-* directories created
    in a build.

    Args:
      output_dir: The location on disk where output artifacts are placed
      image_tag: The tag or commit hash for the image used for the symlink name

    Returns:
      None
    """

    if os.path.islink(image_tag) and output_dir == os.readlink(image_tag):
      return

    # Create a symbolic link pointing to 'output_dir' named 'image_tag'.
    os.symlink(output_dir, image_tag)

  def create_job_control_for_images(
      self, envoy_images: Set[str]) -> List[proto_control.JobControl]:
    """Create new job control objects for each benchmark

    Copy the original job control document and set the envoy images with the
    tags or hashes for the previous and baseline benchmarks.  Also create
    symlinks for the output directories for easier identification

    Args:
      envoy_images: A set of envoy images required for benchmarking

    Returns:
      A list of JobControl objects for each benchmark

    Raises:
      BenchmarkError: if there are less than 2 images detected
    """

    job_control_list = []

    if len(envoy_images) < 2:
      raise base_benchmark.BenchmarkError(
          f"Missing an image name for benchmark: {envoy_images}")

    for image_name in envoy_images:
      # Create a new Job Control object for each image being tested
      new_job_control = self._create_new_job_control(image_name)
      job_control_list.append(new_job_control)

    return job_control_list

  def execute(self) -> None:
    """Run the instantiated benchmark.

    In a local execution context, run the benchmarks sequentially. Start with
    the previous benchmark point(s) since the data could be deduced. If the git
    operations deducing commits or hashes are incorrect we fail faster.

    The benchmarks are run sequentially so that they do not interfere with each
    other.

    Raises:
      NotImplementedError: we have not implemented remote benchmarks yet.  This
        exception alerts us to another point in the execution path that may need
        to be modified
    """
    if self._control.remote:
      # Kick things off in parallel
      raise NotImplementedError(
          "Remote benchmarks have not been implemented yet")

    bar = '=' * 20
    for benchmark in self._test:
      log.info(f"{bar} Running {benchmark.get_name()} for "
               f"{benchmark.get_image()} {bar}")
      benchmark.execute_benchmark()
