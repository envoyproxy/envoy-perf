#!/bin/bash -e

function do_build () {
    bazel build --verbose_failures=true //nighthawk:nighthawk_client
}

function do_test() {
    bazel test --test_output=all --test_env=ENVOY_IP_TEST_VERSIONS=v4only \
    //nighthawk/test:nighthawk_test
}

function do_clang_tidy() {
    ci/run_clang_tidy.sh
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
    export BAZEL_BUILD_OPTIONS="${BAZEL_BUILD_OPTIONS} --local_resources=4096,2,1"
    export BAZEL_TEST_OPTIONS="${BAZEL_TEST_OPTIONS} --local_resources=4096,2,1 --local_test_jobs=4"
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
    clang_tidy)
        export RUN_FULL_CLANG_TIDY=1
        do_clang_tidy
    ;;
    *)
        echo "must be one of [build,test,clang_tidy]"
        exit 1
    ;;
esac
