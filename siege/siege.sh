#!/bin/bash
#
# Compares throughput from two different versions of Envoy, with multiple
# interleaved iterations. The two binaries are supplied on the commmand-line:
#
# Usage:
#    siege.sh clean_envoy_binary experimental_envoy_binary output_dir
#
# The two binaries should generally be built with
#     bazel build -c opt source/exe:envoy-static
# and can then be copied to a safe place (e.g. /tmp) so that they can each
# be based on a single git workspace that you flip between branches.
#
# output_dir is where the logs and raw CSV files get written, but the
# the summarized performance data is printed as a table to stdout.
#
# TODO(jmarantz): rewrite in Python.

set -e
set -u

if [ $# != 3 ]; then
  echo Usage: $0 clean_envoy_binary experimental_envoy_binary output_dir
  exit 1
fi

# Capture arguments as locals for readability.
clean_envoy="$1"
experimental_envoy="$2"
outdir="$3"
aggregate_csv="$outdir/aggregate.csv"

# Connect to the script directory so local references to the yaml configs and
# lorem_ipsum.txt work.
siege_dir=$(dirname $(realpath $0))
cd "$siege_dir"

# Derive some temp filenames from $outdir.
log="$outdir/siege.log"
clean_perf_csv="$outdir/clean.perf.csv"
clean_mem_csv="$outdir/clean.mem.csv"
clean_csv_files="$clean_perf_csv $clean_mem_csv"
experimental_perf_csv="$outdir/experimental.perf.csv"
experimental_mem_csv="$outdir/experimental.mem.csv"
experimental_csv_files="$experimental_perf_csv $experimental_mem_csv"
aggregate_csv="$outdir/aggregate.csv"
csv_files="$clean_csv_files $experimental_csv_files $aggregate_csv"

# TODO(jmarantz): make the configuration pluggable, which means grepping
# for these ports rather than hardcoding them. It's annoying to grep in
# yaml files because there isn't per-line context. Another possibility
# is to scrape them from Envoy log output.
proxy_port=10001
upstream_port=10000
admin_port=8081

envoy_conf="$siege_dir/front-proxy.yaml"
upstream_url="http://127.0.0.1:$upstream_port"
proxy_url="http://127.0.0.1:$proxy_port"

# Siege sometimes hangs when using time-based exit criteria.  See
# https://github.com/JoeDog/siege/issues/66.  In the meantime, use
# repetitions, which don't have that issue. If we were to use time
# we'd specify something like --time=5s.
#
# TODO(jmarantz): it would be nice to make the number of reps configurable,
# e.g. with a command-line option.
reps=2000
siege_args="--reps=$reps --rc=$siege_dir/siege.conf $proxy_url"

# Clean up any old log files, so the CSVs just show the results from
# the runs we are about to do.
rm -f "$log" $csv_files
echo "EnvoyMem, VSZ, RSS" > "$clean_mem_csv"
cp "$clean_mem_csv" "$experimental_mem_csv"

# We use the admin port both for scraping memory and for quitting at
# the end of each run.
admin="http://127.0.0.1:$admin_port"

# Blocks the script until a server started in the background is ready
# to respond to the URL passed as an arg.
function wait_for_url() {
  local url="$1"
  (set +e; set +x; until curl "$url"; do sleep 0.1; done) &>> "$log"
}

# Starts up Envoy that serves as both an origin and a proxy, and then
# sieges it with ~50k requests, measuring the overall throughput, errors,
# and memory usage. The path to the binary and filenames to collect
# performance and memory CSVs are passed in.
function run_envoy_and_siege() {
  local envoy="$1"
  local perf_csv="$2"
  local mem_csv="$3"

  # Run Envoy in the background and wait for it to respond on the upstream
  # port, admin port, and proxy port.
  echo "$envoy" -c "$envoy_conf" "&" &>> "$log"
  "$envoy" -c "$envoy_conf" &>> "$log" &
  envoy_pid="$!"

  wait_for_url "$admin"
  wait_for_url "$proxy_url"
  wait_for_url "$upstream_url"

  # Siege the envoy.
  (set +e; set -x; siege --log="$perf_csv" $siege_args) &>> "$log"

  # Capture Envoy's opinion of how much memory it's using, and also
  # ask the OS what it thinks via ps. Append those to a separate CSV
  # file from the one harvested by siege.
  statmem=$(curl -s "$admin/memory" | grep allocated | cut -d\" -f4)
  pid_vsz_rsz=$(ps -eo pid,vsz,rsz | grep "^[ ]*$envoy_pid ")
  vsz=$(echo "$pid_vsz_rsz" | cut -d\  -f2)
  rsz=$(echo "$pid_vsz_rsz" | cut -d\  -f3)
  echo "$statmem,$vsz,$rsz" >> "$mem_csv"

  # Send Envoy a quit request and wait for the process to exit.
  (set -x; curl -X POST "$admin/quitquitquit") &>> "$log"
  wait
}

# Loops 5x interleaving runs with the clean and experimental versions
# of Envoy, collecting the results in separate CSV files.
echo -n Logging 10 runs to "$log"...
for run in {0..4}; do
  run_envoy_and_siege "$clean_envoy" $clean_csv_files
  echo -n "...$((2*run+1))"
  run_envoy_and_siege "$experimental_envoy" $experimental_csv_files
  echo -n "...$((2*run+2))"
done

echo ""
./siege_result_analysis.py $csv_files

echo ""
column -s, -t < "$aggregate_csv"

echo ""
echo CSV files written to $csv_files "$aggregate_csv"
