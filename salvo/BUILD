licenses(["notice"])

py_binary(
  name = "salvo",
  srcs = [ "salvo.py" ],
  srcs_version = "PY3",
  deps = [
    ":api",
    ":lib",
  ],
)

py_library(
    name = "api",
    visibility = ["//visibility:public"],
    deps = [
        "//src/lib/api:schema_proto",
    ],
)

py_library(
    name = "lib",
    visibility = ["//visibility:public"],
    deps = [
        "//src/lib:helper_library",
    ],
)
