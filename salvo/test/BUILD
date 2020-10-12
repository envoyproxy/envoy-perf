licenses(["notice"])  # Apache 2

py_library(
    name = "api",
    visibility = ["//visibility:public"],
    deps = [
        "//src/lib/api:schema_proto",
    ],
)

py_library(
    name = "lib",
    deps = [
        "//src/lib:helper_library",
    ],
)

py_test(
  name = "test_source_manager",
  srcs = [ "test_source_manager.py" ],
  srcs_version = "PY3",
  deps = [
      "//:api",
      "//:lib",
  ],
)

py_test(
  name = "test_docker",
  srcs = [ "test_docker.py" ],
  srcs_version = "PY3",
  deps = [
      "//:api",
      "//:lib",
  ],
)

py_test(
  name = "test_source_tree",
  srcs = [ "test_source_tree.py" ],
  srcs_version = "PY3",
  deps = [
      "//:lib",
  ],
)

py_test(
  name = "test_protobuf_serialize",
  srcs = [ "test_protobuf_serialize.py" ],
  srcs_version = "PY3",
  deps = [
      "//:api",
      "//:lib",
  ],
)

py_test(
  name = "test_base_benchmark",
  srcs = [ "benchmark/test_base_benchmark.py" ],
  srcs_version = "PY3",
  deps = [
      "//:api",
      "//:lib",
  ],
)

py_test(
  name = "test_fully_dockerized_benchmark",
  srcs = [ "benchmark/test_fully_dockerized_benchmark.py" ],
  srcs_version = "PY3",
  deps = [
      "//:api",
      "//:lib",
  ],
)
