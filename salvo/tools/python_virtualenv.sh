#!/bin/bash

# This script contains a function that sets up a Python virtual environment for
# Salvo, or reuses an existing one if present.

# The directory that will contain the virtual environment.
VENV_DIR="salvo_venv"

reuse_or_create_salvo_venv() {
  if [[ ! -d "${VENV_DIR}"/venv ]]; then
    echo "Creating a new Python virtual environment for Salvo in "${VENV_DIR}"/venv."
    virtualenv "${VENV_DIR}"/venv --python=python3
  else
    echo "Found an existing Python virtual environment for Salvo in "${VENV_DIR}"/venv, reusing it."
  fi

  source "${VENV_DIR}"/venv/bin/activate
  pip install -r requirements.txt
}
