"""
Test source management operations needed for executing benchmarks
"""
import logging
import shlex
import pytest
from unittest import mock

from src.lib import (source_manager, source_tree)

import api.control_pb2 as proto_control

logging.basicConfig(level=logging.DEBUG)

log = logging.getLogger(__name__)

def _run_command_side_effect(*args):
  """Adjust the check_output output so that we can respond differently to
  input arguments.

  Args:
    args: the list of arguments received by the mocked functin
  """
  pass

def _generate_default_benchmark_images(job_control):
  """Generate a default image configuration for the job control object."""

  image_config = job_control.images
  image_config.reuse_nh_images = True
  image_config.nighthawk_benchmark_image = \
    "envoyproxy/nighthawk-benchmark-dev:latest"
  image_config.nighthawk_binary_image = \
    "envoyproxy/nighthawk-dev:latest"

  return image_config

@mock.patch("src.lib.cmd_exec.run_command")
def test_get_envoy_images_for_benchmark(mock_run_command):
  """Verify that we can determine the current and previous image
     tags from a minimal job control object.
  """
  pass

def _run_command_side_effect_for_disk_files(*args):
  """Adjust the check_call output so that we can respond differently to
     input arguments.

  Args:
    args: the list of arguments received by the mocked function
  """
  pass

@mock.patch("src.lib.cmd_exec.run_command")
def test_previous_hash_with_disk_files(mock_run_command):
  """
  Verify that we can determine Envoy images from source locations
  """
  pass


if __name__ == '__main__':
  raise SystemExit(pytest.main(['-s', '-v', __file__]))
