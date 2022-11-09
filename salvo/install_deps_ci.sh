#!/bin/bash

# Install dependencies in upstream CI environment

# Exit immediately if a command exits with a non-zero status.
# pipefail indicates that the return value of a pipeline is the status
# of the last command to exit with a non-zero status.
set -eo pipefail

if [ -f ${HOME}/.salvo_deps_installed ]
then
  echo "Dependencies already installed. Remove \"${HOME}/.salvo_deps_installed\" to reinstall."
  exit 0
fi

pip3 install --upgrade --user pip
ln -sv $(which pip3) /usr/bin/pip3
pip3 install --upgrade --user setuptools
pip3 install --user -r requirements.txt

touch ${HOME}/.salvo_deps_installed
