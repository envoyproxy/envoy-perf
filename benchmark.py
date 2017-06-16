"""Top level python script to create VM, run benchmarking and get result."""


import argparse
import os
import re
import subprocess
import time

import pexpect
import shell_helpers as sh_utils


class BenchmarkError(Exception):
  pass


def CheckStatus(args):
  """This function tries to check the status of the VM Instance.

  Args:
    args: all the arguments to the program
  Raises:
    BenchmarkError: If instance is not RUNNING
  Returns:
    Returns 0, if everything is fine
  """
  status = subprocess.check_output(sh_utils.GetGcloud([
      "instances", "describe",
      args.vm_name, "--zone",
      args.zone], project=args.project))
  cur_status = re.search(r"status:\s+([A-Z]+)", status)
  if cur_status.group(1) == "RUNNING":
    print "Instance is running successfully."
    return 0
  else:
    raise BenchmarkError(("Instance is not running"
                          ". Current status: {}").format(cur_status.group(1)))


def TryFunctionWithTimeout(func, error_handler, num_tries, sleep_bt_attempts,
                           *args, **kwargs):
  """The function tries to run a function without any exception.

  The function tries for a certain number of tries. If it cannot succeed,
  it raises BenchmarkError.
  Args:
    func: the function to try running without exception
    error_handler: the exception that the function should catch and keep trying.
    num_tries: number of tries it should make before raising the final
    exception
    sleep_bt_attempts: number of seconds to sleep between each retry
    *args: arguments to the function
    **kwargs: named arguments to the function
  Raises:
    BenchmarkError: When all tries are failed.
  """
  count = num_tries
  while count > 0:
    try:
      func(*args, **kwargs)
      return
    except error_handler as e:
      count -= 1
      print e
      print ("Problem in connecting. Trying again after"
             " {}s. Total try left: {}.").format(sleep_bt_attempts, count)
    time.sleep(sleep_bt_attempts)
  raise BenchmarkError("All tries failed.")


def RunBenchmark(args, logfile):
  """This function actually runs the whole benchmarking script.

  Args:
    args: the arguments provided to the top-level Python script
    logfile: an opened filestream for logging
  Raises:
    BenchmarkError: Raised when scp cannot connect
  """
  scripts_path = os.path.realpath(args.scripts_path)
  envoy_config_path = os.path.realpath(args.envoy_config_path)
  result_dir = os.path.realpath(args.result_dir)

  if args.create_delete:
    sh_utils.RunGCloudCompute(["instances", "create", "--zone",
                               args.zone, args.vm_name, "--custom-cpu",
                               str(args.cpu), "--custom-memory",
                               str(args.ram), "--image-family",
                               args.os_img_family, "--image-project",
                               args.os_img_project], args.project,
                              logfile=logfile)
    print "Instance created successfully."
  else:
    print "Instance creation is skipped due to --no-create_delete"

  # sh_utils.RunCommand(["gcloud", "config", "set", "compute/zone", args.zone],
  #                     logfile=logfile)
  # sh_utils.RunCommand(["gcloud", "config", "set", "project", args.project],
  #                     logfile=logfile)

  # sleep between attemps is hardcoded here, for now
  TryFunctionWithTimeout(CheckStatus, BenchmarkError, args.num_retries,
                         args.sleep_bt_retry, args)

  TryFunctionWithTimeout(sh_utils.RunSCPLocalToRemote, RuntimeError,
                         args.num_retries, args.sleep_bt_retry,
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

  if args.setup:
    sh_utils.RunSSHCommand(args.username, args.vm_name,
                           args=["--command", "sudo chmod +x *.sh", "--", "-t"],
                           logfile=logfile,
                           zone=args.zone, project=args.project)

    sh_utils.RunSSHCommand(args.username, args.vm_name,
                           args=["--command",
                                 "sudo bash ./init-script.sh {}".format(
                                     args.username),
                                 "--", "-t"],
                           logfile=logfile,
                           zone=args.zone, project=args.project)
    print "Setup complete. Running Benchmark."
  else:
    print "Setup is skipped due to --no-setup."

  # TODO(sohamcodes): this currently takes a fixed config for Envoy. It needs
  # to be changed in future to take multiple configs and run independently.
  sh_utils.RunSSHCommand(args.username, args.vm_name,
                         args=["--command",
                               ("python distribute_proc.py "
                                "./envoy-fastbuild ./envoy-configs/"
                                "simple-loopback.json result.txt")],
                         logfile=logfile, zone=args.zone, project=args.project)
  print "Benchmarking done successfully."

  sh_utils.RunSCPRemoteToLocal([sh_utils.FormatRemoteDestination(
      args.username, args.vm_name, "./result.txt"),
                                "{}/".format(result_dir)], logfile=logfile,
                               zone=args.zone, project=args.project)

  print "Check {}/result.txt file.".format(
      result_dir)

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
  parser.add_argument("--vm_name",
                      help="name of the virtual machine"
                           " that you want to create",
                      default="envoy-vm")
  parser.add_argument("--local_envoy_binary_path",
                      help="local absolute path of the envoy binary",
                      default="./envoy-fastbuild")
  parser.add_argument("--scripts_path",
                      help="local absolute path to the directory of all helper"
                           " scripts and configs", default="./")
  parser.add_argument("--envoy_config_path",
                      help="local absolute path to the directory of "
                           "the envoy configs",
                      default="./envoy-configs")
  parser.add_argument("--result_dir",
                      help="local absolute path to the directory of the "
                           "benchmarking result file",
                      default="./")
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
                      help="the project name.",
                      default="envoy-ci")
  parser.add_argument("--logfile",
                      help="the local log file for this script. New log will be"
                           "appended to this file.", default="benchmark.log")
  parser.add_argument("--num_retries",
                      help="the number of retries for a single command.",
                      type=int, default=15)
  parser.add_argument("--sleep_bt_retry",
                      help="number of seconds to sleep between each retry.",
                      type=int, default=5)

  create_del_parser = parser.add_mutually_exclusive_group(required=False)
  create_del_parser.add_argument("--create_delete", dest="create_delete",
                                 action="store_true",
                                 help="if you want to create/delete new VM.")
  create_del_parser.add_argument("--no-create_delete", dest="create_delete",
                                 action="store_false",
                                 help=("if you don't want to "
                                       "create/delete new VM."))
  parser.set_defaults(create_delete=True)

  skip_setup_parser = parser.add_mutually_exclusive_group(required=False)
  skip_setup_parser.add_argument("--setup", dest="setup",
                                 action="store_true",
                                 help="if you want to run setup.")
  skip_setup_parser.add_argument("--no-setup", dest="setup",
                                 action="store_false",
                                 help="if you want to skip setup.")
  parser.set_defaults(setup=True)

  # TODO(sohamcodes): ability to add more customization on how nginx, Envoy and
  # h2load runs on the VM, by adding more top level parameters

  args = parser.parse_args()

  try:
    logfile = open(args.logfile, "ab")
  finally:
    RunBenchmark(args, logfile)


if __name__ == "__main__":
  main()
