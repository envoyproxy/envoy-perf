#!/usr/bin/env python3

import argparse
import logging
import os
import site
import sys

# Run in the actual bazel directory so that the sys.path
# is setup correctly
if os.path.islink(sys.argv[0]):
  real_exec_dir = os.path.dirname(sys.argv[0])
  os.chdir(real_exec_dir)

site.addsitedir("src")

from lib.message_helper import load_control_doc
from lib.run_benchmark import Benchmark

LOGFORMAT = "%(asctime)s: %(process)d [ %(levelname)-5s] [%(module)-5s] %(message)s"

log = logging.getLogger()


def setup_logging(loglevel=logging.DEBUG):
  """Basic logging configuration """

  logging.basicConfig(format=LOGFORMAT, level=loglevel)


def setup_options():
  """Parse command line arguments required for operation"""

  parser = argparse.ArgumentParser(description="Salvo Benchmark Runner")
  parser.add_argument(
      '--job', dest='jobcontrol', help='specify the location for the job control json document')
  # FIXME: Add an option to generate a default job Control JSON/YAML

  return parser.parse_args()


def main():
  """Driver module for benchmark """

  args = setup_options()
  setup_logging()

  if not args.jobcontrol:
    print("No job control document specified.  Use \"--help\" for usage")
    return 1

  job_control = load_control_doc(args.jobcontrol)

  log.debug("Job definition:\n%s\n%s\n%s\n", '=' * 20, job_control, '=' * 20)

  benchmark = Benchmark(job_control)
  try:
    benchmark.validate()
  # TODO: Create a different class for these exceptions
  except Exception as validation_exception:
    log.error("Unable to validate data needed for benchmark run: %s", validation_exception)
    return 1

  benchmark.execute()

  return 0


if __name__ == '__main__':
  sys.exit(main())

