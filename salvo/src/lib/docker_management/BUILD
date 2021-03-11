load("@rules_python//python:defs.bzl", "py_library", "py_test")

licenses(["notice"])  # Apache 2

package(
    default_visibility = ["//:__subpackages__"],
)

py_library(
    name = "docker_image",
    srcs = [
        "docker_image.py",
    ],
    deps = [
        "//src/lib:constants",
    ],
)

py_library(
    name = "docker_image_builder",
    srcs = [
        "docker_image_builder.py",
    ],
    deps = [
        "//api:schema_proto",
        "//src/lib:constants",
        "//src/lib:source_manager",
        "//src/lib/builder:envoy_builder",
        "//src/lib/builder:nighthawk_builder",
        ":docker_image",
    ],
)

py_library(
    name = "docker_volume",
    srcs = [
        "docker_volume.py",
    ],
    deps = [
        "//src/lib:constants",
    ],
)

py_test(
    name = "test_docker_image",
    srcs = ["test_docker_image.py"],
    srcs_version = "PY3",
    deps = [
        "//api:schema_proto",
        "//src/lib:constants",
        ":docker_image",
        ":docker_volume",
    ],
)

py_test(
    name = "test_docker_volume",
    srcs = ["test_docker_volume.py"],
    srcs_version = "PY3",
    deps = [
        "//api:schema_proto",
        "//src/lib:constants",
        ":docker_volume",
    ],
)

py_test(
    name = "test_docker_image_builder",
    srcs = ["test_docker_image_builder.py"],
    srcs_version = "PY3",
    deps = [
        "//api:schema_proto",
        "//src/lib:constants",
        "//src/lib:source_tree",
        ":docker_image",
        ":docker_volume",
        ":docker_image_builder",
        "//src/lib/builder:envoy_builder",
        "//src/lib/builder:nighthawk_builder"
    ],
)
