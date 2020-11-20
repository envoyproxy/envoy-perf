#!/bin/bash

set -x


function die()
{
  MSG="$1"

  echo ${MSG}
  exit 1
}

PYTYPE=$(which pytype)
if [ -z "${PYTYPE}" ]
then
  if [ -f ${HOME}/.local/bin/pytype ]
  then
    PYTYPE=${HOME}/.local/bin/pytype
  fi
fi
if [ -z "${PYTYPE}" ]
then
  die "Unable to find pytype in path"
fi

echo $PWD

bazel build //...
${PYTYPE} src -P bazel-bin:.
