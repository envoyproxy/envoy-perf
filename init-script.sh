#!/bin/bash
set -e

sudo apt-get update
sudo apt-get install -y make
make lib
make nginx
./install-nghttp.sh
mkdir -p envoy-configs
sudo chown -R sohamcodes:sohamcodes envoy-configs
chmod 766 envoy-fastbuild
