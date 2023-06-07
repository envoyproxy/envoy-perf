package sandboxes

import (
	"encoding/json"
	"net"
	"testing"

	"github.com/google/go-cmp/cmp"
	"github.com/hashicorp/terraform-exec/tfexec"
)

func TestParseInstances(t *testing.T) {
	tests := []struct {
		desc    string
		sbxs    map[Type]Instances
		output  map[string]tfexec.OutputMeta
		want    map[int64]*Instance
		wantErr bool
	}{
		{
			desc: "unsupported sandbox type",
			sbxs: map[Type]Instances{
				Type(-1): {},
			},
			wantErr: true,
		},
		{
			desc:    "no sandbox types provided",
			sbxs:    map[Type]Instances{},
			wantErr: true,
		},
		{
			desc: "no instances provided",
			sbxs: map[Type]Instances{
				TypeDefaultSandboxX64: {},
			},
			wantErr: true,
		},
		{
			desc: "sbxs specifies instance not found in outputs",
			sbxs: map[Type]Instances{
				TypeDefaultSandboxX64: {12345, 67890},
			},
			output: map[string]tfexec.OutputMeta{
				defSbxX64Gen0ControlIPs: {
					Value: json.RawMessage(`
					{
						"12345": ["1.1.1.1"],
					}
`),
				},
				defSbxX64Sut0ControlIPs: {
					Value: json.RawMessage(`
					{
						"12345": ["2.2.2.1"],
					}
`),
				},
				defSbxX64Bac0ControlIPs: {
					Value: json.RawMessage(`
					{
						"12345": ["3.3.3.1"],
					}
`),
				},
				defSbxX64Gen0IPs: {
					Value: json.RawMessage(`
					{
						"12345": ["10.1.1.1"],
					}
`),
				},
				defSbxX64Sut0IPs: {
					Value: json.RawMessage(`
					{
						"12345": ["20.2.2.1"],
					}
`),
				},
				defSbxX64Bac0IPs: {
					Value: json.RawMessage(`
					{
						"12345": ["30.3.3.1"],
					}
`),
				},
			},
			wantErr: true,
		},
		{
			desc: "defSbxX64Gen0ControlIPs is missing",
			sbxs: map[Type]Instances{
				TypeDefaultSandboxX64: {12345},
			},
			output: map[string]tfexec.OutputMeta{
				defSbxX64Sut0ControlIPs: {
					Value: json.RawMessage(`"12345": ["1.1.1.1"]`),
				},
				defSbxX64Bac0ControlIPs: {
					Value: json.RawMessage(`"12345": ["1.1.1.1"]`),
				},
				defSbxX64Gen0IPs: {
					Value: json.RawMessage(`"12345": ["1.1.1.1"]`),
				},
				defSbxX64Sut0IPs: {
					Value: json.RawMessage(`"12345": ["1.1.1.1"]`),
				},
				defSbxX64Bac0IPs: {
					Value: json.RawMessage(`"12345": ["1.1.1.1"]`),
				},
			},
			wantErr: true,
		},
		{
			desc: "defSbxX64Sut0ControlIPs is missing",
			sbxs: map[Type]Instances{
				TypeDefaultSandboxX64: {12345},
			},
			output: map[string]tfexec.OutputMeta{
				defSbxX64Gen0ControlIPs: {
					Value: json.RawMessage(`"12345": ["1.1.1.1"]`),
				},
				defSbxX64Bac0ControlIPs: {
					Value: json.RawMessage(`"12345": ["1.1.1.1"]`),
				},
				defSbxX64Gen0IPs: {
					Value: json.RawMessage(`"12345": ["1.1.1.1"]`),
				},
				defSbxX64Sut0IPs: {
					Value: json.RawMessage(`"12345": ["1.1.1.1"]`),
				},
				defSbxX64Bac0IPs: {
					Value: json.RawMessage(`"12345": ["1.1.1.1"]`),
				},
			},
			wantErr: true,
		},
		{
			desc: "defSbxX64Bac0ControlIPs is missing",
			sbxs: map[Type]Instances{
				TypeDefaultSandboxX64: {12345},
			},
			output: map[string]tfexec.OutputMeta{
				defSbxX64Gen0ControlIPs: {
					Value: json.RawMessage(`"12345": ["1.1.1.1"]`),
				},
				defSbxX64Sut0ControlIPs: {
					Value: json.RawMessage(`"12345": ["1.1.1.1"]`),
				},
				defSbxX64Gen0IPs: {
					Value: json.RawMessage(`"12345": ["1.1.1.1"]`),
				},
				defSbxX64Sut0IPs: {
					Value: json.RawMessage(`"12345": ["1.1.1.1"]`),
				},
				defSbxX64Bac0IPs: {
					Value: json.RawMessage(`"12345": ["1.1.1.1"]`),
				},
			},
			wantErr: true,
		},
		{
			desc: "defSbxX64Gen0IPs is missing",
			sbxs: map[Type]Instances{
				TypeDefaultSandboxX64: {12345},
			},
			output: map[string]tfexec.OutputMeta{
				defSbxX64Gen0ControlIPs: {
					Value: json.RawMessage(`"12345": ["1.1.1.1"]`),
				},
				defSbxX64Sut0ControlIPs: {
					Value: json.RawMessage(`"12345": ["1.1.1.1"]`),
				},
				defSbxX64Bac0ControlIPs: {
					Value: json.RawMessage(`"12345": ["1.1.1.1"]`),
				},
				defSbxX64Sut0IPs: {
					Value: json.RawMessage(`"12345": ["1.1.1.1"]`),
				},
				defSbxX64Bac0IPs: {
					Value: json.RawMessage(`"12345": ["1.1.1.1"]`),
				},
			},
			wantErr: true,
		},
		{
			desc: "defSbxX64Sut0IPs is missing",
			sbxs: map[Type]Instances{
				TypeDefaultSandboxX64: {12345},
			},
			output: map[string]tfexec.OutputMeta{
				defSbxX64Gen0ControlIPs: {
					Value: json.RawMessage(`"12345": ["1.1.1.1"]`),
				},
				defSbxX64Sut0ControlIPs: {
					Value: json.RawMessage(`"12345": ["1.1.1.1"]`),
				},
				defSbxX64Bac0ControlIPs: {
					Value: json.RawMessage(`"12345": ["1.1.1.1"]`),
				},
				defSbxX64Gen0IPs: {
					Value: json.RawMessage(`"12345": ["1.1.1.1"]`),
				},
				defSbxX64Bac0IPs: {
					Value: json.RawMessage(`"12345": ["1.1.1.1"]`),
				},
			},
			wantErr: true,
		},
		{
			desc: "defSbxX64Bac0IPs is missing",
			sbxs: map[Type]Instances{
				TypeDefaultSandboxX64: {12345},
			},
			output: map[string]tfexec.OutputMeta{
				defSbxX64Gen0ControlIPs: {
					Value: json.RawMessage(`"12345": ["1.1.1.1"]`),
				},
				defSbxX64Sut0ControlIPs: {
					Value: json.RawMessage(`"12345": ["1.1.1.1"]`),
				},
				defSbxX64Bac0ControlIPs: {
					Value: json.RawMessage(`"12345": ["1.1.1.1"]`),
				},
				defSbxX64Gen0IPs: {
					Value: json.RawMessage(`"12345": ["1.1.1.1"]`),
				},
				defSbxX64Sut0IPs: {
					Value: json.RawMessage(`"12345": ["1.1.1.1"]`),
				},
			},
			wantErr: true,
		},
		{
			desc: "defSbxX64Gen0ControlIPs has multiple IPs",
			sbxs: map[Type]Instances{
				TypeDefaultSandboxX64: {12345},
			},
			output: map[string]tfexec.OutputMeta{
				defSbxX64Gen0ControlIPs: {
					Value: json.RawMessage(`"12345": ["1.1.1.1", "2.2.2.2"]`),
				},
				defSbxX64Sut0ControlIPs: {
					Value: json.RawMessage(`"12345": ["1.1.1.1"]`),
				},
				defSbxX64Bac0ControlIPs: {
					Value: json.RawMessage(`"12345": ["1.1.1.1"]`),
				},
				defSbxX64Gen0IPs: {
					Value: json.RawMessage(`"12345": ["1.1.1.1"]`),
				},
				defSbxX64Sut0IPs: {
					Value: json.RawMessage(`"12345": ["1.1.1.1"]`),
				},
				defSbxX64Bac0IPs: {
					Value: json.RawMessage(`"12345": ["1.1.1.1"]`),
				},
			},
			wantErr: true,
		},
		{
			desc: "defSbxX64Gen0ControlIPs has multiple IPs",
			sbxs: map[Type]Instances{
				TypeDefaultSandboxX64: {12345},
			},
			output: map[string]tfexec.OutputMeta{
				defSbxX64Gen0ControlIPs: {
					Value: json.RawMessage(`"12345": ["1.1.1.1"]`),
				},
				defSbxX64Sut0ControlIPs: {
					Value: json.RawMessage(`"12345": ["1.1.1.1", "2.2.2.2"]`),
				},
				defSbxX64Bac0ControlIPs: {
					Value: json.RawMessage(`"12345": ["1.1.1.1"]`),
				},
				defSbxX64Gen0IPs: {
					Value: json.RawMessage(`"12345": ["1.1.1.1"]`),
				},
				defSbxX64Sut0IPs: {
					Value: json.RawMessage(`"12345": ["1.1.1.1"]`),
				},
				defSbxX64Bac0IPs: {
					Value: json.RawMessage(`"12345": ["1.1.1.1"]`),
				},
			},
			wantErr: true,
		},
		{
			desc: "defSbxX64Bac0ControlIPs has multiple IPs",
			sbxs: map[Type]Instances{
				TypeDefaultSandboxX64: {12345},
			},
			output: map[string]tfexec.OutputMeta{
				defSbxX64Gen0ControlIPs: {
					Value: json.RawMessage(`"12345": ["1.1.1.1"]`),
				},
				defSbxX64Sut0ControlIPs: {
					Value: json.RawMessage(`"12345": ["1.1.1.1"]`),
				},
				defSbxX64Bac0ControlIPs: {
					Value: json.RawMessage(`"12345": ["1.1.1.1", "2.2.2.2"]`),
				},
				defSbxX64Gen0IPs: {
					Value: json.RawMessage(`"12345": ["1.1.1.1"]`),
				},
				defSbxX64Sut0IPs: {
					Value: json.RawMessage(`"12345": ["1.1.1.1"]`),
				},
				defSbxX64Bac0IPs: {
					Value: json.RawMessage(`"12345": ["1.1.1.1"]`),
				},
			},
			wantErr: true,
		},
		{
			desc: "defSbxX64Gen0IPs has multiple IPs",
			sbxs: map[Type]Instances{
				TypeDefaultSandboxX64: {12345},
			},
			output: map[string]tfexec.OutputMeta{
				defSbxX64Gen0ControlIPs: {
					Value: json.RawMessage(`"12345": ["1.1.1.1"]`),
				},
				defSbxX64Sut0ControlIPs: {
					Value: json.RawMessage(`"12345": ["1.1.1.1"]`),
				},
				defSbxX64Bac0ControlIPs: {
					Value: json.RawMessage(`"12345": ["1.1.1.1"]`),
				},
				defSbxX64Gen0IPs: {
					Value: json.RawMessage(`"12345": ["1.1.1.1", "2.2.2.2"]`),
				},
				defSbxX64Sut0IPs: {
					Value: json.RawMessage(`"12345": ["1.1.1.1"]`),
				},
				defSbxX64Bac0IPs: {
					Value: json.RawMessage(`"12345": ["1.1.1.1"]`),
				},
			},
			wantErr: true,
		},
		{
			desc: "defSbxX64Sut0IPs has multiple IPs",
			sbxs: map[Type]Instances{
				TypeDefaultSandboxX64: {12345},
			},
			output: map[string]tfexec.OutputMeta{
				defSbxX64Gen0ControlIPs: {
					Value: json.RawMessage(`"12345": ["1.1.1.1"]`),
				},
				defSbxX64Sut0ControlIPs: {
					Value: json.RawMessage(`"12345": ["1.1.1.1"]`),
				},
				defSbxX64Bac0ControlIPs: {
					Value: json.RawMessage(`"12345": ["1.1.1.1"]`),
				},
				defSbxX64Gen0IPs: {
					Value: json.RawMessage(`"12345": ["1.1.1.1"]`),
				},
				defSbxX64Sut0IPs: {
					Value: json.RawMessage(`"12345": ["1.1.1.1", "2.2.2.2"]`),
				},
				defSbxX64Bac0IPs: {
					Value: json.RawMessage(`"12345": ["1.1.1.1"]`),
				},
			},
			wantErr: true,
		},
		{
			desc: "defSbxX64Bac0IPs has multiple IPs",
			sbxs: map[Type]Instances{
				TypeDefaultSandboxX64: {12345},
			},
			output: map[string]tfexec.OutputMeta{
				defSbxX64Gen0ControlIPs: {
					Value: json.RawMessage(`"12345": ["1.1.1.1"]`),
				},
				defSbxX64Sut0ControlIPs: {
					Value: json.RawMessage(`"12345": ["1.1.1.1"]`),
				},
				defSbxX64Bac0ControlIPs: {
					Value: json.RawMessage(`"12345": ["1.1.1.1"]`),
				},
				defSbxX64Gen0IPs: {
					Value: json.RawMessage(`"12345": ["1.1.1.1"]`),
				},
				defSbxX64Sut0IPs: {
					Value: json.RawMessage(`"12345": ["1.1.1.1"]`),
				},
				defSbxX64Bac0IPs: {
					Value: json.RawMessage(`"12345": ["1.1.1.1", "2.2.2.2"]`),
				},
			},
			wantErr: true,
		},
		{
			desc: "defSbxX64Gen0ControlIPs has no IPs",
			sbxs: map[Type]Instances{
				TypeDefaultSandboxX64: {12345},
			},
			output: map[string]tfexec.OutputMeta{
				defSbxX64Gen0ControlIPs: {
					Value: json.RawMessage(`"12345": []`),
				},
				defSbxX64Sut0ControlIPs: {
					Value: json.RawMessage(`"12345": ["1.1.1.1"]`),
				},
				defSbxX64Bac0ControlIPs: {
					Value: json.RawMessage(`"12345": ["1.1.1.1"]`),
				},
				defSbxX64Gen0IPs: {
					Value: json.RawMessage(`"12345": ["1.1.1.1"]`),
				},
				defSbxX64Sut0IPs: {
					Value: json.RawMessage(`"12345": ["1.1.1.1"]`),
				},
				defSbxX64Bac0IPs: {
					Value: json.RawMessage(`"12345": ["1.1.1.1"]`),
				},
			},
			wantErr: true,
		},
		{
			desc: "defSbxX64Sut0ControlIPs has no IPs",
			sbxs: map[Type]Instances{
				TypeDefaultSandboxX64: {12345},
			},
			output: map[string]tfexec.OutputMeta{
				defSbxX64Gen0ControlIPs: {
					Value: json.RawMessage(`"12345": ["1.1.1.1"]`),
				},
				defSbxX64Sut0ControlIPs: {
					Value: json.RawMessage(`"12345": []`),
				},
				defSbxX64Bac0ControlIPs: {
					Value: json.RawMessage(`"12345": ["1.1.1.1"]`),
				},
				defSbxX64Gen0IPs: {
					Value: json.RawMessage(`"12345": ["1.1.1.1"]`),
				},
				defSbxX64Sut0IPs: {
					Value: json.RawMessage(`"12345": ["1.1.1.1"]`),
				},
				defSbxX64Bac0IPs: {
					Value: json.RawMessage(`"12345": ["1.1.1.1"]`),
				},
			},
			wantErr: true,
		},
		{
			desc: "defSbxX64Bac0ControlIPs has no IPs",
			sbxs: map[Type]Instances{
				TypeDefaultSandboxX64: {12345},
			},
			output: map[string]tfexec.OutputMeta{
				defSbxX64Gen0ControlIPs: {
					Value: json.RawMessage(`"12345": ["1.1.1.1"]`),
				},
				defSbxX64Sut0ControlIPs: {
					Value: json.RawMessage(`"12345": ["1.1.1.1"]`),
				},
				defSbxX64Bac0ControlIPs: {
					Value: json.RawMessage(`"12345": []`),
				},
				defSbxX64Gen0IPs: {
					Value: json.RawMessage(`"12345": ["1.1.1.1"]`),
				},
				defSbxX64Sut0IPs: {
					Value: json.RawMessage(`"12345": ["1.1.1.1"]`),
				},
				defSbxX64Bac0IPs: {
					Value: json.RawMessage(`"12345": ["1.1.1.1"]`),
				},
			},
			wantErr: true,
		},
		{
			desc: "defSbxX64Gen0IPs has no IPs",
			sbxs: map[Type]Instances{
				TypeDefaultSandboxX64: {12345},
			},
			output: map[string]tfexec.OutputMeta{
				defSbxX64Gen0ControlIPs: {
					Value: json.RawMessage(`"12345": ["1.1.1.1"]`),
				},
				defSbxX64Sut0ControlIPs: {
					Value: json.RawMessage(`"12345": ["1.1.1.1"]`),
				},
				defSbxX64Bac0ControlIPs: {
					Value: json.RawMessage(`"12345": ["1.1.1.1"]`),
				},
				defSbxX64Gen0IPs: {
					Value: json.RawMessage(`"12345": []`),
				},
				defSbxX64Sut0IPs: {
					Value: json.RawMessage(`"12345": ["1.1.1.1"]`),
				},
				defSbxX64Bac0IPs: {
					Value: json.RawMessage(`"12345": ["1.1.1.1"]`),
				},
			},
			wantErr: true,
		},
		{
			desc: "defSbxX64Sut0IPs has no IPs",
			sbxs: map[Type]Instances{
				TypeDefaultSandboxX64: {12345},
			},
			output: map[string]tfexec.OutputMeta{
				defSbxX64Gen0ControlIPs: {
					Value: json.RawMessage(`"12345": ["1.1.1.1"]`),
				},
				defSbxX64Sut0ControlIPs: {
					Value: json.RawMessage(`"12345": ["1.1.1.1"]`),
				},
				defSbxX64Bac0ControlIPs: {
					Value: json.RawMessage(`"12345": ["1.1.1.1"]`),
				},
				defSbxX64Gen0IPs: {
					Value: json.RawMessage(`"12345": ["1.1.1.1"]`),
				},
				defSbxX64Sut0IPs: {
					Value: json.RawMessage(`"12345": []`),
				},
				defSbxX64Bac0IPs: {
					Value: json.RawMessage(`"12345": ["1.1.1.1"]`),
				},
			},
			wantErr: true,
		},
		{
			desc: "defSbxX64Bac0IPs has no IPs",
			sbxs: map[Type]Instances{
				TypeDefaultSandboxX64: {12345},
			},
			output: map[string]tfexec.OutputMeta{
				defSbxX64Gen0ControlIPs: {
					Value: json.RawMessage(`"12345": ["1.1.1.1"]`),
				},
				defSbxX64Sut0ControlIPs: {
					Value: json.RawMessage(`"12345": ["1.1.1.1"]`),
				},
				defSbxX64Bac0ControlIPs: {
					Value: json.RawMessage(`"12345": ["1.1.1.1"]`),
				},
				defSbxX64Gen0IPs: {
					Value: json.RawMessage(`"12345": ["1.1.1.1"]`),
				},
				defSbxX64Sut0IPs: {
					Value: json.RawMessage(`"12345": ["1.1.1.1"]`),
				},
				defSbxX64Bac0IPs: {
					Value: json.RawMessage(`"12345": []`),
				},
			},
			wantErr: true,
		},
		{
			desc: "parses multiple instances",
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
			got, err := parseInstances(tc.sbxs, tc.output)
			if (err != nil) != tc.wantErr {
				t.Errorf("parseInstances => unexpected error: %v, wantErr: %v", err, tc.wantErr)
			}
			if err != nil {
				return
			}

			if diff := cmp.Diff(tc.want, got); diff != "" {
				t.Errorf("parseInstances => unexpected diff (-want, +got):\n%s", diff)
			}
		})
	}
}
