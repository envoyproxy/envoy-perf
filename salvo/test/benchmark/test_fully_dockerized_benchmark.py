#!/usr/bin/env python3
"""
Test the fully dockerized benchmark class
"""

import site
import pytest

site.addsitedir("src")

from lib.api.control_pb2 import JobControl
from lib.benchmark.fully_dockerized_benchmark import Benchmark

def test_images_only_config():
    """
    Test benchmark validation logic
    """

    # create a valid configuration defining images only for benchmark
    job_control = JobControl()
    job_control.remote = True
    job_control.scavenging_benchmark = True

    docker_images = job_control.images
    docker_images.reuse_nh_images = True
    docker_images.nighthawk_benchmark_image = \
        "envoyproxy/nighthawk-benchmark-dev:test_images_only_config"
    docker_images.nighthawk_binary_image = \
        "envoyproxy/nighthawk-dev:test_images_only_config"
    docker_images.envoy_image = \
        "envoyproxy/envoy-dev:f61b096f6a2dd3a9c74b9a9369a6ea398dbe1f0f"

    env = job_control.environment
    env.variables["TMP_DIR"] = "/home/ubuntu/nighthawk_output"
    env.v4only = True
    env.envoy_path = "envoy"

    kwargs = {'control': job_control}
    benchmark = Benchmark(**kwargs)

    # Calling validate shoud not throw an exception
    benchmark.validate()


def test_no_envoy_image_no_sources():
    """
    Test benchmark validation logic.  No Envoy image is specified, we
    expect validate to throw an exception since no sources are present
    """
    # create a valid configuration with a missing Envoy image
    job_control = JobControl()
    job_control.remote = True
    job_control.scavenging_benchmark = True

    docker_images = job_control.images
    docker_images.reuse_nh_images = True
    docker_images.reuse_nh_images = True
    docker_images.nighthawk_benchmark_image = \
        "envoyproxy/nighthawk-benchmark-dev:test_missing_envoy_image"
    docker_images.nighthawk_binary_image = \
        "envoyproxy/nighthawk-dev:test_missing_envoy_image"

    kwargs = {'control': job_control}
    benchmark = Benchmark(**kwargs)

    # Calling validate shoud not throw an exception
    with pytest.raises(Exception) as validation_exception:
        benchmark.validate()

    assert str(validation_exception.value) == "No source configuration specified"


def test_source_to_build_envoy():
    """
    Validate that sources are defined that enable us to build the Envoy image
    """
    # create a valid configuration with a missing Envoy image
    job_control = JobControl()
    job_control.remote = True
    job_control.scavenging_benchmark = True

    docker_images = job_control.images
    docker_images.reuse_nh_images = True
    docker_images.nighthawk_benchmark_image = \
        "envoyproxy/nighthawk-benchmark-dev:test_source_present_to_build_envoy"
    docker_images.nighthawk_binary_image = \
        "envoyproxy/nighthawk-dev:test_source_present_to_build_envoy"


    envoy_source = job_control.source.add()
    envoy_source.envoy = True
    envoy_source.location = "/home/ubuntu/envoy"
    envoy_source.url = "https://github.com/envoyproxy/envoy.git"
    envoy_source.branch = "master"
    envoy_source.hash = "e744a103756e9242342662442ddb308382e26c8b"

    kwargs = {'control': job_control}
    benchmark = Benchmark(**kwargs)

    benchmark.validate()

def test_no_source_to_build_envoy():
    """
    Validate that no sources are defined that enable us to build the missing Envoy image
    """
    # create a valid configuration with a missing Envoy image
    job_control = JobControl()
    job_control.remote = True
    job_control.scavenging_benchmark = True

    docker_images = job_control.images
    docker_images.reuse_nh_images = True
    docker_images.nighthawk_benchmark_image = \
        "envoyproxy/nighthawk-benchmark-dev:test_no_source_present_to_build_envoy"
    docker_images.nighthawk_binary_image = \
        "envoyproxy/nighthawk-dev:test_no_source_present_to_build_envoy"

    envoy_source = job_control.source.add()

    # Denote that the soure is for nighthawk.  Values aren't really checked at this stage
    # since we have a missing Envoy image and a nighthawk source validation should fail.
    envoy_source.nighthawk = True
    envoy_source.location = "/home/ubuntu/envoy"
    envoy_source.url = "https://github.com/envoyproxy/envoy.git"
    envoy_source.branch = "master"
    envoy_source.hash = "e744a103756e9242342662442ddb308382e26c8b"

    kwargs = {'control': job_control}
    benchmark = Benchmark(**kwargs)

    # Calling validate shoud not throw an exception
    with pytest.raises(Exception) as validation_exception:
        benchmark.validate()

    assert str(validation_exception.value) == \
        "No source specified to build undefined Envoy image"

def test_no_source_to_build_nh():
    """
    Validate that no sources are defined that enable us to build the missing Envoy image
    """
    # create a valid configuration with a missing NightHawk container image
    job_control = JobControl()
    job_control.remote = True
    job_control.scavenging_benchmark = True

    docker_images = job_control.images
    docker_images.reuse_nh_images = True
    docker_images.nighthawk_benchmark_image = \
        "envoyproxy/nighthawk-benchmark-dev:test_no_source_present_to_build_nighthawk"
    docker_images.envoy_image = \
        "envoyproxy/envoy-dev:test_no_source_present_to_build_nighthawk"

    job_control.images.CopyFrom(docker_images)

    envoy_source = job_control.source.add()

    # Denote that the soure is for envoy.  Values aren't really checked at this stage
    # since we have a missing Envoy image and a nighthawk source validation should fail.
    envoy_source.envoy = True
    envoy_source.location = "/home/ubuntu/envoy"
    envoy_source.url = "https://github.com/envoyproxy/envoy.git"
    envoy_source.branch = "master"
    envoy_source.hash = "e744a103756e9242342662442ddb308382e26c8b"

    kwargs = {'control': job_control}
    benchmark = Benchmark(**kwargs)

    # Calling validate shoud not throw an exception
    with pytest.raises(Exception) as validation_exception:
        benchmark.validate()

    assert str(validation_exception.value) == \
        "No source specified to build undefined NightHawk image"


def test_no_source_to_build_nh2():
    """
    Validate that no sources are defined that enable us to build the missing Envoy image
    """
    # create a valid configuration with a missing both NightHawk container images
    job_control = JobControl()
    job_control.remote = True
    job_control.scavenging_benchmark = True

    docker_images = job_control.images
    docker_images.envoy_image = \
        "envoyproxy/envoy-dev:test_no_source_present_to_build_both_nighthawk_images"

    envoy_source = job_control.source.add()

    # Denote that the soure is for envoy.  Values aren't really checked at this stage
    # since we have a missing Envoy image and a nighthawk source validation should fail.
    envoy_source.envoy = True
    envoy_source.location = "/home/ubuntu/envoy"
    envoy_source.url = "https://github.com/envoyproxy/envoy.git"
    envoy_source.branch = "master"
    envoy_source.hash = "e744a103756e9242342662442ddb308382e26c8b"

    kwargs = {'control': job_control}
    benchmark = Benchmark(**kwargs)

    # Calling validate shoud not throw an exception
    with pytest.raises(Exception) as validation_exception:
        benchmark.validate()

    assert str(validation_exception.value) == \
        "No source specified to build undefined NightHawk image"

if __name__ == '__main__':
    raise SystemExit(pytest.main(['-s', '-v', __file__]))
