"""
Constants module
"""

"""
The DOCKER_SOCKET_PATH identifies the unix socket creatd by the docker
daemon. In its absense any operations interacting with docker will fail.
"""
DOCKER_SOCKET_PATH = '/var/run/docker.sock'

"""
NIGHTHAWK_EXTERNAL_TEST_DIR is the location within the nighthawk-benchmark container
where user provided test are mounted. The benchmark discovers all tests in this path,
in the container, and runs them
"""
NIGHTHAWK_EXTERNAL_TEST_DIR = '/usr/local/bin/benchmarks/benchmarks.runfiles/nighthawk/benchmarks/external_tests/'
