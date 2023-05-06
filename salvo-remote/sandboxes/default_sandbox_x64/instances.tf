# The VM instances started in the sandbox.

locals {
  ami_prefix = "salvo-component-vm-x64"
}

data "aws_ami" "component_vm_ami" {
  most_recent = true
  owners      = [var.aws_account_id]

  filter {
    name   = "name"
    values = ["${local.ami_prefix}-${var.sandbox_build_id}-*"]
  }

  filter {
    name   = "virtualization-type"
    values = ["hvm"]
  }
}

data "aws_security_group" "salvo_infra_allow_ssh_from_world_security_group" {
  id = var.salvo_infra_allow_ssh_from_world_security_group_id
}

resource "aws_network_interface" "load_generator_to_sut" {
  subnet_id = data.aws_subnet.salvo_infra_load_generator_subnet.id

  tags = {
    Name             = "Load generator to SUT"
    Project          = "Salvo"
    Sandbox_Build_ID = var.sandbox_build_id
  }
}

resource "aws_network_interface" "load_generator_to_control_vm" {
  subnet_id = data.aws_subnet.salvo_infra_control_vm_subnet.id
  # Temporary for debugging.
  security_groups = [data.aws_security_group.salvo_infra_allow_ssh_from_world_security_group.id]

  tags = {
    Name             = "Load generator to control VM"
    Project          = "Salvo"
    Sandbox_Build_ID = var.sandbox_build_id
  }
}

resource "aws_instance" "nighthawk_load_generator" {
  ami           = data.aws_ami.component_vm_ami.id
  instance_type = "t3.nano"
  monitoring    = true
  key_name      = "envoy-shared2"

  network_interface {
    network_interface_id = aws_network_interface.load_generator_to_sut.id
    device_index         = 0
  }

  network_interface {
    network_interface_id = aws_network_interface.load_generator_to_control_vm.id
    device_index         = 1
  }

  tags = {
    Name             = "Nighthawk load generator"
    Project          = "Salvo"
    Sandbox_Build_ID = var.sandbox_build_id
  }
}

resource "aws_network_interface" "sut_to_load_generator" {
  subnet_id = data.aws_subnet.salvo_infra_load_generator_subnet.id

  tags = {
    Name             = "SUT to load generator"
    Project          = "Salvo"
    Sandbox_Build_ID = var.sandbox_build_id
  }
}

resource "aws_network_interface" "sut_to_backend" {
  subnet_id = data.aws_subnet.salvo_infra_backend_subnet.id

  tags = {
    Name             = "SUT to backend"
    Project          = "Salvo"
    Sandbox_Build_ID = var.sandbox_build_id
  }
}

resource "aws_network_interface" "sut_to_control_vm" {
  subnet_id = data.aws_subnet.salvo_infra_control_vm_subnet.id
  # Temporary for debugging.
  security_groups = [data.aws_security_group.salvo_infra_allow_ssh_from_world_security_group.id]

  tags = {
    Name             = "SUT to control VM"
    Project          = "Salvo"
    Sandbox_Build_ID = var.sandbox_build_id
  }
}

resource "aws_instance" "sut" {
  ami           = data.aws_ami.component_vm_ami.id
  instance_type = "t3.small"
  monitoring    = true
  key_name      = "envoy-shared2"

  network_interface {
    network_interface_id = aws_network_interface.sut_to_load_generator.id
    device_index         = 0
  }

  network_interface {
    network_interface_id = aws_network_interface.sut_to_backend.id
    device_index         = 1
  }

  network_interface {
    network_interface_id = aws_network_interface.sut_to_control_vm.id
    device_index         = 2
  }

  tags = {
    Name             = "SUT"
    Project          = "Salvo"
    Sandbox_Build_ID = var.sandbox_build_id
  }
}

resource "aws_network_interface" "backend_to_sut" {
  subnet_id = data.aws_subnet.salvo_infra_backend_subnet.id

  tags = {
    Name             = "Backend to SUT"
    Project          = "Salvo"
    Sandbox_Build_ID = var.sandbox_build_id
  }
}

resource "aws_network_interface" "backend_to_control_vm" {
  subnet_id = data.aws_subnet.salvo_infra_control_vm_subnet.id
  # Temporary for debugging.
  security_groups = [data.aws_security_group.salvo_infra_allow_ssh_from_world_security_group.id]

  tags = {
    Name             = "Backend to control VM"
    Project          = "Salvo"
    Sandbox_Build_ID = var.sandbox_build_id
  }
}

resource "aws_instance" "backend" {
  ami           = data.aws_ami.component_vm_ami.id
  instance_type = "t3.nano"
  monitoring    = true
  key_name      = "envoy-shared2"

  network_interface {
    network_interface_id = aws_network_interface.backend_to_sut.id
    device_index         = 0
  }

  network_interface {
    network_interface_id = aws_network_interface.backend_to_control_vm.id
    device_index         = 1
  }

  tags = {
    Name             = "Backend"
    Project          = "Salvo"
    Sandbox_Build_ID = var.sandbox_build_id
  }
}
