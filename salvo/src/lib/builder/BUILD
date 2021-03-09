load("@rules_python//python:defs.bzl", "py_library", "py_test")

licenses(["notice"])  # Apache 2

package(
  default_visibility = ["//:__subpackages__"],
)

py_library(
    name = "bazel_setup",
    srcs = [
        "bazel_setup.py",
    ],
    deps = [
        "//src/lib:constants",
    ],
)

py_library(
    name = "base_builder",
    srcs = [
        "base_builder.py",
    ],
    deps = [
        "//api:schema_proto",
        "//src/lib/common:file_ops",
        "//src/lib:constants",
        "//src/lib:shell",
        "//src/lib:source_manager",
        ":bazel_setup",
    ],
)

py_library(
    name = "envoy_builder",
    srcs = [
        "envoy_builder.py",
    ],
    deps = [
        "//api:schema_proto",
        "//src/lib:shell",
        "//src/lib:constants",
        ":base_builder"
    ],
)

py_library(
    name = "nighthawk_builder",
    srcs = [
        "nighthawk_builder.py",
    ],
    deps = [
        "//api:schema_proto",
        "//src/lib:shell",
        "//src/lib:source_tree",
        ":base_builder"
    ],
)

py_test(
  name = "test_envoy_builder",
  srcs = [ "test_envoy_builder.py" ],
  srcs_version = "PY3",
  deps = [
      "//api:schema_proto",
      "//src/lib:constants",
      "//src/lib:source_tree",
      "//src/lib:source_manager",
      ":envoy_builder",
  ],
)

py_test(
  name = "test_base_builder",
  srcs = [ "test_base_builder.py" ],
  srcs_version = "PY3",
  deps = [
      "//api:schema_proto",
      "//src/lib:source_manager",
      ":base_builder",
  ],
)

py_test(
  name = "test_nighthawk_builder",
  srcs = [ "test_nighthawk_builder.py" ],
  srcs_version = "PY3",
  deps = [
      "//api:schema_proto",
      "//src/lib/common:file_ops",
      "//src/lib:constants",
      "//src/lib:shell",
      "//src/lib:source_tree",
      "//src/lib:source_manager",
      ":nighthawk_builder",
  ],
)

