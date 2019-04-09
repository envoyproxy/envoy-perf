package(default_visibility = ["//visibility:public"])

load(
    "@envoy//bazel:envoy_build_system.bzl",
    "envoy_cc_binary",
    "envoy_cc_library",
)
load("@envoy_api//bazel:api_build_system.bzl", "api_proto_library")

envoy_cc_binary(
    name = "test-origin",
    repository = "@envoy",
    deps = [
        ":http_test_origin_filter_config",
        "@envoy//source/exe:envoy_main_entry_lib",
    ],
)

api_proto_library(
    name = "http_test_origin_filter_proto",
    srcs = ["http_test_origin_filter.proto"],
)

envoy_cc_library(
    name = "http_test_origin_filter_lib",
    srcs = ["http_test_origin_filter.cc"],
    hdrs = ["http_test_origin_filter.h"],
    repository = "@envoy",
    deps = [
        ":http_test_origin_filter_proto_cc",
        "@envoy//source/exe:envoy_common_lib",
    ],
)

envoy_cc_library(
    name = "http_test_origin_filter_config",
    srcs = ["http_test_origin_filter_config.cc"],
    repository = "@envoy",
    deps = [
        ":http_test_origin_filter_lib",
        "@envoy//include/envoy/server:filter_config_interface",
    ],
)
