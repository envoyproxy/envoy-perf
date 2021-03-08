load("@rules_python//python:defs.bzl", "py_binary", "py_library")

licenses(["notice"])  # Apache 2

py_binary(
    name = "salvo",
    srcs = ["salvo.py"],
    srcs_version = "PY3",
    deps = [
        "//api:schema_proto",
        "//src/lib:job_control_loader",
    ],
)

