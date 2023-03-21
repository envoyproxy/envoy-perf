#!/bin/bash

set -e

# Upgrade installed packages.
sudo apt-get -qq update
sudo apt-get -qq upgrade -y

# Workaround for AzureCLI that requires the older version of libssl.
# The version of .NET Core used by the AzureCLI is not capable of working with
# libssl.so.1.1 yet. Forcing libssl.so.1.0.
# See https://github.com/Azure/azure-cli/issues/22230.
LIBSSL1_DIR="/tmp/libssl1"
wget -q -r -l1 -np \
  -P "${LIBSSL1_DIR}" \
  -A 'libssl1.0.0*ubuntu*amd64.deb' \
  "http://security.ubuntu.com/ubuntu/pool/main/o/openssl1.0/"
LIBSSL1_PACKAGE=`find "${LIBSSL1_DIR}" -type f -name \*.deb | sort | head -n 1`
sudo dpkg -i "${LIBSSL1_PACKAGE}"
sudo sed -i 's/openssl_conf = openssl_init/#openssl_conf = openssl_init/g' /etc/ssl/openssl.cnf

# Setup a local user to run Salvo components.
COMPONENT_DIR="/salvo/components"
sudo groupadd salvo
sudo useradd -ms /bin/bash -g salvo salvo
sudo mkdir -p "${COMPONENT_DIR}"

# Install AzureCLI.
curl -sL https://aka.ms/InstallAzureCLIDeb | sudo bash
az extension add --name azure-devops
az devops configure --defaults organization=https://dev.azure.com/cncf project=envoy

# Download the components built by the Salvo pipeline.
# Depends on AZURE_DEVOPS_EXT_PAT= being set to a valid AZP token.
az pipelines runs artifact download \
  --artifact-name "Envoy server" \
  --run-id "${AZP_BUILD_ID}" \
  --path "${COMPONENT_DIR}"
az pipelines runs artifact download \
  --artifact-name "Nighthawk client" \
  --run-id "${AZP_BUILD_ID}" \
  --path "${COMPONENT_DIR}"
az pipelines runs artifact download \
  --artifact-name "Nighthawk test server" \
  --run-id "${AZP_BUILD_ID}" \
  --path "${COMPONENT_DIR}"

# Unpack the components and make them executable.
sudo tar -xzf /salvo/components/envoy_binary.tar.gz -C /salvo/components/
sudo ln -s /salvo/components/build_envoy_release/envoy /salvo/components/envoy
sudo ln -s /salvo/components/build_envoy_release_stripped/envoy /salvo/components/envoy_stripped
sudo chown -R salvo:salvo /salvo/
sudo chmod 0755 /salvo/components/nighthawk*

# Undo the libssl workaround done for AzureCLI.
sudo sed -i 's/#openssl_conf = openssl_init/openssl_conf = openssl_init/g' /etc/ssl/openssl.cnf
sudo dpkg -r $(dpkg -f "${LIBSSL1_PACKAGE}" Package)
