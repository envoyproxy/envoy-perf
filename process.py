"""The process class to run/kill linux processes."""

import shlex

import sh


class Process(object):
  """Process class which represents a process in linux."""

  def __init__(self, proc_command, outstream):
    """Initializer with arguments.

    Args:
      proc_command: the command to be run
      outstream: this can be plain string containing the file-name, or a file
      output stream. process' stdout, stderr are sent here
    """
    self.command = proc_command
    self.os = outstream
    self.pid = 0  # by default pid is zero; it's updated when command is run

  def RunProcess(self):
    """This function will run the process' command.

      It will run the command in background. Currenlty, we don't support running
      command in foreground.
    Returns:
        Doesn't return anything but
        runs the process by running the proc_command.
    """
    command_args = shlex.split(self.command)
    run = sh.Command(command_args[0])
    self.name = command_args[0]
    running_process = run(command_args[1:], _out=self.os, _err_to_out=True,
                          _bg=True)
    self.pid = running_process.pid

  def KillProcess(self, signal="-9"):
    """This function kills the process with default signal -9.

      This function uses by default, -SIGKILL or -9 signal to kill the
      processes, but it does not recursively kill the process-tree
    Args:
      signal: optional. Needed if you want to specify a particular kill signal.
      default is -9/-SIGKILL
    """
    sh.kill(signal, self.pid, _out=self.os)
