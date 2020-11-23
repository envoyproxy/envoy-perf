#!/bin/bash

set -x


function die()
{
  MSG="$1"

  echo ${MSG}
  exit 1
}

PYTYPE=$(which pytype)
if [ -z "${PYTYPE}"  -a -f ${HOME}/.local/bin/pytype ]
then
  PYTYPE=${HOME}/.local/bin/pytype
fi

if [ -z "${PYTYPE}" ]
then
  die "Unable to find pytype in path"
fi

echo $PWD

bazel build //...
${PYTYPE} src -P bazel-bin:.
