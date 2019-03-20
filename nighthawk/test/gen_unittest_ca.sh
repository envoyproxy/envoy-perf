#!/bin/bash
#
# Create ca_cert.pem for the benchmark client test server.

set -e

TEST_CERT_DIR="${TEST_TMPDIR}"

openssl genrsa -out ${TEST_CERT_DIR}/ca_key.pem 2048
openssl req -new -key ${TEST_CERT_DIR}/ca_key.pem -out ${TEST_CERT_DIR}/ca_cert.csr -batch -sha256
openssl x509 -req -days 730 -in ${TEST_CERT_DIR}/ca_cert.csr -signkey ${TEST_CERT_DIR}/ca_key.pem -out ${TEST_CERT_DIR}/ca_cert.pem
