# Maintainers

This document provides maintenance procedures to assist maintainers.

## Updates to the Envoy and Nighthawk dependency for Salvo

Salvo reuses large parts of Envoy's and Nighthawk's build system and codebase, so keeping Salvo up
to date with Envoy's and Nighthawk's changes is an important maintenance task. When performing the
update, follow this procedure:

1. Create a fork of Salvo, or fetch upstream and merge changes into your fork if you already have
one.
1. Create a new branch from `main`, e.g. `envoy-update`.
1. Sync (copy) [.bazelrc](.bazelrc) from
   [Nighthawk's version](https://github.com/envoyproxy/nighthawk/blob/main/.bazelrc) to
   update our build configurations. Be sure to retain our local modifications,
   all lines that are unique to Salvo are marked with comment `# Salvo unique`.
1. Sync (copy) [ci/run_envoy_docker.sh](ci/run_envoy_docker.sh) from
   [Envoy's version](https://github.com/envoyproxy/envoy/blob/main/ci/run_envoy_docker.sh).
   Be sure to retain our local modifications, all lines that are unique to
   Salvo are marked with comment `# Salvo unique`.
1. Sync (copy) [ci/envoy_build_sha.sh](ci/envoy_build_sha.sh) from
   [Envoy's version](https://github.com/envoyproxy/envoy/blob/main/ci/envoy_build_sha.sh).
   Be sure to retain our local modifications, all lines that are unique to
   Salvo are marked with comment `# Salvo unique`.
1. Run `ci/do_ci.sh test`. Sometimes the dependency update comes with changes
   that break our build. Include any changes required to Salvo to fix that
   in the same PR.
1. If the PR ends up modifying any python files, execute `ci/do_ci.sh fix_format`
   to reformat the files and avoid a CI failure.
1. Create a PR with a title like `Update Envoy to 9753819 (Jan 24th 2021)`,
   describe all performed changes in the PR's description.