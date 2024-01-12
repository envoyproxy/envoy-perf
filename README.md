# Envoy performance tools collection

[![OpenSSF Scorecard](https://api.securityscorecards.dev/projects/github.com/envoyproxy/envoy-perf/badge)](https://securityscorecards.dev/viewer/?uri=github.com/envoyproxy/envoy-perf)

## Performance benchmarking Options

Performance benchmarking can take multiple forms:

1. relatively quick (< 1 hour) tests to run locally during development to
   understand perf impact of changes
2. continuous dashboard of perf changes over time, covering a variety of
   realistic deployment scenarios with multiple machines and configurations
3. continuous-integration tests to prevent checking in performance regressions
   -- similar to coverage tests


## Subdirectories

1. [cloudperf/](cloudperf/README.md) contains what appears to be an attempt
   at measuring performance in a realistic multi-machine
   scenario. However, the instructions don't work, and it hasn't been touched in
   a year (other than moving the files).
2. [siege/](siege/README.md) contains an initial attempt at a simple test to run
   iteratively during development to get a view of the time/space impact of the
   changes under configuration.
2. [salvo/](salvo/README.md) contains a framework that abstracts nighthawk 
   benchmark execution. This is still under active development
