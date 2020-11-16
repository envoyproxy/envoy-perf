# Salvo

This is a framework that abstracts executing multiple benchmarks of the Envoy Proxy using [NightHawk](https://github.com/envoyproxy/nighthawk).

## Example Control Documents

The control document defines the data needed to execute a benchmark. At the moment, the fully dockerized benchmark is the only one supported. This benchmark discoveres user supplied tests for execution and uses docker images to run the tests. In the example below, the user supplied tests files are located in `/home/ubuntu/nighthawk_tests` and are mapped to a volume in the docker container.

To run the benchmark, create a file with the following example contents:

JSON Example:

```json
{
  "remote": false,
  "dockerizedBenchmark": true,
  "images": {
    "reuseNhImages": true,
    "nighthawkBenchmarkImage": "envoyproxy/nighthawk-benchmark-dev:latest",
    "nighthawkBinaryImage": "envoyproxy/nighthawk-dev:latest",
    "envoyImage": "envoyproxy/envoy-dev:f61b096f6a2dd3a9c74b9a9369a6ea398dbe1f0f"
  },
  "environment": {
    "testVersions": IPV_V4ONLY,
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
  envoyPath: 'envoy'
  outputDir: '/home/ubuntu/nighthawk_output'
  testDir: '/home/ubuntu/nighthawk_tests'
  testVersions: IPV_V4ONLY
images:
  reuseNhImages: true
  nighthawkBenchmarkImage: 'envoyproxy/nighthawk-benchmark-dev:latest'
  nighthawkBinaryImage: 'envoyproxy/nighthawk-dev:latest'
  envoyImage: "envoyproxy/envoy-dev:f61b096f6a2dd3a9c74b9a9369a6ea398dbe1f0f"
```

In both examples, the envoy image being tested is a specific hash. This hash can be replaced with "latest" to test the most recently created image against the previous image built from the prior Envoys master commit.

## Building Salvo

```bash
bazel build //:salvo
```

## Running Salvo

```bash
bazel-bin/salvo --job ~/test_data/demo_jobcontrol.yaml
```

## Testing Salvo


From the root package directory, run the do_ci.sh script with the "test" argument. Since this installs packages packages, it will need to be run as root.
```bash
bazel test //src/...
```

## Dependencies

The `install_deps.sh` script will install any dependencies needed to run salvo. 

* python 3.6+
* git
* docker
* tuned/tunedadm (eventually)
