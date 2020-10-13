#!/bin/bash

# Run a CI build/test target

# Avoid using "-x" here so that we do not leak credentials
# in build logs
set -e

trap cleanup EXIT

# Set the build target. If no parameters are specified
# we default to "build"
build_target=${1:-build}


# Gather any test logs for debugging
function cleanup() {
  echo "Gathering logs for ${build_target}"

  cd salvo

  output_dir=/tmp/test_logs
  output_path=$(bazel info output_path)

  if [ -d "${output_path}" ]
  then
    cd ${output_path}
    mkdir -p ${output_dir}
    [ -d k8-fastbuild/testlogs/test ] && tar czf ${output_dir}/logs.tgz -C k8-fastbuild/testlogs test
  fi
}

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


case $build_target in
  "test")
    test_salvo
    ;;
  "build")
    build_salvo
    ;;
  *)
    ;;
esac

exit 0
