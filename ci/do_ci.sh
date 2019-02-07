#!/bin/bash -e

if [[ -f "${HOME:-/root}/.gitconfig" ]]; then
    mv "${HOME:-/root}/.gitconfig" "${HOME:-/root}/.gitconfig_save"
fi

function do_build () {
    bazel build --verbose_failures=true //nighthawk:nighthawk_client
}

function do_test() {
    bazel test --test_output=all --test_env=ENVOY_IP_TEST_VERSIONS=v4only \
      //nighthawk/test:nighthawk_test
}

# TODO(oschaaf): To avoid OOM kicking in, we throttle resources here. Revisit this later
# to see how this was finally resolved in Envoy's code base. There is a TODO for when
# when a later bazel version is deployed in CI here:
# https://github.com/lizan/envoy/blob/2eb772ac7518c8fbf2a8c7acbc1bf89e548d9c86/ci/do_ci.sh#L86
[ -z "$CIRCLECI" ] || export BAZEL_BUILD_OPTIONS="${BAZEL_BUILD_OPTIONS} --local_resources=4096,2,1"
[ -z "$CIRCLECI" ] || export BAZEL_TEST_OPTIONS="${BAZEL_TEST_OPTIONS} --local_resources=4096,2,1 --local_test_jobs=4"

# TODO(oschaaf): hack, this should be done in .circleci/config.yml	# TODO(oschaaf): To avoid OOM kicking in, we throttle resources here. Revisit this later
git submodule update --init --recursive

case "$1" in
  build)
    do_build
  ;;
  test)
    do_test
  ;;
  *)
    echo "must be one of [build,test]"
    exit 1
  ;;
esac
