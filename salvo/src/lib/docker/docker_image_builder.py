"""
This module manages the steps needed to build missing docker images
"""
import logging

from src.lib import (source_tree, source_manager)
from src.lib.docker import docker_image
from src.lib.builder import (envoy_builder, nighthawk_builder)
import api.source_pb2 as proto_source

log = logging.getLogger(__name__)


def build_envoy_docker_image(manager: source_manager.SourceManager,
                             commit_hash: str) -> None:
  """Build an envoy image from source for the specified hash.

  If the build process fails, a CalledProcessError is raised by the
  cmd_exec module.

  Args:
    manager: A SourceManager object handling the Envoy source
    commit_hash: A string identifying the commit hash or tag for the image
      to be built

  Returns:
    None
  """
  pass

def build_missing_envoy_docker_image(
    manager: source_manager.SourceManager,
    envoy_image_tag: str) -> None:
  """Builds an image for a commit hash if no image exists.

  Check available image tags and build an Envoy image if none exists.
  If there are bazel options specified then we will generate a custom
  image built using these options.

  Args:
    manager: A SourceManager object that is a wrapper for git operations.
      The source manager can navigate the commit hashes or tags to determine
      the endpoints for the benchmark

    envoy_image_tag: A commit hash or tag for which we need to
      build an envoy_image
  """
  pass

def build_envoy_image_from_source(manager: source_manager.SourceManager,
                                  image_tag: str) -> str:
  """Builds Envoy from a specified Source Tree.

  Args:
    manager: A SourceManager object that is a wrapper for git operations.
      The source manager can navigate the commit hashes or tags to determine
      the endpoints for the benchmark

  Returns:
    a tag of the Envoy image built
  """
  pass

def generate_envoy_image_name_from_tag(image_tag: str) -> str:
  """Given an image tag, determine the prefix and construct thee full name.

  Args:
    image_tag: The tag for the Envoy docker image

  Returns:
    The full name for the envoy docker image
  """
  pass

def get_envoy_image_prefix(image_hash: str) -> str:
  """Get the image prefix based on the commit hash.

  If a tag is specified use the "envoyproxy/envoy" prefix.  Otherwise assume
  that it is a development image and use "envoyproxy/envoy-dev"

  Args:
    image_tag: The tag for the Envoy docker image

  Returns:
    The prefix used to generate the full Envoy docker image name
  """
  pass

def build_nighthawk_benchmark_image_from_source(
    manager: source_manager.SourceManager) -> None:
  """Build the nighthawk benchmark image from source

  Args:
    manager: A SourceManager object that is a wrapper for git operations.
      The source manager can navigate the commit hashes or tags to determine
      the endpoints for the benchmark
  """
  pass

def build_nighthawk_binary_image_from_source(
    manager: source_manager.SourceManager) -> None:
  """Build the nighthawk binary image from source

  Args:
    manager: A SourceManager object that is a wrapper for git operations.
      The source manager can navigate the commit hashes or tags to determine
      the endpoints for the benchmark
  """
  pass
