load("@rules_python//python:defs.bzl", "py_binary", "py_library")

licenses(["notice"])  # Apache 2

py_library(
    name = "api",
    visibility = ["//visibility:public"],
    deps = [
        "//api:schema_proto",
    ],
)

py_library(
    name = "lib",
    visibility = ["//visibility:public"],
    deps = [
        "//src/lib:job_control_lib",
    ],
)

py_binary(
    name = "salvo",
    srcs = ["salvo.py"],
    srcs_version = "PY3",
    deps = [
        ":api",
        ":lib",
    ],
)

