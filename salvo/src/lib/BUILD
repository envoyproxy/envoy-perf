load("@rules_python//python:defs.bzl", "py_library", "py_test")

licenses(["notice"])  # Apache 2

py_library(
    name = "docker",
    data = [
        "docker_image.py",
        "docker_volume.py",
    ],
)

py_library(
    name = "job_control",
    data = [
        "job_control_loader.py",
    ],
    visibility = ["//visibility:public"],
)

py_library(
    name = "shell",
    data = [
        "cmd_exec.py",
    ],
    visibility = ["//visibility:public"],
)

py_test(
    name = "test_docker_image",
    srcs = ["test_docker_image.py"],
    srcs_version = "PY3",
    deps = [
        ":docker",
        "//api:schema_proto",
    ],
)

py_test(
    name = "test_job_control_loader",
    srcs = ["test_job_control_loader.py"],
    srcs_version = "PY3",
    deps = [
        ":job_control",
        "//api:schema_proto",
    ],
)
