"""This file consists of generic Python helper functions."""

import os
import random
import string

try:
  xrange          # Python 2
except NameError
  xrange = range  # Python 3


def CreateBooleanArgument(parser, argument_name, help_string,
                          **default_condition):
  """The function creates a mututally exclusive argument on parser.

  It creates an argument with the `argument_name` on `parser` with a
  required `help_string`. The given `argument_name` is set to True and the
  --no-`argument_name` is set to False. Default condition is also set.
  Args:
    parser: the parser on which the new argument will be created.
    argument_name: the name of the mutually exclusive argument. The caller needs
    to manually set the default value of the argument.
    help_string: the required help string on the `argument_name`
    **default_condition: provide the default condition for the parser for this
    boolean argument
  """
  temporary_parser = parser.add_mutually_exclusive_group(required=False)
  temporary_parser.add_argument("--{}".format(argument_name),
                                dest=argument_name, help=help_string,
                                action="store_true")

  temporary_parser.add_argument("--no-{}".format(argument_name),
                                dest=argument_name,
                                action="store_false")
  parser.set_defaults(**default_condition)


def GetRandomPassword():
  """This function generates a random 20-length password.

  Returns:
    Returns a random 20-length password consisting of ASCII characters.
  """
  length = 20
  random.seed = os.urandom(1024)
  return "".join(random.choice(string.ascii_letters) for _ in xrange(length))
