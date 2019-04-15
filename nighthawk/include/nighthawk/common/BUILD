load(
    "@envoy//bazel:envoy_build_system.bzl",
    "envoy_basic_cc_library",
    "envoy_package",
)

licenses(["notice"])  # Apache 2

envoy_package()

envoy_basic_cc_library(
    name = "base_includes",
    hdrs = [
        "exception.h",
    ],
    include_prefix = "nighthawk/common",
)
