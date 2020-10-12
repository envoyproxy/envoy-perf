"""
Test source management operations needed for executing benchmarks
"""
import logging
import site
import pytest

site.addsitedir("src")

import lib.source_manager as source_manager
from lib.api.control_pb2 import JobControl

logging.basicConfig(level=logging.DEBUG)

def test_get_envoy_images_for_benchmark():
    """
    Verify that we can determine the current and previous image
    tags from a minimal job control object.  This test actually invokes
    git and creates artifacts on disk.
    """

    job_control = JobControl()
    job_control.remote = False
    job_control.scavenging_benchmark = True

    job_control.images.reuse_nh_images = True
    job_control.images.nighthawk_benchmark_image = "envoyproxy/nighthawk-benchmark-dev:latest"
    job_control.images.nighthawk_binary_image = "envoyproxy/nighthawk-dev:latest"
    job_control.images.envoy_image = "envoyproxy/envoy-dev:latest"

    kwargs = {
        'control' : job_control
    }

    # TODO: Mock the subprocess calls
    src_mgr = source_manager.SourceManager(**kwargs)
    hashes = src_mgr.get_envoy_images_for_benchmark()

    assert hashes is not None
    assert hashes != {}

if __name__ == '__main__':
    raise SystemExit(pytest.main(['-s', '-v', __file__]))
