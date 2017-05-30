#!/bin/bash
set -e

sudo rm -rf nghttp2-1.22.0
sudo rm -rf nghttp2-1.22.0.tar.gz
wget https://github.com/nghttp2/nghttp2/releases/download/v1.22.0/nghttp2-1.22.0.tar.gz
tar -xvf nghttp2-1.22.0.tar.gz
sudo rm -f nghttp2-1.22.0.tar.gz
cd nghttp2-1.22.0
./configure --enable-app
sudo make
sudo make install
sudo ldconfig
cd ..
sudo rm -rf nghttp2-1.22.0

#for curl with HTTP2
cd
sudo apt-get build-dep -y curl
wget https://curl.haxx.se/download/curl-7.47.0.tar.gz
tar -xvf curl-7.47.0.tar.gz
sudo rm -f curl-7.47.0.tar.gz
cd ~/curl-7.47.0
./configure --with-nghttp2=/usr/local --with-ssl
make
sudo make install
sudo ldconfig
cd ..
sudo rm -rf curl-7.47.0
