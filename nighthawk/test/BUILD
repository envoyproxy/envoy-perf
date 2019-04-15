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
    data = ["test_data/hdr_proto_json.gold"],
    repository = "@envoy",
    deps = [
        "//nighthawk/source/client:nighthawk_client_lib",
        "//nighthawk/test/test_common:environment_lib",
        "@envoy//source/common/filesystem:filesystem_lib",
        "@envoy//source/common/protobuf:utility_lib",
        "@envoy//source/common/stats:isolated_store_lib",
        "@envoy//test/test_common:simulated_time_system_lib",
    ],
)
