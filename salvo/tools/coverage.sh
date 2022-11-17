#!/bin/bash

# This script executes all tests and then evaluates the code coverage
# for Salvo.  All individual coverage files are merged to provide one
# report for the entire codebase

# Exit immediately if a command exits with a non-zero status.
# pipefail indicates that the return value of a pipeline is the status
# of the last command to exit with a non-zero status.
set -eo pipefail

# Adapted from https://github.com/bazelbuild/bazel/issues/10660
GITHUB_WORKSPACE=${PWD}

MINIMUM_THRESHOLD=${MINIMUM_THRESHOLD:=97.5}

cd ${GITHUB_WORKSPACE}
if [ ! -d ${GITHUB_WORKSPACE}/coveragepy-lcov-support ]
then
  curl -L https://github.com/ulfjack/coveragepy/archive/lcov-support.tar.gz | tar xz
fi

bazel coverage -t- \
  --instrument_test_targets \
  --test_output=errors \
  --linkopt=--coverage \
  --test_env=PYTHON_COVERAGE=${GITHUB_WORKSPACE}/coveragepy-lcov-support/__main__.py \
  --java_runtime_version=remotejdk_11 \
  //...

# Combine all coverage data into one file
CMD="lcov"
for file in $(find bazel-out/ -name coverage.dat)
do
  CMD="${CMD} -a ${file}"
done

mkdir -p coverage
CMD="${CMD} -o coverage/coverage.dat"
(${CMD})

# Remove files we can't calculate coverage on:
#   - auto-generated protocol buffer libraries.
lcov \
  --remove coverage/coverage.dat \
  -o coverage/coverage_filtered.dat \
  '*_pb2.py'

# Extract all coverage data for salvo project files
lcov \
  -e coverage/coverage_filtered.dat \
  -o coverage/salvo.dat \
  '*/*runfiles/salvo/*'

# Redirect source file paths from the sandbox to the real source files.
# Changes strings like this:
#   SF:/some/path/to/bazel/sandbox/bazel-out/k8-fastbuild/bin/src/lib/docker/test_docker_image.runfiles/salvo/src/lib/constants.py
# To strings like this:
#   SF:src/lib/constants.py
sed -e 's/SF.*\.runfiles\/salvo\/\(.*\)$/SF:\1/' -i coverage/salvo.dat

# Generate HTML coverage report.
mkdir -p coverage/html
genhtml coverage/salvo.dat -o coverage/html
zip -r coverage/html.zip coverage/html/

echo "HTML coverage report generated, view by running:"
echo "  (cd salvo/coverage/html && python3 -m http.server)"
echo "Or download the zip file from salvo/coverage/html.zip"

# Examine the coverage summary and extract the overall coverage percentage.
# If the reported threshold drops below the specified threshold, then we
# fail the build.  There is likely a way to get this from the genhtml output
# so that we don't have to execute lcov an additional time.  However this works.
COVERAGE_PERCENTAGE=$(lcov --summary coverage/salvo.dat 2>&1 | grep lines | awk '{print $2}'| tr -d \%)

if (( $(echo "${COVERAGE_PERCENTAGE} < ${MINIMUM_THRESHOLD}" | bc -l) ))
then
  echo "Test coverage percentage ${COVERAGE_PERCENTAGE}% has dipped below ${MINIMUM_THRESHOLD}%"
  exit 1
fi

echo "Tests coverage ${COVERAGE_PERCENTAGE}% was higher than or equal to ${MINIMUM_THRESHOLD}%"
exit 0
