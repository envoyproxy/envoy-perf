"""This module executes h2load, Nginx and Envoy on separate cores."""

import argparse
import io
import sh


parser = argparse.ArgumentParser()
parser.add_argument("envoy_binary_path",
                    help="the path to the binary file of Envoy")
parser.add_argument("envoy_config_path",
                    help="the path to the config file which Envoy should use")
parser.add_argument("result",
                    help="the name of the result file where benchmarking "
                         "results will be written")
parser.add_argument("--nginx_cores",
                    help="the start and end core numbers for Nginx server to "
                         "run, separated by a comma. default: 0,4",
                    default="0,4")
parser.add_argument("--envoy_cores", help="the start and end core numbers for"
                                          " Envoy to run, separated by a comma."
                                          " default: 5,9", default="5,9")
parser.add_argument("--h2load_cores", help="the start and end core numbers for "
                                           "h2load to run, separated by a "
                                           "comma. default: 10,14",
                    default="10,14")
parser.add_argument("--h2load_reqs", help="number of h2load requests. default: "
                                          "10000", default="10000")
parser.add_argument("--h2load_clients", help="number of h2load clients. "
                                             "default: 100", default="100")
parser.add_argument("--h2load_conns", help="number of h2load connections. "
                                           "default: 10", default="10")
parser.add_argument("--h2load_threads", help="number of h2load threads. "
                                             "default: 5", default="5")

args = parser.parse_args()
envoy_path = args.envoy_binary_path
envoy_config_path = args.envoy_config_path
result = args.result

if args.nginx_cores:
  nums = args.nginx_cores.split(",")
  nginx_start_core = nums[0]
  nginx_end_core = nums[1]

if args.envoy_cores:
  nums = args.envoy_cores.split(",")
  envoy_start_core = nums[0]
  envoy_end_core = nums[1]

if args.h2load_cores:
  nums = args.h2load_cores.split(",")
  h2load_start_core = nums[0]
  h2load_end_core = nums[1]

h2load_reqs = args.h2load_reqs
h2load_clients = args.h2load_clients
h2load_conns = args.h2load_conns
h2load_threads = args.h2load_threads

# allocate nginx to designated cores
buf = io.StringIO()
sh.pgrep("nginx", _out=buf)
for x in buf.getvalue().split("\n"):
  output = io.StringIO()
  if x.strip():
    sh.sudo.taskset("-cp",
                    "{}-{}".format(
                        nginx_start_core, nginx_end_core), x, _out=output)

# allocate envoy to designated cores
# following is the shell command we are trying to replicate
# ./envoy-fastbuild -c envoy-configs/simple-loopback.json\
# -l debug > out.txt 2>&1 &
envoyconfig = "-c {} -l debug".format(envoy_config_path)
outfile = "out.txt"  # this is a temporary file
envoy = sh.Command(envoy_path)
# this creates the process in the background, however it'll be destroyed
# once the python script is finished
# if we really need envoy to keep running on background after exiting the
# python script, then we probably should use subprocess instead of sh
run = envoy(envoyconfig.split(" "), _out=outfile, _err_to_out=True, _bg=True)
print "envoy process id is: " + str(run.pid)
sh.sudo.taskset("-cp", "{}-{}".format(
    envoy_start_core, envoy_end_core), str(run.pid), _out=output)

# allocate h2load to designated cores
open(result, "w").write("")

h2load_res = open(result, "a")

h2load_args = "-c {}-{} h2load https://localhost -n{} -c{} -m{} -t{}".format(
    h2load_start_core, h2load_end_core, h2load_reqs,
    h2load_clients, h2load_conns, h2load_threads)
sh.sudo.taskset(h2load_args.split(" "), _out=h2load_res)
print "h2load direct is done."

h2load_args = "-c {}-{} h2load https://localhost:9000 -n{} -c{} -m{} -t{}".format(
    h2load_start_core, h2load_end_core, h2load_reqs,
    h2load_clients, h2load_conns, h2load_threads)
sh.sudo.taskset(h2load_args.split(" "), _out=h2load_res)
print "h2load against envoy is done."

# run.wait()
