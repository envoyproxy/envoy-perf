package(default_visibility = ["//visibility:public"])

load(
    "@envoy//bazel:envoy_build_system.bzl",
    "envoy_cc_test",
)

envoy_cc_test(
    name = "nighthawk_test",
    srcs = [
        "options_test.cc",
        "benchmark_http_client_test.cc",
        "rate_limiter_test.cc",
        "sequencer_test.cc",
        "streaming_stats_test.cc",
    ],
    repository = "@envoy",
    data = [
        "certs.sh",
        "lorem_ipsum.txt"
    ],
    deps = [
        "@envoy//test/integration:integration_lib",
        "@envoy//test/server:utility_lib",
        "//source/client:nighthawk_client_lib",
    ],
)

