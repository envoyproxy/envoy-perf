#!/bin/bash

# Exit immediately if a command exits with a non-zero status.
# pipefail indicates that the return value of a pipeline is the status
# of the last command to exit with a non-zero status.
set -exo pipefail

function die()
{
  MESSAGE="$1"

  echo ${MESSAGE}
  exit 1
}

echo "in typecheck.sh, PATH is: ${PATH}"

PYTYPE=$(which pytype) || true  # ignore exit code in this line
if [ -z "${PYTYPE}"  -a -f ${HOME}/.local/bin/pytype ]
then
  PYTYPE=${HOME}/.local/bin/pytype
fi

if [ -z "${PYTYPE}" ]
then
  die "Unable to find pytype in path"
fi

echo $PWD

# disable pyi-error here because pyi parser cannot handle 'google.protobuf.descriptor_pb2', refer to
# https://github.com/google/pytype/issues/764
${PYTYPE} src -P bazel-bin:. --disable=pyi-error
