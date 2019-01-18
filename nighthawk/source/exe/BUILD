licenses(["notice"])  # Apache 2

load(
    "//bazel:nighthawk.bzl",
    "nighthawk_cc_platform_dep"
)

load(
    "@envoy//bazel:envoy_build_system.bzl",
    "envoy_cc_binary",
    "envoy_cc_library",
    "envoy_cc_platform_dep",
    "envoy_cc_posix_library",
    "envoy_cc_win32_library",
    "envoy_package",
)

load("@envoy//api/bazel:api_build_system.bzl", "api_proto_library_internal")
load("@envoy//bazel:repositories.bzl", "PPC_SKIP_TARGETS")

envoy_cc_library(
    name = "nighthawk_client_entry_lib",
    srcs = ["client_main_entry.cc"],
    repository = "@envoy",
    visibility = ["//visibility:public"],
    external_deps = [
        "abseil_symbolize",
    ],
    deps = [
        "//source/client:nighthawk_client_lib",
        "@envoy//source/common/common:thread_lib",
    ] 
    #+ envoy_cc_platform_dep("platform_impl_lib"),
)
