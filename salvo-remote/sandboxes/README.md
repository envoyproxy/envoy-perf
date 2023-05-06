# Sandboxes for remote Salvo executions

This directory contains definition of Salvo sandboxes. A sandbox is the
collection of resources needed for a single Salvo execution. These resources
are deployed in AWS. At the minimum a sandbox will contain:

- a VM running Nighthawk (the load generator).
- a VM running Envoy (the system under test or SUT).
- a VM running the Nighthawk test server (the test backend).

Note that the subnets used between the components are part of the common
infrastructure and are already deployed as part of the [VPC
configuration](https://github.com/envoyproxy/ci-infra/blob/main/salvo-infra/vpc.tf)
done in the
[ci-infra](https://github.com/envoyproxy/ci-infra/tree/main/salvo-infra)
repository.

Various sandbox types differ in the amount of instances deployed, amount of
support systems deployed and the topology.

# Available Sandbox types

## The default sandbox

The default sandbox contains the bare minimum of components needed to execute
Salvo tests. The diagram below outlines the topology and content of the default
sandbox. The default sandbox is currently available for the `x64` architecture
only.

![Diagram 1 - the default sandbox](images/the_default_sandbox.png)

# Sandbox creation

When Salvo executes, an execution of the [AZP CI
pipeline](https://github.com/envoyproxy/envoy-perf/blob/main/salvo-remote/azure-pipelines/salvo_pipelines.yml)
is started. Each CI pipeline execution is uniquely identified by a build ID.
This execution will produce binaries and VM disk images for all the sandbox
components.

Once the binaries and VM disk images are built, the AZP CI pipeline starts a
job in the `salvo-control` agent pool on AZP. This job is then picked up by a
Salvo control VM running a Salvo controller that instruments the sandbox
creation.

The Salvo controller uses the Terraform templates found in this directory,
to deploy the sandbox components in AWS.

# Sandbox instance life-cycle

The Terraform configuration for sandboxes uses shared state bucket deployed in
S3 on AWS. The sandbox instances that will be deployed or destroyed are
determined based on the variables passed to Terraform.

When a sandbox is starting up, it needs to locate the binaries and VM disk
images that were produced by the AZP CI pipeline. This is achieved by providing
the sandbox with the build ID that uniquely identifies the AZP CI pipeline
execution that produced them.

Each of the following variables is a list of these build IDs. Each list
represents one sandbox type. Each listed build ID represents an instance of the
sandbox type that should be deployed.

Supported sandbox types:

- `default_sandbox_x64_build_ids`.

For example the Terraform command to deploy a single instance of the default
sandbox with build ID `136112` is:

```shell
terraform apply --var="default_sandbox_build_ids=[\"136112\"]"
```

Any instances that were deployed, but are not named in the variables passed to
Terraform will be destroyed when Terraform is executed. To remove all deployed
sandboxes, simply execute `terraform apply` in this directory with no
arguments.

```shell
terraform apply
```
