"""Top level python script to create VM, run benchmarking and get result."""


import argparse
import time
import pexpect

from shell_helpers import GetGcloud
from shell_helpers import RunCommand
from shell_helpers import RunSCPLocalToRemote
from shell_helpers import RunSCPRemoteToLocal
from shell_helpers import RunSSHCommand
from shell_helpers import RunGCloudCompute


def GetRemoteHost(username, remotehost):
  """This function returns a formatted remote host for ssh, scp.

  Args:
    username: username on remote host
    remotehost: name of remotehost
  Returns:
    A formatted string of remote location for ssh
  """
  return ("{}@{}").format(username, remotehost)

def GetRemoteDestination(username, remotehost, dest="./"):
  """This function returns a formatted remote host for scp.

  Args:
    username: username on remote host
    remotehost: name of remotehost
    dest: destination path on remote host. default: ./
  Returns:
    A formatted string of remote location for scp
  """
  return ("{}:\"{}\"").format(GetRemoteHost(username, remotehost), dest)

def main():
  parser = argparse.ArgumentParser()
  parser.add_argument("vm_name",
                      help="name of the virtual machine"
                           " that you want to create")
  parser.add_argument("local_envoy_binary_path",
                      help="local abosolute path of the envoy binary")
  parser.add_argument("scripts_path",
                      help="local absolute path to the directory of all helper"
                           " scripts and configs")
  parser.add_argument("envoy_config_path",
                      help="local absolute path to the directory of "
                           "the envoy configs")
  parser.add_argument("result_dir",
                      help="local absolute path to the directory of the "
                           "benchmarking result file")
  parser.add_argument("username",
                      help="username on the VM in the cloud-platform")
  parser.add_argument("--zone", help="the zone where you want to create the VM."
                                     " default: us-east1-b",
                      default="us-east1-b")
  parser.add_argument("--cpu", help="number of CPU cores."
                                    " default: 20", type=int, default=20)
  parser.add_argument("--ram", help="amount of ram in the VM in MB."
                                    " default: 76 MB", type=int, default=76)
  parser.add_argument("--os_img_family", help="the os in which you want the "
                                              "benchmark. default: ubuntu-1604-"
                                              "lts",
                      default="ubuntu-1604-lts")
  parser.add_argument("--os_img_project",
                      help="the project in which the os"
                           "can be found. default: ubuntu-os-cloud",
                      default="ubuntu-os-cloud")
  parser.add_argument("--project",
                      help="the project name."
                           "default: envoy-ci",
                      default="envoy-ci")
  parser.add_argument("--logfile",
                      help="the local log file for this script. New log will be"
                           "appended to this file. default: "
                           "benchmark.log", default="benchmark.log")
  # TODO(sohamcodes): ability to add more customization on how nginx, Envoy and
  # h2load runs on the VM, by adding more top level parameters

  args = parser.parse_args()
  envoy_path = args.local_envoy_binary_path
  scripts_path = args.scripts_path.rstrip("/")
  envoy_config_path = args.envoy_config_path.strip("/")
  result_dir = args.result_dir.rstrip("/")
  logfile = open(args.logfile, "ab")

  RunGCloudCompute(["instances", "create", "--zone", args.zone, args.vm_name,
                            "--custom-cpu", str(args.cpu), "--custom-memory",
                            str(args.ram), "--image-family",
                            args.os_img_family,
                            "--image-project", args.os_img_project],
                   logfile=logfile)

  # following code will not be executed if there is an error above
  print "Instance created successfully."

  RunCommand(["gcloud", "config", "set", "compute/zone", args.zone],
             logfile=logfile)
  RunCommand(["gcloud", "config", "set", "project", args.project],
             logfile=logfile)

  # the following loop checks whether the current instance is up and running
  while True:
    status = pexpect.spawn(("gcloud compute instances describe {} --zone"
                            " {}").format(
        args.vm_name, args.zone), logfile=logfile)
    try:
      status.expect(r"status:\s+([A-Z]+)")
      cur_status = status.match.group(1)
      if cur_status == "RUNNING":
        print "Instance is running successfully."
        status.close()
        break
      else:
        print "Instance is not running. Current status: {}.".format(cur_status)
        status.close()
    except Exception as e:
      print ("Status is not found. "
             "There is some problem in finding the instance.")

  RunCommand(["chmod", "766", "transfer_files.sh", "run_remote_scripts.sh"],
             logfile=logfile)

  # # TODO(sohamcodes):remote envoy binary is hardcoded here.
  # # It can be made dynamic.
  count = 15  # scp will be tried 15 times before we say it's failed
  while count > 0:
    try:
      RunSCPLocalToRemote([envoy_path, GetRemoteDestination(
          args.username, args.vm_name, "./envoy-fastbuild"
      )], logfile=logfile)
      break  # if it comes here then scp was successful
    except Exception as e:
      print e
      count -= 1
      print ("Port 22 is not ready yet. Trying again after 5s. "
             "Total try left: {}").format(count)
      time.sleep(5)

  if count == 0:
    raise RuntimeError("scp is not working with the remote machine, {}".format(
        args.vm_name))

  print "Envoy binary transfer complete."

  RunSCPLocalToRemote(["{}/*".format(scripts_path), GetRemoteDestination(
                      args.username, args.vm_name)], logfile=logfile)

  print "Script transfer complete."

  RunSSHCommand([GetRemoteHost(args.username, args.vm_name), "--command",
      "mkdir -p \"envoy-configs\""], logfile=logfile)

  RunSCPLocalToRemote(["{}/*".format(envoy_config_path), GetRemoteDestination(
      args.username, args.vm_name, dest="./envoy-configs/")],
                      logfile=logfile)
  print "Envoy configs transfer complete."

  RunSSHCommand([GetRemoteHost(args.username, args.vm_name),
      "--command", "sudo chmod +x *.sh", "--", "-t"], logfile=logfile)

  RunSSHCommand([GetRemoteHost(args.username, args.vm_name),
     "--command",
      "sudo bash ./init-script.sh {}".format(args.username), "--", "-t"],
                logfile=logfile)

  print "Setup complete. Running Benchmark."

  RunSSHCommand([GetRemoteHost(args.username, args.vm_name), "--command",
                "python distribute_proc.py "
                "./envoy-fastbuild ./envoy-configs/"
                "simple-loopback.json result.txt"], logfile=logfile)
  print "Benchmarking done successfully."

  RunSCPRemoteToLocal([GetRemoteDestination(args.username, args.vm_name,
      "./result.txt"), "{}/".format(result_dir)], logfile=logfile)
  print "Check {}/result.txt file.".format(
      result_dir)
  print "Deleting instance. Wait..."

  # pexpect.run does not take argument as arrays
  pexpect.run("gcloud compute instances delete {}".format(args.vm_name),
              events={"Do you want to continue (Y/n)?": "Y\n"}, logfile=logfile,
              timeout=None)

  print "Instance deleted."

if __name__ == "__main__":
  main()
