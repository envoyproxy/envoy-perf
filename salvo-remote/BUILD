load("@io_bazel_rules_go//go:def.bzl", "go_binary", "go_library", "go_test")
load("@bazel_gazelle//:def.bzl", "gazelle")

# gazelle:prefix github.com/envoyproxy/envoy-perf/salvo-remote
gazelle(name = "gazelle")

go_library(
    name = "salvo-remote_lib",
    srcs = ["salvo_remote.go"],
    importpath = "github.com/envoyproxy/envoy-perf/salvo-remote",
    visibility = ["//visibility:private"],
)

go_binary(
    name = "salvo-remote",
    embed = [":salvo-remote_lib"],
    visibility = ["//visibility:public"],
)

go_test(
    name = "salvo-remote_test",
    srcs = ["salvo_remote_test.go"],
    embed = [":salvo-remote_lib"],
)
