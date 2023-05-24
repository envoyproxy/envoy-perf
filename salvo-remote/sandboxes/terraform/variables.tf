# Instances of the x64 default sandbox to deploy.
variable "default_sandbox_x64_build_ids" {
  type        = list(string)
  description = "Instances of the default sandbox to deploy. The values are instance names and must correspond to the AZP build IDs used to create the binaries and VM images for this sandbox run. Note that any instances that were deployed previously and are not listed in an execution will be destroyed. Specify an empty string to destroy all instances."
  default     = []
}
