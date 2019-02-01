load("@envoy//api/bazel:api_build_system.bzl", "api_proto_library_internal")
load(
    "@envoy//bazel:envoy_build_system.bzl",
    "envoy_cc_library",
)

licenses(["notice"])  # Apache 2

api_proto_library_internal(
    name = "benchmark_options",
    srcs = ["options.proto"],
    visibility = ["//visibility:public"],
)

envoy_cc_library(
    name = "nighthawk_client_lib",
    srcs = [
    ],
    hdrs = [
    ],
    repository = "@envoy",
    visibility = ["//visibility:public"],
    deps = [
        "//include/nighthawk/client:client_includes",
        "//include/nighthawk/common:base_includes",
        "//source/common:nighthawk_common_lib",
        "@envoy//source/common/common:compiler_requirements_lib",
        "@envoy//source/common/common:thread_impl_lib_posix",
        "@envoy//source/exe:envoy_common_lib",
    ],
)
