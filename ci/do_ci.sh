#!/bin/bash

# Run a CI build/test target

# Avoid using "-x" here so that we do not leak credentials
# in build logs
set -e

# Build the salvo framework
function build_salvo() {
  echo "Building Salvo"
  pushd salvo
  bazel build //:salvo
  popd
}
 
# Test the salvo framework
# TODO(abaptiste) Tests currently fail in CI, but pass locally. 
function test_salvo() {
  echo "Running Salvo unit tests"
  pushd salvo
  bazel test //test:*
  popd
}


# Set the build target. If no parameters are specified
# we default to "build"
build_target=${1:-build}

case $build_target in
  "build")
    build_salvo
    ;;
  *)
    ;;
esac

exit 0
