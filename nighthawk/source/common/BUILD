licenses(["notice"])  # Apache 2

load(
    "@envoy//bazel:envoy_build_system.bzl",
    "envoy_cc_binary",
    "envoy_cc_library",
    "envoy_cc_platform_dep",
    "envoy_cc_posix_library",
    "envoy_cc_win32_library",
    "envoy_package",
)

envoy_cc_library(
    name = "nighthawk_common_lib",
    srcs = [
        "rate_limiter.cc",
        "sequencer.cc",
        "stream_decoder.cc",
        "streaming_stats.cc",
    ],
    hdrs = [
        "rate_limiter.h",
        "sequencer.h",
        "ssl.h",
        "stream_decoder.h",
        "streaming_stats.h",
    ],
    visibility = ["//visibility:public"],
    repository = "@envoy",
    deps = [
        "//include/nighthawk/common:base_includes",
        "//include/nighthawk/client:client_includes",
        "@envoy//source/exe:envoy_common_lib",
        "@envoy//source/common/common:compiler_requirements_lib",
        "@envoy//source/common/stats:stats_lib",
        "@envoy//source/server/config_validation:server_lib",
        "@envoy//source/common/common:thread_impl_lib_posix",
    ]
)
