variable "aws_account_id" {
  type        = string
  nullable    = false
  description = "The AWS account ID where all Salvo resources are deployed."
}

variable "sandbox_build_id" {
  type        = string
  nullable    = false
  description = "The AZP build ID used to create the binaries and VM images for this sandbox."
}

variable "salvo_vpc_id" {
  type        = string
  nullable    = false
  description = "The ID of the Salvo VPC where all sandboxes are started."
}

variable "salvo_infra_control_vm_subnet_id" {
  type        = string
  nullable    = false
  description = "The ID of the Salvo subnet where control VMs are deployed."
}

variable "salvo_infra_load_generator_subnet_id" {
  type        = string
  nullable    = false
  description = "The ID of the Salvo subnet where load generators are deployed."
}

variable "salvo_infra_backend_subnet_id" {
  type        = string
  nullable    = false
  description = "The ID of the Salvo subnet where backends are deployed."
}

variable "salvo_infra_allow_ssh_from_world_security_group_id" {
  type        = string
  nullable    = false
  description = "ID of a security group to use when allowing SSH from the world."
}
