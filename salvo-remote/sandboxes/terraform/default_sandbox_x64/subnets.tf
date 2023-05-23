# Reads the IDs of the pre-existing Salvo VPC and network subnets.

data "aws_vpc" "salvo_infra_vpc" {
  id = var.salvo_vpc_id
}

data "aws_subnet" "salvo_infra_control_vm_subnet" {
  id = var.salvo_infra_control_vm_subnet_id
}

data "aws_subnet" "salvo_infra_load_generator_subnet" {
  id = var.salvo_infra_load_generator_subnet_id
}

data "aws_subnet" "salvo_infra_backend_subnet" {
  id = var.salvo_infra_backend_subnet_id
}
