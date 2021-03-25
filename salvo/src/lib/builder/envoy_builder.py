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
    super(EnvoyBuilder, self).__init__(manager)
    self._source_tree = self._source_manager.get_source_tree(
        proto_source.SourceRepository.SRCID_ENVOY
    )

    self._source_repo = self._source_manager.get_source_repository(
        proto_source.SourceRepository.SRCID_ENVOY
    )
    self.set_build_dir(self._source_tree.get_source_directory())

  def _validate(self) -> None:
    """Validate the identity of the source defined from which Envoy is
    built.
    """
    if self._source_repo.identity != proto_source.SourceRepository.SRCID_ENVOY:
      raise EnvoyBuilderError("This class builds Envoy only.")

  def clean_envoy(self) -> None:
    """Remove all build artifacts."""
    self._validate()
    self._run_bazel_clean()

  def build_envoy(self) -> None:
    """Run bazel build to generate the envoy-static."""
    cmd_params = cmd_exec.CommandParameters(cwd=self._build_dir)
    cmd = "bazel build {bazel_options}".format(
        bazel_options=self._generate_bazel_options(
            proto_source.SourceRepository.SRCID_ENVOY
        )
    )
    if not cmd.endswith(" "):
      cmd += " "
    cmd += constants.ENVOY_BINARY_BUILD_TARGET
    cmd_exec.run_check_command(cmd, cmd_params)

  def build_envoy_binary_from_source(self) -> str:
    """Build an Envoy binary from source.

    This method cleans the working directory, compiles the binary,
    and returns the name of the final envoy binary.

    Returns:
      A string representation of the path to the created binary
    """

    self._validate()
    self._source_tree.copy_source_directory()
    self._source_tree.checkout_commit_hash()

    self.clean_envoy()
    self.build_envoy()

    return os.path.join(self._build_dir, constants.ENVOY_BINARY_TARGET_OUTPUT_PATH)

  def build_envoy_image_from_source(self) -> None:
    """Build an Envoy docker image from source.

    This method performs a few steps. It compiles the envoy binary,
    stages it for inclusion in a docker image, and builds the docker
    image.

    Returns:
      None
    """
    self.build_envoy_binary_from_source()
    self.stage_envoy(False)
    self.create_docker_image()

  def stage_envoy(self, strip_binary: bool) -> None:
    """Copy and optionally strip the Envoy binary.

    After we compile Envoy, copy the binary into a platform directory
    for inclusion in the docker image. It is unclear the intent of the
    'targetplatform' parameter in the Dockerfile, so we use a static
    string. Ultimately the compiled binary is staged for packaging in
    the resulting image.

    Args:
      strip_binary: determines whether we use objcopy to strip debug
        symbols from the envoy binary. If strip_binary is False, we
        simply copy the binary to its destination

        Callers use False for now, until we expose a control for
        manipulating this parameter.

    Returns:
      None
    """
    # Stage the envoy binary for the docker image
    dir_mode = 0o755
    pwd = os.getcwd()
    os.chdir(self._build_dir)

    if not os.path.exists('build_release_stripped'):
      os.mkdir('build_release_stripped', dir_mode)

    os.chdir(pwd)

    cmd = "objcopy --strip-debug " if strip_binary else "cp -fv "
    cmd += constants.ENVOY_BINARY_TARGET_OUTPUT_PATH
    cmd += " build_release_stripped/envoy"

    cmd_params = cmd_exec.CommandParameters(cwd=self._build_dir)
    cmd_exec.run_command(cmd, cmd_params)

  def _generate_docker_ignore(self) -> None:
    """Generate a dockerignore file to reduce the context size."""

    omit_from_dockerignore = ['configs', 'build_release_stripped', 'ci']

    pwd = os.getcwd()
    os.chdir(self._build_dir)

    discovered_files = glob.glob('*')
    files_to_write = filter(
        lambda f: f not in omit_from_dockerignore, discovered_files
    )

    with open('.dockerignore', 'w') as dockerignore:
      for entry in files_to_write:
        dockerignore.write("{entry}\n".format(entry=entry))

    os.chdir(pwd)

  def create_docker_image(self) -> None:
    """Build a docker image with the newly compiled Envoy binary."""

    self._generate_docker_ignore()
    commit_hash = self._source_repo.commit_hash

    cmd = "docker build "
    cmd += "-f ci/Dockerfile-envoy "
    cmd += "-t envoyproxy/envoy-dev:{hash} ".format(hash=commit_hash)
    cmd += "--build-arg TARGETPLATFORM=\'.\' ."

    cmd_params = cmd_exec.CommandParameters(cwd=self._build_dir)
    cmd_exec.run_command(cmd, cmd_params)
