"""
Module to build an Envoy docker image from a source directory
"""

import glob
import os
import logging

from src.lib import (cmd_exec, constants, source_manager)
from src.lib.builder import base_builder
import api.source_pb2 as proto_source

log = logging.getLogger(__name__)


class EnvoyBuilderError(Exception):
  """An error raised when an unrecoverable situation occurs while
     building Envoy components.
  """

class EnvoyBuilder(base_builder.BaseBuilder):
  """This class encapsulates the logic to build the envoy binary
     and container image from source.
  """

  def __init__(self, manager: source_manager.SourceManager) -> None:
    """Initialize the builder with the location of the source and the
       commit hash at which we are operating.

    Args:
      manager: The source manager object handling the source needed
        to build Envoy
    """
    pass

  def _validate(self) -> None:
    """Validate the identity of the source defined from which Envoy is
    built.
    """
    pass

  def clean_envoy(self) -> None:
    """Remove all build artifacts."""
    pass

  def build_envoy(self) -> None:
    """Run bazel build to generate the envoy-static binary."""
    pass

  def build_envoy_image_from_source(self) -> None:
    """Build an Envoy docker image from source.

    This method performs a few steps. It compiles the envoy binary,
    stages it for inclusion in a docker image, and builds the docker
    image.

    Returns:
      None
    """
    pass

  def stage_envoy(self, strip_binary: bool) -> None:
    """Copy and optionally strip the Envoy binary.

    Args:
      strip_binary: determines whether we use objcopy to strip debug
        symbols from the envoy binary. If strip_binary is False, we
        simply copy the binary to its destination

        Callers use False for now, until we expose a control for
        manipulating this parameter.

    Returns:
      None
    """
    pass

  def _generate_docker_ignore(self) -> None:
    """Generate a dockerignore file to reduce the context size."""
    pass

  def create_docker_image(self) -> None:
    """Build a docker image with the newly compiled Envoy binary."""
    pass
