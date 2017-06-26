"""This file consists of generic Python helper functions."""


def CreateMutuallyExclusiveArgument(parser, argument_name, help_string):
  """The function creates a mututally exclusive argument on parser.

  It just creates an argument against the `argument_name` on parser with a
  required help_string. The given `argument_name` is set to True and the
  --no-`argument_name` is set to False. It doesn't set the default value. The
  caller needs to set the default against `argument_name`.
  Args:
    parser: the parser on which the new argument will be created.
    argument_name: the name of the mutually exclusive argument. The caller needs
    to manually set the default value of the argument.
    help_string: the required help string on the `argument_name`
  """
  temporary_parser = parser.add_mutually_exclusive_group(required=False)
  temporary_parser.add_argument("--{}".format(argument_name),
                                dest=argument_name, help=help_string,
                                action="store_true")

  temporary_parser.add_argument("--no-{}".format(argument_name),
                                dest=argument_name,
                                action="store_false")
