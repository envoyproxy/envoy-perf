# Defines a Packer template that builds an AMI image of a Salvo test component
# VM.

packer {
  required_plugins {
    amazon = {
      version = ">= 1.2.1"
      source  = "github.com/hashicorp/amazon"
    }
  }
}

variable "azure_devops_ext_pat" {
  type    = string
  default = "default_azure_devops_ext_pat_is_not_valid"
}

variable "azp_build_id" {
  type    = string
  default = "default_build_id_is_not_valid"
}

# See https://developer.hashicorp.com/packer/plugins/builders/amazon/ebs.
source "amazon-ebs" "salvo-component-vm-x64" {
  ami_name                    = "salvo-component-vm-x64-${var.azp_build_id}-{{timestamp}}"
  instance_type               = "m6i.large"
  region                      = "us-west-1"
  vpc_id                      = "vpc-09623ca46adcf44aa" # salvo-vpc
  associate_public_ip_address = true
  subnet_id                   = "subnet-06a291300c69ce70c" # salvo-packer-subnet

  source_ami_filter {
    filters = {
      # Found with:
      # aws ec2 describe-images --owners 'aws-marketplace' --output json --region us-east-2 --filters "Name=product-code,Values=4s6b2r2vfe46kyul508kf459f"
      name                = "ubuntu-minimal/images/hvm-ssd/ubuntu-jammy-22.04-amd64-minimal-*"
      root-device-type    = "ebs"
      virtualization-type = "hvm"
    }
    most_recent = true
    owners      = ["679593333241"]
  }
  encrypt_boot = true
  ssh_username = "ubuntu"

  run_tags = {
    "Project" : "Packer"
  }
  run_volume_tags = {
    "Project" : "Packer"
  }
  tags = {
    "Project" : "Salvo",
    "AmiType" : "salvo-component-vm-x64"
    "AzpBuildId" : "${var.azp_build_id}"
  }
}

build {
  name = "salvo-component-vm-x64"
  sources = [
    "source.amazon-ebs.salvo-component-vm-x64"
  ]

  # See https://developer.hashicorp.com/packer/docs/provisioners/shell.
  provisioner "shell" {
    script = "salvo-component-vm.sh"
    env = {
      "AZURE_DEVOPS_EXT_PAT" : "${var.azure_devops_ext_pat}"
      "AZP_BUILD_ID" : "${var.azp_build_id}"
    }
    execute_command = "{{.Vars}} sudo -S -E sh -eux '{{.Path}}'"
  }
}
