"""
This module abstracts the higher level functions of managing source
code
"""
import logging
from typing import List

from src.lib import source_tree
import api.source_pb2 as proto_source
import api.control_pb2 as proto_control

log = logging.getLogger(__name__)

"""The KNOWN_REPOSITORIES map contains the known remote locations for the source
   code needed to build Envoy.
"""
_KNOWN_REPOSITORIES = {'envoy': 'https://github.com/envoyproxy/envoy.git'}

# In the list of benchmarks to execute, the Baseline image is always
# the last entry
BASELINE = -1

class SourceManagerError(Exception):
  """Raised when an unrecoverable error is encountered while working with
     a source tree.
  """

class SourceManager(object):
  """This class is a manager for SourceTree objects.

  SourceTree objects abstract the git operations needed to manipulate source
  code checked out on disk.
  """

  def __init__(self, control: proto_control.JobControl) -> None:
    """Set the job control containing the source locations.

    Args:
      control: The JobControl object defining the parameters of the benchmark
    """
    self._control = control
    self._builder = None

  def determine_envoy_hashes_from_source(self) -> List[str]:
    """Determine the previous commit hash or tag from the baseline envoy image.

    Returns:
      a List containing current and previous commit hashes needed to identify
        the envoy image for benchmarking.

    Raises:
      a SourceManagerError if we are unable to determine the prior commit
        or tag
    """
    return []

  def find_all_images_from_specified_tags(self) -> List[str]:
    """Find all images required for benchmarking from the images specified
       in the job control object.

    Returns:
      a list of commit hashes or tags needed to identify docker images
        needed for the benchmark execution.

    Raises:
      SourceManagerError: if no images are specified in the control
        document.  We require the nighthawk images to be specified at a
        minimum.  We will not build those from source yet.
    """
    return []

  def find_all_images_from_specified_sources(self) -> List[str]:
    """Find all images required for benchmarking from the source and hashes
       specified in the job control object.

    Returns:
      a list of commit hashes or tags needed to identify docker images
        needed for the benchmark execution.

    Raises:
      SourceManagerError: if no images are specified in the control
        document. We require the nighthawk images to be specified at a
        minimum.  We will not build those from source yet.
    """
    return []

  def get_envoy_hashes_for_benchmark(self) -> List[str]:
    """Determine the hashes for the baseline and previous Envoy Image.

    Using the name and tag for the envoy image specified in the control
    document, determine the previous image hash.  Return all discovered
    hashes.

    If secondary images or secondary hashes are present, we will use these
    images for benchmarking and will not do any hash deduction.

    Returns:
      A List of commit hashes or tags that identify the envoy image for
       the baseline benchmark, and the previous envoy image the results
       are compared against
    """
    return []

  def get_image_hashes_from_disk_source(
      self, disk_source_tree: source_tree.SourceTree,
      commit_hash: str) -> List[str]:
    """Determine the previous hash to the specified commit.

    Args:
      disk_source_tree: A SourceTree object managing the source on disk
      commit_hash: a string indicating the commit hash from which we
        determine its predecessor

    Returns:
      a List of commit hashes discovered.

    Raises:
      SourceManagerError: if we are not able to deterimine hashes prior to
        the identified commit
    """
    return []

def get_source_repository(self, \
    source_id: proto_source.SourceRepository.SourceIdentity) \
    -> proto_source.SourceRepository:
    """Find and return the source repository object with the specified id

    Args:
      source_id: The identity of the source object we seek (eg.
        SRCID_NIGHTHAWK or SRCID_ENVOY)

    Return:
      a Source repository matching the specified source_id

    Raises:
      SourceManagerError: If no source exists matching the specified source_id
    """
    return proto_source.SourceRepository()
