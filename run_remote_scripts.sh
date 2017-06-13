#!/bin/bash

# $1 - virtual-machine name
# $2 - username on the VM in the cloud-platform
# $3 - abosolute directory path for the result file
set -e

gcloud compute ssh --ssh-flag="-t" --command="sudo chmod +x *.sh" $1
gcloud compute ssh --ssh-flag="-t" --command="sudo bash ./init-script.sh $2" $1
echo -e "Running Benchmark.\n"
gcloud compute ssh $1 --command="python distribute_proc.py ./envoy-fastbuild ./envoy-configs/simple-loopback.json result.txt"
echo -e "Benchmarking complete.\n"
rm -f $3/result.txt
gcloud compute scp $1:./result.txt $3/
