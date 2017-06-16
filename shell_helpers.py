"""The file contains some helper functions to the shell commands."""

import pexpect


def FormatRemoteHost(username, remotehost):
  """This function returns a formatted remote host for ssh, scp.

  Args:
    username: username on remote host
    remotehost: name of remotehost
  Returns:
    A formatted string of remote location for ssh
  """
  command = "{}@{}".format(username, remotehost)
  return command


def FormatRemoteDestination(username, remotehost, dest="./"):
  """This function returns a formatted remote host for scp.

  Args:
    username: username on remote host
    remotehost: name of remotehost
    dest: destination path on remote host. default: ./
  Returns:
    A formatted string of remote location for scp
  """
  command = "{}:\"{}\"".format(FormatRemoteHost(username, remotehost), dest)
  return command


def WrapOverBash(args):
  """This function takes any arguments and wraps over bash.

  Args:
    args: array of arguments.
  Returns:
    an array prepended by ["bash", "-c"]
  """
  command = ["bash", "-c"]
  command.append(" ".join(args))
  return command


def GetSCPLocalToRemote(sourcefiles, username, remotehost, dest="./"):
  """The function returns a formatted scp command for local to remote transfers.

  It expects one or more source files and single destination. Destination can
  be directory or file.
  Args:
    sourcefiles: array of sourcefiles to be copied
    username: username on the remotehost
    remotehost: name of the remotehost on which files will be transferred
    dest: destination directory on the remotehost
  Returns:
    Returns the formatted scp command
  """
  command = ["scp", "--recurse"]
  command.extend(sourcefiles)
  command.append(FormatRemoteDestination(username, remotehost, dest=dest))
  return command


def GetSSHCommand(username, remotehost, args=None, zone=None):
  """The function returns formatted ssh command.

  Args:
    username: username on the remotehost
    remotehost: name of the remotehost on which files will be transferred
    args: any extra arguments with the ssh, as array
    zone: the zone in which the remotehost is located
  Returns:
    Formatted ssh command
  """
  command = ["ssh"]
  if zone:
    command.extend(["--zone", zone])
  command.append(FormatRemoteHost(username, remotehost))
  if args:
    command.extend(args)
  return command


def GetGcloud(args, project=None):
  """Get gcloud command with arguments.

  Functionalities might be expanded later to run gcloud commands.
  Args:
    args: command with arguments as an array
    project: the project on which the glcoud compute will work
  Returns:
    returns thr formatted command for gcloud compute
  """
  command = ["gcloud", "compute"]
  if project:
    command.extend(["--project", project])

  command.extend(args)
  return command


def RunCommand(args, timeout=None, logfile=None):
  """Runs a given command through pexpect.run.

  This function acts as a wrapper over pxpect.run . You can have exception or
  return values based on the exitstatus of the command execution. If exitstatus
   is not zero, then it will return -1, unless you want RuntimeError. If there
  is TIMEOUT, then exception is raised. If events do not match, command's
  output is printed, and -1 is returned.
  Args:
    args: command with arguments as an array
    timeout: timeout for pexpect.run .
    logfile: an opened filestream to write the output
  Raises:
    RuntimeError: Command's exit status is not zero
  Returns:
    Returns -1, if bad exitstatus is not zero and when events do not match
    Otherwise returns 0, if everything is fine
  """
  child = pexpect.spawn(args[0], args=args[1:], timeout=timeout,
                        logfile=logfile)
  child.expect(pexpect.EOF)
  child.close()
  if child.exitstatus:
    print args
    raise RuntimeError(("Error: {}\nProblem running command. "
                        "Exit status: {}").format(child.before,
                                                  child.exitstatus))
  return 0


def RunSSHCommand(username, remotehost, args=None, logfile=None, zone=None,
                  project=None):
  """This function runs the SSH command.

  Args:
    username: username on the remotehost
    remotehost: name of the remotehost on which files will be transferred
    args: any extra arguments with the ssh, as array
    logfile: an opened filestream to write log
    zone: the zone in which the remotehost is located
    project: the project in which the remotehost belongs to
  Returns:
    Returns the return value of RunCommand
  """
  command = GetGcloud(GetSSHCommand(username, remotehost, args=args, zone=zone),
                      project=project)
  return RunCommand(command, timeout=None,
                    logfile=logfile)


def RunSCPLocalToRemote(sourcefiles, username, remotehost, dest="./",
                        logfile=None, zone=None, project=None):
  """The function transfers files from local machine to remote host.

  It expects one or more source files and single destination. Destination can
  be directory or file. It acts just as a formatter, and not a syntax-checker
  Args:
    sourcefiles: array of sourcefiles to be copied
    username: username on the remotehost
    remotehost: name of the remotehost on which files will be transferred
    dest: destination directory on the remotehost
    logfile: an opened filestream to write log
    zone: the zone in which the remotehost is located
    project: the project in which the remotehost belongs to
  Returns:
    Returns the return value of RunCommand
  """
  command = GetSCPLocalToRemote(sourcefiles, username, remotehost, dest=dest)
  if zone:
    command.extend(["--zone", zone])
  command = WrapOverBash(GetGcloud(command,
                                   project=project))
  # this is done to allow wild card characters through pexpect
  # command = "bash -c \"{}\"".format(command)
  return RunCommand(command, logfile=logfile)


def RunSCPRemoteToLocal(args, logfile=None, zone=None, project=None):
  """This function does the opposite of RunSCPLocalToRemote.

  Copies a file or directory from remote host to local machine.
  Args:
    args: command with arguments as an array
    logfile: an opened filestream to write log
    zone: the zone in which the remotehost is located
    project: the project in which the remotehost belongs to
  Returns:
    Returns the return value of RunCommand
  """
  command = ["scp", "--recurse"]
  command.extend(args)
  if zone:
    command.extend(["--zone", zone])
  command = WrapOverBash(GetGcloud(command, project=project))
  return RunCommand(command, logfile=logfile)


def RunGCloudCompute(args, project, logfile=None):
  """This function runs a gcloud compute command.

  Args:
    args: command with arguments as an array
    project: the project in which the remotehost belongs to
    logfile: an opened filestream to write log
  Returns:
    Returns the return value of RunCommand
  """
  return RunCommand(GetGcloud(args, project), logfile=logfile)
