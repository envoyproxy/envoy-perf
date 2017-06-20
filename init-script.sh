#!/bin/bash

# $1 - it is the username on the VM in the cloud-platform

set -e

sudo apt-get update
sudo apt-get install -y make
sudo make lib
python generate_config.py ./templates/
python generate_scripts.py ./templates/ $1
sudo make nginx
./install-nghttp.sh
chmod 766 envoy-fastbuild
