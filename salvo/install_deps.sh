#!/bin/bash

# Install dependencies locally

if [ ${UID} -ne 0 ]
then
  echo "This script needs root priviliges to install dependencies. Continuing may elicit failures from tests"
  exit 0
fi

if [ -f ${HOME}/.salvo_deps_installed ]
then
  echo "Dependencies already installed. Remove \"${HOME}/.salvo_deps_installed\" to reinstall."
  exit 0
fi

/usr/bin/apt update
/usr/bin/apt -y install \
  docker.io
/usr/bin/apt -y install \
  lcov \
  openjdk-11-jdk \
  python3-docker \
  python3-pip \
  python3-pytest


pip3 install --upgrade --user pip
pip3 install --upgrade --user setuptools
pip3 install --user -r requirements.txt

touch ${HOME}/.salvo_deps_installed
