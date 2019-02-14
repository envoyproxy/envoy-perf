load(
    "@envoy//bazel:envoy_build_system.bzl",
    "envoy_basic_cc_library",
    "envoy_package",
)

licenses(["notice"])  # Apache 2

envoy_package()

envoy_basic_cc_library(
    name = "client_includes",
    hdrs = [
        "options.h",
    ],
    include_prefix = "nighthawk/client",
    deps = [
        "@envoy//include/envoy/common:base_includes",
        "@envoy//source/common/protobuf",
    ],
)
