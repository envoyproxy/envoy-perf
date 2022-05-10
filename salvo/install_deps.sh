#!/bin/bash

if [ ${UID} -ne 0 ]
then
  echo "This script needs root priviliges to install dependencies. Continuing may elicit failures from tests"
fi

if [ -f ${HOME}/.salvo_deps_installed ]
then
  echo "Dependencies already installed. Remove \"${HOME}/.salvo_deps_installed\" to reinstall."
  exit 0
fi

pip3 install --upgrade --user pip
pip3 install --upgrade --user setuptools
pip3 install --user -r requirements.txt

touch ${HOME}/.salvo_deps_installed
