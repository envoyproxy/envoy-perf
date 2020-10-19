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
  name = "test_docker",
  srcs = [ "test_docker.py" ],
  srcs_version = "PY3",
  deps = [
      "//:api",
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
