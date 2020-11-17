"""
Module to execute a command and return the output generated.  Returns both
stdout and stderr in the buffer.  We also convert a byte array to a string
so callers manipulate one type of object
"""
import shlex
import subprocess
import logging

log = logging.getLogger(__name__)


def run_command(cmd, **kwargs):
  """Run the specified command returning its output to the caller.

  Args:
      cmd: The command to be executed
      kwargs: Additional optional arguments provided to check_output

  Returns:
      The output produced by the command
  """
  output = ''
  try:
    log.debug(f"Executing command: {cmd} with args {kwargs}")
    cmd_array = shlex.split(cmd)
    output = subprocess.check_output(cmd_array, stderr=subprocess.STDOUT, **kwargs)

    if isinstance(output, bytes):
      output = output.decode('utf-8').strip()

    log.debug(f"Returning output: [{output}]")
  except subprocess.CalledProcessError as process_error:
    log.error(f"Unable to execute {cmd}: {process_error}")
    raise

  return output
