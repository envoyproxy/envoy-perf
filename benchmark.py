"""Top level python script to create VM, run benchmarking and get result."""

import argparse
import shlex

import pexpect
import sh  # sh is for more simplied shell calls


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
                      help="the project name"
                           "default: envoy-ci",
                      default="envoy-ci")
  parser.add_argument("--logfile",
                      help="the local log file for this script. default: "
                           "logfile.log", default="logfile.log")

  args = parser.parse_args()
  envoy_path = args.local_envoy_binary_path
  scripts_path = args.scripts_path
  envoy_config_path = args.envoy_config_path
  result_dir = args.result_dir

  create = pexpect.spawn(("gcloud compute instances create --zone {} {}"
                          " --custom-cpu {} --custom-memory {}"
                          " --image-family {} --image-project {}").format(
                              args.zone, args.vm_name, args.cpu, args.ram,
                              args.os_img_family, args.os_img_project),
                         logfile=open(args.logfile, "a")
                        )
  print "Instance created."
  create.close()

  # the following loop checks whether the current instance is up and running
  while True:
    status = pexpect.spawn("gcloud compute instances describe {}".format(
        args.vm_name), logfile=open(args.logfile, "a"))
    status.expect(r"status:\s+([A-Z+])")
    cur_status = status.match.group(1)
    if cur_status == "RUNNING":
      status.close()
      break
    status.close()

  config_setup = pexpect.spawn("gcloud config set compute/zone {}".format(
      args.zone), logfile=open(args.logfile, "a"))
  config_setup.close()
  config_setup = pexpect.spawn("gcloud config set project {}".format(
      args.project),
                               logfile=open(args.logfile, "a"))
  config_setup.close()

  sh.chmod("766", "transfer_files.sh", "run_remote_scripts.sh")
  transfer = pexpect.spawn("bash", "./transfer_files.sh", args.vm_name,
                           envoy_path, scripts_path, envoy_config_path)

  transfer.close()

  if transfer.exitstatus != 0:
    raise RuntimeError("Error in transferring files.")

  remote_run = pexpect.spawn("bash", "./run_remote_scripts.sh", args.vm_name,
                             args.username, result_dir)
  remote_run.close()

  if transfer.exitstatus != 0:
    raise RuntimeError("Error in remotely running scripts.")

if __name__ == "__main__":
  main()
