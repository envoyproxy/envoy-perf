// salvo-remote instruments the execution of performance tests on a sandbox
// running remotely on AWS.
package main

import (
	"context"
	"flag"
	"fmt"
	"os"

	"github.com/envoyproxy/envoy-perf/salvo-remote/sandboxes"
)

var buildID = flag.Int("build_id", 0, "The ID of the AZP build that produced components and binaries for this salvo-remote execution. Can be overridden by providing a different ID in -build_id_override.")
var buildIDOverride = flag.Int("build_id_override", 0, "If set, it overrides the value set via -build_id.")

// validateFlags validates the provided flag values.
func validateFlags() error {
	if *buildID <= 0 {
		return fmt.Errorf("got -build_id(%d), -build_id must be set to a positive integer", *buildID)
	}
	if *buildIDOverride < 0 {
		return fmt.Errorf("got -build_id_override(%d), -build_id_override cannot be negative.", *buildIDOverride)
	}
	return nil
}

// getBuildID determines what build ID should Salvo execute with.
func getBuildID() int {
	if (*buildIDOverride) != 0 {
		return *buildIDOverride
	}
	return *buildID
}

// sandboxManager abstracts a type that manages sandbox instances.
type sandboxManager interface {
	Start(context.Context, map[sandboxes.Type]sandboxes.Instances) error
}

// runSalvoRemote executes Salvo remotely and returns the exit code.
func runSalvoRemote(sm sandboxManager) error {
	if err := validateFlags(); err != nil {
		return fmt.Errorf("validateFlags => %v", err)
	}

	sbxs := map[sandboxes.Type]sandboxes.Instances{
		sandboxes.TypeDefaultSandboxX64: {getBuildID()},
	}
	ctx := context.Background()

	if err := sm.Start(ctx, sbxs); err != nil {
		return fmt.Errorf("sm.Start => %v", err)
	}
	return nil
}

// mainWithErrCode returns an error code after execution.
func mainWithErrCode() int {
	flag.Parse()
	if err := runSalvoRemote(sandboxes.NewManager()); err != nil {
		fmt.Printf("salvo-remote: %v\n", err)
		return 1
	}
	return 0
}

func main() {
	os.Exit(mainWithErrCode())
}
