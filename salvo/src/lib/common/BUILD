load("@rules_python//python:defs.bzl", "py_library")

package(
  default_visibility = ["//:__subpackages__"],
)

py_library(
    name = "file_ops",
    data = [
        "file_ops.py",
    ],
)
py_test(
    name = "test_file_ops",
    srcs = ["test_file_ops.py"],
    srcs_version = "PY3",
    deps = [
        ":file_ops",
    ],
)
