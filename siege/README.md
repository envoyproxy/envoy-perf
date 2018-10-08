# Envoy simple performance scripts.

**Development-focused benchmarks:**

When updating code in Envoy it is often useful to try to reason about the
performance impact of a change you are making. It is handy to have a suite of
scripts to help measure performance. These scripts should not be used for
absolute benchmarking.

When running performance benchmarks, some basic principles can help give the
best results:

1. Run performance benchmarks on optimized builds: `bazel build -c opt source/exe:envoy-static`.
2. Don't let any other software run on the machine at the same time.
3. Make sure the configuration you are testing actually hits the code you are editing.
4. If you are testing code changes, interleave runs between an envoy-static built from master
   and one built from your branch.

**About Siege:**

Siege is a github project that efficiently pummels an HTTP server with requests and measures
overall throughput, error rate, and max latency.

**Prerequisites:**

You must have python3 and the siege binary installed, either from the distro or by
building from https://github.com/JoeDog/siege.

```shell
sudo apt-get install siege
```

**Building the clean and experimental version of Envoy**

```shell
cd ../envoy
bazel build -c opt source/exe:envoy-static
mv bazel /tmp/envoy.experimental
git checkout master
bazel build -c opt source/exe:envoy-static
mv bazel /tmp/envoy.clean
```

