load(
    "@envoy//bazel:envoy_build_system.bzl",
    "envoy_cc_test",
)

package(default_visibility = ["//visibility:public"])

envoy_cc_test(
    name = "nighthawk_test",
    srcs = [
        "frequency_test.cc",
    ],
    repository = "@envoy",
    deps = [
        "//nighthawk/source/client:nighthawk_client_lib",
    ],
)
