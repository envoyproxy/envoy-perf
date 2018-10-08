# Envoy performance tools collection

**Performance benchmarking Options**

Performance benchmarking can take multiple forms:

1. relatively quick (< 1 hour) tests to run locally during development to
   understand perf impact of changes
2. continuous dashboard of perf changes over time, covering a variety of
   realistic deployment scenarios with multiple machines and configurations
3. continuous-integration tests to prevent checking in performance regressions
   -- similar to coverage tests


**Subdirectories**

1. cloudperf/ contains what appears to be an attempt an attempt at measuring
   performance in a realistic multi-machine scenario. However, the insructions
   don't work, and it hasn't been touched in a year (other than moving the
   files).
