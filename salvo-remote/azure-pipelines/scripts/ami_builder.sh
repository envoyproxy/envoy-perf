#!/bin/bash

set -e

# Required tokens, see:
# https://github.com/envoyproxy/envoy-perf/blob/main/salvo-remote/azure-pipelines/README.md
export AZURE_DEVOPS_EXT_PAT=${AZURE_DEVOPS_EXT_PAT:-}
export AWS_ACCESS_KEY_ID=${AWS_ACCESS_KEY_ID:-}
export AWS_SECRET_ACCESS_KEY=${AWS_SECRET_ACCESS_KEY:-}

# The id of the AZP build that produced the component binaries to be included in
# the AWS AMI.
export BUILD_ID=${BUILD_ID:-}

packer init
packer build \
  -var "azure_devops_ext_pat=${AZURE_DEVOPS_EXT_PAT}" \
  -var "azp_build_id=${BUILD_ID}" \
  salvo-remote/packer-ami-build/salvo-component-vm-x64.pkr.hcl
