load("@rules_python//python:defs.bzl", "py_library", "py_test")

package(
    default_visibility = ["//:__subpackages__"]
)

py_library(
    name = "benchmark_errors",
    data = [
        "benchmark_errors.py",
    ],
)

py_library(
    name = "benchmark",
    data = [
        "base_benchmark.py",
        "fully_dockerized_benchmark.py"
    ],
    deps = [
        ":benchmark_errors",
        "//src/lib/docker:docker_image",
        "//src/lib/docker:docker_volume",
    ],
)

py_test(
  name = "test_base_benchmark",
  srcs = [ "test_base_benchmark.py" ],
  srcs_version = "PY3",
  deps = [
      "//api:schema_proto",
      "//src/lib/docker:docker_image",
      ":benchmark"
  ],
)

py_test(
  name = "test_fully_dockerized_benchmark",
  srcs = [ "test_fully_dockerized_benchmark.py" ],
  srcs_version = "PY3",
  deps = [
      "//api:schema_proto",
      "//src/lib/docker:docker_image",
      ":benchmark"
  ],
)

