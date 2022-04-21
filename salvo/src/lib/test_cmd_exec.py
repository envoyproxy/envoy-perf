"""Test command execution needed for executing benchmarks."""
import pytest
import subprocess
from unittest import mock
from src.lib import cmd_exec


def check_call_side_effect(args, **kwargs):
  """Return output for the check call command.

  Args:
    args: The list of arguments passed to the subprocess.check_call method
    kwargs: The keyword arguments passed to the subprocess.check_call method.
      We are most interestd in stdout and stderr since these are the conduits
      via which we get the command output
  """
  cmd = args[0]
  if cmd == 'spanish_output_stdout':
    assert 'stdout' in kwargs
    f_stdout = kwargs['stdout']
    f_stdout.write("No te hablas una palabra del espanol")
    return 0

  elif cmd == 'spanish_output_stderr':
    assert 'stderr' in kwargs
    f_stderr = kwargs['stderr']
    f_stderr.write("No te hablas una palabra del espanol en stderr")
    return 0

  elif cmd == 'command_error':
    raise subprocess.CalledProcessError(1, cmd, "command failed")

  raise NotImplementedError(f"Unhandled args={args} and kwargs={kwargs}")


@mock.patch('subprocess.check_call')
def test_run_command(mock_check_call):
  """Verify that we can return the output from a check_call call."""
  mock_check_call.side_effect = check_call_side_effect

  cmd_parameters = cmd_exec.CommandParameters(cwd='/tmp')
  cmd = 'spanish_output_stdout'
  output = cmd_exec.run_command(cmd, cmd_parameters)
  assert output == 'No te hablas una palabra del espanol'

  cmd = 'spanish_output_stderr'
  output = cmd_exec.run_command(cmd, cmd_parameters)
  assert output == 'No te hablas una palabra del espanol en stderr'


@mock.patch('subprocess.check_call')
def test_run_command_fail(mock_check_call):
  """Verify that a CalledProcessError is bubbled to the caller if the command fails."""
  mock_check_call.side_effect = check_call_side_effect

  cmd_parameters = cmd_exec.CommandParameters(cwd='/tmp')
  cmd = 'command_error'

  output = ''
  with pytest.raises(subprocess.CalledProcessError) as process_error:
    output = cmd_exec.run_command(cmd, cmd_parameters)

  assert not output
  assert f"Command \'{cmd}\' returned non-zero exit status" in str(process_error.value)


@mock.patch('subprocess.check_call')
def test_run_check_command_fail(mock_check_call):
  """Verify that a CalledProcessError is bubbled to the caller if the command fails."""
  mock_check_call.side_effect = check_call_side_effect

  cmd_parameters = cmd_exec.CommandParameters(cwd='/tmp')
  cmd = 'command_error'

  output = ''
  with pytest.raises(subprocess.CalledProcessError) as process_error:
    output = cmd_exec.run_check_command(cmd, cmd_parameters)

  assert not output
  assert f"Command \'{cmd}\' returned non-zero exit status" in str(process_error.value)


if __name__ == '__main__':
  raise SystemExit(pytest.main(['-s', '-v', __file__]))
