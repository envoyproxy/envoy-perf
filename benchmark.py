"""Top level python script to create VM, run benchmarking and get result."""


import argparse
import time

import pexpect


def GetSCPLocalToRemote(sourcefiles, username, remotehost, dest="./"):
  """The function returns a formatted scp command for local to remote transfers.

  It expects one or more source files and single destination. Destination can
  be directory or file.
  Args:
    sourcefiles: multiple source files in an array
    username: username on the remote host
    remotehost: name of remote host
    dest: a single directory or a file. default:./ which is home
  Returns:
    Returns the formatted scp command
  """
  command = "scp --recurse"
  for f in sourcefiles:
    command = "{} \"{}\"".format(command, f)
  return "{} \"{}\"@\"{}\":\"{}\"".format(command, username, remotehost, dest)


def GetSSHCommand(remotecommand, username, remotehost, flag=None):
  """The function returns formatted ssh command.

  Args:
    remotecommand: remote command to be executed
    username: username on the remote host
    remotehost: name of remote host
    flag: optional flag to be passed to the ssh
  Returns:
    Formatted ssh command
  """
  if flag is None:
    return "ssh \"{}\"@\"{}\" --command=\"{}\"".format(
        username, remotehost, remotecommand)
  else:
    return ("ssh \"{}\"@\"{}\" --ssh-flag=\"{}\""
            " --command=\"{}\"").format(username, remotehost, flag,
                                        remotecommand)


def GetGcloud(arguments):
  """Get gcloud command with arguments.

  Functionalities might be expanded later to run gcloud commands.
  Args:
    arguments: arguments to be given to gcloud compute
  Returns:
    returns thr formatted command for gcloud compute
  """
  return "gcloud compute {}".format(arguments)


def RunCommand(command, timeout=180, logfile=open("logfile.log", "a"), ev=None,
               exceptiononbadexit=False):
  """Runs a given command through pexpect.run.

  This function acts as a wrapper over pxpect.run . You can have exception or
  return values based on the exitstatus of the command execution. If exitstatus
   is not zero, then it will return -1, unless you want RuntimeError. If there
  is TIMEOUT, then exception is raised. If events do not match, command's
  output is printed, and -1 is returned.
  Args:
    command: the command to run via pexpect.run
    timeout: timeout for pexpect.run . default: 180 seconds
    logfile: an opened filestream to write the output
    ev: any events that is to be attached to pexpect.run
    exceptiononbadexit: do you want an exception if a bad exit happens
  Returns:
    Returns -1, if bad exitstatus is not zero and exceptiononbadexit is False
    and when events do not match
    Otherwise returns 0, if everything is fine
  """
  try:
    (command_output, exitstatus) = pexpect.run(command, timeout=timeout,
                                               withexitstatus=True,
                                               logfile=logfile, events=ev)
    if exitstatus != 0:
      print command_output
      if exceptiononbadexit:
        raise RuntimeError("Exit status: {}.".format(exitstatus))
      return -1
  except pexpect.TIMEOUT:
    raise RuntimeError("Following command taking too long: {}", command)
  except pexpect.EOF:
    print "EOF found."
    print command_output
    return -1
  return 0


def RunSSHCommand(command, username, remotehost, flag=None):
  """This function runs the SSH command.

  Args:
    command: the command to run on remote host
    username: the username to login to remote host
    remotehost: name of remote host
    flag: optional flags to ssh
  Returns:
    Returns the return value of RunCommand
  """
  command = GetGcloud(GetSSHCommand(command, username, remotehost, flag=flag))
  return RunCommand(command, exceptiononbadexit=True, timeout=None)


def RunSCPLocalToRemote(sourcefiles, username, remotehost, dest="./",
                        exceptiononbadexit=False):
  """The function transfers files from local machine to remote host.

  It expects one or more source files and single destination. Destination can
  be directory or file. It acts just as a formatter, and not a syntax-checker
  Args:
    sourcefiles: multiple source files in an array
    username: username on the remote host
    remotehost: name of remote host
    dest: a single directory or a file. default:./ which is home
    exceptiononbadexit: do you want an exception if a bad exit happens
  Returns:
    Returns the return value of RunCommand
  """
  command = GetGcloud(GetSCPLocalToRemote(sourcefiles, username, remotehost,
                                          dest=dest))
  # this is done to allow wild card characters through pexpect
  command = "bash -c \"{}\"".format(command)
  return RunCommand(command, exceptiononbadexit=exceptiononbadexit)


def RunSCPRemoteToLocal(source, username, remotehost, dest,
                        exceptiononbadexit=True):
  """This function does the opposite of RunSCPLocalToRemote.

  Copies a file or directory from remote host to local machine.
  Args:
    source: source filename
    username: username on the remote host
    remotehost: name of remote host
    dest: local filename
    exceptiononbadexit: do you want an exception if bad exit happens
  Returns:
    Returns the return value of RunCommand
  """
  command = ("bash"
             " -c \"{}\"").format(GetGcloud("scp --recurse {}@{}:{} {}".format(
                 username, remotehost, source, dest)))
  return RunCommand(command, exceptiononbadexit=exceptiononbadexit)


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

  RunCommand(GetGcloud(("instances create --zone {} {} "
                        " --custom-cpu {} --custom-memory {}"
                        " --image-family {} --image-project {}").format(
                            args.zone, args.vm_name, args.cpu, args.ram,
                            args.os_img_family, args.os_img_project)),
             exceptiononbadexit=True)
  # following code will not be executed if there is an error
  print "Instance created successfully."

  RunCommand("gcloud config set compute/zone {}".format(args.zone),
             exceptiononbadexit=True)
  RunCommand("gcloud config set project {}".format(args.project),
             exceptiononbadexit=True)

  # the following loop checks whether the current instance is up and running
  while True:
    status = pexpect.spawn(GetGcloud("instances describe {} --zone {}".format(
        args.vm_name, args.zone)), logfile=open(args.logfile, "a"))
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

  RunCommand("chmod 766 transfer_files.sh run_remote_scripts.sh",
             exceptiononbadexit=True)

  # TODO(sohamcodes):remote envoy binary is hardcoded here.
  # It can be made dynamic.
  count = 15  # scp will be tried 15 times before we say it's failed
  while count > 0 and RunSCPLocalToRemote([envoy_path], args.username,
                                          args.vm_name,
                                          dest="./envoy-fastbuild") != 0:
    count -= 1
    print ("Port 22 is not ready yet. Trying again after 5s. "
           "Total try left: {}").format(count)
    time.sleep(5)

  if count == 0:
    raise RuntimeError("scp is not working with remote machine {}".format(
        args.vm_name))

  print "envoy binary transfer complete."

  RunSCPLocalToRemote(["{}/*".format(scripts_path)],
                      args.username, args.vm_name, exceptiononbadexit=True)

  print "Script transfer complete."

  RunSSHCommand("mkdir -p \"envoy-configs\"", args.username, args.vm_name)

  RunSCPLocalToRemote(["{}/*".format(envoy_config_path)],
                      args.username, args.vm_name, dest="./envoy-configs/",
                      exceptiononbadexit=True)
  print "Envoy configs transfer complete."

  RunSSHCommand("sudo chmod +x *.sh", args.username, args.vm_name, flag="-t")

  RunSSHCommand("sudo bash ./init-script.sh {}".format(
      args.username), args.username, args.vm_name, flag="-t")

  print "Setup complete. Running Benchmark."

  RunSSHCommand("python distribute_proc.py "
                "./envoy-fastbuild ./envoy-configs/"
                "simple-loopback.json result.txt",
                args.username, args.vm_name)
  print "Benchmarking done successfully."

  RunSCPRemoteToLocal("./result.txt", args.username, args.vm_name, "./")
  print "Check {}/result.txt file.".format(
      result_dir)
  print "Deleting instance. Wait..."

  RunCommand(GetGcloud("instances delete {}".format(args.vm_name)),
             ev={"Do you want to continue (Y/n)?": "Y\n"},
             exceptiononbadexit=True)

  print "Instance deleted."

if __name__ == "__main__":
  main()
