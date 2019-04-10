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

`test-server.yaml` sample content

```yaml
static_resources:
  listeners:
  # define an origin server on :10000 that always returns "lorem ipsum..."
  - address:
      socket_address:
        address: 0.0.0.0
        port_value: 10000
    filter_chains:
    - filters:
      - name: envoy.http_connection_manager
        config: 
          generate_request_id: false
          codec_type: auto
          stat_prefix: ingress_http
          route_config:
            name: local_route
            virtual_hosts:
            - name: service
              domains:
              - "*"
          http_filters:
          - name: envoy.fault
            config:
              max_active_faults: 100
              delay:
                header_delay: {}
                percentage:
                  numerator: 100
          - name: test-server   # before envoy.router because order matters!
            config:
              response_size: 10
              response_headers:
              - { header: { key: "foo", value: "bar"} }
              - { header: { key: "foo", value: "bar2"}, append: true }
              - { header: { key: "x-nh", value: "1"}}
          - name: envoy.router
            config:
              dynamic_stats: false
admin:
  access_log_path: /tmp/envoy.log
  address:
    socket_address:
      address: 0.0.0.0
      port_value: 8081
```

## Running the test server


```
# If you already have Envoy running, you might need to set --base-id to allow the test-server to start.
➜ /bazel-bin/nighthawk/source/server/server --config-path /path/to/test-server-server.yaml

# Verify the test server with a curl command similar to:
➜ curl -H "x-envoy-fault-delay-request: 1" -H "x-nighthawk-test-server-config: {response_size:20}"  -X POST --data "fooooo" -vv 127.0.0.1:10000 
Note: Unnecessary use of -X or --request, POST is already inferred.
* Rebuilt URL to: 127.0.0.1:10000/
*   Trying 127.0.0.1...
* TCP_NODELAY set
* Connected to 127.0.0.1 (127.0.0.1) port 10000 (#0)
> POST / HTTP/1.1
> Host: 127.0.0.1:10000
> User-Agent: curl/7.58.0
> Accept: */*
> x-envoy-fault-delay-request: 1
> x-nighthawk-test-server-config: {response_size:20}
> Content-Length: 6
> Content-Type: application/x-www-form-urlencoded
> 
* upload completely sent off: 6 out of 6 bytes
< HTTP/1.1 200 OK
< content-length: 20
< content-type: text/plain
< foo: bar
< foo: bar2
< x-nh: 1
< date: Wed, 10 Apr 2019 21:54:21 GMT
< server: envoy
< 
* Connection #0 to host 127.0.0.1 left intact
aaaaaaaaaaaaaaaaaaaa
```

