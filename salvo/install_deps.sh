#!/bin/bash

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
  docker.io \
  python3-pytest \
  python3-docker \
  openjdk-11-jdk


pip3 install --upgrade --user pip
pip3 install --upgrade --user setuptools
pip3 install --user -r requirements.txt

touch ${HOME}/.salvo_deps_installed
