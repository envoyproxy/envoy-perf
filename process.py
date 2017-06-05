"""The process class to be used by other functions to run/kill linux processes.

"""

import io
import sh
import shlex


class Process(object):
  """Process class which represents a process in linux."""

  def __init__(self, pid=None, proc_name=None, proc_command=None,
               outstream=None):
    """Initializer with optional arguments.

    Args:
      pid: if pid is available
      proc_name: if pid is already there, then attach a proc_name
      proc_command: use this if you want to run a new process and don't have pid
      outstream: this can be plain string containing the file-name, or a file
      output stream
    """
    self.pid = pid
    self.name = proc_name
    self.command = proc_command
    self.os = outstream

  def run_process(self, background=False):
    """this function will run the command if command_pid is not None.

      Otherwise, the function has no effect.
    Args:
      background: True/False
    Returns:
        Doesn't return anything but
        runs the process by running the proc_command.
    """
    if self.command is not None:
      command_args = shlex.split(self.command)
      run = sh.Command(command_args[0])
      running_process = run(command_args[1:], _out=self.os, _bg=background)
      self.pid = running_process.pid
      self.name = command_args[0]

  def kill_process(self, signal="-9"):
    """this function kills the process.

      this function uses -TERM signal to kill the processes, but
      if it does not kill recursively kill the process-tree
    Args:
      signal: optional. Needed if you want to specify a particular kill signal.
      default is -9/-SIGKILL
    """
    sh.kill(signal, self.pid)
