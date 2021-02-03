#!/bin/bash

# This script executes all tests and then evaluates the code coverage
# for Salvo.  All individual coverage files are merged to provide one
# report for the entire codebase

# Adapted from https://github.com/bazelbuild/bazel/issues/10660
GITHUB_WORKSPACE=${PWD}

cd ${GITHUB_WORKSPACE}
if [ ! -d ${GITHUB_WORKSPACE}/coveragepy-lcov-support ]
then
  curl -L https://github.com/ulfjack/coveragepy/archive/lcov-support.tar.gz | tar xz
fi

bazel coverage -t- --instrument_test_targets \
	--test_output=errors \
  --linkopt=--coverage \
	--test_env=PYTHON_COVERAGE=${GITHUB_WORKSPACE}/coveragepy-lcov-support/__main__.py \
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

# Extract all coverage data for salvo project files
lcov -e coverage/coverage.dat -o coverage/salvo.dat '*/salvo/src/lib/*.py'

# Redirect source file paths from the sandbox to the real source files.
# Changes strings like this:
#   SF:/some/path/to/bazel/sandbox/bazel-out/k8-fastbuild/bin/src/lib/docker/test_docker_image.runfiles/salvo/src/lib/constants.py
# To strings like this:
#   SF:src/lib/constants.py
sed -e 's/SF.*\.runfiles\/salvo\/\(.*\)$/SF:\1/' -i coverage/salvo.dat

# Generate HTML coverage report.
mkdir -p coverage/html
genhtml coverage/salvo.dat -o coverage/html
echo "HTML coverage report generated, view by running:"
echo "  (cd coverage/html && python3 -m http.server)"
