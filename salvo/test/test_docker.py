#!/usr/bin/env python3
"""
Test Docker interactions
"""

import re
import site
import pytest

site.addsitedir("src")

from lib.docker_helper import DockerHelper

def test_pull_image():
    """Test retrieving an image"""
    helper = DockerHelper()
    container = helper.pull_image("oschaaf/benchmark-dev:latest")
    assert container is not None

def test_run_image():
    """Test executing a command in an image"""
    env = ['key1=val1', 'key2=val2']
    cmd = ['uname', '-r']
    image_name = 'oschaaf/benchmark-dev:latest'

    helper = DockerHelper()
    kwargs = {}
    kwargs['environment'] = env
    kwargs['command'] = cmd
    result = helper.run_image(image_name, **kwargs)

    assert result is not None
    assert re.match(r'[0-9\-a-z]', result.decode('utf-8')) is not None

def test_list_images():
    """Test listing available images"""
    helper = DockerHelper()
    images = helper.list_images()
    assert images != []

if __name__ == '__main__':
    raise SystemExit(pytest.main(['-s', '-v', __file__]))
