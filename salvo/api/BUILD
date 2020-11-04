load("@com_google_protobuf//:protobuf.bzl", "py_proto_library")

licenses(["notice"])  # Apache 2

py_proto_library(
    name = "schema_proto",
    srcs = glob(
        ["*.proto"],
        allow_empty = False,
    ),
    visibility = ["//visibility:public"],
)
