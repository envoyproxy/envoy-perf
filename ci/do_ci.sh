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

function do_coverage() {
    gcc -v && \
	gcov -v && \
	env && \
    bazel coverage $BAZEL_BUILD_OPTIONS -s --test_output=all --verbose_failures --experimental_cc_coverage nighthawk/test/...  --instrumentation_filter=//nighthawk/...,. --coverage_report_generator=@bazel_tools//tools/test/CoverageOutputGenerator/java/com/google/devtools/coverageoutputgenerator:Main --combined_report=lcov; genhtml bazel-out/_coverage/_coverage_report.dat
}

# TODO(oschaaf): hack, this should be done in .circleci/config.yml
git submodule update --init --recursive

# TODO(oschaaf): To avoid OOM kicking in, we throttle resources here. Revisit this later
# to see how this was finally resolved in Envoy's code base. There is a TODO for when
# when a later bazel version is deployed in CI here:
# https://github.com/lizan/envoy/blob/2eb772ac7518c8fbf2a8c7acbc1bf89e548d9c86/ci/do_ci.sh#L86
if [ -n "$CIRCLECI" ]; then
    if [[ -f "${HOME:-/root}/.gitconfig" ]]; then
        mv "${HOME:-/root}/.gitconfig" "${HOME:-/root}/.gitconfig_save"
        echo 1
    fi
    export BAZEL_BUILD_OPTIONS="${BAZEL_BUILD_OPTIONS} --jobs 4"
    export BAZEL_TEST_OPTIONS="${BAZEL_TEST_OPTIONS} --jobs 4 --local_test_jobs=4"
    export MAKEFLAGS="-j 4"
fi

if [ "$1" != "coverage" ]; then
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
