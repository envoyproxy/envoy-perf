package(default_visibility = ["//visibility:public"])

load(
    "@envoy//bazel:envoy_build_system.bzl",
    "envoy_cc_binary",
)

envoy_cc_binary(
    name = "nighthawk_client",
    repository = "@envoy",
    stamped = True,
    deps = ["//source/exe:nighthawk_client_entry_lib",
    ],
)
