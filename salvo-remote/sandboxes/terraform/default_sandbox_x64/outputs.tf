# Outputs provided by the module.

output "load_generator_0_control_vm_subnet_ip_list" {
  value = aws_network_interface.load_generator_to_control_vm.private_ip_list
  description = "The private IP addresses of the first load generator VM in the control VM subnet."
}

output "load_generator_0_load_generator_subnet_ip_list" {
  value = aws_network_interface.load_generator_to_sut.private_ip_list
  description = "The private IP addresses of the first load generator VM in the load generator subnet."
}

output "sut_0_control_vm_subnet_ip_list" {
  value = aws_network_interface.sut_to_control_vm.private_ip_list
  description = "The private IP addresses of the first SUT VM in the control VM subnet."
}

output "sut_0_load_generator_subnet_ip_list" {
  value = aws_network_interface.sut_to_load_generator.private_ip_list
  description = "The private IP addresses of the first SUT VM in the load generator subnet."
}

output "backend_0_control_vm_subnet_ip_list" {
  value = aws_network_interface.backend_to_control_vm.private_ip_list
  description = "The private IP addresses of the first backend VM in the control VM subnet."
}

output "backend_0_backend_subnet_ip_list" {
  value = aws_network_interface.backend_to_sut.private_ip_list
  description = "The private IP addresses of the first backend VM in the backend subnet."
}
