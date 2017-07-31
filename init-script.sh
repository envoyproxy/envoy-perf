#!/bin/bash

# $1 - it is the username on the VM in the cloud-platform
# $2 - number of nginx worker processes
# $3 - --ssl or --no-ssl for benchmarking

set -e

chmod +x ./install-gcloud.sh
./install-gcloud.sh
sudo apt-get update
sudo apt-get install -y make
sudo make lib
python generate_config.py ./templates/ --worker_proc_count $2 $3
python generate_scripts.py ./templates/ $1
sudo rm -f *.pyc  # Because the script is being run as root, pyc's ownership is set to root and it creates problem in transferring file in the next run
sudo make nginx
./install-nghttp.sh
chmod 766 envoy-fastbuild
