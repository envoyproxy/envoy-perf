"""
Module to execute a command and return the output generated.  Returns both
stdout and stderr in the buffer.  We also convert bytes objects to a string
so callers manipulate one type of object
"""
import collections
import shlex
import subprocess
import logging

log = logging.getLogger(__name__)

CommandParameters = collections.namedtuple("CommandParameters", [
    'cwd', # A string specifying the working directory ofthe executing command
])

def run_command(cmd: str, parameters: CommandParameters) -> str:
  """Run the specified command returning its output to the caller.

  Args:
      cmd: The command to be executed
      parameters: Additional arguments provided to check_output. Most
        importantly, we specify 'cwd' which is the intended working directory
        where the command is to be executed.  Other parameters supported
        by the subprocess module will be added as they become necessary for
        execution.

  Returns:
      The output produced by the command

  Raises:
    subprocess.CalledProcessError if there was a failure executing the specified
      command
  """
  output = ''
  try:
    log.debug(f"Executing command: [{cmd}] with args [{parameters._asdict()}]")
    cmd_array = shlex.split(cmd)
    output = subprocess.check_output(
      cmd_array, stderr=subprocess.STDOUT, **parameters._asdict())

    if isinstance(output, bytes):
      output = output.decode('utf-8').strip()

    log.debug(f"Returning output: [{output}]")
  except subprocess.CalledProcessError as process_error:
    log.error(f"Unable to execute [{cmd}]: {process_error}")
    raise

  return output
