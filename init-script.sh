#!/bin/bash

# $1 - it is the username on the VM in the cloud-platform
# $2 - number of nginx worker processes

set -e

chmod +x ./install-gcloud.sh
./install-gcloud.sh
sudo apt-get update
sudo apt-get install -y make
sudo make lib
python generate_config.py ./templates/ --worker_proc_count $2
python generate_scripts.py ./templates/ $1
sudo make nginx
./install-nghttp.sh
chmod 766 envoy-fastbuild
