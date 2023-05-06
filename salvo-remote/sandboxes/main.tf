# Infrastructure representing one Salvo sandbox.

terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 4.61"
    }
  }
}

provider "aws" {
  region = "us-west-1"
}

locals {
  # These common resources are defined in the ci-infra repository:
  # https://github.com/envoyproxy/ci-infra/tree/main/salvo-infra
  aws_account_id                                     = "457956385456"
  salvo_vpc_id                                       = "vpc-0b1493d6a970c32bd"
  salvo_infra_control_vm_subnet_id                   = "subnet-0a47206b17680514a"
  salvo_infra_load_generator_subnet_id               = "subnet-09614946e63a4f7df"
  salvo_infra_backend_subnet_id                      = "subnet-029d2ecae1b899d05"
  salvo_infra_allow_ssh_from_world_security_group_id = "sg-0c678b37287643979"
}

# Default sandbox configuration for Salvo.
module "default_sandbox_x64" {
  source = "./default_sandbox_x64"

  for_each = toset(var.default_sandbox_x64_build_ids)

  sandbox_build_id                                   = each.key
  aws_account_id                                     = local.aws_account_id
  salvo_vpc_id                                       = local.salvo_vpc_id
  salvo_infra_control_vm_subnet_id                   = local.salvo_infra_control_vm_subnet_id
  salvo_infra_load_generator_subnet_id               = local.salvo_infra_load_generator_subnet_id
  salvo_infra_backend_subnet_id                      = local.salvo_infra_backend_subnet_id
  salvo_infra_allow_ssh_from_world_security_group_id = local.salvo_infra_allow_ssh_from_world_security_group_id
}
