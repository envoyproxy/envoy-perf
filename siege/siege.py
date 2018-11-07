#!/usr/bin/env python3
#
# Compares throughput from two different versions of Envoy, with multiple
# interleaved iterations. The two binaries are supplied on the commmand-line:
#
# Usage:
#    siege.py clean_envoy_binary experimental_envoy_binary output_dir
#
# The two binaries should generally be built with
#     bazel build -c opt source/exe:envoy-static
# and can then be copied to a safe place (e.g. /tmp) so that they can each
# be based on a single git workspace that you flip between branches.
#
# output_dir is where the logs and raw CSV files get written, but the
# the summarized performance data is printed as a table to stdout.

import json
import os
import requests
import subprocess
import sys
import time
import urllib.request

# TODO(jmarantz): make the configuration pluggable, which means grepping
# for these ports rather than hardcoding them. It's annoying to grep in
# yaml files because there isn't per-line context. Another possibility
# is to scrape them from Envoy log output.
proxy_port = 10001
upstream_port = 10000
admin_port = 8081

upstream_url = "http://127.0.0.1:%d" % upstream_port
proxy_url = "http://127.0.0.1:%d" % proxy_port

# We use the admin port both for scraping memory and for quitting at
# the end of each run.
admin = "http://127.0.0.1:%d" % admin_port

def main(argv):
  if len(argv) != 4:
    print("Usage: %s clean_envoy_binary experimental_envoy_binary output_dir"
          % argv[0])
    sys.exit(1)

  # Capture arguments as locals for readability.
  clean_envoy = argv[1]
  experimental_envoy = argv[2]
  outdir = argv[3]
  aggregate_csv = os.path.join(outdir, "aggregate.csv")

  # Connect to the script directory so local references to the yaml configs and
  # lorem_ipsum.txt work.
  siege_dir = os.path.abspath(os.path.dirname(argv[0]))
  os.chdir(siege_dir)

  # Derive some temp filenames from $outdir.
  log = os.path.join(outdir, "siege.log")
  clean_perf_csv = os.path.join(outdir, "clean.perf.csv")
  clean_envoy_csv = os.path.join(outdir, "clean.envoy.csv")
  clean_csv_files = [clean_perf_csv, clean_envoy_csv]
  experimental_perf_csv = os.path.join(outdir, "experimental.perf.csv")
  experimental_envoy_csv = os.path.join(outdir, "experimental.envoy.csv")
  experimental_csv_files = [experimental_perf_csv, experimental_envoy_csv]
  aggregate_csv = os.path.join(outdir, "aggregate.csv")
  csv_files = clean_csv_files + experimental_csv_files + [aggregate_csv]
  envoy_conf = os.path.join(siege_dir, "front-proxy.yaml")
  siege_conf = os.path.join(siege_dir, "siege.conf")
  siege_analysis = os.path.join(siege_dir, "siege_result_analysis.py")

  # Siege sometimes hangs when using time-based exit criteria.  See
  # https://github.com/JoeDog/siege/issues/66.  In the meantime, use
  # repetitions, which don't have that issue. If we were to use time
  # we'd specify something like --time=5s.
  #
  # TODO(jmarantz): it would be nice to make the number of reps configurable,
  # e.g. with a command-line option.
  reps = 2000
  siege_args = ["--reps=%d" % reps, "--rc=%s" % siege_conf, proxy_url]

  # Clean up any old log files, so the CSVs just show the results from
  # the runs we are about to do. This is needed for the perf CSVs because
  # otherwise siege appends the new runs to the previous contents of the
  # file.
  for fname in [clean_perf_csv, experimental_perf_csv, log]:
    if os.path.exists(fname):
      os.remove(fname)

  with open(log, "a") as logfile:
    # Echoes a command to the logfile, and then returns it. This is
    # intended to wrap the command argment to subprocess.Popen and
    # subprocess.call so we can see in the log how they were run.
    def echo(command):
      logfile.write(" ".join(command) + "\n")
      logfile.flush()
      return command

    # Starts up Envoy that serves as both an origin and a proxy, and then sieges
    # it with ~50k requests, measuring the overall throughput, errors, and
    # memory usage, and contention. The path to the binary and filenames to
    # collect performance CSV into a file that's passed in, and return some
    # memory and contention info.
    def runEnvoyAndSiege(envoy_binary, csv_files):
      # Run Envoy in the background and wait for it to respond on the upstream
      # port, admin port, and proxy port.
      envoy_args = [envoy_binary, "-c", envoy_conf, "--enable-mutex-tracing"]
      envoy = subprocess.Popen(echo(envoy_args), stdout=logfile, stderr=logfile)
      for url in [admin, proxy_url, upstream_url]:
        waitForUrl(url)

      # Siege the envoy.
      subprocess.call(echo(["siege", "--log=" + csv_files[0]] + siege_args),
                      stdout=logfile, stderr=logfile)

      # Capture Envoy's opinion of how much memory it's using, and also
      # ask the OS what it thinks via ps. Append those to a separate CSV
      # file from the one harvested by siege.
      statmem = loadJson(admin + "/memory")["allocated"]
      contention = loadJson(admin + "/contention")
      num_contentions = contention["num_contentions"]
      lifetime_wait_cycles = contention["lifetime_wait_cycles"]

      vsz = 0
      rsz = 0
      pid_str = "%d" % envoy.pid
      ps_lines = subprocess.check_output("ps -eo pid,vsz,rsz", shell=True)
      for line in ps_lines.decode('utf-8').split("\n"):
        pid_vsz_rsz = line.split(" ")
        if pid_vsz_rsz[0] == pid_str:
          vsz = pid_vsz_rsz[1]
          rsz = pid_vsz_rsz[2]
          break

      with open(csv_files[1], "a") as envoy_csv:
        envoy_csv.write("%s,%s,%s,%s,%s\n" % (
            statmem, vsz, rsz, num_contentions, lifetime_wait_cycles))

      # Send Envoy a quit request and wait for the process to exit.
      requests.post(admin + "/quitquitquit")
      envoy.wait()

    for envoy_csv in [clean_envoy_csv, experimental_envoy_csv]:
      with open(envoy_csv, "w") as envoy_csv_file:
        envoy_csv_file.write("EnvoyMem, VSZ, RSS, Contentions, WaitCycles\n")

    # Loops 5x interleaving runs with the clean and experimental versions
    # of Envoy, collecting the results in separate CSV files.
    progress("Logging 10 runs to %s " % log)
    for run in range(0, 5):
      runEnvoyAndSiege(clean_envoy, clean_csv_files)
      progress("...%d" % (2 * run + 1))
      runEnvoyAndSiege(experimental_envoy, experimental_csv_files)
      progress("...%d" % (2 * run + 2))

    print("\n")
    subprocess.call(echo([siege_analysis] + csv_files))

    # TODO(jmarantz): consider integrating siege_result_analysis.py into this
    # driver rather than calling it as a subprocess, and also consider using
    # a Python table-printing library rather than /usr/bin/column.
    os.system("column -s, -t < %s" % aggregate_csv)
    print("\n\nCSV files written to %s\n" % ", ".join(csv_files))

# Emits a string to stdout and flushes it, without necessarily adding a newline.
def progress(s):
  sys.stdout.write(s)
  sys.stdout.flush()

# Blocks the script until a server started in the background is ready
# to respond to the URL passed as an arg.
def waitForUrl(url):
  def readUrl():
    handle = urllib.request.urlopen(url)
    handle.read()
    handle.close()

  # Try only 100x (~10 seconds) before giving up
  for _ in range(0, 100):
    try:
      readUrl()
      return
    except IOError:
      time.sleep(0.1)
  # If we didn't get a succesful read in the loop, just call readUrl()
  # outside the try/except block and let the exception propagate.
  readUrl()

# Reads text output from a URL and decodes it as JSON, returning the
# JSON object.
def loadJson(url):
  with urllib.request.urlopen(url) as handle:
    data = handle.read().decode("utf-8")
    return json.loads(data)

main(sys.argv)
