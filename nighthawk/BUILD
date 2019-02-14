load(
    "@envoy//bazel:envoy_build_system.bzl",
    "envoy_cc_binary",
    "envoy_cc_library",
)

package(default_visibility = ["//visibility:public"])

envoy_cc_library(
    name = "hdrhistogram_c",
    srcs = glob(["hdrhistogram_c/src/*.c"]),
    hdrs = glob(["hdrhistogram_c/src/*.h"]),
    copts = [
        "-std=gnu99",
        "-Wno-implicit-function-declaration",
        "-Wno-error",
    ],
    repository = "@envoy",
    visibility = ["//visibility:public"],
)

envoy_cc_binary(
    name = "nighthawk_client",
    repository = "@envoy",
    deps = [
        "//nighthawk/source/exe:nighthawk_client_entry_lib",
    ],
)
