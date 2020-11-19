load("@rules_python//python:defs.bzl", "py_library", "py_test")

licenses(["notice"])  # Apache 2

package(
    default_visibility = ["//:__subpackages__"],
)

py_library(
    name = "benchmark",
    data = [
        "base_benchmark.py",
        "fully_dockerized_benchmark.py"
    ],
    deps = [
        "//src/lib:docker_image",
        "//src/lib:docker_volume",
    ],
)

py_test(
  name = "test_fully_dockerized_benchmark",
  srcs = [ "test_fully_dockerized_benchmark.py" ],
  srcs_version = "PY3",
  deps = [
      "//api:schema_proto",
      "//src/lib:docker_image",
      ":benchmark"
  ],
)

