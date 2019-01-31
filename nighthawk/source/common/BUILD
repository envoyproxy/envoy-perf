load(
    "@envoy//bazel:envoy_build_system.bzl",
    "envoy_cc_library",
)

licenses(["notice"])  # Apache 2

envoy_cc_library(
    name = "nighthawk_common_lib",
    srcs = [
        "rate_limiter.cc",
        "sequencer.cc",
        "stream_decoder.cc",
        "streaming_stats.cc",
    ],
    hdrs = [
        "frequency.h",
        "rate_limiter.h",
        "sequencer.h",
        "ssl.h",
        "stream_decoder.h",
        "streaming_stats.h",
    ],
    repository = "@envoy",
    visibility = ["//visibility:public"],
    deps = [
        "//include/nighthawk/client:client_includes",
        "//include/nighthawk/common:base_includes",
        "@envoy//source/common/common:compiler_requirements_lib",
        "@envoy//source/common/common:thread_impl_lib_posix",
        "@envoy//source/common/stats:stats_lib",
        "@envoy//source/exe:envoy_common_lib",
        "@envoy//source/server/config_validation:server_lib",
    ],
)
