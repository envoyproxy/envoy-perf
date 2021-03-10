#!/usr/bin/env python3

import argparse
import logging
import os
import sys

from src.lib.job_control_loader import load_control_doc
from src.lib.run_benchmark import BenchmarkRunner

LOGFORMAT = "%(asctime)s: %(process)d [ %(levelname)-5s] [%(module)-5s] %(message)s"

log = logging.getLogger()


def setup_logging(loglevel: int=logging.DEBUG) -> None:
  """Basic logging configuration.

  Configure the logger with our defined format and set the log level which
  defaults to debug

  Args:
    loglevel configures the level of the logger.  The default is DEBUG
      level logging
  """
  logging.getLogger('docker').setLevel(logging.ERROR)
  logging.getLogger('urllib3').setLevel(logging.ERROR)

  logging.basicConfig(format=LOGFORMAT, level=loglevel)


def setup_options() -> argparse.Namespace:
  """Parse command line arguments required for operation.

  Read all command line arguments and return a namespace with consumable
  data
  """

  parser = argparse.ArgumentParser(description="Salvo Benchmark Runner")
  parser.add_argument('--job',
                      dest='jobcontrol',
                      help='specify the location for the job control json document')
  # TODO: Add an option to generate a default job Control JSON/YAML
  return parser.parse_args()

def main() -> int:
  """Driver module for benchmark.

  This is the main function for starting a benchmark.  It verifies that a
  Job Control object was specified and from that starts the execution.

  The benchmark object encapsulates the different benchmark modes and it
  is responsible for selecting the correct classes to instantiate
  """

  args = setup_options()
  setup_logging()

  if not args.jobcontrol:
    print("No job control document specified.  Use \"--help\" for usage")
    return 1

  job_control = load_control_doc(args.jobcontrol)
  if job_control is None:
    log.error(f"Unable to load or parse job control: {args.jobcontrol}")
    return 1

  log.debug("Job definition:\n%s\n%s\n%s\n", '=' * 20, job_control, '=' * 20)

  # Execute the benchmark given the contents of the job control file
  benchmark = BenchmarkRunner(job_control)
  benchmark.execute()

  return 0


if __name__ == '__main__':
  sys.exit(main())
