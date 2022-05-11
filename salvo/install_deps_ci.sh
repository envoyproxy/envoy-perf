#!/bin/bash

# Install dependencies in upstream CI environment

if [ -f ${HOME}/.salvo_deps_installed ]
then
  echo "Dependencies already installed. Remove \"${HOME}/.salvo_deps_installed\" to reinstall."
  exit 0
fi

pip3 install --upgrade --user pip
pip3 install --upgrade --user setuptools
pip3 install --user -r requirements.txt

touch ${HOME}/.salvo_deps_installed
