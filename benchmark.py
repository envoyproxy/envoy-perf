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


def FormatRemoteHost(username, remotehost):
  """This function returns a formatted remote host for ssh, scp.

  Args:
    username: username on remote host
    remotehost: name of remotehost
  Returns:
    A formatted string of remote location for ssh
  """
  return ("{}@{}").format(username, remotehost)


def FormatRemoteDestination(username, remotehost, dest="./"):
  """This function returns a formatted remote host for scp.

  Args:
    username: username on remote host
    remotehost: name of remotehost
    dest: destination path on remote host. default: ./
  Returns:
    A formatted string of remote location for scp
  """
  return ("{}:\"{}\"").format(FormatRemoteHost(username, remotehost), dest)


def RunBenchmark(args, logfile):
  """This function actually runs the whole benchmarking script.

  Args:
    args: the arguments provided to the top-level Python script
    logfile: an opened filestream for logging
  Raises:
    RuntimeError: Raised when scp cannot connect
  """

  if args.create_delete == "yes" or args.create_delete.strip() == "y":
    sh_utils.RunGCloudCompute(["instances", "create", "--zone",
                               args.zone, args.vm_name, "--custom-cpu",
                               str(args.cpu), "--custom-memory",
                               str(args.ram), "--image-family",
                               args.os_img_family, "--image-project",
                               args.os_img_project],
                              logfile=logfile)
    print "Instance created successfully."
  else:
    print ("You have selected not to create the Instance. "
           "No Instance is created")

  sh_utils.RunCommand(["gcloud", "config", "set", "compute/zone", args.zone],
                      logfile=logfile)
  sh_utils.RunCommand(["gcloud", "config", "set", "project", args.project],
                      logfile=logfile)

  args.scripts_path = os.path.realpath(args.scripts_path)
  args.envoy_config_path = os.path.realpath(args.envoy_config_path)
  args.result_dir = os.path.realpath(args.result_dir)

  # the following loop checks whether the current instance is up and running
  while True:
    # status = pexpect.spawn(("gcloud compute instances describe {} --zone"
    #                         " {}").format(args.vm_name, args.zone),
    #                        logfile=logfile)
    try:
      status = subprocess.check_output(sh_utils.GetGcloud([
          "instances", "describe",
          args.vm_name, "--zone",
          args.zone]))
      cur_status = re.search(r"status:\s+([A-Z]+)", status)
      if cur_status.group(1) == "RUNNING":
        print "Instance is running successfully."
        break
      else:
        print "Instance is not running. Current status: {}.".format(
            cur_status.group(1))
    except subprocess.CalledProcessError as e:
      print ("Status is not found. "
             "There is some problem in parsing the status of the Instance.")
      raise BenchmarkError(e)

  sh_utils.RunCommand(["chmod", "766", "transfer_files.sh",
                       "run_remote_scripts.sh"],
                      logfile=logfile)

  # # TODO(sohamcodes):remote envoy binary is hardcoded here.
  # # It can be made dynamic.
  count = 15  # scp will be tried 15 times before we say it's failed
  while count > 0:
    try:
      sh_utils.RunSCPLocalToRemote([args.local_envoy_binary_path,
                                    FormatRemoteDestination(args.username,
                                                            args.vm_name,
                                                            "./envoy-fastbuild"
                                                           )],
                                   logfile=logfile)
      break  # if it comes here then scp was successful
    except RuntimeError as e:
      print e
      count -= 1
      print ("Port 22 is not ready yet. Trying again after 5s. "
             "Total try left: {}").format(count)
      time.sleep(5)

  if count == 0:
    raise RuntimeError("scp cannot connect to the remote machine, {}".format(
        args.vm_name))

  print "Envoy binary transfer complete."

  sh_utils.RunSCPLocalToRemote(["{}/*".format(args.scripts_path),
                                FormatRemoteDestination(args.username,
                                                        args.vm_name)],
                               logfile=logfile)

  print "Script transfer complete."

  sh_utils.RunSSHCommand([FormatRemoteHost(args.username, args.vm_name),
                          "--command", "mkdir -p \"envoy-configs\""],
                         logfile=logfile)

  sh_utils.RunSCPLocalToRemote(["{}/*".format(args.envoy_config_path),
                                FormatRemoteDestination(args.username,
                                                        args.vm_name,
                                                        dest="./envoy-configs/")
                               ],
                               logfile=logfile)
  print "Envoy configs transfer complete. Setting up the environment."

  if args.skip_setup == "no" or args.create_delete.strip() == "n":
    sh_utils.RunSSHCommand([FormatRemoteHost(args.username, args.vm_name),
                            "--command", "sudo chmod +x *.sh", "--", "-t"],
                           logfile=logfile)

    sh_utils.RunSSHCommand([FormatRemoteHost(args.username, args.vm_name),
                            "--command",
                            "sudo bash ./init-script.sh {}".format(
                                args.username),
                            "--", "-t"],
                           logfile=logfile)
    print "Setup complete. Running Benchmark."
  else:
    print "You have selected not to run setup."

  # TODO(sohamcodes): this currently takes a fixed config for Envoy. It needs
  # to be changed in future to take multiple configs and run independently.
  sh_utils.RunSSHCommand([FormatRemoteHost(args.username, args.vm_name),
                          "--command", "python distribute_proc.py "
                          "./envoy-fastbuild ./envoy-configs/"
                          "simple-loopback.json result.txt"], logfile=logfile)
  print "Benchmarking done successfully."

  sh_utils.RunSCPRemoteToLocal([FormatRemoteDestination(args.username,
                                                        args.vm_name,
                                                        "./result.txt"),
                                "{}/".format(args.result_dir)], logfile=logfile)

  print "Check {}/result.txt file.".format(
      args.result_dir)

  if args.create_delete == "yes" or args.create_delete.strip() == "y":
    print "Deleting instance. Wait..."
    # pexpect.run does not take argument as arrays
    pexpect.run("gcloud compute instances delete {}".format(args.vm_name),
                events={"Do you want to continue (Y/n)?": "Y\n"},
                logfile=logfile,
                timeout=None)
    print "Instance deleted."
  else:
    print ("You have selected not to delete the Instance. "
           "No Instance is not deleted.")


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

  parser.add_argument("--create_delete", help="Do you want to create/delete"
                                              " a VM? (yes/no)",
                      default="yes")
  parser.add_argument("--skip_setup", help="Do you want to skip the setup?"
                                           "(yes/no)",
                      default="yes")

  # TODO(sohamcodes): ability to add more customization on how nginx, Envoy and
  # h2load runs on the VM, by adding more top level parameters

  args = parser.parse_args()

  try:
    logfile = open(args.logfile, "ab")
  finally:
    RunBenchmark(args, logfile)


if __name__ == "__main__":
  main()
