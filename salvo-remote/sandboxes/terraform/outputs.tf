# Outputs the sandbox types expose. These are consumed by the Salvo controller.

output "default_sandbox_x64_build_ids_to_load_generator_0_control_vm_subnet_ip_list" {
  value = {
    for build_id, sandbox in module.default_sandbox_x64 : build_id => sandbox.load_generator_0_control_vm_subnet_ip_list
  }
  description = "A map of default_sandbox_x64_build_ids to the private IP addresses of the first load generator VM in the control VM subnet."
}

output "default_sandbox_x64_build_ids_to_load_generator_0_load_generator_subnet_ip_list" {
  value = {
    for build_id, sandbox in module.default_sandbox_x64 : build_id => sandbox.load_generator_0_load_generator_subnet_ip_list
  }
  description = "A map of default_sandbox_x64_build_ids to the private IP addresses of the first load generator VM in the load_generator subnet."
}

output "default_sandbox_x64_build_ids_to_sut_0_control_vm_subnet_ip_list" {
  value = {
    for build_id, sandbox in module.default_sandbox_x64 : build_id => sandbox.sut_0_control_vm_subnet_ip_list
  }
  description = "A map of default_sandbox_x64_build_ids to the private IP addresses of the first SUT VM in the control VM subnet."
}

output "default_sandbox_x64_build_ids_to_sut_0_load_generator_subnet_ip_list" {
  value = {
    for build_id, sandbox in module.default_sandbox_x64 : build_id => sandbox.sut_0_load_generator_subnet_ip_list
  }
  description = "A map of default_sandbox_x64_build_ids to the private IP addresses of the first SUT VM in the load generator subnet."
}

output "default_sandbox_x64_build_ids_to_backend_0_control_vm_subnet_ip_list" {
  value = {
    for build_id, sandbox in module.default_sandbox_x64 : build_id => sandbox.backend_0_control_vm_subnet_ip_list
  }
  description = "A map of default_sandbox_x64_build_ids to the private IP addresses of the first backend VM in the control VM subnet."
}

output "default_sandbox_x64_build_ids_to_backend_0_backend_subnet_ip_list" {
  value = {
    for build_id, sandbox in module.default_sandbox_x64 : build_id => sandbox.backend_0_backend_subnet_ip_list
  }
  description = "A map of default_sandbox_x64_build_ids to the private IP addresses of the first backend VM in the backend subnet."
}
