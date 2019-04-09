# Nighthawk test origin

A test-origin filter which is capable of generating test responses.

## Testing

```bash
bazel test -c opt //nighthawk/source/server:http_test_origin_filter_integration_test
```

## Building

```bash
bazel build -c opt //nighthawk/source/server:test-origin
```

## Configuring the test origin

```yaml
- name: envoy.fault # Optionally add the fault filter to induce delays on responses.
config:
    max_active_faults: 100
    delay:
    header_delay: {}
    percentage:
        numerator: 100
- name: test-origin   # Insert the test-origin before envoy.router, because order matters!
config:
    key: x-supplied-by
    val: nighthawk-test-origin
```

## Running the test origin


```
# If you already have Envoy running, you might need to set --base-id to allow the test-origin to start.
../bazel-bin/nighthawk/source/server/origin --config-path /path/to/test-origin-origin.yaml

curl -H "x-envoy-fault-delay-request: 2000" -H "x-test-origin-response-size: 1024" testorigin:testport
```

