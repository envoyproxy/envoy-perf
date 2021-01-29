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

CMD="lcov"
for file in $(find bazel-out/ -name coverage.dat)
do
  CMD="${CMD} -a ${file}"
done

mkdir -p coverage
CMD="${CMD} -o coverage/coverage.dat"
(${CMD})

