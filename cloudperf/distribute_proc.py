"""This module executes h2load, Nginx and Envoy on separate cores."""

import argparse
from collections import defaultdict
import json
import time

import pexpect
from process import Process
import utils


# TODO(sohamcodes): This function needs to eventually support arbitrary mask.
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
  taskset_command_args = ["-ac", "{}-{}".format(start_core, end_core)]
  taskset_command_args.extend(proc_command)
  taskset_proc = Process("taskset", out, args=taskset_command_args)
  taskset_proc.RunProcess()
  return taskset_proc


def RunAndParseH2Load(h2load_command, h2load_timeout=None, logfile=None):
  """Runs the h2load command and returns a JSON dictionary of parsed result.

  Args:
    h2load_command: the command to run for h2load. can be wrapped over other
    commands like taskset
    h2load_timeout: the number of seconds pspawn would wait before timeout.
    logfile: An opened filestream to write the log of h2load run
  Returns:
    The JSON dictionaries corresponding to h2load output.
  Raises:
    RuntimeError: When h2load run causes some error
  """
  # TODO(sohamcodes): logfile for h2load needs to be handled separately.
  # for now, it only works as a single log file, capturing log of multiple
  # h2load runs
  child = pexpect.spawn(h2load_command, logfile=logfile,
                        timeout=h2load_timeout)

  child.expect(r"finished in\s+(\d+\.?\d*)([a-z]+),")  # total time
  total_time, unit = child.match.groups()
  total_time = {
      "unit": unit,
      "data": float(total_time)
  }

  child.expect(r"\s+(\d+\.?\d*)\s*req/s,")  # total requests per second
  req = child.match.group(1)
  total_req_p_sec = {
      "unit": "req/s",  # we know that it will always be req/s
      "data": float(req)
  }

  child.expect(r"\s+(\d+\.?\d*)\s*([A-Z]*)B/s")  # total Bytes per second
  data, unit = child.match.groups()
  total_data_p_sec = {
      "unit": "{}B/s".format(unit),  # {M}B/s
      "data": float(data)
  }

  child.expect(r"requests:\s+(\d+)\s+total,\s+(\d+)\s+started,\s+(\d+)\s+done"
               r",\s+(\d+)\s+succeeded,\s+(\d+)\s+failed,\s+(\d+)\s+errored,\s"
               r"+(\d+)\s+timeout")
  (req_tot, req_sta, req_done, req_suc, req_fail, req_err,
   req_tout) = child.match.groups()

  requests_stat = {
      "total": req_tot,
      "started": req_sta,
      "done": req_done,
      "success": req_suc,
      "fail": req_fail,
      "error": req_err,
      "timeout": req_tout
  }

  child.expect(r"status codes: (\d+)\s+2xx,\s+(\d+)\s+3xx,\s+(\d+)\s+4xx"
               r",\s+(\d+)\s+5xx")
  stat_2xx, stat_3xx, stat_4xx, stat_5xx = child.match.groups()
  status_codes = {
      "2xx": stat_2xx,
      "3xx": stat_3xx,
      "4xx": stat_4xx,
      "5xx": stat_5xx
  }

  child.expect(r"traffic:[\s\w.]+\((\d+)\)\s+total,\s+[\s\w.]+\((\d+)\)"
               r"\s+headers\s+\(space savings\s+(\d+\.?\d*)%\),\s+[\s\w.]+"
               r"\((\d+)\)\s+data")
  (traf_tot, traf_head, traf_save,
   traf_data) = child.match.groups()

  traffic_detail = {
      "traffic_total": traf_tot,
      "traffic_headers": traf_head,
      "traffic_savings%": float(traf_save),
      "traffic_data": traf_data
  }

  child.expect(r"time for request\s*:\s+(\d+\.?\d*)([a-z]+)\s+(\d+\.?\d*)"
               r"([a-z]+)\s+(\d+\.?\d*)([a-z]+)\s+(\d+\.?\d*)([a-z]+)\s+"
               r"(\d+\.?\d*)%")
  (tfr_min, tfr_min_unit, tfr_max, tfr_max_unit,
   tfr_mean, tfr_mean_unit, tfr_sd, tfr_sd_unit,
   tfr_sd_per) = child.match.groups()
  time_for_request = {
      "min": {
          "unit": tfr_min_unit,
          "data": float(tfr_min)
      },
      "max": {
          "unit": tfr_max_unit,
          "data": float(tfr_max)
      },
      "mean": {
          "unit": tfr_mean_unit,
          "data": float(tfr_mean)
      },
      "sd": {
          "unit": tfr_sd_unit,
          "data": float(tfr_sd)
      },
      "sd%": float(tfr_sd_per)
  }

  child.expect(r"time for connect\s*:\s+(\d+\.?\d*)([a-z]+)\s+(\d+\.?\d*)"
               r"([a-z]+)\s+(\d+\.?\d*)([a-z]+)\s+(\d+\.?\d*)([a-z]+)\s+"
               r"(\d+\.?\d*)%")
  (tfc_min, tfc_min_unit, tfc_max, tfc_max_unit,
   tfc_mean, tfc_mean_unit, tfc_sd, tfc_sd_unit,
   tfc_sd_per) = child.match.groups()
  time_for_connect = {
      "min": {
          "unit": tfc_min_unit,
          "data": float(tfc_min)
      },
      "max": {
          "unit": tfc_max_unit,
          "data": float(tfc_max)
      },
      "mean": {
          "unit": tfc_mean_unit,
          "data": float(tfc_mean)
      },
      "sd": {
          "unit": tfc_sd_unit,
          "data": float(tfc_sd)
      },
      "sd%": float(tfc_sd_per)
  }

  child.expect(r"time to 1st byte\s*:\s+(\d+\.?\d*)([a-z]+)\s+(\d+\.?\d*)"
               r"([a-z]+)\s+(\d+\.?\d*)([a-z]+)\s+(\d+\.?\d*)([a-z]+)\s+"
               r"(\d+\.?\d*)%")
  (tfb_min, tfb_min_unit, tfb_max, tfb_max_unit,
   tfb_mean, tfb_mean_unit, tfb_sd, tfb_sd_unit,
   tfb_sd_per) = child.match.groups()
  time_for_1st_byte = {
      "min": {
          "unit": tfb_min_unit,
          "data": float(tfb_min)
      },
      "max": {
          "unit": tfb_max_unit,
          "data": float(tfb_max)
      },
      "mean": {
          "unit": tfb_mean_unit,
          "data": float(tfb_mean)
      },
      "sd": {
          "unit": tfb_sd_unit,
          "data": float(tfb_sd)
      },
      "sd%": float(tfb_sd_per)
  }

  child.expect(r"req/s\s*:\s*(\d+\.?\d*)\s+(\d+\.?\d*)\s+(\d+\.?\d*)\s+"
               r"(\d+\.?\d*)\s+(\d+\.?\d*)%")
  (rps_min, rps_max, rps_mean, rps_sd, rps_sd_per) = child.match.groups()
  req_per_sec = {
      "min": float(rps_min),
      "max": float(rps_max),
      "mean": float(rps_mean),
      "sd": float(rps_sd),
      "sd%": float(rps_sd_per)
  }

  while child.isalive():
    print "h2load is still alive, after parsing is complete."
    time.sleep(2)

  child.close()

  if child.exitstatus != 0:
    raise RuntimeError("Error: problem running h2load. Check log.")
  single_result_json = {
      "total_time": total_time,
      "total_req_per_sec": total_req_p_sec,
      "total_data_per_sec": total_data_p_sec,
      "requests_statistics": requests_stat,
      "status_codes_statistics": status_codes,
      "traffic_details": traffic_detail,
      "time_for_request": time_for_request,
      "time_for_connect": time_for_connect,
      "time_for_1st_byte": time_for_1st_byte,
      "req/s": req_per_sec
  }
  return single_result_json


def GetNginxCommandLineArguments():
  """This function returns the nginx configuration.

  Right now, it just returns hardcoded values. Later on, we might return user-
  provided values
  Returns:
    Returns the Nginx commandline arguments
  """
  return ["-c", "/etc/nginx/nginx.conf", "-g", "daemon off;"]


# TODO(sohamcodes): debug is always included now. Later on, debug should be
# enabled based on the debug-mode
def GetEnvoyCommandLineArguments(envoy_config_path, envoy_thread_number):
  """This function returns the Envoy configuration.

  Args:
    envoy_config_path: the path to the envoy's config file.
    envoy_thread_number: number of worker threads for Envoy
  Returns:
    Formatted envoy configuration. Right now it always include the debug info.
  """
  return ["-c", envoy_config_path, "-l", "error", "--concurrency",
          str(envoy_thread_number)]


def GetCoreRange(start, end):
  """This function returns the core numbers separated by comma for range.

  Args:
    start: starting core number
    end: ending core number
  Returns:
    Core numbers, separated by comma.
  """
  start_num = int(start)
  end_num = int(end)
  comma_string = str(start)
  for i in range(start_num + 1, end_num + 1):
    comma_string = "{},{}".format(comma_string, i)
  return comma_string


def main():
  parser = argparse.ArgumentParser(
      formatter_class=argparse.ArgumentDefaultsHelpFormatter)
  parser.add_argument("envoy_binary_path",
                      help="the path to the binary file of Envoy")
  parser.add_argument("envoy_config_path",
                      help="the path to the config file which Envoy should use")
  parser.add_argument("result",
                      help="the name of the result file where benchmarking "
                           "results will be written")
  parser.add_argument("--nginx_cores",
                      help="the start and end core numbers for Nginx server to "
                           "run, separated by a comma.",
                      default="0,10")
  parser.add_argument("--envoy_cores",
                      help="the start and end core numbers for"
                           " Envoy to run, separated by a comma.",
                      default="11,18")
  parser.add_argument("--h2load_cores",
                      help="the start and end core numbers for "
                           "h2load to run, separated by a comma.",
                      default="19,19")
  parser.add_argument("--h2load_warmup",
                      help="period of time in seconds to warm up for h2load",
                      default="5")
  parser.add_argument("--h2load_clients", help="number of h2load clients.",
                      default="10")
  parser.add_argument("--h2load_con_conn", help=("number of h2load concurrent"
                                                 " connections."),
                      default="10")
  parser.add_argument("--h2load_duration",
                      help=("period of time in seconds for"
                            " measurements in h2load"),
                      default="5")

  # TODO(sohamcodes): range for port number should be checked
  parser.add_argument("--direct_port", help="the direct port for benchmarking.",
                      type=int, default=4500)

  parser.add_argument("--envoy_port",
                      help="the Envoy proxy port for benchmarking",
                      type=int, default=9000)
  parser.add_argument("--num_iter",
                      help="the number of times h2load will be run",
                      type=int, default=5)

  parser.add_argument("--h2load_timeout",
                      help="the maximum number of seconds to wait for h2load"
                           " to return some result", type=int, default=120)

  parser.add_argument("--arrangement", help=("the type of arrangement in"
                                             " this experiment."),
                      default="single-vm-permanent")
  utils.CreateBooleanArgument(parser, "ssl",
                              ("turn on if you want"
                               " to enable ssl for the benchmarking"),
                              ssl=True)
  utils.CreateBooleanArgument(parser, "h1",
                              ("turn on if you want"
                               " to enable HTTP1.1, instead of default h2"),
                              h1=False)

  args = parser.parse_args()
  print args.h1

  if args.nginx_cores:
    nginx_start_core, nginx_end_core = args.nginx_cores.split(",")

  if args.envoy_cores:
    envoy_start_core, envoy_end_core = args.envoy_cores.split(",")

  if args.h2load_cores:
    h2load_start_core, h2load_end_core = args.h2load_cores.split(",")

  h2load_threads = int(h2load_end_core) - int(h2load_start_core) + 1

  # allocate nginx to designated cores
  output = "nginx_out.log"
  nginx_command = ["nginx"]
  nginx_command.extend(GetNginxCommandLineArguments())
  nginx_process = AllocProcessToCores(nginx_start_core,
                                      nginx_end_core, output,
                                      nginx_command)
  print "nginx process id is {}".format(nginx_process.pid)

  # allocate envoy to designated cores
  envoy_thread_number = int(envoy_end_core) - int(envoy_start_core) + 1
  envoy_command = [args.envoy_binary_path]
  envoy_command.extend(GetEnvoyCommandLineArguments(args.envoy_config_path,
                                                    envoy_thread_number))
  outfile = "envoy_out.log"  # this is envoy output file
  envoy_process = AllocProcessToCores(envoy_start_core, envoy_end_core,
                                      outfile, envoy_command)
  print "envoy process id is {}".format(envoy_process.pid)

  result_json = defaultdict(list)
  logfile = open("h2load_log.log", "ab+")
  mplog_direct = open("mpstat_direct.log", "ab+")
  mplog_envoy = open("mpstat_envoy.log", "ab+")
  cores_string = "{},{},{}".format(
      GetCoreRange(nginx_start_core, nginx_end_core),
      GetCoreRange(h2load_start_core, h2load_end_core),
      GetCoreRange(envoy_start_core, envoy_end_core))

  for _ in xrange(args.num_iter):
    # allocate h2load to designated cores as foreground process
    mpstat_direct = Process("mpstat -P {} 1".format(
        cores_string), mplog_direct)
    mpstat_direct.RunProcess()
    h2load_command = ("taskset -ac {}-{} "
                      "h2load http{ssl}://localhost:{} -n 0 --warm-up-time {}"
                      " -c{} -D {} -t{} -m{} {http2}").format(
                          h2load_start_core, h2load_end_core, args.direct_port,
                          args.h2load_warmup, args.h2load_clients,
                          args.h2load_duration, h2load_threads,
                          args.h2load_con_conn,
                          ssl="s" if args.ssl else "",
                          http2="--h1" if args.h1 else "")
    result_json["direct-{}".format(args.arrangement)].append(RunAndParseH2Load(
        h2load_command, args.h2load_timeout, logfile=logfile))
    mpstat_direct.KillProcess("-SIGINT")
    print "h2load direct is done."

    mpstat_envoy = Process("mpstat -P {} 1".format(
        cores_string), mplog_envoy)
    mpstat_envoy.RunProcess()
    h2load_command = ("taskset -ac {}-{} "
                      "h2load http{ssl}://localhost:{} -n 0 --warm-up-time {}"
                      " -c{} -D {} -t{} -m{} {http2}").format(
                          h2load_start_core, h2load_end_core, args.envoy_port,
                          args.h2load_warmup, args.h2load_clients,
                          args.h2load_duration, h2load_threads,
                          args.h2load_con_conn,
                          ssl="s" if args.ssl else "",
                          http2="--h1" if args.h1 else "")
    result_json["envoy-{}".format(args.arrangement)].append(RunAndParseH2Load(
        h2load_command, args.h2load_timeout, logfile=logfile))
    mpstat_envoy.KillProcess("-SIGINT")
    print "h2load with envoy is done."

  # killing nginx, envoy processes
  nginx_process.KillProcess("-QUIT")
  envoy_process.KillProcess()

  with open(args.result, "w") as f:
    json.dump(result_json, f)

if __name__ == "__main__":
  main()
