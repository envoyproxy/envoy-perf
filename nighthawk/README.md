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
# build it
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

   -v <trace|debug|info|warn|error>,  --verbosity <trace|debug|info|warn
      |error>
     Verbosity of the output. Possible values: [trace, debug, info, warn,
     error, critical]. The default level is 'info'.

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

# run a benchmark on cores 0 and 1
$ nighthawk taskset -c 0-1 bazel-bin/nighthawk/nighthawk_client --duration 5 --rps 20000 --concurrency auto http://127.0.0.1:10000/
[09:37:12.960525][23146][I] [nighthawk/source/client/client.cc:85] Detected 2 (v)CPUs with affinity..
[09:37:12.960571][23146][I] [nighthawk/source/client/client.cc:89] Starting 2 threads / event loops. Test duration: 5 seconds.
[09:37:12.960573][23146][I] [nighthawk/source/client/client.cc:91] Global targets: 2 connections and 40000 calls per second.
[09:37:12.960575][23146][I] [nighthawk/source/client/client.cc:95]    (Per-worker targets: 1 connections and 20000 calls per second)
[09:37:17.984787][23147][I] [nighthawk/source/client/client.cc:158] > worker 0: 19999.89/second. Mean: 28.37μs. Stdev: 6.22μs. Connections good/bad/overflow: 1/0/0. Replies: good/fail:100001/0. Stream resets: 0. 
[09:37:17.984839][23148][I] [nighthawk/source/client/client.cc:158] > worker 1: 19999.88/second. Mean: 30.95μs. Stdev: 5.52μs. Connections good/bad/overflow: 1/0/0. Replies: good/fail:100001/0. Stream resets: 0. 
[09:37:17.985595][23146][I] [nighthawk/source/client/client.cc:178] Global #complete:200000. Mean: 29.66μs. Stdev: 6.02μs.
[09:37:17.985601][23146][I] [nighthawk/source/common/statistic_impl.cc:142] Hdr Latencies (uncorrected).
[09:37:17.985603][23146][I] [nighthawk/source/common/statistic_impl.cc:143]   Percentile        Latency (us)
[09:37:17.985644][23146][I] [nighthawk/source/common/statistic_impl.cc:151]           50%         29.791
[09:37:17.985720][23146][I] [nighthawk/source/common/statistic_impl.cc:151]           75%         30.223
[09:37:17.985761][23146][I] [nighthawk/source/common/statistic_impl.cc:151]           90%         30.943
[09:37:17.985840][23146][I] [nighthawk/source/common/statistic_impl.cc:151]           99%         55.263
[09:37:17.985911][23146][I] [nighthawk/source/common/statistic_impl.cc:151]         99.9%         90.111
[09:37:17.986055][23146][I] [nighthawk/source/common/statistic_impl.cc:151]        99.99%        176.383
[09:37:17.986156][23146][I] [nighthawk/source/common/statistic_impl.cc:151]       99.999%        380.671
[09:37:17.986257][23146][I] [nighthawk/source/common/statistic_impl.cc:151]          100%        426.751
[09:37:17.987423][23146][I] [nighthawk/source/client/client.cc:202] Done. Wrote measurements/1549960637987376677.json.
```

Nighthawk will create a directory called `measurement/` and log results in json format there.
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
- Consider tuning the benchmarking system for low latency
  - Tuning the system manually, or with tuned.
  - TODO(oschaaf): link resources.
- When using Nighthawk with concurrency > 1 or multiple connections, workers may produce significantly different
  results for various reasons:
  - Server fairness. For example, connections may end up being serviced by the same server thread, or not.
  - One of the clients may be unlucky and spend time waiting on requests from the other(s)
    being serviced.
  - Nighthawk makes an effort to delay the start of each worker so that from a global perspective
    requests will end up evenly spaced in time. This step isn't very sophisticated at the moment,
    and any noise during this step may cause irregularities in request timings.
- Finally, consider using two machines to completely isolate client and server.
  
  
