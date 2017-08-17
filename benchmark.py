"""Top level python script to create VM, run benchmarking and get result."""


import argparse
import os
import re
import StringIO
import subprocess
import time

import pexpect
import requests
import shell_helpers as sh_utils
import utils


class BenchmarkError(Exception):
  pass


def CheckStatus(args):
  """This function tries to check the status of the VM Instance.

  Args:
    args: all the arguments to the program
  Returns:
    Returns None, if everything is fine
    Otherwise, return the error message and status parsed
  """
  status = subprocess.check_output(sh_utils.GetGcloud([
      "instances", "describe",
      args.vm_name, "--zone",
      args.zone], project=args.project, service="compute"))
  cur_status = re.search(r"status:\s+([A-Z]+)", status)
  if cur_status.group(1) == "RUNNING":
    print "Instance is running successfully."
    return None
  else:
    return ("Instance is not running"
            ". Current status: {}").format(cur_status.group(1))


def GetOwnIP():
  return requests.get(("http://metadata.google.internal/computeMetadata"
                       "/v1/instance/"
                       "network-interfaces/0/access-configs/0/external-ip"),
                      headers={"Metadata-Flavor": "Google"}).content.strip()


def TryFunctionWithTimeout(func, error_handler, num_tries,
                           sleep_between_attempt_secs, *args, **kwargs):
  """The function tries to run a function without any exception.

  The function tries for a certain number of tries. If it cannot succeed,
  it raises BenchmarkError.
  Args:
    func: the function to try running without exception
    error_handler: the exception that the function should catch and keep trying.
    num_tries: number of tries it should make before raising the final
    exception
    sleep_between_attempt_secs: number of seconds to sleep between each retry
    *args: arguments to the function
    **kwargs: named arguments to the function
  Raises:
    BenchmarkError: When all tries are failed.
  """
  count = num_tries
  while count > 0:
    try:
      count -= 1
      ret_val = func(*args, **kwargs)
      if not ret_val:
        return
      else:
        print ret_val
    except error_handler as e:
      print e
    print ("Problem running function, {}. Trying again after"
           " {}s. Total tries left: {}.").format(func,
                                                 sleep_between_attempt_secs,
                                                 count)
    time.sleep(sleep_between_attempt_secs)
  raise BenchmarkError("All tries failed.")


def GetBooleanFormattedArgument(boolean_var, arg_name):
  """This function appends argument to the `main command`.

  It takes a boolean var and decides whether to add the arg or append --no-
  in front of the argument. It also adds any default argument along with it.

  Args:
    boolean_var: the boolean variable to decide whether to append --no- for
    `arg_name`
    arg_name: name of the argument to append
  Returns:
    Returns the appended command
  """
  if boolean_var:
    formatted_arg = "--{}".format(arg_name)
  else:
    formatted_arg = "--no-{}".format(arg_name)
  return formatted_arg


def RunBenchmark(args, logfile):
  """This function provides top-level control over benchmark execution.

  Args:
    args: the arguments provided to the top-level Python script
    logfile: an opened filestream for logging
  Raises:
    BenchmarkError: Raised when scp cannot connect
  """
  scripts_path = os.path.realpath(args.scripts_path)
  envoy_config_path = os.path.realpath(args.envoy_config_path)

  if args.create_delete:
    sh_utils.RunGCloudCompute(["instances", "create", "--zone",
                               args.zone, args.vm_name, "--custom-cpu",
                               str(args.cpu), "--custom-memory",
                               str(args.ram), "--image-family",
                               args.os_img_family, "--image-project",
                               args.os_img_project,
                               "--scopes",
                               "default,sql,sql-admin,cloud-platform",
                               "--service-account", args.service_account],
                              args.project,
                              logfile=logfile)
    # cloud-platform scope is used to authorize the VM to
    # do `gcloud sql` and other operations
    print "Instance created successfully."
  else:
    print "Instance creation is skipped due to --no-create_delete"

  TryFunctionWithTimeout(CheckStatus, BenchmarkError, args.num_retries,
                         args.sleep_between_retry, args)

  TryFunctionWithTimeout(sh_utils.RunSCPLocalToRemote, RuntimeError,
                         args.num_retries, args.sleep_between_retry,
                         [args.local_envoy_binary_path], args.username,
                         args.vm_name, dest="./envoy-fastbuild",
                         logfile=logfile, zone=args.zone,
                         project=args.project)
  print "Envoy binary transfer complete."

  sh_utils.RunSCPLocalToRemote(["{}/*".format(scripts_path)], args.username,
                               args.vm_name,
                               logfile=logfile,
                               zone=args.zone, project=args.project)
  print "Script transfer complete."

  sh_utils.RunSSHCommand(args.username, args.vm_name,
                         args=["--command", "mkdir -p \"envoy-configs\""],
                         logfile=logfile,
                         zone=args.zone, project=args.project)

  sh_utils.RunSCPLocalToRemote(["{}/*".format(envoy_config_path)],
                               args.username, args.vm_name,
                               dest="./envoy-configs/",
                               logfile=logfile,
                               zone=args.zone, project=args.project)
  print "Envoy configs transfer complete. Setting up the environment."

  nginx_start_core, nginx_end_core = args.nginx_cores.split(",")
  # total cores available are: int(nginx_end_core) - int(nginx_start_core) + 1
  # but one is master process, so that is not included in calculation below
  nginx_worker_proc_count = int(nginx_end_core) - int(nginx_start_core)
  if args.setup:
    print "Setup started (this may take some time)..."
    sh_utils.RunSSHCommand(args.username, args.vm_name,
                           args=["--command", "sudo chmod +x *.sh", "--", "-t"],
                           logfile=logfile,
                           zone=args.zone, project=args.project)
    sh_utils.RunSSHCommand(args.username, args.vm_name,
                           args=["--command",
                                 ("sudo bash ./init-script.sh {} {}"
                                  " {ssl} {http2}").format(
                                      args.username, nginx_worker_proc_count,
                                      ssl="--ssl" if args.ssl else "--no-ssl",
                                      http2="--h1" if args.h1 else "--no-h1"),
                                 "--", "-t"],
                           logfile=logfile,
                           zone=args.zone, project=args.project)
    print "Setup complete. Running Benchmark."
  else:
    # even if setup is skipped, we need to change the ownership of nginx log
    sh_utils.RunSSHCommand(args.username, args.vm_name,
                           args=["--command",
                                 ("sudo chown -R {}:{} /var/log/nginx "
                                  "/etc/nginx/").format(
                                      args.username, args.username),
                                 "--", "-t"],
                           logfile=logfile,
                           zone=args.zone, project=args.project)
    # the nginx worker processes count setup
    sh_utils.RunSSHCommand(args.username, args.vm_name,
                           args=["--command",
                                 ("python generate_config.py ./templates/ "
                                  "--worker_proc_count {} {ssl}"
                                  " {http2}").format(
                                      nginx_worker_proc_count,
                                      ssl="--ssl" if args.ssl else "--no-ssl",
                                      http2="--h1" if args.h1 else "--no-h1")],
                           logfile=logfile,
                           zone=args.zone, project=args.project)
    sh_utils.RunSSHCommand(args.username, args.vm_name,
                           args=["--command",
                                 ("python generate_scripts.py ./templates/ "
                                  "{}").format(
                                      args.username)],
                           logfile=logfile,
                           zone=args.zone, project=args.project)
    sh_utils.RunSSHCommand(args.username, args.vm_name,
                           args=["--command", "sudo make nginx",
                                 "--", "-t"],
                           logfile=logfile,
                           zone=args.zone, project=args.project)
    print "Setup is skipped due to --no-setup."

  # TODO(sohamcodes): this currently takes a fixed config for Envoy. It needs
  # to be changed in future to take multiple configs and run independently.
  print "Benchmarking is started."
  sh_utils.RunSSHCommand(args.username, args.vm_name,
                         args=["--command",
                               ("python distribute_proc.py "
                                "./envoy-fastbuild ./envoy-configs/"
                                "simple-loopback.json result.json "
                                "--nginx_cores {} "
                                "--envoy_cores {} "
                                "--h2load_cores {} "
                                "--h2load_warmup {} "
                                "--h2load_clients {} "
                                "--h2load_duration {} "
                                "--h2load_timeout {} "
                                "--h2load_con_conn {} "
                                "--num_iter {}"
                                "--arrangement {} {ssl} {http2}").format(
                                    args.nginx_cores, args.envoy_cores,
                                    args.h2load_cores, args.h2load_warmup,
                                    args.h2load_clients, args.h2load_duration,
                                    args.h2load_timeout, args.h2load_con_conn,
                                    args.num_iter, args.arrangement,
                                    ssl="--ssl" if args.ssl else "--no-ssl",
                                    http2="--h1" if args.h1 else "--no-h1")],
                         logfile=logfile, zone=args.zone, project=args.project)
  print "Benchmarking done successfully."

  ownip = StringIO.StringIO()
  sh_utils.RunSSHCommand(args.username, args.vm_name,
                         args=["--command",
                               ("echo -e \"import benchmark\nprint "
                                "benchmark.GetOwnIP()\" | python")],
                         logfile=ownip, zone=args.zone, project=args.project)

  data_store_command = ("python store_data.py --ownip {}"
                        " --runid {} --envoy_hash {} --username {}").format(
                            ownip.getvalue().strip(),
                            args.runid, args.envoy_hash, args.db_username)

  data_store_command = "{} {} --db_instance_name {}".format(
      data_store_command, GetBooleanFormattedArgument(
          args.create_db_instance, "create_instance"), args.db_instance_name)

  data_store_command = "{} {} --database {}".format(
      data_store_command, GetBooleanFormattedArgument(
          args.create_db, "create_db"), args.database)

  data_store_command = "{} {}".format(
      data_store_command,
      GetBooleanFormattedArgument(args.delete_db, "delete_db"))

  sh_utils.RunSSHCommand(args.username, args.vm_name,
                         args=["--command",
                               data_store_command],
                         logfile=logfile, zone=args.zone, project=args.project)
  print "Data stored into database."

  if args.create_delete:
    print "Deleting instance. Wait..."
    # pexpect.run does not take argument as arrays
    pexpect.run(("gcloud compute --project {}"
                 " instances delete {} --zone {}").format(
                     args.project, args.vm_name, args.zone),
                events={"Do you want to continue (Y/n)?": "Y\n"},
                logfile=logfile,
                timeout=None)
    print "Instance deleted."
  else:
    print "Instance deletion is skipped due to --no-create_delete."


def main():
  parser = argparse.ArgumentParser(
      formatter_class=argparse.ArgumentDefaultsHelpFormatter)
  parser.add_argument("--service_account",
                      help="email-id of the service-account",
                      default="envoy-service@envoy-ci.iam.gserviceaccount.com")
  parser.add_argument("--vm_name",
                      help="name of the virtual machine"
                           " that you want to create",
                      default="envoy-vm")
  parser.add_argument("--local_envoy_binary_path",
                      help="local relative path of the envoy binary",
                      default="./envoy-fastbuild")
  curdir = os.getcwd()
  parser.add_argument("--scripts_path",
                      help="local relative path to the directory of all helper"
                           " scripts and configs", default=curdir)
  parser.add_argument("--envoy_config_path",
                      help="local relative path to the directory of "
                           "the envoy configs",
                      default="./envoy-configs")
  parser.add_argument("--username",
                      help="username on the VM in the cloud-platform",
                      default="envoy")
  parser.add_argument("--zone", help="the zone where you want "
                                     "to create the VM.",
                      default="us-east1-b")
  parser.add_argument("--cpu", help="number of CPU cores.",
                      type=int, default=20)
  parser.add_argument("--ram", help="amount of ram in the VM in MB.",
                      type=int, default=76)
  parser.add_argument("--os_img_family", help="the os in which you want the "
                                              "benchmark.",
                      default="ubuntu-1604-lts")
  parser.add_argument("--os_img_project",
                      help="the project in which the os can be found.",
                      default="ubuntu-os-cloud")
  parser.add_argument("--project",
                      help="the project name in Google Cloud.",
                      default="envoy-ci")
  parser.add_argument("--logfile",
                      help="the local log file for this script. New log will be"
                           "appended to this file.", default="benchmark.log")
  parser.add_argument("--num_retries",
                      help="the number of retries for a single command.",
                      type=int, default=15)
  parser.add_argument("--sleep_between_retry",
                      help="number of seconds to sleep between each retry.",
                      type=int, default=5)
  parser.add_argument("--db_instance_name",
                      help="the name of the gcloud instance",
                      default="envoy-db-instance")
  parser.add_argument("--tier", help="the tier of GCloud SQL service",
                      default="db-n1-standard-2")
  parser.add_argument("--db_username", help="username on the DB",
                      default="root")
  parser.add_argument("--table_name", help=("the table which stores "
                                            "the benchmarking data"),
                      default="envoy_stat")
  parser.add_argument("--envoy_hash",
                      help="the hash of envoy version",
                      required=True)
  parser.add_argument("--runid",
                      help="the run id of this benchmark",
                      default="0")
  parser.add_argument("--database", help="name of the database",
                      default="envoy_stat_db")
  # This argument is appended with the category (Direct/Envoy) in the DB
  # The argument tells what was the configuration of the machines and experiment
  # Such as whether it was a single-vm, whether the VM was permanent one
  # or created newly everytime the test was being conducted
  parser.add_argument("--arrangement", help=("the type of arrangement of"
                                             "machines in"
                                             " this experiment."),
                      default="single-vm-permanent")
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
                      help=("period of time in seconds"
                            " for measurements in h2load"),
                      default="5")
  parser.add_argument("--h2load_timeout",
                      help="the maximum number of seconds to wait for h2load"
                           " to return some result", type=int, default=120)
  parser.add_argument("--num_iter",
                      help=("the number of times h2load will be"
                            " executed, separately for direct and Envoy"),
                      type=int, default=5)

  utils.CreateBooleanArgument(parser, "create_delete",
                              ("if you want to create and "
                               "delete new benchmarking VM."),
                              create_delete=True)

  utils.CreateBooleanArgument(parser, "setup",
                              ("if you want to run"
                               " setup on benchmarking VM."),
                              setup=True)

  utils.CreateBooleanArgument(parser, "create_db_instance",
                              ("turn on if you want to create"
                               " a Google Cloud SQL instance"),
                              create_db_instance=True)

  utils.CreateBooleanArgument(parser, "create_db",
                              ("turn on if you want"
                               " to create the DB"),
                              create_db=True)

  utils.CreateBooleanArgument(parser, "delete_db",
                              ("turn on if you want"
                               " to delete the DB"),
                              delete_db=True)
  utils.CreateBooleanArgument(parser, "ssl",
                              ("turn on if you want"
                               " to enable ssl for the benchmarking"),
                              ssl=True)
  utils.CreateBooleanArgument(parser, "h1",
                              ("turn on if you want"
                               " to enable HTTP1.1, instead of default h2"),
                              h1=False)

  args = parser.parse_args()

  with open(args.logfile, "ab") as logfile:
    RunBenchmark(args, logfile)


if __name__ == "__main__":
  main()
