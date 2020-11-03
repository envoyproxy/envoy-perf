py_library(
  name = "api",
  visibility = ["//visibility:public"],
  deps = [
    "//src/lib/api:schema_proto",
  ]
)

py_library(
  name = "docker_lib",
  visibility = ["//visibility:public"],
  data = [
    'docker_image.py',
    'docker_volume.py',
  ],
)

py_library(
  name = "job_control_lib",
  visibility = ["//visibility:public"],
  data = [
    'job_control_loader.py',
  ],
)

py_library(
  name = "shell_lib",
  visibility = ["//visibility:public"],
  data = [
    'cmd_exec.py',
  ],
)

py_test(
  name = "test_docker_image",
  visibility = ["//visibility:public"],
  srcs = [ "test_docker_image.py" ],
  srcs_version = "PY3",
  deps = [
      "//:api",
      "docker_lib",
  ],
)

py_test(
  name = "test_job_control_loader",
  visibility = ["//visibility:public"],
  srcs = [ "test_job_control_loader.py" ],
  srcs_version = "PY3",
  deps = [
      "//:api",
      "job_control_lib",
  ],
)
