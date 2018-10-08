#!/bin/bash
#
# Compares throughput from two different versions of Envoy, with multiple
# interleaved iterations. The two binaries are supplied on the commmand-line:
#
# Usage:
#    siege.sh clean_envoy_binary experimental_envoy_binary output_dir

set -e
set -u

clean_envoy="$1"
experimental_envoy="$2"
outdir="$3"

siege_dir=$(dirname $(realpath $0))

log="$outdir/siege.log"
clean_csv="$outdir/clean.csv"
clean_mem="$outdir/clean.mem"
experimental_csv="$outdir/experimental.csv"
experimental_mem="$outdir/experimental.mem"

# TODO(jmarantz): make the configuration pluggable, which means grepping
# for these ports rather than hardcoding them. It's annoying to grep in
# yaml files because there isn't per-line context.
proxy_port=10001
upstream_port=10000
admin_port=8081

envoy_conf="$siege_dir/front-proxy.yaml"
file="lorem_ipsum.txt"
upstream_url="http://127.0.0.1:$upstream_port/$file"
proxy_url="http://127.0.0.1:$proxy_port/$file"

# siege sometimes hangs when using time-based exit criteria.  See
# https://github.com/JoeDog/siege/issues/66 .  In the meantime, use
# repetitions, which don't have that issue.
# --time=5s
reps=2000
siege_args="--reps=$reps --rc=$siege_dir/siege.conf $proxy_url"

rm -f "$log" "$clean_csv" "$experimental_csv"
echo "Stats Mem, VSZ, RSS" > "$clean_mem"
cp "$clean_mem" "$experimental_mem"

admin="http://127.0.0.1:$admin_port"

function wait_for_url() {
  local url="$1"
  (set +e; set +x; until curl "$url"; do sleep 0.1; done) &>> "$log"
}

function run_envoy_and_siege() {
  local envoy="$1"
  local csv="$2"
  local mem="$3"

  # Run Envoy in the background and wait for it to respond on the upstream
  # port, admin port, and proxy port.
  echo "$envoy" -c "$envoy_conf" "&" &>> "$log"
  "$envoy" -c "$envoy_conf" &>> "$log" &
  envoy_pid="$!"

  wait_for_url "$admin"
  wait_for_url "$proxy_url"
  wait_for_url "$upstream_url"

  # Siege the envoy, then quit and wait for the background process to exit
  (set +e; set -x; siege --log="$csv" $siege_args) &>> "$log"

  statmem=$(curl -s "$admin/memory" | grep allocated | cut -d\" -f4)

  # Collecting the envoy PID with $! after instantiating it doesn't seem to
  # work. Maybe it forks? In any case, get it now via grep.
  
  pid_vsz_rsz=$(ps -eo pid,vsz,rsz | grep "^[ ]*$envoy_pid ")
  vsz=$(echo "$pid_vsz_rsz" | cut -d\  -f2)
  rsz=$(echo "$pid_vsz_rsz" | cut -d\  -f3)
  echo "$statmem,$vsz,$rsz" >> "$mem"

  (set -x; curl -X POST "$admin/quitquitquit") &>> "$log"
  wait
}


echo -n Logging 10 runs to "$log"...
for run in {0..4}; do
  run_envoy_and_siege "$clean_envoy" "$clean_csv" "$clean_mem"
  echo -n "...$((2*run+1))"
  run_envoy_and_siege "$experimental_envoy" "$experimental_csv" "$experimental_mem"
  echo -n "...$((2*run+2))"
done

echo ""
./siege_result_analysis.py "$clean_csv" "$experimental_csv"

echo ""
echo CSV files written to "$clean_csv" and "$experimental_csv"
