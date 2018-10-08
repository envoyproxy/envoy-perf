#!/bin/bash
set -e

sudo rm -rf nghttp2-1.22.0
sudo rm -rf nghttp2-1.22.0.tar.gz
wget --no-check-certificate https://github.com/sohamm17/nghttp2/archive/temporary.tar.gz -O ./nghttp2.tar.gz
mkdir -p ./nghttp2
tar --strip-components=1 -xvf nghttp2.tar.gz -C ./nghttp2
sudo rm -f nghttp2.tar.gz
cd nghttp2
autoreconf -i
automake
autoconf
./configure --enable-app
sudo make
sudo make install
sudo ldconfig
cd ..
sudo rm -rf nghttp2

#for curl with HTTP2
cd
# sudo apt-get build-dep -y curl
wget https://curl.haxx.se/download/curl-7.47.0.tar.gz
tar -xvf curl-7.47.0.tar.gz
sudo rm -f curl-7.47.0.tar.gz
cd ./curl-7.47.0
./configure --with-nghttp2=/usr/local --with-ssl
make
sudo make install
sudo ldconfig
cd ..
sudo rm -rf curl-7.47.0
