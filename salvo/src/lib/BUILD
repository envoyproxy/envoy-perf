load("@rules_python//python:defs.bzl", "py_library", "py_test")

licenses(["notice"])  # Apache 2

py_library(
    name = "api",
    visibility = ["//visibility:public"],
    deps = [
        "//src/lib/api:schema_proto",
    ],
)

py_library(
    name = "docker_lib",
    data = [
        "docker_image.py",
        "docker_volume.py",
    ],
    visibility = ["//visibility:public"],
)

py_library(
    name = "job_control_lib",
    data = [
        "job_control_loader.py",
    ],
    visibility = ["//visibility:public"],
)

py_library(
    name = "shell_lib",
    data = [
        "cmd_exec.py",
    ],
    visibility = ["//visibility:public"],
)

py_test(
    name = "test_docker_image",
    srcs = ["test_docker_image.py"],
    srcs_version = "PY3",
    visibility = ["//visibility:public"],
    deps = [
        "docker_lib",
        "//:api",
    ],
)

py_test(
    name = "test_job_control_loader",
    srcs = ["test_job_control_loader.py"],
    srcs_version = "PY3",
    visibility = ["//visibility:public"],
    deps = [
        "job_control_lib",
        "//:api",
    ],
)
