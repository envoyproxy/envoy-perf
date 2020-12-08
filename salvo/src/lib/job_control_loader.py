"""
This object abstracts the loading of json strings into protobuf objects
"""
import json
import logging
import yaml

import api.control_pb2 as proto_control
import google.protobuf.json_format as json_format

log = logging.getLogger(__name__)


def _load_json_doc(filename: str) -> proto_control.JobControl:
  """Load a disk file as JSON.

  This function reads the specified filename and parses the contents
  as JSON.

  Args:
      filename: The file whose contents are to be read as JSON data

  Returns:
      A JobControl object populated with the contents from the
        specified JSON file
  """
  contents = None
  log.debug(f"Opening JSON file {filename}")
  try:
    with open(filename, 'r') as json_doc:
      contents = json_format.Parse(json_doc.read(), proto_control.JobControl())
  except FileNotFoundError as file_not_found:
    log.exception(f"Unable to load {filename}: {file_not_found}")
  except json_format.Error as json_parse_error:
    log.exception(
        f"Unable to parse JSON contents {filename}: {json_parse_error}")

  return contents


def _load_yaml_doc(filename: str) -> proto_control.JobControl:
  """Load a disk file as YAML.

  This function reads the specified filename and parses the contents
  as YAML.

  Args:
      filename: The file whose contents are to be read as YAML data

  Returns:
      A JobControl object populated with the contents from the
        specified YAML file
  """
  log.debug(f"Opening YAML file {filename}")
  contents = None
  try:
    with open(filename, 'r') as yaml_doc:
      contents = yaml.load(yaml_doc.read())
      contents = json_format.Parse(
          json.dumps(contents), proto_control.JobControl())
  except FileNotFoundError as file_not_found:
    log.exception(f"Unable to load {filename}: {file_not_found}")
  except json_format.Error as yaml_parse_error:
    log.exception(
        f"Unable to parse YAML contents {filename}: {yaml_parse_error}")

  return contents

def load_control_doc(filename: str) -> proto_control.JobControl:
  """Return a JobControl object from the identified filename.

  This function uses the extension of the specified file to read its
  contents as YAML or JSON

  Args:
      filename: The file whose contents are to be read and parsed as
        a Job Control object.

  Returns:
      A JobControl object populated with the contents from the
        specified filename
  """
  contents = None

  # Try loading the contents based on the file extension
  if filename.endswith('.json'):
    log.debug(f"Loading JSON file {filename}")
    return _load_json_doc(filename)
  elif filename.endswith('.yaml'):
    log.debug(f"Loading YAML file {filename}")
    return _load_yaml_doc(filename)
  else:
    log.debug(f"Auto-detecting contents of {filename}")
    # Attempt to autodetect the contents
    try:
      contents = _load_json_doc(filename)
    except json_format.Error:
      log.info(f"Parsing {filename} as JSON failed.  Trying YAML")

    if not contents:
      try:
        contents = _load_yaml_doc(filename)
      except json_format.Error:
        log.info(f"Parsing {filename} as YAML failed.")

  return contents

