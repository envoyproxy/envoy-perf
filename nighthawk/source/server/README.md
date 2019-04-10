# Nighthawk test server

A test-server filter which is capable of generating test responses.

## Testing

```bash
bazel test -c opt //nighthawk/source/server:http_test_server_filter_integration_test
```

## Building

```bash
bazel build -c opt //nighthawk/source/server:test-server
```

## Configuring the test server

```yaml
- name: envoy.fault # Optionally add the fault filter to induce delays on responses.
config:
    max_active_faults: 100
    delay:
    header_delay: {}
    percentage:
        numerator: 100
- name: test-server   # Insert the test-server before envoy.router, because order matters!
config:
    key: x-supplied-by
    val: nighthawk-test-server
```

## Running the test server


```
# If you already have Envoy running, you might need to set --base-id to allow the test-server to start.
../bazel-bin/nighthawk/source/server/server --config-path /path/to/test-server-server.yaml

curl -H "x-envoy-fault-delay-request: 2000" -H "x-test-server-response-size: 1024" testserver:testport
```

