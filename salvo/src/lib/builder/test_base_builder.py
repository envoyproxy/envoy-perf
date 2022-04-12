import pytest

from src.lib import source_manager
from src.lib.builder import base_builder

import api.control_pb2 as proto_control
import api.source_pb2 as proto_source


class DerivedBuilder(base_builder.BaseBuilder):

  def __init__(self, manager: source_manager.SourceManager):
    super(DerivedBuilder, self).__init__(manager)

  def do_something(self):
    self._validate()


def test_validate_must_be_overidden():
  """Verify that the base _validate method must be overridden and raises
  an exception otherwise.
  """
  control = proto_control.JobControl(remote=False, scavenging_benchmark=True)
  control.source.add(
      identity=proto_source.SourceRepository.SourceIdentity.SRCID_ENVOY,
      source_path='/some_random_envoy_directory',
  )
  manager = source_manager.SourceManager(control)
  builder = DerivedBuilder(manager)

  with pytest.raises(NotImplementedError) as not_implemented:
    builder.do_something()

  assert str(not_implemented.value) == "Method should be overridden"


if __name__ == '__main__':
  raise SystemExit(pytest.main(['-s', '-v', __file__]))
