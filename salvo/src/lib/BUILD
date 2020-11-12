load("@rules_python//python:defs.bzl", "py_library", "py_test")

licenses(["notice"])  # Apache 2

py_library(
    name = "docker_image",
    data = [
        "docker_image.py",
    ],
    visibility = ["//visibility:public"],
)

py_library(
    name = "docker_volume",
    data = [
        "docker_volume.py",
    ],
    visibility = ["//visibility:public"],
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
)

py_test(
    name = "test_docker_image",
    srcs = ["test_docker_image.py"],
    srcs_version = "PY3",
    deps = [
        ":docker_image",
        ":docker_volume",
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
