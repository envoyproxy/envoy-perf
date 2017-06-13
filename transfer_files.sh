#!/bin/bash

# $1 - vm_name
# $2 - envoy-binary file location
# $3 - absolute location of all the necessary scripts
# $4 - absolute location of envoy configs
set -e

gcloud compute scp $2 $1:./envoy-fastbuild
echo -e "envoy-binary transfer complete.\n"

gcloud compute scp --scp-flag="-r" $3/Makefile $3/install-nghttp.sh $3/init-script.sh $3/default $3/nginx.conf $3/distribute_proc.py $3/process.py $3/generate_scripts.py $3/generate_config.py $3/templates/ $1:./
echo -e "Scripts transfer complete.\n"

gcloud compute ssh $1 --command="mkdir -p envoy-configs"
gcloud compute scp --recurse $4/* $1:./envoy-configs/
echo -e "Envoy configs transfer complete.\n"
