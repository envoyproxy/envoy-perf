package sandboxes

import (
	"net"
	"testing"

	"github.com/google/go-cmp/cmp"
)

func TestUnmarshalBuildIPMap(t *testing.T) {
	tests := []struct {
		desc    string
		rawJSON string
		want    map[int64][]net.IP
		wantErr bool
	}{
		{
			desc:    "fails when unmarshal fails",
			rawJSON: "not a json",
			wantErr: true,
		},
		{
			desc:    "fails when build id zero",
			rawJSON: `{"0": []}`,
			wantErr: true,
		},
		{
			desc:    "fails when build id negative",
			rawJSON: `{"-1": []}`,
			wantErr: true,
		},
		{
			desc:    "fails when build id has no IPs",
			rawJSON: `{"1": []}`,
			wantErr: true,
		},
		{
			desc:    "fails when IP does not parse",
			rawJSON: `{"1": ["a.a.a.a"]}`,
			wantErr: true,
		},
		{
			desc:    "parses build ids and IPs",
			rawJSON: `{"1": ["1.1.1.1", "1.1.1.2"], "2": ["2.2.2.2"]}`,
			want: map[int64][]net.IP{
				1: {
					net.ParseIP("1.1.1.1"),
					net.ParseIP("1.1.1.2"),
				},
				2: {net.ParseIP("2.2.2.2")},
			},
		},
	}

	for _, tc := range tests {
		t.Run(tc.desc, func(t *testing.T) {
			got, err := unmarshalBuildIPMap([]byte(tc.rawJSON))
			if (err != nil) != tc.wantErr {
				t.Errorf("unmarshalBuildIPMap => unexpected error: %v, wantErr: %v", err, tc.wantErr)
			}
			if err != nil {
				return
			}

			if diff := cmp.Diff(tc.want, got); diff != "" {
				t.Errorf("unmarshalBuildIPMap => unexpected diff (-want, +got):\n%s", diff)
			}
		})
	}
}
