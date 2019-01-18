licenses(["notice"])  # Apache 2

load(
    "//bazel:nighthawk.bzl",
    "nighthawk_cc_platform_dep"
)

load(
    "@envoy//bazel:envoy_build_system.bzl",
    "envoy_cc_binary",
    "envoy_cc_library",
    "envoy_cc_posix_library",
    "envoy_cc_win32_library",
)

load("@envoy//api/bazel:api_build_system.bzl", "api_proto_library_internal")
load("@envoy//bazel:repositories.bzl", "PPC_SKIP_TARGETS")

api_proto_library_internal(
    name = "benchmark_options",
    srcs = ["options.proto"],
    visibility = ["//visibility:public"],
)

envoy_cc_library(
    name = "nighthawk_client_lib",
    srcs = [
        "client.cc",
	    "options_impl.cc",
        "benchmark_http_client.cc",
    ],
    hdrs = [
        "client.h",
    	"options_impl.h",
        "benchmark_http_client.h",
    ],
    visibility = ["//visibility:public"],
    repository = "@envoy",
    deps = [
        ":benchmark_options_cc",
        "//include/nighthawk/common:base_includes",
        "//include/nighthawk/client:client_includes",
        "//source/common:nighthawk_common_lib",
        "@envoy//source/exe:envoy_common_lib",
        "@envoy//source/common/common:compiler_requirements_lib",
        "@envoy//source/common/common:thread_impl_lib_posix",
    ]
)
