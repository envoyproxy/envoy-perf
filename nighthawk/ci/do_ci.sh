#!/bin/bash -e

if [[ -f "${HOME:-/root}/.gitconfig" ]]; then
    mv "${HOME:-/root}/.gitconfig" "${HOME:-/root}/.gitconfig_save"
fi

function do_build () {
    bazel build --verbose_failures=true //:nighthawk_client
}

function do_test() {
    bazel test --test_output=all --test_env=ENVOY_IP_TEST_VERSIONS=v4only \
      //test:nighthawk_test
}

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
