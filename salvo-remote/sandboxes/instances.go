// instances.go defined data types that described deployed sandbox instances.
package sandboxes

import (
	"errors"
	"fmt"
	"net"

	"encoding/json"

	"github.com/hashicorp/terraform-exec/tfexec"
)

// Instance describes a single sandbox instance.
type Instance struct {
	// Type identifies the type of the sandbox instance.
	Type Type

	// LoadGenerators are the load generator VMs deployed in the sandbox.
	LoadGenerators []*VM

	// SUTs are the system under test VMs deployed in the sandbox.
	SUTs []*VM

	// Backends are the backend VMs deployed in the sandbox.
	Backends []*VM
}

// newInstanceWithSingleVM creates an instance of the specified type with a single VM instance of each kind.
func newInstanceWithSingleVM(typ Type) *Instance {
	return &Instance{
		Type:           typ,
		LoadGenerators: []*VM{{}},
		SUTs:           []*VM{{}},
		Backends:       []*VM{{}},
	}
}

// String implements fmt.Stringer.
func (i *Instance) String() string {
	b, err := json.Marshal(i)
	if err != nil {
		panic(err)
	}
	return string(b)
}

// VM describes a VM deployed in a sandbox.
type VM struct {
	// IP is the primary private IP address of the VM.
	// This is the IP address on the interface that either originates or receives load.
	IP net.IP

	// ControlIP is a private IP address that can be used by the control VM when accessing the VM.
	// Note, the control VM is the VM that runs salvo-remote (this code).
	ControlIP net.IP
}

const (
	// Names of Terraform outputs that provide the primary private IPs of the VMs in the sandbox.
	// These are the IPs that originate and receive load.
	defSbxX64Gen0ControlIPs = "default_sandbox_x64_build_ids_to_load_generator_0_control_vm_subnet_ip_list"
	defSbxX64Sut0ControlIPs = "default_sandbox_x64_build_ids_to_sut_0_control_vm_subnet_ip_list"
	defSbxX64Bac0ControlIPs = "default_sandbox_x64_build_ids_to_backend_0_control_vm_subnet_ip_list"

	// Names of Terraform outputs that provide the private IPs that can be used to control the VMs.
	defSbxX64Gen0IPs = "default_sandbox_x64_build_ids_to_load_generator_0_load_generator_subnet_ip_list"
	defSbxX64Sut0IPs = "default_sandbox_x64_build_ids_to_sut_0_load_generator_subnet_ip_list"
	defSbxX64Bac0IPs = "default_sandbox_x64_build_ids_to_backend_0_backend_subnet_ip_list"
)

// parseInstances takes a Terraform output and parses it to identify sandbox instances.
// The returned value maps sandbox build IDs to the sandbox instance.
func parseInstances(sbxs map[Type]Instances, output map[string]tfexec.OutputMeta) (map[int64]*Instance, error) {
	if len(sbxs) == 0 {
		return nil, errors.New("at least one sandbox type has to be specified")
	}

	res := map[int64]*Instance{}
	for typ, insts := range sbxs {
		if len(insts) == 0 {
			return nil, fmt.Errorf("no instances specified for sandbox type %s(%d), at least one instance must be specified", typ, typ)
		}

		switch typ {
		case TypeDefaultSandboxX64:
			instRes, err := parseDefaultSandboxX64(insts, output)
			if err != nil {
				return nil, err
			}
			combineInst(res, instRes)
		default:
			return nil, fmt.Errorf("unsupported sandbox type %s(%d)", typ, typ)
		}
	}

	return res, nil
}

// combineInst combines instance b into instance a.
func combineInst(a, b map[int64]*Instance) {
	for k, v := range b {
		a[k] = v
	}
}

// parseDefaultSandboxX64 parses the Terraform outputs for a sendbox of type TypeDefaultSandboxX64.
func parseDefaultSandboxX64(insts Instances, output map[string]tfexec.OutputMeta) (map[int64]*Instance, error) {
	res := map[int64]*Instance{}
	for _, instNum := range insts {
		inst := newInstanceWithSingleVM(TypeDefaultSandboxX64)
		res[instNum] = inst

		for _, data := range []struct {
			tfVar     string
			instField *net.IP
		}{
			{defSbxX64Gen0ControlIPs, &inst.LoadGenerators[0].ControlIP},
			{defSbxX64Sut0ControlIPs, &inst.SUTs[0].ControlIP},
			{defSbxX64Bac0ControlIPs, &inst.Backends[0].ControlIP},
			{defSbxX64Gen0IPs, &inst.LoadGenerators[0].IP},
			{defSbxX64Sut0IPs, &inst.SUTs[0].IP},
			{defSbxX64Bac0IPs, &inst.Backends[0].IP},
		} {
			outMeta, ok := output[data.tfVar]
			if !ok {
				return nil, fmt.Errorf("Terraform output doesn't contain variable %q", data.tfVar)
			}

			idIPs, err := unmarshalBuildIPMap(outMeta.Value)
			if err != nil {
				return nil, fmt.Errorf("unmarshalBuildIPMap for variable %q: %v, raw json: %q", data.tfVar, err, outMeta.Value)
			}

			ips, ok := idIPs[instNum]
			if !ok {
				return nil, fmt.Errorf("Terraform output doesn't contain sandbox instance %d in variable %q, got idIPs: %+v", instNum, data.tfVar, idIPs)
			}

			if got, want := len(ips), 1; got != want {
				return nil, fmt.Errorf("Terraform returned invalid number(%d) of IPs in sandbox instance %d, variable %q, wanted %d, got ips: %+v", got, instNum, data.tfVar, want, ips)
			}
			*data.instField = ips[0]
		}
	}
	return res, nil
}
