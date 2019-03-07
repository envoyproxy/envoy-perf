#!/bin/bash -e

function do_build () {
    bazel build $BAZEL_BUILD_OPTIONS --verbose_failures=true //nighthawk:nighthawk_client
}

function do_test() {
    bazel test $BAZEL_BUILD_OPTIONS $BAZEL_TEST_OPTIONS --test_output=all --test_env=ENVOY_IP_TEST_VERSIONS=v4only \
    //nighthawk/test:nighthawk_test
}

function do_test_with_valgrind() {
    apt-get update && apt-get install valgrind && \
    bazel build $BAZEL_BUILD_OPTIONS -c dbg //nighthawk/test:nighthawk_test && \
    nighthawk/tools/valgrind-tests.sh
}

function do_clang_tidy() {
    ci/run_clang_tidy.sh
}

#BAZEL_TEST_OPTIONS="${BAZEL_TEST_OPTIONS} -c dbg --copt=-DNDEBUG"


function do_coverage() {
    [[ -z "${SRCDIR}" ]] && SRCDIR="${PWD}"
    [[ -z "${BAZEL_COVERAGE}" ]] && BAZEL_COVERAGE=bazel
    [[ -z "${VALIDATE_COVERAGE}" ]] && VALIDATE_COVERAGE=true
    
    # This is the target that will be run to generate coverage data. It can be overridden by consumer
    # projects that want to run coverage on a different/combined target.
    [[ -z "${COVERAGE_TARGET}" ]] && COVERAGE_TARGET="//nighthawk/test/..."
    
    # Generate coverage data.
    "${BAZEL_COVERAGE}" coverage ${BAZEL_TEST_OPTIONS} \
    "${COVERAGE_TARGET}"  \
    --experimental_cc_coverage \
    --instrumentation_filter=//nighthawk/source/...,//nighthawk/include/...,-//nighthawk/hdrhistogram_c/...,-//nighthawk/envoy/... \
    --coverage_report_generator=@bazel_tools//tools/test/CoverageOutputGenerator/java/com/google/devtools/coverageoutputgenerator:Main \
    --combined_report=lcov
    
    # Generate HTML
    declare -r COVERAGE_DIR="${SRCDIR}"/generated/coverage
    declare -r COVERAGE_SUMMARY="${COVERAGE_DIR}/coverage_summary.txt"
    mkdir -p "${COVERAGE_DIR}"
    genhtml bazel-out/_coverage/_coverage_report.dat --output-directory="${COVERAGE_DIR}" | tee "${COVERAGE_SUMMARY}"
    
    [[ -z "${ENVOY_COVERAGE_DIR}" ]] || rsync -av "${COVERAGE_DIR}"/ "${ENVOY_COVERAGE_DIR}"
    
    if [ "$VALIDATE_COVERAGE" == "true" ]
    then
        COVERAGE_VALUE=$(grep -Po '.*lines[.]*: \K(\d|\.)*' "${COVERAGE_SUMMARY}")
        COVERAGE_THRESHOLD=97.5
        COVERAGE_FAILED=$(echo "${COVERAGE_VALUE}<${COVERAGE_THRESHOLD}" | bc)
        
        echo "HTML coverage report is in ${COVERAGE_DIR}/coverage.html"
        
        if test ${COVERAGE_FAILED} -eq 1; then
            echo Code coverage ${COVERAGE_VALUE} is lower than limit of ${COVERAGE_THRESHOLD}
            exit 1
        else
            echo Code coverage ${COVERAGE_VALUE} is good and higher than limit of ${COVERAGE_THRESHOLD}
        fi
    fi
}

# TODO(oschaaf): To avoid OOM kicking in, we throttle resources here. Revisit this later
# to see how this was finally resolved in Envoy's code base. There is a TODO for when
# when a later bazel version is deployed in CI here:
# https://github.com/lizan/envoy/blob/2eb772ac7518c8fbf2a8c7acbc1bf89e548d9c86/ci/do_ci.sh#L86
if [ -n "$CIRCLECI" ]; then
    # TODO(oschaaf): hack, this should be done in .circleci/config.yml
    git submodule update --init --recursive
    if [[ -f "${HOME:-/root}/.gitconfig" ]]; then
        mv "${HOME:-/root}/.gitconfig" "${HOME:-/root}/.gitconfig_save"
        echo 1
    fi
    export BAZEL_BUILD_OPTIONS="${BAZEL_BUILD_OPTIONS} --jobs 8"
    export BAZEL_TEST_OPTIONS="${BAZEL_TEST_OPTIONS} --jobs 8 --local_test_jobs=8"
    export MAKEFLAGS="-j 8"
fi

if [ "$1" == "coverage" ]; then
    export CC=gcc
    export CXX=g++
else
    export PATH=/usr/lib/llvm-7/bin:$PATH
    export CC=clang
    export CXX=clang++
fi

case "$1" in
    build)
        do_build
    ;;
    test)
        do_test
    ;;
    test_with_valgrind)
        do_test_with_valgrind
    ;;
    clang_tidy)
        export RUN_FULL_CLANG_TIDY=1
        do_clang_tidy
    ;;
    coverage)
        do_coverage
    ;;
    *)
        echo "must be one of [build,test,clang_tidy,test_with_valgrind,coverage]"
        exit 1
    ;;
esac
