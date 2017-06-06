"""This module executes h2load, Nginx and Envoy on separate cores."""

import argparse
import StringIO

from process import Process


def AllocProcessToCores(start_core, end_core, out,
                        background, proc_command=None, pid=None):
  """Allocate processes to designated stretch of cores.

  Args:
    start_core: the start of the stretch of cores to allocate to the process.
    end_core: the end of the stretch of cores to allocate to the process.
    out: file name or output stream for redirection purpose.
    background: True/False
    proc_command: the command to run on designated cores.
    pid: if directly want to set affinity of pids, either proc_command or pid
    should be given.
  Returns:
    the taskset process id is returned
  """
  if pid is None:
    taskset_command = "taskset -ac {}-{} {}".format(start_core,
                                                    end_core, proc_command)
  else:
    print "Error: Invalid/Unavailable pid/process command."
  taskset_proc = Process(proc_name="taskset",
                         proc_command=taskset_command, outstream=out)
  taskset_proc.RunProcess(background=background)
  return taskset_proc


def ParseH2Load(iostream):
  """Parses h2load output on a given stream and overwrite the stream.

    starts overwriting from the current position of the stream

  Args:
    iostream: reads unformatted output from this stream and then writes back.
  """
  initial_pos = iostream.tell()
  buf = StringIO.StringIO()
  for line in iostream:
    if line.find("finished in") != -1:
      buf.write(line)
      break
  # read and take the rest of the stream
  for line in iostream:
    buf.write(line)

  # print buf.getvalue()
  print initial_pos

  # seek to the initial position to overwrite
  iostream.seek(initial_pos, 0)
  for line in buf.getvalue().split("\n"):
    # print line
    iostream.write("{}\n".format(line))

  # delete rest of the stuff
  # iostream.truncate()


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
  direct_port = args.direct_port
  envoy_port = args.envoy_port

  # allocate nginx to designated cores
  output = StringIO.StringIO()
  nginx_process = AllocProcessToCores(nginx_start_core,
                                      nginx_end_core, output, True,
                                      proc_command="nginx -c "
                                                   "/etc/nginx/nginx.conf "
                                                   "-g \"daemon off;\"")
  print "nginx process id is {}".format(nginx_process.pid)

  # allocate envoy to designated cores
    # following is the shell command we are trying to replicate
  # ./envoy-fastbuild -c envoy-configs/simple-loopback.json\
  # -l debug > out.txt 2>&1 &
  envoy_command = "{} -c {} -l debug".format(envoy_path, envoy_config_path)
  outfile = "out.txt"  # this is a temporary dump output file
  # run =
  # envoy(envoyconfig.split(" "), _out=outfile, _err_to_out=True, _bg=True)
  # print "envoy process id is: " + str(run.pid)
  # sh.sudo.taskset("-cp", "{}-{}".format(
  #     envoy_start_core, envoy_end_core), str(run.pid), _out=output)
  envoy_process = AllocProcessToCores(envoy_start_core, envoy_end_core,
                                      outfile, True, proc_command=envoy_command)
  print "envoy process id is {}".format(envoy_process.pid)

  # allocate h2load to designated cores
  open(result, "w").write("")

  h2load_res = open(result, "a")
  pos_before_result = h2load_res.tell()

  h2load_command = "h2load https://localhost:{} -n{} -c{} -m{} -t{}".format(
      direct_port, h2load_reqs, h2load_clients, h2load_conns, h2load_threads)
  # sh.sudo.taskset(h2load_args.split(" "), _out=h2load_res)
  AllocProcessToCores(h2load_start_core, h2load_end_core,
                      h2load_res, False, proc_command=h2load_command)

  h2load_res = open(result, "r+")  # read+write mode to provide to ParseH2Load
  h2load_res.seek(pos_before_result, 0)
  ParseH2Load(h2load_res)
  print "h2load direct is done."

  h2load_res = open(result, "a")
  pos_before_result = h2load_res.tell()

  h2load_command = "h2load https://localhost:{} -n{} -c{} -m{} -t{}".format(
      envoy_port, h2load_reqs, h2load_clients, h2load_conns, h2load_threads)
  # sh.sudo.taskset(h2load_args.split(" "), _out=h2load_res)
  AllocProcessToCores(h2load_start_core, h2load_end_core,
                      h2load_res, False, proc_command=h2load_command)

  h2load_res = open(result, "r+")  # read+write mode to provide to ParseH2Load
  h2load_res.seek(pos_before_result, 0)
  ParseH2Load(h2load_res)
  print "h2load against envoy is done."

    # killing nginx, envoy processes
  nginx_process.KillProcess("-QUIT")
  envoy_process.KillProcess()

  # run.wait()

if __name__ == "__main__":
  main()
