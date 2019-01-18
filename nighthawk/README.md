# Nighthawk PoC

*A benchmarking tool based on Envoy*

## Current state

This project is in proof-of-concept mode. Supports HTTP/1.1 and HTTP/2 over http
and https.

NOTE: https certificates are not validated.


## Building and running the benchmark


```bash
# TODO(oschaaf): Collect and list prerequisites. Currently mostly the same as envoy.
# build it
bazel build //:nighthawk_client

# test it
bazel test //test:nighthawk_test

# start envoy
➜ taskset -c 0-1 /path/to/envoy --config-path tools/envoy.yaml

# run a benchmark
➜ taskset -c 2-4 bazel-bin/nighthawk_client --concurrency auto --rps 500 --connections 1 --duration 5 http://127.0.0.1:10000/ 
[14:20:40.724350][011494][I] [source/client/client.cc:110] Detected 3 (v)CPUs with affinity..
[14:20:40.724394][011494][I] [source/client/client.cc:114] Starting 3 threads / event loops. Test duration: 5 seconds.
[14:20:40.724401][011494][I] [source/client/client.cc:116] Global targets: 3 connections and 1500 calls per second.
[14:20:40.724405][011494][I] [source/client/client.cc:120]    (Per-worker targets: 1 connections and 500 calls per second)
[14:20:45.726344][011495][I] [source/client/client.cc:207] > worker 0: 499.80/second. Mean: 84.56μs. Stdev: 4.08μs. Connections good/bad/overflow: 1/0/0. Replies: good/fail:2500/0. Stream resets: 0. 
[14:20:45.726340][011496][I] [source/client/client.cc:207] > worker 1: 499.80/second. Mean: 85.28μs. Stdev: 3.95μs. Connections good/bad/overflow: 1/0/0. Replies: good/fail:2500/0. Stream resets: 0. 
[14:20:45.726586][011497][I] [source/client/client.cc:207] > worker 2: 499.80/second. Mean: 85.26μs. Stdev: 2.42μs. Connections good/bad/overflow: 1/0/0. Replies: good/fail:2500/0. Stream resets: 0. 
[14:20:45.726708][011494][I] [source/client/client.cc:227] Global complete:7497. Mean: 85.03μs. Stdev: 3.58μs.
[14:20:45.727550][011494][I] [source/client/client.cc:242] Done. Run 'tools/stats.py res.txt benchmark' for hdrhistogram.

➜ tools/stats.py res.txt benchmark
Uncorrected hdr histogram percentiles (us)
p50: 84
p75: 85
p90: 86
p99: 97
p99.9: 108
p99.99: 204
p99.999: 216
p100: 216
min: 76.821
max: 216.201
mean: 85.03485487528344
median: 84.581
var: 12.824523210792997
stdev: 3.5811343469343617




```

## CLI arguments

```
➜ bazel-bin/nighthawk_client --help

USAGE:

   bazel-bin/nighthawk_client  [-v <trace|debug|info|warn|error>]
                               [--concurrency <string>] [--h2] [--timeout
                               <uint64_t>] [--duration <uint64_t>]
                               [--connections <uint64_t>] [--rps
                               <uint64_t>] [--] [--version] [-h] <uri
                               format>


Where:

   -v <trace|debug|info|warn|error>,  --verbosity <trace|debug|info|warn
      |error>
     Verbosity of the output. Possible values: [trace, debug, info, warn,
     error, critical]. The default level is 'info'.

   --concurrency <string>
     The number of concurrent event loops that should be used. Specify
     'auto' to let nighthawk run leverage all (aligned) vCPUs. Note that
     increasing this effectively multiplies configured --rps and
     --connection values. Default: 1.

   --h2
     Use HTTP/2

   --timeout <uint64_t>
     Timeout period in seconds used for both connection timeout and grace
     period waiting for lagging responses to come in after the test run is
     done. Default: 5.

   --duration <uint64_t>
     The number of seconds that the test should run. Default: 5.

   --connections <uint64_t>
     The number of connections that the test should maximally use. Default:
     1.

   --rps <uint64_t>
     The target requests-per-second rate. Default: 5.

   --,  --ignore_rest
     Ignores the rest of the labeled arguments following this flag.

   --version
     Displays version information and exits.

   -h,  --help
     Displays usage information and exits.

   <uri format>
     (required)  uri to benchmark. http:// and https:// are supported, but
     in case of https no certificates are validated.


   Nighthawk is a web server benchmarking tool.
```

## Development

At the moment the PoC incorporates a .vscode. This has preconfigured tasks
and launch settings to build the benchmarking client and tests, as well us
run tests. It also provides the right settings for intellisense and wiring up
the IDE for debugging. 
