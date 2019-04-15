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
        "rate_limiter.h",
        "statistic.h",
    ],
    include_prefix = "nighthawk/common",
    deps = [
        "@envoy//include/envoy/common:base_includes",
        "@envoy//source/common/common:minimal_logger_lib",
        "@envoy//source/common/common:non_copyable",
        "@envoy//source/common/protobuf",
    ],
)
