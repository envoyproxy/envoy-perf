load("@rules_python//python:defs.bzl", "py_library", "py_test")

licenses(["notice"])  # Apache 2

package(
    default_visibility = ["//:__subpackages__"],
)

py_library(
    name = "job_control",
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
        ":constants",
        ":job_control",
        "//api:schema_proto",
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
        "//src/lib/common:fileops"
    ],
)

py_library(
    name = "source_manager",
    srcs = [
        "source_manager.py",
    ],
    deps = [
        ":source_tree",
    ],
)

py_test(
  name = "test_source_tree",
  srcs = [ "test_source_tree.py" ],
  srcs_version = "PY3",
  deps = [
      "//api:schema_proto",
      ":source_tree",
      ":shell"
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

