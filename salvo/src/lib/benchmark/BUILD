load("@rules_python//python:defs.bzl", "py_library", "py_test")

package(
    default_visibility = ["//:__subpackages__"]
)

py_library(
  name = "benchmark",
  srcs = [
      "base_benchmark.py",
      "fully_dockerized_benchmark.py",
      "scavenging_benchmark.py"
  ],
  srcs_version = "PY3",
  deps = [
      "//src/lib/docker_management:docker_image",
      "//src/lib/docker_management:docker_volume",
      "//src/lib/builder:nighthawk_builder",
      "//src/lib/builder:envoy_builder"
  ],
)

py_test(
  name = "test_base_benchmark",
  srcs = [ "test_base_benchmark.py" ],
  srcs_version = "PY3",
  deps = [
      "//api:schema_proto",
      "//src/lib/docker_management:docker_image",
      ":benchmark"
  ],
)

py_test(
  name = "test_scavenging_benchmark",
  srcs = [
    "test_scavenging_benchmark.py",
    "generate_benchmark_test_objects.py"
  ],
  srcs_version = "PY3",
  deps = [
      "//api:schema_proto",
      "//src/lib:source_manager",
      ":benchmark"
  ],
)

py_test(
  name = "test_fully_dockerized_benchmark",
  srcs = [
    "test_fully_dockerized_benchmark.py",
    "generate_benchmark_test_objects.py"
  ],
  srcs_version = "PY3",
  deps = [
      "//api:schema_proto",
      "//src/lib/docker_management:docker_image",
      ":benchmark"
  ],
)

