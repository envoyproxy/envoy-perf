load(
    "@envoy//bazel:envoy_build_system.bzl",
    "envoy_basic_cc_library",
    "envoy_cc_binary",
)

package(default_visibility = ["//visibility:public"])

envoy_cc_binary(
    name = "nighthawk_client",
    repository = "@envoy",
    deps = [
        "//nighthawk/source/exe:nighthawk_client_entry_lib",
    ],
)

envoy_cc_binary(
    name = "nighthawk_test_origin",
    repository = "@envoy",
    deps = [
        "//nighthawk/source/server:http_test_origin_filter_config",
        "@envoy//source/exe:envoy_main_entry_lib",
    ],
)
