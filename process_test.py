import unittest
import pytest
import sh
from io import StringIO

from process import Process


class TestUM(unittest.TestCase):

  def setUp(self):
    pass

  def test_normal_init(self):
    """This test checks all the attributes of the process class except args."""
    logfile = open("logfile.log", "w")
    p = Process("taskset", logfile)
    self.assertEqual(p.command, "taskset")
    self.assertEqual(p.os, logfile)
    self.assertEqual(p.pid, 0)
    self.assertEqual(p.args, None)

  def test_no_val(self):
    """This test checks the exception caused by empty proc_command."""
    logfile = open("logfile.log", "w")
    error_message = "argument proc_command should be given."
    with pytest.raises(ValueError) as e:
      p = Process(" ", logfile)
    self.assertEqual(error_message, str(e.value))

  def test_args(self):
    """This test checks all the attributes along with args."""
    logfile = open("logfile.log", "w")
    args = ["-l", "-a"]
    p = Process("ls", logfile, args=args)
    self.assertEqual(p.command, "ls")
    self.assertEqual(p.os, logfile)
    self.assertEqual(p.pid, 0)
    self.assertEqual(p.args, args)

  def test_no_output_stream(self):
    args = ["-l", "-a"]
    with pytest.raises(TypeError) as e:
      p = Process("ls", args=args)

  def test_ls_run(self):
    process_log = StringIO()
    shell_log = StringIO()
    args = ["-l", "-a"]
    p = Process("ls", process_log, args=args)
    p.RunProcess()
    sh.ls(args, _out = shell_log)
    self.assertEqual(process_log.getvalue(), shell_log.getvalue())

  def test_ls_run_without_array_args(self):
    process_log = StringIO()
    shell_log = StringIO()
    p = Process("ls -la", process_log)
    p.RunProcess()
    sh.ls("-la", _out = shell_log)
    self.assertEqual(process_log.getvalue(), shell_log.getvalue())

  def test_random_executable(self):
    process_log = StringIO()
    p = Process("random executable", None)
    with pytest.raises(sh.CommandNotFound) as e:
      p.RunProcess()

  # TODO(sohamcodes): Needs to write more test cases.
  

if __name__ == '__main__':
  unittest.main()
