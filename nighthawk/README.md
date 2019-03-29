# Nighthawk

*A L7 HTTP protocol family benchmarking tool based on Envoy*

## Current state

The nighthawk client supports HTTP/1.1 and HTTP/2 over HTTP and HTTPS.

HTTPS certificates are not yet validated

## Prerequisites

### Ubuntu

First, follow steps 1 and 2 over at [Quick start Bazel build for developers](https://github.com/envoyproxy/envoy/blob/master/bazel/README.md#quick-start-bazel-build-for-developers).

## Building and testing Nighthawk
```bash
# build it. for best accuracy it is important to specify -c opt.
bazel build -c opt //nighthawk:nighthawk_client

# test it
bazel test -c opt //nighthawk/test:nighthawk_test
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

   -v <trace|debug|info|warn|error|critical>,  --verbosity <trace|debug|info|warn
      |error|critical>
     Verbosity of the output. Possible values: [trace, debug, info, warn,
     error, critical]. The default level is 'warn'.

   --concurrency <string>
     The number of concurrent event loops that should be used. Specify
     'auto' to let Nighthawk leverage all vCPUs that have affinity to the Nighthawk
     process. Note that increasing this results in an effective load multiplier
     combined with the configured --rps and --connections values. Default: 1.

   --h2
     Use HTTP/2

   --timeout <uint64_t>
     Timeout period in seconds used for both connection timeout and grace
     period waiting for lagging responses to come in after the test run is
     done. Default: 5.

   --duration <uint64_t>
     The number of seconds that the test should run. Default: 5.

   --connections <uint64_t>
     The number of connections per event loop that the test should maximally use. Default:
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

```bash
# start the benchmark target (Envoy in this case) on core 3.
$ taskset -c 3 /path/to/envoy --config-path nighthawk/tools/envoy.yaml

# run a quick benchmark using cpu cores 0 and 1.
$ taskset -c 0-1 bazel-bin/nighthawk/nighthawk_client --connections 20 --rps 20000 --duration 5 --concurrency auto -v info http://127.0.0.1:10000/
Nighthawk - A layer 7 protocol benchmarking tool.
[23:11:09.078497][3431][I] [nighthawk/source/client/client.cc:69] Detected 2 (v)CPUs with affinity..
[23:11:09.078521][3431][I] [nighthawk/source/client/client.cc:73] Starting 2 threads / event loops. Test duration: 5 seconds.
[23:11:09.078524][3431][I] [nighthawk/source/client/client.cc:75] Global targets: 40 connections and 40000 calls per second.
[23:11:09.078526][3431][I] [nighthawk/source/client/client.cc:79]    (Per-worker targets: 20 connections and 20000 calls per second)
Merged statistics:
benchmark_http_client.queue_to_connect: Count: 200205. Mean: 0.92 μs. pstdev: 0.79 μs.
  Percentile          Value (usec)
          50%          0.906
          75%          0.928
          90%          0.949
          99%          1.009
        99.9%          1.662
       99.99%         48.649
      99.999%         71.223
         100%         72.327

benchmark_http_client.request_to_response: Count: 200205. Mean: 35.35 μs. pstdev: 38.04 μs.
  Percentile          Value (usec)
          50%         32.745
          75%         33.427
          90%         34.077
          99%         57.885
        99.9%        514.143
       99.99%        1526.65
      99.999%        3703.81
         100%        3737.86

sequencer.blocking: Count: 149. Mean: 70.58 μs. pstdev: 68.95 μs.
  Percentile          Value (usec)
          50%         42.353
          75%         92.499
          90%        157.351
          99%        309.935
        99.9%        317.167
       99.99%        317.167
      99.999%        317.167
         100%        317.167

sequencer.callback: Count: 200205. Mean: 37.08 μs. pstdev: 38.32 μs.
  Percentile          Value (usec)
          50%         34.447
          75%         35.123
          90%         35.789
          99%         60.209
        99.9%        523.807
       99.99%         1532.1
      99.999%        3707.26
         100%        3741.44


Merged counters
counter client.benchmark.http_2xx:200207
counter client.upstream_cx_http1_total:40
counter client.upstream_cx_rx_bytes_total:721345821
counter client.upstream_cx_total:40
counter client.upstream_cx_tx_bytes_total:12012420
counter client.upstream_rq_pending_total:40
counter client.upstream_rq_total:200207
[23:11:14.175907][3431][I] [nighthawk/source/client/client.cc:213] Done. Wrote measurements/1553811074141331579.json.
```

Nighthawk will create a directory called `measurements/` and log results in json format there.
The name of the file will be `<epoch.json>`, which contains:

- The start time of the test, and a serialization of the Nighthawk options involved.
- The mean latency and the observed standard deviation.
- Latency percentiles produced by HdrHistogram.

## Accuracy and repeatability considerations when using the Nighthawk client.

- Processes not related to the benchmarking task at hand may add significant noise. Consider stopping any
  processes that are not needed. 
- Be aware that power state management and CPU Frequency changes are able to introduce significant noise.
  When idle, Nighthawk uses a busy loop to achieve precise timings when starting requests, which helps minimize this.
  Still, consider disabling c-state changes in the system BIOS.
- Be aware that CPU Thermal throttling may skew results.
- Consider using `taskset` to isolate client and server. On machines with multiple physical CPU's there is a choice here.
  You can partition client and server on the same physical processor, or run each of them on a different physical CPU.
- Consider disabling hyper-threading.
- Consider tuning the benchmarking system for low latency (manually, or with tuned).
  - TODO(oschaaf): link resources.
- When using Nighthawk with concurrency > 1 or multiple connections, workers may produce significantly different results. That can happen because of various reasons:
  - Server fairness. For example, connections may end up being serviced by the same server thread, or not.
  - One of the clients may be unlucky and structurally spend time waiting on requests from the other(s)
    being serviced due to interference of request release timings and server processing time.
- Consider using separate machines for the clients and server(s).
