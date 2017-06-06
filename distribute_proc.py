"""This module executes h2load, Nginx and Envoy on separate cores."""

import argparse
import json
import StringIO
import pexpect

from process import Process


def AllocProcessToCores(start_core, end_core, out, proc_command):
  """Allocate processes to designated stretch of cores.

    Always runs a process in background curently.

  Args:
    start_core: the start of the stretch of cores to allocate to the process.
    end_core: the end of the stretch of cores to allocate to the process.
    out: file name or output stream for redirection purpose.
    proc_command: the command to run on designated cores.
  Returns:
    The taskset process id is returned
  """
  if proc_command is not None:
    taskset_command = "taskset -ac {}-{} {}".format(start_core,
                                                    end_core, proc_command)
  else:
    print "Error: Invalid/Unavailable process command."
  taskset_proc = Process(taskset_command, out, proc_name="taskset")
  taskset_proc.RunProcess()
  return taskset_proc


# TODO(sohamcodes): This should eventually parse out the results and use this
# for statistical or visualization purposes. For now, we just write to a text
# file.
def RunAndParseH2Load(h2load_command, iostream):
  """Parses h2load output on a given stream and overwrite the stream.

    Starts overwriting from the current position of the stream.

  Args:
    h2load_command: the command to run for h2load. can be wrapped over other
    commands like taskset
    iostream: reads unformatted output from this stream and then writes back.
  """
  child = pexpect.spawn(h2load_command, logfile=open("log.txt", "wb"))

  total_time = {
      "total_time": {
          "unit": None,
          "data": []
      }
  }

  child.expect("finished in\s+(\d+).(\d+)([a-z]*),")  # total millisecond time
  time_d, time_dp, unit = child.match.groups()
  total_time["total_time"]["unit"] = unit
  total_time["total_time"]["data"].append("{}.{}".format(time_d, time_dp))
  print json.dumps(total_time)

  child.expect("\s+(\d+).*(\d*)\s*req/s,")  # total requests per second
  child.expect("\s+(\d+).*(\d*)\s*([A-Z]*)B/s")  # total Bytes per second
  child.expect("\n")

  # h2load_child.expect("finished in")
  iostream.write(child.after)
  # h2load_child.expect(pexpect.EOF)
  # iostream.write(h2load_child.before)
  child.close()
  if child.exitstatus != 0:
    print "Error: problem running h2load. Check log.txt"


def ParseStartAndEndCore(comma_sep_string):
  """This function parses out a comma-separated string to two separate values.

  Args:
    comma_sep_string: the comma-separated string.
  Returns:
    A tuple of two values
  """
  values = comma_sep_string.split(",")
  return (values[0], values[1])


def GetNginxConfig():
  """This function returns the nginx configuration.

  Right now, it just returns hardcoded values. Later on, we might return user-
  provided values
  Returns:
    Returns the nginx configuration
  """
  return "-c /etc/nginx/nginx.conf -g \"daemon off;\""


# TODO(sohamcodes): debug is always included now. Later on, debug should be
# enabled based on the debug-mode
def GetEnvoyConfig(envoy_config_path):
  """This function returns the Envoy configuration.

  Args:
    envoy_config_path: the path to the envoy's config file.
  Returns:
    Formatted envoy configuration. Right now it always include the debug info
  """
  return "-c {} -l debug".format(envoy_config_path)


def main():
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
  parser.add_argument("--envoy_cores",
                      help="the start and end core numbers for"
                           " Envoy to run, separated by a comma."
                           " default: 5,9", default="5,9")
  parser.add_argument("--h2load_cores",
                      help="the start and end core numbers for "
                           "h2load to run, separated by a "
                           "comma. default: 10,14",
                      default="10,14")
  parser.add_argument("--h2load_reqs",
                      help="number of h2load requests. default: "
                           "10000", default="10000")
  parser.add_argument("--h2load_clients", help="number of h2load clients. "
                                               "default: 100", default="100")
  parser.add_argument("--h2load_conns", help="number of h2load connections. "
                                             "default: 10", default="10")
  parser.add_argument("--h2load_threads", help="number of h2load threads. "
                                               "default: 5", default="5")

  parser.add_argument("--direct_port", help="the direct port for benchmarking"
                                            ". default: 4500", default="4500")

  parser.add_argument("--envoy_port",
                      help="the Envoy proxy port for benchmarking"
                           ". default: 9000", default="9000")

  args = parser.parse_args()
  envoy_path = args.envoy_binary_path
  envoy_config_path = args.envoy_config_path
  result = args.result

  if args.nginx_cores:
    nginx_start_core, nginx_end_core = ParseStartAndEndCore(args.nginx_cores)

  if args.envoy_cores:
    envoy_start_core, envoy_end_core = ParseStartAndEndCore(args.envoy_cores)

  if args.h2load_cores:
    h2load_start_core, h2load_end_core = ParseStartAndEndCore(args.h2load_cores)

  h2load_reqs = args.h2load_reqs
  h2load_clients = args.h2load_clients
  h2load_conns = args.h2load_conns
  h2load_threads = args.h2load_threads
  direct_port = args.direct_port
  envoy_port = args.envoy_port

  # allocate nginx to designated cores
  output = StringIO.StringIO()
  nginx_process = AllocProcessToCores(nginx_start_core,
                                      nginx_end_core, output,
                                      "nginx {}".format(GetNginxConfig()))
  print "nginx process id is {}".format(nginx_process.pid)

  # allocate envoy to designated cores
  # following is the shell command we are trying to replicate
  # ./envoy-fastbuild -c envoy-configs/simple-loopback.json\
  # -l debug > out.txt 2>&1 &
  envoy_command = "{} {}".format(envoy_path, GetEnvoyConfig(envoy_config_path))
  outfile = "out.txt"  # this is a temporary dump output file
  # run =
  # envoy(envoyconfig.split(" "), _out=outfile, _err_to_out=True, _bg=True)
  # print "envoy process id is: " + str(run.pid)
  # sh.sudo.taskset("-cp", "{}-{}".format(
  #     envoy_start_core, envoy_end_core), str(run.pid), _out=output)
  envoy_process = AllocProcessToCores(envoy_start_core, envoy_end_core,
                                      outfile, envoy_command)
  print "envoy process id is {}".format(envoy_process.pid)

  # allocate h2load to designated cores
  open(result, "w").write("")  # truncate the whole current result file

  h2load_command = ("taskset -ac {}-{} "
                    "h2load https://localhost:{} -n{} -c{} -m{} -t{}").format(
                        h2load_start_core, h2load_end_core, direct_port,
                        h2load_reqs, h2load_clients, h2load_conns,
                        h2load_threads)
  # sh.sudo.taskset(h2load_args.split(" "), _out=h2load_res)
  # AllocProcessToCores(h2load_start_core, h2load_end_core,
  #                     h2load_res, False, proc_command=h2load_command)

  RunAndParseH2Load(h2load_command, open(result, "a"))
  print "h2load direct is done."

  h2load_command = ("taskset -ac {}-{} "
                    "h2load https://localhost:{} -n{} -c{} -m{} -t{}").format(
                        h2load_start_core, h2load_end_core, envoy_port,
                        h2load_reqs, h2load_clients, h2load_conns,
                        h2load_threads)
  # sh.sudo.taskset(h2load_args.split(" "), _out=h2load_res)
  # AllocProcessToCores(h2load_start_core, h2load_end_core,
  #                     h2load_res, False, proc_command=h2load_command)

  RunAndParseH2Load(h2load_command, open(result, "a"))
  print "h2load with envoy is done."

  # killing nginx, envoy processes
  nginx_process.KillProcess("-QUIT")
  envoy_process.KillProcess()

  # run.wait()

if __name__ == "__main__":
  main()
