load("@com_google_protobuf//:protobuf.bzl", "py_proto_library")

package(
    default_visibility = ["//:__subpackages__"],
)

py_proto_library(
    name = "schema_proto",
    srcs = [
        "control.proto",
        "docker_volume.proto",
        "env.proto",
        "image.proto",
        "source.proto",
    ],
)
