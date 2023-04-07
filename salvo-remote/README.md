# Remote execution of Salvo

This directory contains scripts, code and configuration related to the remote
execution mode of Salvo.

## What is Salvo

Salvo is a performance measurement framework primarily aimed at tracking the
long-term performance of the [Envoy proxy](https://www.envoyproxy.io/).

## Engineering documentation

The following documents outline the requirements for and design of Salvo.

- [Requirements](https://docs.google.com/document/d/1mAma-ksRN0OIBInoZKUdjdaIhK2nTQxFnCujq2fKi4E/edit).
- [Design
  document](https://docs.google.com/document/d/1Qfueli357u4QgOb-7-8RL98N0XnMeu2k6VJDoUwN0A4/edit?resourcekey=0-AyeFMQHHiuajx8JK2w_yfA).
- [Definition of the Minimum Viable Product
  (MVP)](https://docs.google.com/document/d/15auKcxLfw8iILL7EF4tJ8VrnHce6KiZvd9tzWweT0DY/edit).
- [Roadmap](https://docs.google.com/document/d/1LIWYuEaS4wwbmbaWj7cSsDzda3-o4ia-LN-bnfI94Yc/edit).
- [Design pivot to direct VM
  execution](https://docs.google.com/document/d/1auXzV-AEXgMzbtdG06XlZ2d9X5l_XadMheA9h51E7yc/edit).

## Current status

Salvo's
[MVP](https://docs.google.com/document/d/15auKcxLfw8iILL7EF4tJ8VrnHce6KiZvd9tzWweT0DY/edit)
is in development. Project status can be seen in the task list and the Gantt
chart:

- [Task
  list](https://app.asana.com/read-only/Salvo-MVP/1203151608185622/c3a265ce3aaf6f108ff846613c1dd8e9/list)
- [Gantt
  chart](https://app.asana.com/read-only/Salvo-MVP-Gantt/1203151608185622/3630497a685762a972cc33e16803be5c/timeline)

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

## Contributions

Contributions to Salvo on all levels, whether design, code or testing are
welcome. Please contact us if you would like to participate.

## Contact details

### People

- Project lead: Jakub Sobon ([mum4k](https://github.com/mum4k))
  (mumak@google.com)
- Contributor: Fei Deng ([fei-deng](https://github.com/fei-deng))
- Contributor: Xin Huang [gyohuangxin](https://github.com/gyohuangxin)

### Slack channels

You can also reach out to us on [Envoy Slack](envoyproxy.slack.com) in channel
`#salvo`.
