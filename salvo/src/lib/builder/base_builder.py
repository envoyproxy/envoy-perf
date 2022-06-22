"""Base builder class initializing the temporary directories and environment variables needed to \
execute bazel."""
import os
import logging

from src.lib import (cmd_exec, constants, source_manager)
from src.lib.common import file_ops
from src.lib.builder import bazel_setup
import api.source_pb2 as proto_source

log = logging.getLogger(__name__)


class BaseBuilderError(Exception):
  """An error raised from the BaseBuilder class if we encounter a situation where no progress can \
  be made."""


class BaseBuilder():
  """BaseBuilder class encapsulating common build methods and objects managing sources."""

  def __init__(self, manager: source_manager.SourceManager) -> None:
    """Initialize the builder with the location of the source and setup temporary directories \
    needed for operation.

    Args:
      manager: The SourceManager object handling the source code used by this builder object
    """
    self._source_manager = manager

    # TODO(abaptiste): Preserve the location of the source so that
    # if nothing changes we can reuse the same disk data.  This could
    # be considered a sandbox of sorts.
    temp_dir = os.getenv('SALVO_HOMEDIR', constants.SALVO_TMP)

    # self._cache_dir is where the bazel cache is created
    self._cache_dir = file_ops.get_random_dir(temp_dir)

    # self._build_dir is where the source is copied or checked out. This is
    # the working directory where bazel operations are performed.  The
    # _build_dir is set from the destination directory of the source in the
    # source_tree object
    self._build_dir = None

    os.environ['HOME'] = self._cache_dir.name
    log.debug(f"Using HOME={os.environ['HOME']}")

    bazel_setup.setup_clang_env()

  def set_build_dir(self, source_directory: str) -> None:
    """Set the source directory where build operations take place.

    Args:
      source_directory: The location of the source being built
    """
    self._build_dir = source_directory

  def _validate(self) -> None:
    """Verify the source and other dependencies required to build an artifact.

    This method should be overridden by a derived class.

    Raises:
      NotImplementedError: if this base method is invoked.
    """
    raise NotImplementedError("Method should be overridden")

  def _run_bazel_clean(self) -> None:
    """Run bazel clean in the source tree directory."""
    assert self._build_dir

    cmd_params = cmd_exec.CommandParameters(cwd=self._build_dir)
    cmd = "bazel clean"
    output = cmd_exec.run_command(cmd, cmd_params, False)
    log.debug(f"Clean output: {output}")

  def _generate_bazel_options(self, source_id: proto_source.SourceRepository.SourceIdentity) -> str:
    """Generate the options string that we supply to bazel when building Envoy or NightHawk.

    Args:
      source_id: The identity of the source object containing the options
        we specify to bazel

    Returns:
      A string with options supplied to bazel when compiling artifacts
    """
    options = []

    optimized_builds = True

    source_repo = self._source_manager.get_source_repository(source_id)
    bazel_options = source_repo.bazel_options
    for option in bazel_options:
      if option.parameter not in options:
        options.append(option.parameter)
      if optimized_builds and option.parameter.startswith("-c"):
        optimized_builds = False

    if optimized_builds:
      options.append("-c opt")

    return " ".join(options)
