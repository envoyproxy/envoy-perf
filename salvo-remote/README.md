# Remote execution of Salvo

This directory contains scripts, code and configuration related to the remote
execution mode of Salvo.

## What is Salvo

Salvo is a performance measurement framework primarily aimed at tracking the
long-term performance of the [Envoy proxy](https://www.envoyproxy.io/).

## Engineering documentation

The following documents outline the requirements for and design of Salvo.

- [Requirements](https://1drv.ms/w/c/41f5e3e2a47dacf2/EdqGBqz-dPtDmGfI7d6yLg4BPicDimc6mScj-sehZ_jGsg?e=zg9F4G).
- [Design
  document](https://1drv.ms/w/c/41f5e3e2a47dacf2/EZZJ8DIs84JPm_GjW9PEAtgBVYu_uY9hEnLQCoZwR4YJBg?e=FESTxo).
- [Definition of the Minimum Viable Product
  (MVP)](https://1drv.ms/w/c/41f5e3e2a47dacf2/EYgOE6itYKhPgRG9pxuv6qkBzVhjHpqU2D814G7sSnFaZA?e=3LEHSu).
- [Roadmap](https://1drv.ms/w/c/41f5e3e2a47dacf2/ERIlwSS0DA5MixuqAFofrp0BAPuwt_fqjnAs2r7PF05G0Q?e=RxvTAl).
- [Design pivot to direct VM
  execution](https://1drv.ms/w/c/41f5e3e2a47dacf2/EQtPDYrP2oNMmLP7Ajn38bYBGuIRGT5vvmaW5BaC8M-Lvg?e=n5irug).

## Current status

Salvo's
[MVP](https://1drv.ms/w/c/41f5e3e2a47dacf2/EYgOE6itYKhPgRG9pxuv6qkBzVhjHpqU2D814G7sSnFaZA?e=3LEHSu)
is in development.

## Overview

Salvo is a framework that reuses existing components:

- [Nighthawk](https://github.com/envoyproxy/nighthawk) is used as the load
  generator.
- [Nighthawk's test
  server](https://github.com/envoyproxy/nighthawk/tree/main/source/server) is
  used as the fake backend.
- [Envoy](https://github.com/envoyproxy/envoy) is the system under test.
- [Nighthawk's benchmarking test
  suite](https://github.com/envoyproxy/nighthawk/tree/main/benchmarks) is used
  to execute individual test cases.
- [An Azure
  pipeline](https://github.com/envoyproxy/envoy-perf/tree/main/salvo-remote/azure-pipelines)
  is used to build binaries and test components.
- The infrastructure and individual test sandboxes run on AWS.

### Code locations

Salvo's code and configuration is split into multiple locations and
repositories:

- The [salvo](../salvo) directory in this repository stores code that is used
  for local execution of Salvo.
- This (the `salvo-remote`) directory contains code and configuration related
  to the remote execution of Salvo. The directory content deals with the
  instrumentation of individual test sandboxes and test runs, i.e. resources
  that are started for a run and terminated afterwards.
- The [envoyproxy/ci-infra](https://github.com/envoyproxy/ci-infra) repository
  contains code and configurations related to the remote execution of Salvo.
  The directory deals with the common (always-on) infrastructure that Salvo
  uses across all the remote executions.

### Building salvo-remote

#### Install dependencies

- Install [bazelisk](https://github.com/bazelbuild/bazelisk).


#### Build salvo-remote

```sh
bazel build ...
```

#### Run salvo-remote unit tests

```sh
bazel test ...
```

## Contributions

Contributions to Salvo on all levels, whether design, code or testing are
welcome. Please contact us if you would like to participate.

## Contact details

### People

- Project lead: Jakub Sobon ([mum4k](https://github.com/mum4k))
  (mumak@google.com)
- Contributor: Fei Deng ([fei-deng](https://github.com/fei-deng))
- Contributor: Xin Huang ([gyohuangxin](https://github.com/gyohuangxin))

### Slack channels

You can also reach out to us on [Envoy Slack](https://envoyproxy.slack.com) in
channel `#salvo`.
