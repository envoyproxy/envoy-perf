#!/bin/bash

# This script sets up a Python virtual environment for Salvo, or reuses an
# existing one if present.

# Exit immediately if a command exits with a non-zero status.
# pipefail indicates that the return value of a pipeline is the status
# of the last command to exit with a non-zero status.
set -eo pipefail

# The directory that will contain the virtual environment.
VENV_DIR="salvo_venv"

if [[ ! -d "${VENV_DIR}"/venv ]]; then
  echo "Creating a new Python virtual environment for Salvo in "${VENV_DIR}"/venv."
  virtualenv "${VENV_DIR}"/venv --python=python3
else
  echo "Found an existing Python virtual environment for Salvo in "${VENV_DIR}"/venv, reusing it."
fi

source "${VENV_DIR}"/venv/bin/activate
pip install -r requirements.txt
exit 0
