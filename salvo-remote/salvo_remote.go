// salvo-remote instruments the execution of performance tests on a sandbox
// running remotely on AWS.
package main

import (
	"flag"
	"fmt"
	"os"
)

var buildID = flag.String("build_id", "", "The ID of the AZP build that produced components and binaries for this salvo-remote execution. Can be overridden by providing a different ID in -build_id_override.")
var buildIDOverride = flag.String("build_id_override", "current", "If set to other value than 'current', this overrides the value set via -build_id.")

func main() {
	flag.Parse()
	fmt.Printf("salvo-remote not implemented yet, executed with -build_id %q and -build_id_override %q\n", *buildID, *buildIDOverride)
	os.Exit(1)
}
