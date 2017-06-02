#!/bin/bash

# $1 - virtual-machine name
# $2 - envoy-binary file location

set -e

gcloud compute instances create --zone "us-east1-b" $1 --custom-cpu 20 --custom-memory 76 --image-family ubuntu-1604-lts --image-project ubuntu-os-cloud
echo -e "Instance Created. Needs to wait for 30s.\n"
sleep 30s
gcloud config set compute/zone "us-east1-b"
gcloud config set project "envoy-ci"
cd ~/Google/scripts/
gcloud compute scp ./Makefile ./install-nghttp.sh ./init-script.sh ./default ./nginx.conf ./distribute_proc.py $1:./
gcloud compute scp $2 $1:./envoy-fastbuild
gcloud compute ssh --ssh-flag="-t" --command="sudo chmod +x *.sh" $1
cd ~/Google/envoy/
gcloud compute ssh --ssh-flag="-t" --command="sudo bash ./init-script.sh" $1
gcloud compute scp --recurse ./generated/configs/* $1:./envoy-configs/
gcloud compute ssh $1 --ssh-flag="-t" --command="sudo python3 distribute_proc.py ./envoy-fastbuild ./envoy-configs/simple-loopback.json"
cd -
gcloud compute scp $1:./result.txt ./
echo -e "Y" | gcloud compute instances delete $1
