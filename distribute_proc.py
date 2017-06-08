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
  taskset_proc = Process(taskset_command, out)
  taskset_proc.RunProcess()
  return taskset_proc


def RunAndParseH2Load(h2load_command):
  """Parses h2load output on a given stream and overwrite the stream.

    Starts overwriting from the current position of the stream.

  Args:
    h2load_command: the command to run for h2load. can be wrapped over other
    commands like taskset
  Returns:
    The Json dictionaries corresponding to h2load output.
  """
  child = pexpect.spawn(h2load_command, logfile=open("log.txt", "rb+"))

  child.expect(r"finished in\s+(\d+\.?\d*)([a-z]+),")  # total time
  time, unit = child.match.groups()
  total_time = {
      "unit": unit,
      "data": float(time)
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

  child.close()

  if child.exitstatus != 0:
    print "Error: problem running h2load. Check log.txt"
    return None
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


def ParseStartAndEndCore(comma_sep_string):
  """This function parses out a comma-separated string to two separate values.

  Args:
    comma_sep_string: the comma-separated string.
  Returns:
    A tuple of two separated values
  """
  values = comma_sep_string.split(",")
  return (values[0], values[1])


def AddResultToJsonDict(single_result_json, full_dict, title):
  """This function adds a single result to the full json dictionary.

  Args:
    single_result_json: the statistics of a single h2load run in json
    full_dict: the dictionary in which single result will be appended.
    title: this does not need to be unique, if it matches with any existing
    value, then new result will be appended in the existing title category
  """

  if title not in full_dict:
    full_dict[title] = []

  full_dict[title].append(single_result_json)


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
  parser.add_argument("--num_iter",
                      help="the number of times h2load will be run"
                           ". default: 5", type=int, default=5)

  args = parser.parse_args()
  envoy_path = args.envoy_binary_path
  envoy_config_path = args.envoy_config_path
  result = args.result
  number_iteration = args.num_iter

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
  output = "nginx_out.txt"
  nginx_process = AllocProcessToCores(nginx_start_core,
                                      nginx_end_core, output,
                                      "nginx {}".format(GetNginxConfig()))
  print "nginx process id is {}".format(nginx_process.pid)

  # allocate envoy to designated cores
  envoy_command = "{} {}".format(envoy_path, GetEnvoyConfig(envoy_config_path))
  outfile = "envoy_out.txt"  # this is envoy output file
  envoy_process = AllocProcessToCores(envoy_start_core, envoy_end_core,
                                      outfile, envoy_command)
  print "envoy process id is {}".format(envoy_process.pid)

  result_json = {}

  for _ in xrange(number_iteration):
    # allocate h2load to designated cores
    h2load_command = ("taskset -ac {}-{} "
                      "h2load https://localhost:{} -n{} -c{} -m{} -t{}").format(
                          h2load_start_core, h2load_end_core, direct_port,
                          h2load_reqs, h2load_clients, h2load_conns,
                          h2load_threads)

    AddResultToJsonDict(RunAndParseH2Load(h2load_command),
                        result_json, "direct")
    print "h2load direct is done."

    h2load_command = ("taskset -ac {}-{} "
                      "h2load https://localhost:{} -n{} -c{} -m{} -t{}").format(
                          h2load_start_core, h2load_end_core, envoy_port,
                          h2load_reqs, h2load_clients, h2load_conns,
                          h2load_threads)
    AddResultToJsonDict(RunAndParseH2Load(h2load_command),
                        result_json, "envoy")
    print "h2load with envoy is done."

  # killing nginx, envoy processes
  nginx_process.KillProcess("-QUIT")
  envoy_process.KillProcess()

  with open(result, "w") as f:
    json.dump(result_json, f)

if __name__ == "__main__":
  main()
