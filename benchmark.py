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
      ret_val = func(*args, **kwargs)
      count -= 1
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

  if args.setup:
    print "Setup started (this may take some time)..."
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
                                "simple-loopback.json result.json")],
                         logfile=logfile, zone=args.zone, project=args.project)
  print "Benchmarking done successfully."

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

  ownip = StringIO.StringIO()
  sh_utils.RunSSHCommand(args.username, args.vm_name,
                         args=["--command",
                               ("echo -e \"import benchmark\nprint "
                                "benchmark.GetOwnIP()\" | python")],
                         logfile=ownip, zone=args.zone, project=args.project)

  data_store_command = ("python store_data.py --ownip {}"
                        " --runid {} --envoy_hash {}").format(
                            ownip.getvalue().strip(),
                            args.runid, args.envoy_hash)

  if args.create_db_instance:
    data_store_command = ("{} --create_instance --db_instance_name {}").format(
        data_store_command, args.db_instance_name)
  else:
    data_store_command = "{} --no-create_instance".format(data_store_command)

  if args.create_db:
    data_store_command = ("{} --create_db --database {}").format(
        data_store_command, args.database)
  else:
    data_store_command = "{} --no-create_db".format(data_store_command)

  if args.delete_db:
    data_store_command = ("{} --delete_db").format(
        data_store_command)
  else:
    data_store_command = "{} --no-delete_db".format(data_store_command)

  sh_utils.RunSSHCommand(args.username, args.vm_name,
                         args=["--command",
                               data_store_command],
                         logfile=logfile, zone=args.zone, project=args.project)
  print "Data stored into database."


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
  parser.add_argument("--scripts_path",
                      help="local relative path to the directory of all helper"
                           " scripts and configs", default="./")
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
  parser.add_argument("--db_password",
                      help="password for the username on the DB",
                      default="password")
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

  utils.CreateBooleanArgument(parser, "create_delete",
                              ("if you want to create/"
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

  # TODO(sohamcodes): ability to add more customization on how nginx, Envoy and
  # h2load runs on the VM, by adding more top level parameters

  args = parser.parse_args()

  with open(args.logfile, "ab") as logfile:
    RunBenchmark(args, logfile)


if __name__ == "__main__":
  main()
