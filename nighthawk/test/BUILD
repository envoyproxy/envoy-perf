load(
    "@envoy//bazel:envoy_build_system.bzl",
    "envoy_cc_test",
)

package(default_visibility = ["//visibility:public"])

envoy_cc_test(
    name = "nighthawk_test",
    srcs = [
        "frequency_test.cc",
        "options_test.cc",
        "rate_limiter_test.cc",
        "statistic_test.cc",
        "utility_test.cc",
    ],
    data = ["hdr_proto_json.gold"],
    repository = "@envoy",
    deps = [
        "//nighthawk/source/client:nighthawk_client_lib",
        "@envoy//test/integration:integration_lib",
        "@envoy//test/server:utility_lib",
    ],
)
