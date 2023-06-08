// json.go contains functions that unmarshal JSON messages received from Terraform.
package sandboxes

import (
	"encoding/json"
	"fmt"
	"net"
	"strconv"
)

// unmarshalBuildIPMap unmarshals a map of build IDs to IP addresses.
func unmarshalBuildIPMap(rawJSON []byte) (map[int64][]net.IP, error) {
	buildIPs := map[string][]string{}
	if err := json.Unmarshal(rawJSON, &buildIPs); err != nil {
		return nil, fmt.Errorf("json.Unmarshal => %v", err)
	}

	res := map[int64][]net.IP{}
	for idStr, ips := range buildIPs {
		id, err := strconv.ParseInt(idStr, 10, 64)
		if err != nil {
			return nil, fmt.Errorf("unable to convert build ID %q to an integer: %v", idStr, err)
		}

		if id < 1 {
			return nil, fmt.Errorf("parsed invalid build ID %d, expected a positive integer", id)
		}
		if len(ips) == 0 {
			return nil, fmt.Errorf("build ID %d has no IP addresses", id)
		}

		for _, ipStr := range ips {
			ip := net.ParseIP(ipStr)
			if ip == nil {
				return nil, fmt.Errorf("in build ID %d, unable to parse %q as an IP address", id, ipStr)
			}
			res[id] = append(res[id], ip)
		}
	}
	return res, nil
}
