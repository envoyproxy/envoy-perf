"""
Module to execute a command and return the output generated.  Returns both
stdout and stderr in the buffer.  We also convert bytes objects to a string
so callers manipulate one type of object
"""
import shlex
import subprocess
import typing
import logging
import tempfile

log = logging.getLogger(__name__)

# Encapsulates parameters and their values required to execute a command
CommandParameters = typing.NamedTuple("CommandParameters", [
    ('cwd', str), # A string specifying the working directory of the executing
                  # command
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

  # Because the stdout/stderr from nighthawk can be large, we redirect it to
  # a temporary file and re-read the output to return to the caller.  This
  # method also appears to capture output more consistently in the event of a
  # failed command execution.
  output = ''
  params = parameters._asdict()
  tmpfile = tempfile.TemporaryFile(
      mode='w+', dir=params['cwd'], prefix='cmd_output'
  )

  try:
    log.debug(f"Executing command: [{cmd}] with args [{parameters._asdict()}]")
    cmd_array = shlex.split(cmd)

    subprocess.check_call(cmd_array, stdout=tmpfile, stderr=tmpfile,
                          **parameters._asdict())

  except subprocess.CalledProcessError as process_error:
    log.error(f"Unable to execute [{cmd}]: {process_error}")
    raise

  finally:
    tmpfile.flush()
    tmpfile.seek(0)
    output = tmpfile.read()
    tmpfile.close()

    if isinstance(output, bytes):
      output = output.decode('utf-8').strip()

    log.debug(f"Returning output: [{output}]")

  return output

def run_check_command(cmd: str, parameters: CommandParameters) -> None:
  """Run the specified command checking its exit status. If the command exits
     with a non-zero return code an exception is raised.

  Args:
      cmd: The command to be executed
      parameters: Additional arguments provided to check_output. Most
        importantly, we specify 'cwd' which is the intended working directory
        where the command is to be executed.  Other parameters supported
        by the subprocess module will be added as they become necessary for
        execution.

  Raises:
    subprocess.CalledProcessError if there was a failure executing the specified
      command
  """
  try:
    log.debug(f"Executing command: [{cmd}] with args [{parameters._asdict()}]")
    cmd_array = shlex.split(cmd)
    subprocess.check_call(
        cmd_array, stderr=subprocess.STDOUT, **parameters._asdict())

  except subprocess.CalledProcessError as process_error:
    log.error(f"Unable to execute [{cmd}]: {process_error}")
    raise
