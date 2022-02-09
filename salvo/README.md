# Salvo

## What is Salvo

This is a framework that abstracts executing multiple benchmarks of the Envoy Proxy using [Nighthawk](https://github.com/envoyproxy/nighthawk).

## Goals of Salvo

Salvo allows Envoy developers to perform A/B testing to monitor performance change of Envoy. Salvo provides the local excution mode allowing developers to run a benchark on their own machine and also provides the remote excution mode to run a benchmark on a remote machine, such as a remote CI system.

## Dependencies

The [`install_deps.sh`](./install_deps.sh) script can be used to install any dependencies required by Salvo.

## Building Salvo

To build Salvo, use the following command:

```bash
bazel build //...
```

## Benchmark Test Cases for Salvo

Benchmark test cases for Salvo are defined as Python files with test cases written in pytest framework, here is an example: https://github.com/envoyproxy/nighthawk/blob/main/benchmarks/test/test_discovery.py. Users can provide thier own Python files of test cases into Salvo.

## Control Documents

The control document defines the data needed to execute a benchmark. We support the fully dockerized benchmark, the scavenging benchmark and the binary benchmark. 

### Fully Dockerized Benchmark

The Fully Dockerized Benchmark discoveres user supplied tests for execution and uses docker images to run the tests. In the example below, the user supplied tests files are located in `/home/ubuntu/nighthawk_tests` and are mapped to a volume in the docker container.

To run the dockerized benchmark, create a file with the following example contents:

JSON Example:

```json
{
  "remote": false,
  "dockerizedBenchmark": true,
  "images": {
    "reuseNhImages": true,
    "nighthawkBenchmarkImage": "envoyproxy/nighthawk-benchmark-dev:latest",
    "nighthawkBinaryImage": "envoyproxy/nighthawk-dev:latest",
    "envoyImage": "envoyproxy/envoy:v1.21.0"
  },
  "environment": {
    "testVersion": IPV_V4ONLY,
    "envoyPath": "envoy",
    "outputDir": "/home/ubuntu/nighthawk_output",
    "testDir": "/home/ubuntu/nighthawk_tests"
  }
}
```

YAML Example:

```yaml
remote: false
dockerizedBenchmark: true
environment:
  outputDir: '/home/ubuntu/nighthawk_output'
  testDir: '/home/ubuntu/nighthawk_tests'
  testVersion: IPV_V4ONLY
  envoyPath: 'envoy'
images:
  reuseNhImages: true
  nighthawkBenchmarkImage: 'envoyproxy/nighthawk-benchmark-dev:latest'
  nighthawkBinaryImage: 'envoyproxy/nighthawk-dev:latest'
  envoyImage: "envoyproxy/envoy:v1.21.0"
```

`remote`: Whether to enable remote excution mode.

`dockerizedBenchmark`: It will run fully dockerized benchmarks.

`environment.outputDir`: The directory where benchmark results will be placed.

`environment.testDir`: The directory where test case files placed, it's optional. If you want to provide your own test cases, put test files like [this one](https://github.com/envoyproxy/nighthawk/blob/main/benchmarks/test/test_discovery.py) into the testDir.

`environment.testVersion`: Specify the ip address family to use, choose from "IPV_V4ONLY", "IPV_V6ONLY" and "ALL".

`environment.envoyPath`: Envoy is called 'Envoy' in the Envoy Docker image.

`images.reuseNhImages`: Whether to reuse Nighthawk image if it exsists on the machine.

`images.nighthawkBenchmarkImage`: The image of Nighthawk benchmarking tests.   

`images.nighthawkBinaryImage`: Nighthawk tools will be sourced from this Docker image.

`images.envoyImage`: The specific Envoy docker image to test.

In both examples above, the envoy image being tested is a specific tag. This tag can be replaced with "latest" to test the most recently created image against the previous image built from the prior tag. If a commit hash is used, we find the previous commit hash and benchmark that container. In summary, tags are compared to tags, hashes are compared to hashes.

### Scavenging Benchmark

The Scavenging Benchmark builds and runs [Nighthawk benchmark testsuite](https://github.com/envoyproxy/nighthawk/tree/main/benchmarks) on the local machine and uses a specified Envoy image for testing. Tests are discovered in the specified directory in the Environment object:

```yaml
remote: false
scavengingBenchmark: true
environment:
  envoyPath: envoy
  outputDir: /home/ubuntu/nighthawk_output
  testDir: /home/ubuntu/nighthawk_tests
  testVersion: IPV_V4ONLY
images:
  nighthawkBenchmarkImage: envoyproxy/nighthawk-benchmark-dev:latest
  nighthawkBinaryImage: envoyproxy/nighthawk-dev:latest
  envoyImage: envoyproxy/envoy:v1.21.0
  reuseNhImages: true
source:
- identity: SRCID_NIGHTHAWK
  source_url: https://github.com/envoyproxy/nighthawk.git
```

`scavengingBenchmark`: It will run scavenging benchmarks.

`source.identity`: Specify whether this source location is Envoy or Nighthawk.

In this example, the v1.21.0 Envoy tag is pulled and an Envoy image generated where the Envoy binary has profiling enabled. The user may specify option strings supported by bazel to adjust the compilation process.

### Binary Benchmark

The binary benchmark runs an envoy binary as the test target.  The binary is compiled from the source commit specified. As is the case with other benchmarks as well, the previous commit is deduced and a benchmark is executed for these code points. All Nighthawk components are built from source. This benchmark runs on the local host directly.

Example Job Control specification for executing a binary benchmark:

```yaml
remote: false
binaryBenchmark: true
environment:
  outputDir: /home/ubuntu/nighthawk_output
  testDir: /home/ubuntu/nighthawk_tests
  testVersion: IPV_V4ONLY
images:
  nighthawkBenchmarkImage: envoyproxy/nighthawk-benchmark-dev:latest
  nighthawkBinaryImage: envoyproxy/nighthawk-dev:latest
source:
- identity: SRCID_ENVOY
  commit_hash: v1.21.0
  source_url: https://github.com/envoyproxy/envoy.git
  bazelOptions:
  - parameter: --jobs 4
  - parameter: --define tcmalloc=gperftools
- identity: SRCID_NIGHTHAWK
  source_url: https://github.com/envoyproxy/nighthawk.git
```

`binaryBenchmark`: It will run binary benchmarks.

`source.commit_hash`: Specify a commit hash if applicable. If not specified we will determine this from the source tree. We will also use this field to identify the corresponding Nighthawk or Envoy image used for the benchmark.

`source.BazelOption`: A list of compiler options and flags to supply to bazel when building the source of Nighthawk or Envoy. 


## Running Salvo

The resulting 'binary' in the bazel-bin directory can then be invoked with a job control document:

```bash
bazel-bin/salvo --job <path to>/demo_jobcontrol.yaml
```

Salvo creates a symlink in the local directory to the location of the  output artifacts for each Envoy version tested.

## Example Benchmark outputs of Salvo

`nighthawk-human.txt` file provides the human-readable benchmark results from Nighthawk.

```
Nighthawk - A layer 7 protocol benchmarking tool.

benchmark_http_client.latency_2xx (29999 samples)
  min: 0s 000ms 360us | mean: 0s 000ms 546us | max: 0s 010ms 441us | pstdev: 0s 000ms 198us

  Percentile  Count       Value
  0.5         15000       0s 000ms 512us
  0.75        22501       0s 000ms 577us
  0.8         24000       0s 000ms 599us
  0.9         27000       0s 000ms 665us
  0.95        28500       0s 000ms 747us
  0.990625    29718       0s 001ms 029us
  0.99902344  29970       0s 002ms 797us

Queueing and connection setup latency (30000 samples)
  min: 0s 000ms 005us | mean: 0s 000ms 009us | max: 0s 000ms 516us | pstdev: 0s 000ms 003us

  Percentile  Count       Value
  0.5         15007       0s 000ms 009us
  0.75        22505       0s 000ms 010us
  0.8         24000       0s 000ms 011us
  0.9         27000       0s 000ms 012us
  0.95        28500       0s 000ms 014us
  0.990625    29719       0s 000ms 017us
  0.99902344  29971       0s 000ms 027us

Request start to response end (29999 samples)
  min: 0s 000ms 360us | mean: 0s 000ms 545us | max: 0s 010ms 440us | pstdev: 0s 000ms 198us

  Percentile  Count       Value
  0.5         15003       0s 000ms 512us
  0.75        22501       0s 000ms 576us
  0.8         24000       0s 000ms 598us
  0.9         27001       0s 000ms 665us
  0.95        28500       0s 000ms 746us
  0.990625    29718       0s 001ms 028us
  0.99902344  29970       0s 002ms 796us

Response body size in bytes (29999 samples)
  min: 1024 | mean: 1024.0 | max: 1024 | pstdev: 0.0

Response header size in bytes (29999 samples)
  min: 129 | mean: 129.0 | max: 129 | pstdev: 0.0

Blocking. Results are skewed when significant numbers are reported here. (900 samples)
  min: 0s 000ms 059us | mean: 0s 000ms 766us | max: 0s 009ms 460us | pstdev: 0s 000ms 728us

  Percentile  Count       Value
  0.5         450         0s 000ms 673us
  0.75        675         0s 000ms 848us
  0.8         720         0s 000ms 900us
  0.9         810         0s 001ms 108us
  0.95        855         0s 001ms 362us
  0.990625    892         0s 004ms 265us
  0.99902344  900         0s 009ms 460us

Initiation to completion (29999 samples)
  min: 0s 000ms 372us | mean: 0s 000ms 563us | max: 0s 010ms 468us | pstdev: 0s 000ms 201us

  Percentile  Count       Value
  0.5         15002       0s 000ms 528us
  0.75        22500       0s 000ms 595us
  0.8         24001       0s 000ms 618us
  0.9         27000       0s 000ms 687us
  0.95        28500       0s 000ms 770us
  0.990625    29718       0s 001ms 054us
  0.99902344  29970       0s 002ms 868us

Counter                                 Value       Per second
benchmark.http_2xx                      29999       999.97
cluster_manager.cluster_added           1           0.03
default.total_match_count               1           0.03
membership_change                       1           0.03
runtime.load_success                    1           0.03
runtime.override_dir_not_exists         1           0.03
upstream_cx_http1_total                 1           0.03
upstream_cx_rx_bytes_total              35578814    1185960.08
upstream_cx_total                       1           0.03
upstream_cx_tx_bytes_total              2940000     97999.97
upstream_rq_pending_total               1           0.03
upstream_rq_total                       30000       1000.00
```

## Testing Salvo

From the envoy-perf project directory, run the do_ci.sh script with the "test" argument. Since this installs packages packages, it will need to be run as root.

To test Salvo itself, change into the salvo directory and use:

```bash
bazel test //...
```
