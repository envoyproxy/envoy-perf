// salvo-remote instruments the execution of performance tests on a sandbox
// running remotely on AWS.
package main

import (
	"flag"
	"fmt"
	"os"
)

var buildID = flag.String("build_id", "", "The ID of the AZP build that produced components and binaries for this salvo-remote execution.")

func main() {
	flag.Parse()
	fmt.Printf("salvo-remote not implemented yet, executed with -build_id %q\n", *buildID)
	os.Exit(1)
}
