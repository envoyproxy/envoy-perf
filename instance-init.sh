#!/bin/bash

# $1 - virtual-machine name
# $2 - envoy-binary file location
# $3 - absolute path of all the necessary scripts
# $4 - absolute path of envoy configs
# $5 - abosolute directory path for the result file
# $6 - username on the VM in the cloud-platform

set -e

gcloud compute instances create --zone "us-east1-b" $1 --custom-cpu 20 --custom-memory 76 --image-family ubuntu-1604-lts --image-project ubuntu-os-cloud
echo -e "Instance Created. Needs to wait for 30s.\n"
sleep 30s
gcloud config set compute/zone "us-east1-b"
gcloud config set project "envoy-ci"

chomod 766 transfer_files.sh run_remote_scripts.sh
./transfer_files.sh $1 $2 $3 $4

./run_remote_scripts $1 $6 $5
