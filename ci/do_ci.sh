#!/bin/bash

# Run a CI build/test target

# Avoid using "-x" here so that we do not leak credentials
# in build logs
set -e

# Setup Python virtual environment.
function setup_venv() {
  tools/python_virtualenv.sh
}

# Build the salvo framework
function build_salvo() {
  echo "Building Salvo"
  pushd salvo

  setup_venv
  bazel build //...
  tools/typecheck.sh

  popd
}
 
# Test the salvo framework
function test_salvo() {
  echo "Running Salvo unit tests"
  pushd salvo

  setup_venv
  tools/coverage.sh

  popd
}

# Check the Salvo python files format
function check_format() {
  echo "Checking the Salvo python files format"
  pushd salvo

  tools/format_python_tools.sh check

  popd
}

# Fix the Salvo python files format
function fix_format() {
  echo "Fixing the Salvo python files format"
  pushd salvo

  setup_venv
  tools/format_python_tools.sh fix 

  popd
}

# Calacute Salvo test coverage
function coverage() {
  echo "Calcuting the Salvo unit tests coverage"
  pushd salvo

  export MINIMUM_THRESHOLD=97
  echo "Setting the minimum threshold of coverage to ${MINIMUM_THRESHOLD}%"
  setup_venv
  tools/coverage.sh

  popd
}

# Set the build target. If no parameters are specified
# we default to "build"
build_target=${1:-build}

case $build_target in
  "build")
    build_salvo
    ;;
  "test")
    test_salvo
    ;;
  "check_format")
    check_format
    ;;
  "fix_format")
    fix_format
    ;;
  "coverage")
    coverage
    ;;
  *)
    echo "must be one of [build, test, check_format, fix_format, coverage]"
    exit 1
    ;;
esac

exit 0
