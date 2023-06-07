package main

import (
	"context"
	"errors"
	"strings"
	"testing"

	"github.com/envoyproxy/envoy-perf/salvo-remote/sandboxes"
	"github.com/google/go-cmp/cmp"
)

// fakeSandboxManager is a fake sandboxes.Manager implementation.
type fakeSandboxManager struct {
	// startOut is the output to return when Start is called.
	startOut map[int64]*sandboxes.Instance
	// startErr is the error to return when Start is called.
	startErr error

	// sbxs are the sandbox instances used when Start() was called.
	sbxs map[sandboxes.Type]sandboxes.Instances
}

func newFakeSandboxManager(startOut map[int64]*sandboxes.Instance, startErr error) *fakeSandboxManager {
	return &fakeSandboxManager{
		startOut: startOut,
		startErr: startErr,
	}
}

func (fsm *fakeSandboxManager) Start(ctx context.Context, sbxs map[sandboxes.Type]sandboxes.Instances) (map[int64]*sandboxes.Instance, error) {
	fsm.sbxs = sbxs
	return fsm.startOut, fsm.startErr
}

func TestRunSalvoRemote(t *testing.T) {
	tests := []struct {
		desc            string
		buildID         int64
		buildIDOverride int64
		fakeSMStartErr  error
		wantSbxs        map[sandboxes.Type]sandboxes.Instances
		wantErrSubstr   string
	}{
		{
			desc:          "fails when -build_id negative",
			buildID:       -1,
			wantErrSubstr: "build_id must be set to a positive",
		},
		{
			desc:          "fails when -build_id zero",
			buildID:       0,
			wantErrSubstr: "build_id must be set to a positive",
		},
		{
			desc:            "fails when -build_id_override negative",
			buildID:         12345,
			buildIDOverride: -1,
			wantErrSubstr:   "build_id_override cannot be negative",
		},
		{
			desc:           "fails when Start fails",
			buildID:        12345,
			fakeSMStartErr: errors.New("fake error"),
			wantSbxs: map[sandboxes.Type]sandboxes.Instances{
				sandboxes.TypeDefaultSandboxX64: {12345},
			},
			wantErrSubstr: "sm.Start =>",
		},
		{
			desc:    "starts sandbox with -build_id",
			buildID: 12345,
			wantSbxs: map[sandboxes.Type]sandboxes.Instances{
				sandboxes.TypeDefaultSandboxX64: {12345},
			},
		},
		{
			desc:            "starts sandbox with -build_id_override",
			buildID:         12345,
			buildIDOverride: 67890,
			wantSbxs: map[sandboxes.Type]sandboxes.Instances{
				sandboxes.TypeDefaultSandboxX64: {67890},
			},
		},
	}

	for _, tc := range tests {
		t.Run(tc.desc, func(t *testing.T) {
			*buildID = tc.buildID
			*buildIDOverride = tc.buildIDOverride

			fsm := newFakeSandboxManager(map[int64]*sandboxes.Instance{}, tc.fakeSMStartErr)
			err := runSalvoRemote(fsm)
			if (err != nil) != (tc.wantErrSubstr != "") {
				t.Errorf("runSalvoRemote => unexpected error %v, wantErrSubstr: %q", err, tc.wantErrSubstr)
			}
			if err != nil && !strings.Contains(err.Error(), tc.wantErrSubstr) {
				t.Errorf("runSalvoRemote => unexpected error text, got:%q, want substring: %q", err, tc.wantErrSubstr)

			}

			if diff := cmp.Diff(tc.wantSbxs, fsm.sbxs); diff != "" {
				t.Errorf("runSalvoRemote => unexpected sandbox instances started, diff (-want, +got):\n%s", diff)
			}
		})
	}
}
