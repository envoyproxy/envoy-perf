"""This module sets up environment variables required to execute bazel salvo."""
import os

from src.lib import constants


def get_clang_dir() -> str:
  """Return the directory prefix where clang resides.

  For now we return a static path.  More is needed here to discover the real
  location since clang can live in /opt/llvm/bin as well.

  Returns:
    a string with the directory prefix where clang appears
  """
  paths = [constants.OPT_LLVM, constants.USR_BIN]
  for path in paths:
    if os.path.exists(os.path.join(path, 'clang')):
      return path

  return ''


def setup_clang_env() -> None:
  """Set the environment variables to use clang as a compiler."""
  # Use CC from the environment if specified. If not, use clang
  # TODO: We need additional sanity checks to ensure that the binaries
  #       we are trying to use exist and fail fast if they are absent.
  if any(['CC' not in os.environ, 'CXX' not in os.environ]):
    clang_dir = get_clang_dir()
    os.environ['CC'] = os.path.join(clang_dir, 'clang')
    os.environ['CXX'] = os.path.join(clang_dir, 'clang++')
