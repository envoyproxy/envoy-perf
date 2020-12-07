"""Module defining Exceptions raised from benchmark classes"""


class BenchmarkError(Exception):
  """Errror raised in a benchmark for an unresolvable condition."""

class BenchmarkEnvironmentError(Exception):
  """An Error raised if the environment variables required are not
     able to be set.
  """

class FullyDockerizedBenchmarkError(Exception):
  """Error rasied when running a fully dockerized benchmark in cases
     where we cannot make progress due to abnormal conditions.
  """
