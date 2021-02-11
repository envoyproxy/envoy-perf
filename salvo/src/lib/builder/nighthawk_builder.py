"""
Module to build NightHawk artifacts
"""
import logging

from src.lib.builder import base_builder
from src.lib import (constants, cmd_exec, source_manager)
import api.source_pb2 as proto_source

log = logging.getLogger(__name__)

class NightHawkBuilderError(Exception):
  """An error raised when an unrecoverable situation occurs when
     building NightHawk components.
  """

def _execute_docker_image_script(script: str, build_dir: str) -> None:
  """Run the specified script to build a docker image.

  The docker image tags are "fixed" at "latest" for the binary container.

  The benchmark image's tag can be adjusted using DOCKER_IMAGE_TAG however
  this value defaults to "latest" as well.  We are not currently exposing a
  method to set this environment variable.

  When buliding the nighthhawk components we use the most recent source by
  default.

  Args:
    script: The shell script in the nighthawk repository that builds
      the benchmark and binary docker images.
    build_dir: The nighthawk source location
  """
  cmd_params = cmd_exec.CommandParameters(cwd=build_dir)
  output = cmd_exec.run_command(script, cmd_params)
  log.debug(f"NightHawk Docker image output for {script}: {output}")

class NightHawkBuilder(base_builder.BaseBuilder):
  """This class encapsulates the logic to build the nighthawk binaries
      benchmark scripts, and container images from source.
  """

  def __init__(self, manager: source_manager.SourceManager) -> None:
    """Initialize the builder with the location of the source and the
       commit hash at which we are operating.

    Args:
      source_repo: The SourceRepository object describing the location
        containig the source code, and the desired commit hash or tag
        at which we operate.
    """
    super(NightHawkBuilder, self).__init__(manager)
    self._source_repo = self._source_manager.get_source_repository(
        proto_source.SourceRepository.SourceIdentity.SRCID_NIGHTHAWK
    )

    self._source_tree = self._source_manager.get_source_tree(
        proto_source.SourceRepository.SourceIdentity.SRCID_NIGHTHAWK
    )

  def _validate(self) -> None:
    """ Verify the identity of the source being used."""

    if not self._source_repo or self._source_repo.identity != \
        proto_source.SourceRepository.SourceIdentity.SRCID_NIGHTHAWK:
      raise NightHawkBuilderError(
          "This module supports building NightHawk Only")

  def prepare_nighthawk_source(self) -> None:
    """Stage the nighthawk source in a directory where we can manipulate it.

    Pull the source from github or copy the specified path into a temporary
    directory where we can build the NightHawk binaries, scripts and docker
    images.

    Returns:
      a SourceTree pointing to the location on disk where we can build
        artifacts
    """
    pass


  def build_nighthawk_benchmarks(self) -> None:
    """Build the NightHawk benchmarks target.

    This target is required for the scavenging benchmark. It is also a pre-
    requisite to building the benchmark container image
    """
    pass

  def build_nighthawk_binaries(self) -> None:
    """Build the NightHawk client and server binaries.

    This is a pre-requisite to building the nighthawk binary docker image
    """
    pass

  def build_nighthawk_benchmark_image(self) -> None:
    """Build the NightHawk benchmark docker image."""
    pass

  def build_nighthawk_binary_image(self) -> None:
    """Build the NightHawk binary docker image."""
    pass
