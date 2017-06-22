"""The process class to run/kill linux processes."""

import shlex

import sh


class Process(object):
  """Process class which represents a process in linux."""

  def __init__(self, proc_command, outstream, args=None):
    """Initializer with arguments.

    Args:
      proc_command: the command to be run
      outstream: this can be plain string containing the file-name, or a file
      output stream. process' stdout, stderr are sent here
      args: if you want to provide arguments as an array. Make sure to provide
      proc_command as a single command, in case you are providing this value
    Raises:
      ValueError: when proc_command is empty or have no value
    """
    if not proc_command.strip():
      raise ValueError("argument proc_command should be given.")
    self.command = proc_command
    self.os = outstream
    self.pid = 0  # by default pid is zero; it's updated when command is run
    self.args = args

  def RunProcess(self):
    """This function will run the process' command.

      It will run the command in background. Currenlty, we don't support running
      command in foreground.
    Returns:
        Doesn't return anything but
        runs the process by running the proc_command.
    """
    if not self.args:  # when arguments are not provided as array
      command_args = shlex.split(self.command)
      run = sh.Command(command_args[0])
      self.name = command_args[0]
      command_args = command_args[1:]
    else:  # when argument is provided as array
      command_args = self.args
      run = sh.Command(self.command)
      self.name = self.command

    running_process = run(command_args, _out=self.os, _err_to_out=True,
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
