package sandboxes

import (
	"context"
	"encoding/json"
	"errors"
	"net"
	"strings"
	"testing"

	"github.com/google/go-cmp/cmp"
	"github.com/hashicorp/terraform-exec/tfexec"
)

// tfexecTerraformAPI is a fake implementation of terraformAPI.
type fakeTerraformAPI struct {
	// initErr is the error to return when initTf is called.
	initErr error
	// applyErr is the error to return when Apply is called on the Terraform object.
	applyErr error
	// outputErr is the error to return when Output is called on the Terraform object.
	outputErr error
	// output is the output to return when Output is called on the Terraform object.
	output map[string]tfexec.OutputMeta
}

// newFakeTerraformAPI creates a new fakeTerraformAPI instance.
func newFakeTerraformAPI(initErr, applyErr, outputErr error, output map[string]tfexec.OutputMeta) *fakeTerraformAPI {
	return &fakeTerraformAPI{
		initErr:   initErr,
		applyErr:  applyErr,
		outputErr: outputErr,
		output:    output,
	}
}

func (f *fakeTerraformAPI) initTf(ctx context.Context, workingDir string) (terraform, error) {
	if f.initErr != nil {
		return nil, f.initErr
	}
	return newFakeTerraform(f.applyErr, f.outputErr, f.output), nil
}

// fakeTerraform is a fake implementation of Terraform.
type fakeTerraform struct {
	// applyErr is the error to return when Apply is called on the Terraform object.
	applyErr error
	// outputErr is the error to return when Output is called on the Terraform object.
	outputErr error
	// output is the output to return when Output is called on the Terraform object.
	output map[string]tfexec.OutputMeta
}

// newFakeTerraform returns a new fake Terraform object.
func newFakeTerraform(applyErr, outputErr error, output map[string]tfexec.OutputMeta) *fakeTerraform {
	return &fakeTerraform{
		applyErr:  applyErr,
		outputErr: outputErr,
		output:    output,
	}
}

func (f *fakeTerraform) Apply(ctx context.Context, opts ...tfexec.ApplyOption) error {
	return f.applyErr
}

func (f *fakeTerraform) Output(ctx context.Context, opts ...tfexec.OutputOption) (map[string]tfexec.OutputMeta, error) {
	return f.output, f.outputErr
}

func TestStart(t *testing.T) {
	tests := []struct {
		desc          string
		sbxs          map[Type]Instances
		initErr       error
		applyErr      error
		outputErr     error
		output        map[string]tfexec.OutputMeta
		want          map[int64]*Instance
		wantErrSubstr string
	}{
		{
			desc:          "fails when no sandboxes specified",
			wantErrSubstr: "at least one sandbox",
		},
		{
			desc: "fails on unsupported sandbox type",
			sbxs: map[Type]Instances{
				-1: {12345},
			},
			wantErrSubstr: "unsupported sandbox type",
		},
		{
			desc: "fails on sandbox with no instances",
			sbxs: map[Type]Instances{
				TypeDefaultSandboxX64: nil,
			},
			wantErrSubstr: "zero instances",
		},
		{
			desc: "fails with duplicate instances",
			sbxs: map[Type]Instances{
				TypeDefaultSandboxX64: {12345, 12345},
			},
			wantErrSubstr: "duplicate instance",
		},
		{
			desc: "fails with negative instance",
			sbxs: map[Type]Instances{
				TypeDefaultSandboxX64: {-1},
			},
			wantErrSubstr: "minimum allowed",
		},
		{
			desc: "fails with instance zero",
			sbxs: map[Type]Instances{
				TypeDefaultSandboxX64: {0},
			},
			wantErrSubstr: "minimum allowed",
		},
		{
			desc: "fails when terraform initialization fails",
			sbxs: map[Type]Instances{
				TypeDefaultSandboxX64: {12345},
			},
			initErr:       errors.New("fake error"),
			wantErrSubstr: "fake error",
		},
		{
			desc: "fails when terraform apply fails",
			sbxs: map[Type]Instances{
				TypeDefaultSandboxX64: {12345},
			},
			applyErr:      errors.New("fake error"),
			wantErrSubstr: "tf.Apply =>",
		},
		{
			desc: "fails when terraform output fails",
			sbxs: map[Type]Instances{
				TypeDefaultSandboxX64: {12345},
			},
			outputErr:     errors.New("fake error"),
			wantErrSubstr: "tf.Output =>",
		},
		{
			desc: "successfully starts a sandbox instance",
			sbxs: map[Type]Instances{
				TypeDefaultSandboxX64: {12345},
			},
			output: map[string]tfexec.OutputMeta{
				defSbxX64Gen0ControlIPs: {
					Value: json.RawMessage(`
					{
						"12345": ["1.1.1.1"]
					}
`),
				},
				defSbxX64Sut0ControlIPs: {
					Value: json.RawMessage(`
					{
						"12345": ["2.2.2.1"]
					}
`),
				},
				defSbxX64Bac0ControlIPs: {
					Value: json.RawMessage(`
					{
						"12345": ["3.3.3.1"]
					}
`),
				},
				defSbxX64Gen0IPs: {
					Value: json.RawMessage(`
					{
						"12345": ["10.1.1.1"]
					}
`),
				},
				defSbxX64Sut0IPs: {
					Value: json.RawMessage(`
					{
						"12345": ["20.2.2.1"]
					}
`),
				},
				defSbxX64Bac0IPs: {
					Value: json.RawMessage(`
					{
						"12345": ["30.3.3.1"]
					}
`),
				},
			},
			want: map[int64]*Instance{
				12345: {
					Type: TypeDefaultSandboxX64,
					LoadGenerators: []*VM{
						{
							IP:        net.ParseIP("10.1.1.1"),
							ControlIP: net.ParseIP("1.1.1.1"),
						},
					},
					SUTs: []*VM{
						{
							IP:        net.ParseIP("20.2.2.1"),
							ControlIP: net.ParseIP("2.2.2.1"),
						},
					},
					Backends: []*VM{
						{
							IP:        net.ParseIP("30.3.3.1"),
							ControlIP: net.ParseIP("3.3.3.1"),
						},
					},
				},
			},
		},
		{
			desc: "successfully starts multiple sandbox instances",
			sbxs: map[Type]Instances{
				TypeDefaultSandboxX64: {12345, 67890},
			},
			output: map[string]tfexec.OutputMeta{
				defSbxX64Gen0ControlIPs: {
					Value: json.RawMessage(`
					{
						"12345": ["1.1.1.1"],
						"67890": ["1.1.1.2"]
					}
`),
				},
				defSbxX64Sut0ControlIPs: {
					Value: json.RawMessage(`
					{
						"12345": ["2.2.2.1"],
						"67890": ["2.2.2.2"]
					}
`),
				},
				defSbxX64Bac0ControlIPs: {
					Value: json.RawMessage(`
					{
						"12345": ["3.3.3.1"],
						"67890": ["3.3.3.2"]
					}
`),
				},
				defSbxX64Gen0IPs: {
					Value: json.RawMessage(`
					{
						"12345": ["10.1.1.1"],
						"67890": ["10.1.1.2"]
					}
`),
				},
				defSbxX64Sut0IPs: {
					Value: json.RawMessage(`
					{
						"12345": ["20.2.2.1"],
						"67890": ["20.2.2.2"]
					}
`),
				},
				defSbxX64Bac0IPs: {
					Value: json.RawMessage(`
					{
						"12345": ["30.3.3.1"],
						"67890": ["30.3.3.2"]
					}
`),
				},
			},
			want: map[int64]*Instance{
				12345: {
					Type: TypeDefaultSandboxX64,
					LoadGenerators: []*VM{
						{
							IP:        net.ParseIP("10.1.1.1"),
							ControlIP: net.ParseIP("1.1.1.1"),
						},
					},
					SUTs: []*VM{
						{
							IP:        net.ParseIP("20.2.2.1"),
							ControlIP: net.ParseIP("2.2.2.1"),
						},
					},
					Backends: []*VM{
						{
							IP:        net.ParseIP("30.3.3.1"),
							ControlIP: net.ParseIP("3.3.3.1"),
						},
					},
				},
				67890: {
					Type: TypeDefaultSandboxX64,
					LoadGenerators: []*VM{
						{
							IP:        net.ParseIP("10.1.1.2"),
							ControlIP: net.ParseIP("1.1.1.2"),
						},
					},
					SUTs: []*VM{
						{
							IP:        net.ParseIP("20.2.2.2"),
							ControlIP: net.ParseIP("2.2.2.2"),
						},
					},
					Backends: []*VM{
						{
							IP:        net.ParseIP("30.3.3.2"),
							ControlIP: net.ParseIP("3.3.3.2"),
						},
					},
				},
			},
		},
	}

	for _, tc := range tests {
		t.Run(tc.desc, func(t *testing.T) {
			fakeAPI := newFakeTerraformAPI(tc.initErr, tc.applyErr, tc.outputErr, tc.output)
			m := NewManager(customTerraformAPI(fakeAPI))
			ctx := context.Background()
			got, err := m.Start(ctx, tc.sbxs)
			if (err != nil) != (tc.wantErrSubstr != "") {
				t.Errorf("Start => unexpected error: %v, wantErrSubstr: %q", err, tc.wantErrSubstr)
			}
			if err != nil && !strings.Contains(err.Error(), tc.wantErrSubstr) {
				t.Errorf("Start => unexpected error substring, got:%q, want substring:%q", err, tc.wantErrSubstr)

			}

			if diff := cmp.Diff(tc.want, got); diff != "" {
				t.Errorf("Start => unexpected diff (-want, +got):\n%s", diff)
			}
		})
	}
}

func TestStopAll(t *testing.T) {
	tests := []struct {
		desc          string
		initErr       error
		applyErr      error
		wantErrSubstr string
	}{
		{
			desc:          "fails when terraform initialization fails",
			initErr:       errors.New("fake error"),
			wantErrSubstr: "fake error",
		},
		{
			desc:          "fails when terraform apply fails",
			applyErr:      errors.New("fake error"),
			wantErrSubstr: "tf.Apply =>",
		},
		{
			desc: "successfully stops all sandbox instances",
		},
	}

	for _, tc := range tests {
		t.Run(tc.desc, func(t *testing.T) {
			fakeAPI := newFakeTerraformAPI(tc.initErr, tc.applyErr, nil, nil)
			m := NewManager(customTerraformAPI(fakeAPI))
			ctx := context.Background()
			err := m.StopAll(ctx)
			if (err != nil) != (tc.wantErrSubstr != "") {
				t.Errorf("Stop => unexpected error: %v, wantErrSubstr: %q", err, tc.wantErrSubstr)
			}
			if err != nil && !strings.Contains(err.Error(), tc.wantErrSubstr) {
				t.Errorf("Stop => unexpected error substring, got:%q, want substring:%q", err, tc.wantErrSubstr)

			}
		})
	}
}

func TestSbxsToTfVars(t *testing.T) {
	tests := []struct {
		desc    string
		sbxs    map[Type]Instances
		want    []string
		wantErr bool
	}{
		{
			desc:    "fails when no sandboxes specified",
			wantErr: true,
		},
		{
			desc: "fails on unsupported sandbox type",
			sbxs: map[Type]Instances{
				-1: {12345},
			},
			wantErr: true,
		},
		{
			desc: "fails on sandbox with no instances",
			sbxs: map[Type]Instances{
				TypeDefaultSandboxX64: nil,
			},
			wantErr: true,
		},
		{
			desc: "fails with duplicate instances",
			sbxs: map[Type]Instances{
				TypeDefaultSandboxX64: {12345, 12345},
			},
			wantErr: true,
		},
		{
			desc: "fails with negative instance",
			sbxs: map[Type]Instances{
				TypeDefaultSandboxX64: {-1},
			},
			wantErr: true,
		},
		{
			desc: "fails with instance zero",
			sbxs: map[Type]Instances{
				TypeDefaultSandboxX64: {0},
			},
			wantErr: true,
		},
		{
			desc: "correct vars for a single instance",
			sbxs: map[Type]Instances{
				TypeDefaultSandboxX64: {12345},
			},
			want: []string{
				"default_sandbox_x64_build_ids=[12345]",
			},
		},
		{
			desc: "correct vars for multiple instances",
			sbxs: map[Type]Instances{
				TypeDefaultSandboxX64: {12345, 67890},
			},
			want: []string{
				"default_sandbox_x64_build_ids=[12345,67890]",
			},
		},
	}

	for _, tc := range tests {
		t.Run(tc.desc, func(t *testing.T) {
			got, err := sbxsToTfVars(tc.sbxs)
			if (err != nil) != tc.wantErr {
				t.Errorf("sbxsToTfVars => unexpected error: %v, wantErr: %v", err, tc.wantErr)
			}
			if diff := cmp.Diff(tc.want, got); diff != "" {
				t.Errorf("sbxsToTfVars => unexpected diff (-want, +got):\n%s", diff)
			}
		})
	}
}
