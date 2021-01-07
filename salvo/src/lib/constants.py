"""This module defines string constants used in various parts of Salvo"""

# The DOCKER_SOCKET_PATH identifies the unix socket creatd by the docker
# daemon. In its absense any operations interacting with docker will fail.
DOCKER_SOCKET_PATH = '/var/run/docker.sock'

# SALVO_TMP is the path where any temporary directories are created when
# operating locally
SALVO_TMP = '/tmp/salvo'

# NIGHTHAWK_EXTERNAL_TEST_DIR is the location within the nighthawk-benchmark
# container where user provided test are mounted. The benchmark discovers all
# tests in this path, in the container, and executes them
NIGHTHAWK_EXTERNAL_TEST_DIR = ('/usr/local/bin/benchmarks/benchmarks.runfiles'
                               '/nighthawk/benchmarks/external_tests/')

# OPT_LLVM and USR_BIN are directory prefixes where we search for the clang
# compiler used to build the Envoy binary
OPT_LLVM = '/opt/llvm/bin/'
USR_BIN = '/usr/bin'

