load("@rules_python//python:defs.bzl", "py_library", "py_test")

licenses(["notice"])  # Apache 2

package(
    default_visibility = ["//:__subpackages__"],
)

py_library(
    name = "job_control_loader",
    srcs = [
        "job_control_loader.py",
    ],
)

py_library(
    name = "constants",
    srcs = [
        "constants.py",
    ],
)

py_library(
    name = "shell",
    srcs = [
        "cmd_exec.py",
    ],
)

py_test(
    name = "test_job_control_loader",
    srcs = ["test_job_control_loader.py"],
    srcs_version = "PY3",
    deps = [
        "//api:schema_proto",
        ":constants",
        ":job_control_loader",
    ],
)

py_library(
    name = "source_tree",
    srcs = [
        "source_tree.py",
    ],
    deps = [
        "//api:schema_proto",
        ":shell",
        ":constants",
        "//src/lib/common:file_ops"
    ],
)

py_library(
    name = "source_manager",
    srcs = [
        "source_manager.py",
    ],
    deps = [
        ":constants",
        ":source_tree",
    ],
)

py_library(
    name = "run_benchmark",
    srcs = [
        "run_benchmark.py",
    ],
    deps = [
        "//src/lib/benchmark:benchmark",
        "//src/lib/common:file_ops",
        "//src/lib/docker:docker_image_builder",
        ":source_manager",
    ],
)

py_test(
  name = "test_cmd_exec",
  srcs = [ "test_cmd_exec.py" ],
  srcs_version = "PY3",
  deps = [
      ":shell"
  ],
)

py_test(
  name = "test_source_tree",
  srcs = [ "test_source_tree.py" ],
  srcs_version = "PY3",
  deps = [
      "//api:schema_proto",
      ":source_tree",
      ":shell",
      ":constants"
  ],
)

py_test(
  name = "test_source_manager",
  srcs = [ "test_source_manager.py" ],
  srcs_version = "PY3",
  deps = [
      "//api:schema_proto",
      ":source_tree",
      ":source_manager",
      ":shell"
  ],
)

