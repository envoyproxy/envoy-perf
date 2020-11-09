#!/bin/bash

if [ ${UID} -ne 0 ]
then
  echo "This script needs root priviliges to install dependencies. Continuing may elicit failures from tests"
  exit 0
fi

/usr/bin/apt update
/usr/bin/apt -y install \
  docker.io \
  python3-pytest \
  python3-docker
