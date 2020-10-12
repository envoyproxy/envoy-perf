#!/usr/bin/env python3
"""
Test the base Docker class to ensure that we are parsing the control
object correctly
"""

import site
import pytest
from unittest import mock

site.addsitedir("src")

from lib.api.control_pb2 import JobControl
from lib.benchmark.base_benchmark import BaseBenchmark

def test_is_remote():
    """
    Verify that the local vs remote config is read correctly
    """

    # Local Invocation
    job_control = JobControl()
    job_control.remote = False
    job_control.scavenging_benchmark = True
    kwargs = {'control' : job_control}
    benchmark = BaseBenchmark(**kwargs)
    assert not benchmark.is_remote()

    # Remote Invocation
    job_control = JobControl()
    job_control.remote = True
    job_control.scavenging_benchmark = True
    kwargs = {'control' : job_control}
    benchmark = BaseBenchmark(**kwargs)
    assert benchmark.is_remote()

    # Unspecified should default to local
    job_control = JobControl()
    job_control.scavenging_benchmark = True
    kwargs = {'control' : job_control}
    benchmark = BaseBenchmark(**kwargs)
    assert not benchmark.is_remote()


def test_run_image():
    """
    Verify that we are calling the docker helper with expected arguments
    """

    # Create a minimal JobControl object to instantiate the Benchmark class
    job_control = JobControl()
    job_control.scavenging_benchmark = True

    with mock.patch('lib.docker_helper.DockerHelper.run_image',
                    mock.MagicMock(return_value='output string'))  \
                        as magic_mock:
        kwargs = {'control' : job_control}
        benchmark = BaseBenchmark(**kwargs)

        run_kwargs = {'environment': ['nothing_really_matters']}
        result = benchmark.run_image("this_really_doesnt_matter_either", **run_kwargs)


        # Verify that we are running the docker with all the supplied parameters
        magic_mock.assert_called_once_with("this_really_doesnt_matter_either",
                                           environment=['nothing_really_matters'])

        # Verify that the output from the container is returned.
        assert result == 'output string'

def test_pull_images():
    """
    Verify that when we pull images get a list of images names  back
    If the images fail to be retrieved, we should get an empty list
    """
    job_control = JobControl()
    job_control.images.reuse_nh_images = True
    job_control.images.nighthawk_benchmark_image = "envoyproxy/nighthawk-benchmark-dev:latest"

    with mock.patch('lib.docker_helper.DockerHelper.pull_image',
                    mock.MagicMock(return_value='envoyproxy/nighthawk-benchmark-dev:latest')) \
                        as magic_mock:
        kwargs = {'control' : job_control}
        benchmark = BaseBenchmark(**kwargs)

        result = benchmark.pull_images()

        magic_mock.assert_called_once_with('envoyproxy/nighthawk-benchmark-dev:latest')
        assert result != []
        assert len(result) == 1
        assert job_control.images.nighthawk_benchmark_image in result

def test_get_docker_volumes():
    """
    Test and validate the volume structure used when starting a container
    """
    volumes = BaseBenchmark.get_docker_volumes('/tmp/my-output-dir', '/tmp/my-test-dir')
    assert volumes is not None
    assert volumes != {}

    # Example volume structure:
    # {
    #    '/var/run/docker.sock': {
    #        'bind': '/var/run/docker.sock',
    #        'mode': 'rw'
    #    },
    #    '/tmp/my-output-dir': {
    #        'bind': '/tmp/my-output-dir',
    #        'mode': 'rw'
    #    },
    #    '/tmp/my-test-dir': {
    #        'bind': '/usr/local/bin/benchmarks/benchmarks.runfiles/nighthawk/benchmarks/external_tests/',
    #        'mode': 'ro'
    #    }
    # }

    # Assert that the docker socket is present in the mounts
    for volume in ['/var/run/docker.sock', '/tmp/my-output-dir', '/tmp/my-test-dir']:
        assert volume in volumes
        assert all(['bind' in volumes[volume], 'mode' in volumes[volume]])

        # Assert that we map the directory paths identically in the container except
        # for the tet directory
        if volume == '/tmp/my-test-dir':
            assert volumes[volume]['bind'] != volume
        else:
            assert volumes[volume]['bind'] == volume

if __name__ == '__main__':
    raise SystemExit(pytest.main(['-s', '-v', __file__]))
