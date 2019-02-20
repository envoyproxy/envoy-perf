load(
    "@envoy//bazel:envoy_build_system.bzl",
    "envoy_cc_library",
)

licenses(["notice"])  # Apache 2

envoy_cc_library(
    name = "nighthawk_common_lib",
    srcs = [
        "rate_limiter_impl.cc",
        "sequencer_impl.cc",
        "statistic_impl.cc",
        "utility.cc",
    ],
    hdrs = [
        "frequency.h",
        "platform_util_impl.h",
        "rate_limiter_impl.h",
        "sequencer_impl.h",
        "statistic_impl.h",
        "utility.h",
    ],
    repository = "@envoy",
    visibility = ["//visibility:public"],
    deps = [
        "//nighthawk:hdrhistogram_c",
        "//nighthawk/include/nighthawk/client:client_includes",
        "//nighthawk/include/nighthawk/common:base_includes",
        "//nighthawk/source/client:benchmark_options_cc",
        "@envoy//source/common/common:compiler_requirements_lib",
        "@envoy//source/common/common:minimal_logger_lib",
        "@envoy//source/common/common:thread_impl_lib_posix",
        "@envoy//source/common/stats:stats_lib",
        "@envoy//source/exe:envoy_common_lib",
        "@envoy//source/server/config_validation:server_lib",
    ],
)
