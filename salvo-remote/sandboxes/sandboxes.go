// Package sandboxes manages the life cycle of a Salvo remote sandbox.
package sandboxes

import (
	"context"
	"errors"
	"fmt"
	"log"
	"strings"

	"github.com/hashicorp/go-version"
	"github.com/hashicorp/hc-install/product"
	"github.com/hashicorp/hc-install/releases"
	"github.com/hashicorp/terraform-exec/tfexec"
)

// sandboxDefDir is the directory where the sandbox Terraform definition files are located.
const sandboxDefDir = "terraform/"

// Type enumerates the types of sandboxes supported.
type Type int

// String implements fmt.Stringer()
func (t Type) String() string {
	if n, ok := typeNames[t]; ok {
		return n
	}
	return "TypeUnknown"
}

// typeNames maps Type values to human readable names.
var typeNames = map[Type]string{
	TypeDefaultSandboxX64: "default_sandbox_x64_build_ids",
}

const (
	typeUnknown Type = iota

	// TypeDefaultSandboxX64 is the default sandbox, see https://github.com/envoyproxy/envoy-perf/tree/main/salvo-remote/sandboxes/terraform/default_sandbox_x64.
	TypeDefaultSandboxX64
)

// Instances represent sandbox instances, each integer is an AZP Build ID corresponding to AZP pipeline execution that built the components for the sandbox.
type Instances []int

// terraformAPI abstracts calls to functions that interact with Terraform.
// Exists to support dependency injection for unit testing.
type terraformAPI interface {
	// initTf installs Terraform, initializes and returns the Terraform object.
	initTf(ctx context.Context, workingDir string) (terraform, error)
}

// terraform abstracts the real tfexec.Terraform object.
// Exists to support dependency injection for unit testing.
type terraform interface {
	Apply(ctx context.Context, opts ...tfexec.ApplyOption) error
}

// tfexecTerraformAPI implements terraformAPI using the real tfexec library.
type tfexecTerraformAPI struct {
}

func (t *tfexecTerraformAPI) initTf(ctx context.Context, workingDir string) (terraform, error) {
	return initTf(ctx, workingDir)
}

// Manager manages sandbox instances.
type Manager struct {
	tAPI terraformAPI
}

// Option is used to provide options to NewManager.
type Option interface {
	// set sets the provided option.
	set(*Manager)
}

// option implements Option.
type option func(*Manager)

// set implements Option.set.
func (o option) set(m *Manager) {
	o(m)
}

// customTerraformAPI creates the manager with a custom Terraform API.
func customTerraformAPI(tAPI terraformAPI) Option {
	return option(func(m *Manager) {
		m.tAPI = tAPI
	})
}

// NewManager creates a new Sandbox manager.
func NewManager(opts ...Option) *Manager {
	m := &Manager{
		tAPI: &tfexecTerraformAPI{},
	}
	for _, opt := range opts {
		opt.set(m)
	}
	return m
}

// Start starts the specified sandbox instances.
func (m *Manager) Start(ctx context.Context, sbxs map[Type]Instances) error {
	tf, err := m.tAPI.initTf(ctx, sandboxDefDir)
	if err != nil {
		return err
	}

	vars, err := sbxsToTfVars(sbxs)
	if err != nil {
		return err
	}
	var opts []tfexec.ApplyOption
	for _, v := range vars {
		opts = append(opts, tfexec.Var(v))
	}

	log.Printf("Starting Salvo sbxs %+v.", sbxs)
	if err := tf.Apply(ctx, opts...); err != nil {
		return fmt.Errorf("tf.Apply => %v", err)
	}
	return nil
}

// StopAll stops all sandbox instances.
func (m *Manager) StopAll(ctx context.Context) error {
	tf, err := m.tAPI.initTf(ctx, sandboxDefDir)
	if err != nil {
		return err
	}

	log.Printf("Stopping all Salvo sandboxes.")
	if err := tf.Apply(ctx); err != nil {
		return fmt.Errorf("tf.Apply => %v", err)
	}
	return nil
}

// sbxsToTfVars validates and converts the requested sandbox instances to Terraform variables.
func sbxsToTfVars(sbxs map[Type]Instances) ([]string, error) {
	if len(sbxs) == 0 {
		return nil, errors.New("at least one sandbox type must be specified")
	}

	var vars []string
	for t, instances := range sbxs {
		if _, ok := typeNames[t]; !ok {
			return nil, fmt.Errorf("unsupported sandbox type %s(%d)", t, t)
		}
		if len(instances) == 0 {
			return nil, fmt.Errorf("requested sandboxes specified sandbox Type %v with zero instances, at least one instance (one build ID) must be specified", t)
		}
		seen := map[int]bool{}
		var instStrs []string
		for _, inst := range instances {
			if seen[inst] {
				return nil, fmt.Errorf("requested sandboxes specified sandbox Type %v with duplicate instance (build ID) %d", t, inst)
			}
			seen[inst] = true

			if min := 1; inst < min {
				return nil, fmt.Errorf("requested sandboxes specified sandbox Type %v with instance (build ID) %d, the minimum allowed instance is %d", t, inst, min)
			}
			instStrs = append(instStrs, fmt.Sprintf("%d", inst))
		}
		opt := fmt.Sprintf("%s=[%s]", t, strings.Join(instStrs, ","))
		log.Printf("Adding Terraform option %q.", opt)
		vars = append(vars, opt)
	}
	return vars, nil
}

// initTf installs Terraform, initializes and returns the Terraform object.
func initTf(ctx context.Context, workingDir string) (terraform, error) {
	log.Printf("Installing the Terraform binary.")
	installer := &releases.ExactVersion{
		Product: product.Terraform,
		Version: version.Must(version.NewVersion("1.4.6")),
	}

	execPath, err := installer.Install(ctx)
	if err != nil {
		return nil, fmt.Errorf("installer.Install => %v", err)
	}

	log.Printf("Initializing the Terraform binary.")
	tf, err := tfexec.NewTerraform(sandboxDefDir, execPath)
	if err != nil {
		return nil, fmt.Errorf("tfexec.NewTerraform => %v", err)
	}

	if err := tf.Init(ctx); err != nil {
		return nil, fmt.Errorf("tf.Init => %v", err)
	}
	return tf, nil
}
