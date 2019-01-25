# Nighthawk

*A L7 HTTP protocol family benchmarking tool based on Envoy*

## Current state

The nighthawk client supports HTTP/1.1 and HTTP/2 over HTTP and HTTPS.

HTTPS certificates are not yet validated

## Prerequisites

### Ubuntu

First, follow steps 1 and 2 over at [Quick start Bazel build for developers](https://github.com/envoyproxy/envoy/blob/master/bazel/README.md#quick-start-bazel-build-for-developers).


### Optionally (for hdrhistogram)


```bash
sudo apt-get install python3 python3-pip
sudo pip3 install hdrhistogram jsonpickle
```

## Building and testing Nighthawk
```bash
# build it
bazel build -c opt //:nighthawk_client

# test it
bazel test -c opt //test:nighthawk_test
```

## Using the Nighthawk client

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
     'auto' to let Nighthawk run leverage all (aligned) vCPUs. Note that
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


   Nighthawk, a L7 HTTP protocol family benchmarking tool.
```

## Sample benchmark run

```zsh
# start envoy on core 2
$ taskset -c 3 /path/to/envoy --config-path tools/envoy.yaml

# run the benchmark on cores 0 and 1
$ taskset -c 0-1 bazel-bin/nighthawk_client --concurrency auto --rps 30000 --connections 1 --duration 3 http://127.0.0.1:10000/ && tools/stats.py res.txt benchmark
[15:58:16.907520][032275][I] [source/client/client.cc:110] Detected 2 (v)CPUs with affinity..
[15:58:16.907555][032275][I] [source/client/client.cc:114] Starting 2 threads / event loops. Test duration: 3 seconds.
[15:58:16.907558][032275][I] [source/client/client.cc:116] Global targets: 2 connections and 60000 calls per second.
[15:58:16.907559][032275][I] [source/client/client.cc:120]    (Per-worker targets: 1 connections and 30000 calls per second)
[15:58:19.908829][032277][I] [source/client/client.cc:199] > worker 1: 29999.99/second. Mean: 25.48μs. Stdev: 3.14μs. Connections good/bad/overflow: 1/0/0. Replies: good/fail:90001/0. Stream resets: 0. 
[15:58:19.908837][032276][I] [source/client/client.cc:199] > worker 0: 29986.44/second. Mean: 32.74μs. Stdev: 3.50μs. Connections good/bad/overflow: 1/0/0. Replies: good/fail:89961/0. Stream resets: 0. 
[15:58:19.908973][032275][I] [source/client/client.cc:219] Global #complete:179960. Mean: 29.11μs. Stdev: 4.92μs.
[15:58:19.928943][032275][I] [source/client/client.cc:234] Done. Run 'tools/stats.py res.txt benchmark' for hdrhistogram.
Uncorrected hdr histogram percentiles (us)
p50: 27
p75: 32
p90: 33
p99: 42
p99.9: 66
p99.99: 102
p99.999: 268
p100: 344
min: 21.446
max: 344.251
mean: 29.110338769726607
median: 27.6875
var: 24.221109683905244
stdev: 4.921494659542489
```

