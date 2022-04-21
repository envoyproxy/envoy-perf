"""
This module abstracts the higher level functions of managing source code
"""
import logging
from typing import Set

from src.lib import (constants, source_tree)

import api.source_pb2 as proto_source
import api.control_pb2 as proto_control

log = logging.getLogger(__name__)
"""The KNOWN_REPOSITORIES map contains the known remote locations for the
   source code needed to build Envoy and NightHawk
"""
_KNOWN_REPOSITORIES = {
    proto_source.SourceRepository.SourceIdentity.SRCID_ENVOY: constants.ENVOY_GITHUB_REPO,
    proto_source.SourceRepository.SourceIdentity.SRCID_NIGHTHAWK: constants.NIGHTHAWK_GITHUB_REPO
}


def _extract_tag_from_image(image_name: str) -> str:
  """Extract the tag from the docker image name.

  Args:
    image_name: The docker image name

  Return:
    a string containing the image tag. For example:
      envoyproxy/envoy:v1.15.3 -> v1.15.3
  """

  return image_name.split(':')[-1]


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
    self._source_tree = {}
    for source_id, _ in _KNOWN_REPOSITORIES.items():
      self._source_tree[source_id] = self._create_source_tree(source_id)

  def determine_envoy_hashes_from_source(self) -> Set[str]:
    """Determine the previous commit hash or tag from the baseline envoy image.

    Returns:
      a set containing current and previous commit hashes needed to identify
        the envoy image for benchmarking.

    Raises:
      a SourceManagerError if we are unable to determine the prior commit
        or tag
    """
    envoy_source_tree = self.get_source_tree(
        proto_source.SourceRepository.SourceIdentity.SRCID_ENVOY)

    result = envoy_source_tree.pull()
    if not result:
      log.error("Unable to pull source from origin.  Copying source instead")
      result = envoy_source_tree.copy_source_directory()

    if not result:
      raise SourceManagerError("Unable to obtain the source to determine commit hashes")

    commit_hash = self._get_image_hash(envoy_source_tree)

    return self.get_image_hashes_from_disk_source(envoy_source_tree, commit_hash)

  def _get_image_hash(self, envoy_source):
    """Return the tag for the identified Envoy image.

    Use the image string to get the tag from which we find its predecessor.
    If no image is specified in the control document, use the head commit hash
    from the source tree.

    Args:
      envoy_source:  The source tree object managing Envoy's source code

    Returns:
      the identified image tag or head commit hash
    """
    envoy_image = self._control.images.envoy_image
    if envoy_image:
      commit_hash = _extract_tag_from_image(envoy_image)
      log.debug(f"Found tag [{commit_hash}] in image [{envoy_image}]")
    else:
      commit_hash = envoy_source.get_head_hash()

    return commit_hash

  def find_all_images_from_specified_tags(self) -> Set[str]:
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
    images = self._control.images
    if not all([images.nighthawk_benchmark_image, images.nighthawk_binary_image]):
      # Determine whether we have sources for building NightHawk
      nighthawk_source = self.get_source_tree(
          proto_source.SourceRepository.SourceIdentity.SRCID_NIGHTHAWK)
      if not nighthawk_source:
        raise SourceManagerError("No images are specified or able to be built from the "
                                 "control document")

    envoy_image = images.envoy_image
    if not envoy_image:
      log.debug("No Envoy image defined in control document. "
                "Sources and a hash should be specified so that we can "
                "build the image")
      return set()

    # Let's see if additional images are specified.  If so, return
    # them all in a list.

    hash_set = set()
    # NOTE: The baseline is always the last image in our list
    test_single_image = images.test_single_image
    additional_images = images.additional_envoy_images
    if test_single_image and additional_images:
      raise SourceManagerError(
          '"additional_envoy_image" cannot be set with "test_single_image" enabled')
    if additional_images:
      additional_tags = [_extract_tag_from_image(image) for image in images.additional_envoy_images]

      # Do not add hashes that we have already discovered
      hash_set = hash_set.union(additional_tags)
      hash_set.add(_extract_tag_from_image(envoy_image))
    elif test_single_image:
      hash_set.add(_extract_tag_from_image(envoy_image))
    else:
      # We have to deduce the previous image by commit hash
      hash_set = self.determine_envoy_hashes_from_source()

    return hash_set

  def find_all_images_from_specified_sources(self) -> Set[str]:
    """Find all images required for benchmarking from the source and hashes
       specified in the job control object.

    Returns:
      a Set of commit hashes or tags needed to identify docker images
        needed for the benchmark execution.

    Raises:
      SourceManagerError: if no images are specified in the control
        document. We require the nighthawk images to be specified at a
        minimum.  We will not build those from source yet.
    """
    hash_set = set()

    source_repo = self.get_source_repository(proto_source.SourceRepository.SRCID_ENVOY)

    # We have a source, see whether additional hashes are specified
    test_single_commit = source_repo.test_single_commit
    additional_hashes = source_repo.additional_hashes
    if test_single_commit and additional_hashes:
      raise SourceManagerError(
          '"additional_hashes" cannot be set with "test_single_commit" enabled')
    if additional_hashes:
      hash_set = hash_set.union(additional_hashes)

    if source_repo.commit_hash and (additional_hashes or test_single_commit):
      hash_set = hash_set.union([source_repo.commit_hash])
      return hash_set

    # If we don't have a commit_hash specified and no additional hashes
    # we need to do discovery
    if source_repo.commit_hash:
      tree = self.get_source_tree(proto_source.SourceRepository.SRCID_ENVOY)
      hash_set = self.get_image_hashes_from_disk_source(tree, source_repo.commit_hash)

    return hash_set

  def get_envoy_hashes_for_benchmark(self) -> Set[str]:
    """Determine the hashes for the baseline and previous Envoy Image.

    Using the name and tag for the envoy image specified in the control
    document, determine the previous image hash.  Return all discovered
    hashes.

    If secondary images or secondary hashes are present, we will use these
    images for benchmarking and will not do any hash deduction.

    Returns:
      A Set of commit hashes or tags that identify the envoy image for
       the baseline benchmark, and the previous envoy image the results
       are compared against
    """

    # Evaluate specfied images first
    image_hashes = self.find_all_images_from_specified_tags()

    # Fall back to sources next
    source_tags = self.find_all_images_from_specified_sources()

    # Don't add tags for images we already discovered
    return image_hashes.union(source_tags)

  def get_image_hashes_from_disk_source(self, disk_source_tree: source_tree.SourceTree,
                                        commit_hash: str) -> Set[str]:
    """Determine the previous hash to the specified commit.

    Args:
      disk_source_tree: A SourceTree object managing the source on disk
      commit_hash: a string indicating the commit hash from which we
        determine its predecessor

    Returns:
      a Set of commit hashes discovered.

    Raises:
      SourceManagerError: if we are not able to deterimine hashes prior to
        the identified commit
    """

    previous_hash = None
    try:
      previous_hash = disk_source_tree.get_previous_commit_hash(commit_hash)
    except source_tree.SourceTreeError:
      raise SourceManagerError(f"Unable to find a commit hash prior to [{commit_hash}]")

    if not previous_hash:
      raise SourceManagerError(f"Received empty commit hash prior to [{commit_hash}]")

    return set([previous_hash, commit_hash])

  def get_source_repository(
      self,
      source_id: proto_source.SourceRepository.SourceIdentity) -> proto_source.SourceRepository:
    """Find and return the source repository object with the specified id

    Args:
      source_id: The identity of the source object we seek (eg.
        SRCID_NIGHTHAWK or SRCID_ENVOY)

    Return:
      a Source repository matching the specified source_id

    Raises:
      SourceManagerError: If no source exists matching the specified source_id
    """

    source_name = proto_source.SourceRepository.SourceIdentity.Name(source_id)

    # Filter source objects that do not match the source_id and return the
    # first remaining object. We expect one source repository defined for
    # NightHawk and Envoy, so one object is filtered out and one should remain
    source = next(filter(lambda s: s.identity == source_id, self._control.source), None)

    # See if any of the known sources can work for the ID if none was specified
    if not source and source_id in _KNOWN_REPOSITORIES:
      log.debug(f"Using default location for {source_name}")
      source = proto_source.SourceRepository(identity=source_id,
                                             source_url=_KNOWN_REPOSITORIES[source_id])
      log.debug(f"{source_name} configured with:\n{source}")

    if not source:
      raise SourceManagerError(f"Unable to find a source with the requested ID: {source_name}")

    return source

  def _create_source_tree(
      self, source_id: proto_source.SourceRepository.SourceIdentity) -> source_tree.SourceTree:
    """Creates a source tree object from a SourceRepository.

    Args:
      source_id: The identity of the source object we seek (eg.
        SRCID_NIGHTHAWK or SRCID_ENVOY)
    Returns:
      a source tree object managing the identified source repository
    """

    repo = self.get_source_repository(source_id)
    return source_tree.SourceTree(repo)

  def get_source_tree(
      self, source_id: proto_source.SourceRepository.SourceIdentity) -> source_tree.SourceTree:
    """Returns the source tree object identified by source_id.

    Args:
      source_id: The identity of the source tree we seek (eg.
        SRCID_NIGHTHAWK or SRCID_ENVOY)

    Returns:
      a source tree object managing the identified source repository

    Raises:
      SourceManagerError if no source tree is found
    """

    if source_id not in self._source_tree:
      source_name = proto_source.SourceRepository.SourceIdentity.Name(source_id)
      raise SourceManagerError(f"No Source tree defined for: {source_name}")

    return self._source_tree[source_id]

  def get_build_options(
      self, source_id: proto_source.SourceRepository.SourceIdentity) -> proto_source.BazelOption:
    """Determine whether build options are specified in the control object
    and return them

    Args:
      source_id: The identity of the source object we seek (eg.
        SRCID_NIGHTHAWK or SRCID_ENVOY)

    Return:
      the Bazel Options defined in the source identified by the
        specified source_id

    Raises:
      SourceManagerError: If no options are defined in the source object
    """

    source = self.get_source_repository(source_id)
    bazel_options = source.bazel_options

    if not bazel_options:
      source_name = proto_source.SourceRepository.SourceIdentity.Name(source_id)
      raise SourceManagerError(f"No Bazel Options are defined in source: {source_name}")

    return bazel_options

  def have_build_options(self, source_id: proto_source.SourceRepository.SourceIdentity) -> bool:
    """Determine whether build options are specified in the control object
       and return a boolean.  This is used to determine whether we build
       images or use the already available images

    Args:
      source_id: The identity of the source object we seek (eg.
        SRCID_NIGHTHAWK or SRCID_ENVOY)

    Return:
      a boolean indicating the presense of user specified bazel options
    """
    try:
      build_options = self.get_build_options(source_id)
      options_present = len(build_options) >= 1
    except SourceManagerError:
      options_present = False

    return options_present
