load("@bazel_tools//tools/build_defs/repo:http.bzl", "http_archive")

def salvo_remote_dependencies():
  """Loads dependencies of Salvo-remote into the Bazel WORKSPACE."""
  http_archive(
      name = "io_bazel_rules_go",
      sha256 = "6dc2da7ab4cf5d7bfc7c949776b1b7c733f05e56edc4bcd9022bb249d2e2a996",
      urls = [
          "https://mirror.bazel.build/github.com/bazelbuild/rules_go/releases/download/v0.39.1/rules_go-v0.39.1.zip",
          "https://github.com/bazelbuild/rules_go/releases/download/v0.39.1/rules_go-v0.39.1.zip",
      ],
  )
