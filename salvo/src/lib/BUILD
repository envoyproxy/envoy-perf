py_library(
  name = "helper_library",
  data = glob([
      '*.py',
      'benchmark/*.py',
      'common/*.py',
  ], allow_empty=False) + 
  [
    "//:api",
  ],
  visibility = ["//visibility:public"],
)
