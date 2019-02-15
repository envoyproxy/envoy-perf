load(
    "@envoy//bazel:envoy_build_system.bzl",
    "envoy_cc_binary",
    "envoy_cc_library",
)

package(default_visibility = ["//visibility:public"])

envoy_cc_library(
    name = "hdrhistogram_c",
    srcs = [
        "hdrhistogram_c/src/hdr_encoding.c",
        "hdrhistogram_c/src/hdr_histogram.c",
        "hdrhistogram_c/src/hdr_histogram_log.c",
        "hdrhistogram_c/src/hdr_interval_recorder.c",
        "hdrhistogram_c/src/hdr_thread.c",
        "hdrhistogram_c/src/hdr_time.c",
        "hdrhistogram_c/src/hdr_writer_reader_phaser.c",
    ],
    hdrs = [
        "hdrhistogram_c/src/hdr_atomic.h",
        "hdrhistogram_c/src/hdr_encoding.h",
        "hdrhistogram_c/src/hdr_endian.h",
        "hdrhistogram_c/src/hdr_histogram.h",
        "hdrhistogram_c/src/hdr_histogram_log.h",
        "hdrhistogram_c/src/hdr_interval_recorder.h",
        "hdrhistogram_c/src/hdr_tests.h",
        "hdrhistogram_c/src/hdr_thread.h",
        "hdrhistogram_c/src/hdr_time.h",
        "hdrhistogram_c/src/hdr_writer_reader_phaser.h",
    ],
    copts = [
        "-std=gnu99",
        "-Wno-implicit-function-declaration",
        "-Wno-error",
    ],
    repository = "@envoy",
)

envoy_cc_binary(
    name = "nighthawk_client",
    repository = "@envoy",
    deps = [
        "//nighthawk/source/exe:nighthawk_client_entry_lib",
    ],
)
