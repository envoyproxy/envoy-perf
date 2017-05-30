#!/bin/bash

set -e

gcloud compute instances create --zone "us-east1-b" $1 --custom-cpu 20 --custom-memory 76 --image-family ubuntu-1604-lts --image-project ubuntu-os-cloud
cd ~/Google/scripts/
gcloud compute --project "envoy-ci" scp ./Makefile ./install-nghttp.sh ./init-script.sh ./default ./nginx.conf $1:./ --zone "us-east1-b"
cd ~/Google/envoy
gcloud compute --project "envoy-ci" scp --recurse ./generated/configs/* $1:./envoy-configs/ --zone "us-east1-b"
gcloud compute --project "envoy-ci" scp --recurse ./generated/configs/* $1:./envoy-configs/ --zone "us-east1-b"
gcloud compute --project "envoy-ci" scp /tmp/envoy-docker-build/envoy/source/exe/envoy-fastbuild $1:./envoy-fastbuild --zone "us-east1-b"
