export TEST_WORKSPACE=.
export TEST_SRCDIR="$(pwd)"
export ENVOY_IP_TEST_VERSIONS="v4only"
valgrind --leak-check=full --track-origins=yes --gen-suppressions=all --suppressions=envoy/tools/valgrind-suppressions.txt --suppressions=tools/valgrind-suppressions.txt bazel-bin/test/nighthawk_test
