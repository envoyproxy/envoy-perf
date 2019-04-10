package(default_visibility = ["//visibility:public"])

load(
    "@envoy//bazel:envoy_build_system.bzl",
    "envoy_cc_test",
)
load("@envoy_api//bazel:api_build_system.bzl", "api_proto_library")

envoy_cc_test(
    name = "http_test_server_filter_integration_test",
    srcs = ["http_test_server_filter_integration_test.cc"],
    repository = "@envoy",
    deps = [
        "//nighthawk/source/server:http_test_server_filter_config",
        "@envoy//test/integration:http_integration_lib",
    ],
)
