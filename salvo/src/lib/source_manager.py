"""
This module abstracts the higher level functions of managing source
code
"""
import logging
import tempfile

import lib.source_tree as tree

log = logging.getLogger(__name__)

SOURCE_REPOSITORY = {'envoy': 'https://github.com/envoyproxy/envoy.git'}

# TODO(abaptiste): Use Enum
CURRENT = 'baseline'
PREVIOUS = 'previous'


class SourceManager(object):

  def __init__(self, **kwargs):
    self._control = kwargs.get('control', None)

  def get_envoy_images_for_benchmark(self):
    """
    From the envoy image specified in the control document, determine
    the current image hash and the previous image hash.
    """
    image_hashes = {}
    source_tree = None
    hash = None

    # Determine if we have an image or a source location
    images = self._control.images
    if images:
      envoy_image = images.envoy_image
      tag = envoy_image.split(':')[-1]
      log.debug(f"Found tag {tag} in image {envoy_image}")
      hash = tag

      name = 'envoy'
      kwargs = {'origin': SOURCE_REPOSITORY[name], 'name': name}
      source_tree = tree.SourceTree(**kwargs)
    else:
      # TODO(abaptiste): Need to handle the case where source is specified.  We should have
      # a source location on disk, so we need to create the source_tree
      # a bit differently
      raise NotImplementedError("Discovering hashes from source is not yet implemented")

    # Pull the source
    result = source_tree.pull()
    if not result:
      log.error(f"Unable to pull source from origin {kwargs['origin']}")
      return None

    # TODO(abaptiste): Use an explicit hash since "latest" can change
    # if hash == 'latest':
    #     hash = source_tree.get_head_hash()

    # Get the previous hash to the tag
    previous_hash = source_tree.get_previous_commit_hash(hash)
    if previous_hash is not None:
      image_hashes = {CURRENT: hash, PREVIOUS: previous_hash}

    log.debug(f"Found hashes: {image_hashes}")
    return image_hashes
