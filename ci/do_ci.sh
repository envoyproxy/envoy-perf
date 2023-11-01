#!/bin/bash

# Run a CI build/test target

# Avoid using "-x" here so that we do not leak credentials
# in build logs
set -e

# Setup a Python virtual environment.
function setup_salvo_venv() {
  echo "Installing virtualenv"
  pip3 install --upgrade vitualenv
  
  source tools/python_virtualenv.sh
  reuse_or_create_salvo_venv
}

# Build the salvo framework.
function build_salvo() {
  echo "Building salvo"
  pushd salvo

  setup_salvo_venv
  bazel build //...
  tools/typecheck.sh

  popd
}

# Build the salvo-remote controller.
function build_salvo_remote() {
  echo "Building salvo-remote"
  pushd salvo-remote

  bazel build ...

  popd
}

# Test the salvo framework.
function test_salvo() {
  echo "Running salvo unit tests"
  pushd salvo

  setup_salvo_venv
  bazel test //...

  popd
}

# Test the salvo-remote controller.
function test_salvo_remote() {
  echo "Running salvo-remote unit tests"
  pushd salvo-remote

  bazel test ...

  popd
}

# Check the salvo python files format.
function check_format() {
  echo "Checking the salvo python files format"
  pushd salvo

  setup_salvo_venv
  tools/format_python_tools.sh check

  popd
}

# Check the salvo-remote Go files.
function check_format_salvo_remote() {
  echo "Checking the salvo-remote Go files"
  pushd salvo-remote

  go vet ./...
  diff -u <(echo -n) <(gofmt -d -s .)

  popd
}

# Fix the salvo python files format.
function fix_format() {
  echo "Fixing the salvo python files format"
  pushd salvo

  setup_salvo_venv
  tools/format_python_tools.sh fix 

  popd
}

# Fix the salvo-remote Go files format.
function fix_format_salvo_remote() {
  echo "Fixing the salvo-remote Go files format"
  pushd salvo-remote

  gofmt -w -s .

  popd
}

# Calculate salvo test coverage.
function coverage() {
  echo "Calculating the salvo unit tests coverage"
  pushd salvo

  export MINIMUM_THRESHOLD=97
  echo "Setting the minimum threshold of coverage to ${MINIMUM_THRESHOLD}%"
  setup_salvo_venv
  tools/coverage.sh

  popd
}

# Calculate salvo-remote test coverage.
function coverage_salvo_remote() {
  echo "Calculating the salvo-remote unit tests coverage"
  pushd salvo-remote

  # TODO(mum4k): Implement coverage threshold checking.
  bazel coverage ...

  popd
}

# Package the salvo-remote binary and sandbox definitions into a zip file.
function package_salvo_remote_and_sandboxes() {
  echo "Packaging salvo-remote and sandboxes"
  pushd salvo-remote

  bazel build -c opt salvo-remote
  cp bazel-bin/salvo-remote_/salvo-remote .
  chmod 0755 salvo-remote
  zip -r \
    bazel-bin/salvo-remote.zip \
    salvo-remote sandboxes/terraform \
    -x \*/.terraform/\*

  # If we are running under ci/run_envoy_docker.sh, this is the only directory
  # accessible by the host (outside of Docker).
  export BUILD_DIR="/build"
  if [ -d ${BUILD_DIR} ]; then
    cp bazel-bin/salvo-remote.zip ${BUILD_DIR}
  fi

  popd
}



# Set the build target. If no parameters are specified
# we default to "build"
build_target=${1:-build}

case $build_target in
  "build")
    build_salvo
    ;;
  "build_salvo_remote")
    build_salvo_remote
    ;;
  "test")
    test_salvo
    ;;
  "test_salvo_remote")
    test_salvo_remote
    ;;
  "check_format")
    check_format
    ;;
  "check_format_salvo_remote")
    check_format_salvo_remote
    ;;
  "fix_format")
    fix_format
    ;;
  "fix_format_salvo_remote")
    fix_format_salvo_remote
    ;;
  "coverage")
    coverage
    ;;
  "coverage_salvo_remote")
    coverage_salvo_remote
    ;;
  "package_salvo_remote_and_sandboxes")
    package_salvo_remote_and_sandboxes
    ;;
  *)
    echo "must be one of [build, build_salvo_remote, test, test_salvo_remote, check_format, check_format_salvo_remote, fix_format, fix_format_salvo_remote, coverage, coverage_salvo_remote, package_salvo_remote_and_sandboxes]"
    exit 1
    ;;
esac

exit 0
