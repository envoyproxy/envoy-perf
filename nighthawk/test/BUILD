load(
    "@envoy//bazel:envoy_build_system.bzl",
    "envoy_cc_test",
)

package(default_visibility = ["//visibility:public"])

envoy_cc_test(
    name = "nighthawk_test",
    srcs = [
        "benchmark_http_client_test.cc",
        "frequency_test.cc",
        "options_test.cc",
        "rate_limiter_test.cc",
        "sequencer_test.cc",
        "streaming_stats_test.cc",
    ],
    data = [
        "certs.sh",
        "lorem_ipsum.txt",
    ],
    repository = "@envoy",
    deps = [
        "//source/client:nighthawk_client_lib",
        "@envoy//test/integration:integration_lib",
        "@envoy//test/server:utility_lib",
    ],
)
