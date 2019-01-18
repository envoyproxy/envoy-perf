#/bin/bash

# This script symlinks bazel's output base into the root of the workspace
# as a directory '/tmp/nighthawk_bazel_output_base'. This can be used by IDE's to
# get to the header files of dependencies.
# See .vscode/c_cpp_properties.json for an example.

set -e

if [ -f nighthawk.code-workspace ]; then
    target=$(bazel info output_base)
    ln -sf "$target" /tmp/nighthawk_bazel_output_base
    echo "Symlinked $target to /tmp/nighthawk_bazel_output_base"
else
    echo "This script should be executed from the git root"
    exit 1
fi
