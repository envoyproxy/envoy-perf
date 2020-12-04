"""
Test module to validate parsing of the job control document
"""
import os
import json
import tempfile
import pytest

import google.protobuf.json_format as json_format
import src.lib.constants as constants
import src.lib.job_control_loader as job_ctrl

import api.control_pb2 as proto_control
import api.source_pb2 as proto_source
import api.docker_volume_pb2 as proto_docker_volume


def _write_object_to_disk(pb_obj, path):
  """Store a formatted json document to disk.

  Args:
      pb_obj: The Protocol Buffer object to be serialized
      path: The file to which the object's contents are
        written

  Returns:
      None
  """
  json_obj = json_format.MessageToJson(pb_obj, indent=2)
  with open(path, 'w') as json_doc:
    json_doc.write(json_obj)

  print("\n===== BEGIN ======")
  print(json_obj)
  print("====== END ========\n")


def _serialize_and_read_object(pb_obj):
  """Serialize a protobuf object to disk.

  Serialize the protobuf object to disk and re-read it to
  verify it is JSON.

  Args:
      pb_obj: The Protocol Buffer object to be serialized

  Returns:
      None
  """
  with tempfile.NamedTemporaryFile(mode='w', delete=True) as tmp:
    _write_object_to_disk(pb_obj, tmp.name)

    with open(tmp.name, 'r') as json_file:
      json_object = json.loads(json_file.read())
      assert json_object is not None
      assert json_object != {}


def _validate_job_control_object(job_control):
  """Common verification method for a job control object.

  This method reads an object and verifies its data fields
  match a predetermined set of data

  Args:
      job_control: The Protocol Buffer object whose data fields
        are to be examined and verified

  Returns:
      None
  """
  assert job_control is not None

  # Verify execution location
  assert job_control.remote

  # Verify configured benchmark
  assert job_control.scavenging_benchmark
  assert not job_control.dockerized_benchmark
  assert not job_control.binary_benchmark

  # Verify sources
  assert job_control.source is not None or job_control.source != []
  assert len(job_control.source) == 2

  saw_envoy = False
  saw_nighthawk = False
  for source in job_control.source:
    if source.identity == \
        proto_source.SourceRepository.SourceIdentity.SRCID_NIGHTHAWK:
      assert not source.source_path
      assert source.source_url == "https://github.com/envoyproxy/nighthawk.git"
      assert source.branch == "master"
      assert not source.commit_hash
      saw_nighthawk = True

    elif source.identity == \
        proto_source.SourceRepository.SourceIdentity.SRCID_ENVOY:
      assert source.source_path == "/home/ubuntu/envoy"
      assert not source.source_url
      assert source.branch == "master"
      assert source.commit_hash == "random_commit_hash_string"
      saw_envoy = True

  assert saw_envoy
  assert saw_nighthawk

  # Verify images
  assert job_control.images is not None
  assert job_control.images.reuse_nh_images
  assert job_control.images.nighthawk_benchmark_image == \
      "envoyproxy/nighthawk-benchmark-dev:latest"
  assert job_control.images.nighthawk_binary_image == \
      "envoyproxy/nighthawk-dev:latest"
  assert job_control.images.envoy_image == \
      "envoyproxy/envoy-dev:f61b096f6a2dd3a9c74b9a9369a6ea398dbe1f0f"

  # Verify environment
  assert job_control.environment is not None
  assert job_control.environment.test_version == job_control.environment.IPV_V4ONLY
  assert job_control.environment.variables is not None
  assert 'TMP_DIR' in job_control.environment.variables
  assert job_control.environment.output_dir is not None
  assert job_control.environment.output_dir == '/home/ubuntu/nighthawk_output'
  assert job_control.environment.test_dir is not None
  assert job_control.environment.test_dir == '/home/ubuntu/nighthawk_tests'

  assert job_control.environment.variables['TMP_DIR'] == "/home/ubuntu/nighthawk_output"


def test_control_doc_parse_yaml():
  """Verify that we can consume a yaml formatted control document.

  This method reads a yaml representation of the job control document,
  serializes it, then verifies that the serialized data matches the
  input.
  """
  control_yaml = """
      remote: true
      scavengingBenchmark: true
      source:
        - identity: SRCID_NIGHTHAWK
          source_url: "https://github.com/envoyproxy/nighthawk.git"
          branch: "master"
        - identity: SRCID_ENVOY
          source_path: "/home/ubuntu/envoy"
          branch: "master"
          commit_hash: "random_commit_hash_string"
      images:
        reuseNhImages: true
        nighthawkBenchmarkImage: "envoyproxy/nighthawk-benchmark-dev:latest"
        nighthawkBinaryImage: "envoyproxy/nighthawk-dev:latest"
        envoyImage: "envoyproxy/envoy-dev:f61b096f6a2dd3a9c74b9a9369a6ea398dbe1f0f"
      environment:
        testVersion: IPV_V4ONLY
        envoyPath: "envoy"
        outputDir: "/home/ubuntu/nighthawk_output"
        testDir: "/home/ubuntu/nighthawk_tests"
        variables:
          TMP_DIR: "/home/ubuntu/nighthawk_output"
    """

  # Write YAML contents to a temporary file that we clean up once
  # the object is parsed
  job_control = None
  with tempfile.NamedTemporaryFile(mode='w', delete=False) as tmp:
    tmp.write(control_yaml)
    tmp.close()
    job_control = job_ctrl.load_control_doc(tmp.name)
    os.unlink(tmp.name)

  _validate_job_control_object(job_control)


def test_control_doc_parse():
  """Verify that we can consume a JSON formatted control document.

  This method reads a JSON representation of the job control document,
  serializes it, then verifies that the serialized data matches the
  input.
  """

  control_json = """
    {
      "remote": true,
      "scavengingBenchmark": true,
      "source": [
        {
          "identity": SRCID_NIGHTHAWK,
          "source_url": "https://github.com/envoyproxy/nighthawk.git",
          "branch": "master"
        },
        {
          "identity": SRCID_ENVOY,
          "source_path": "/home/ubuntu/envoy",
          "branch": "master",
          "commit_hash": "random_commit_hash_string"
        }
      ],
      "images": {
        "reuseNhImages": true,
        "nighthawkBenchmarkImage": "envoyproxy/nighthawk-benchmark-dev:latest",
        "nighthawkBinaryImage": "envoyproxy/nighthawk-dev:latest",
        "envoyImage": "envoyproxy/envoy-dev:f61b096f6a2dd3a9c74b9a9369a6ea398dbe1f0f"
      },
      "environment": {
        testVersion: IPV_V4ONLY,
        "envoyPath": "envoy",
        "outputDir": "/home/ubuntu/nighthawk_output",
        "testDir": "/home/ubuntu/nighthawk_tests",
        "variables": {
          "TMP_DIR": "/home/ubuntu/nighthawk_output"
        }
      }
    }
    """

  # Write JSON contents to a temporary file that we clean up once
  # the object is parsed
  job_control = None
  with tempfile.NamedTemporaryFile(mode='w', delete=False) as tmp:
    tmp.write(control_json)
    tmp.close()
    job_control = job_ctrl.load_control_doc(tmp.name)
    os.unlink(tmp.name)

  _validate_job_control_object(job_control)


def test_generate_control_doc():
  """Verify that we can serialize an object to a file in JSON format.

  This method reads a JSON representation of the job control document,
  serializes it, then verifies that the serialized data can be re-read.
  """
  job_control = proto_control.JobControl()
  job_control.remote = True
  job_control.scavenging_benchmark = True

  nighthawk_source = job_control.source.add()
  nighthawk_source.identity = \
      proto_source.SourceRepository.SourceIdentity.SRCID_NIGHTHAWK
  nighthawk_source.source_url = "https://github.com/envoyproxy/nighthawk.git"
  nighthawk_source.branch = "master"

  envoy_source = job_control.source.add()
  envoy_source.identity = \
      proto_source.SourceRepository.SourceIdentity.SRCID_ENVOY
  envoy_source.source_path = "/home/ubuntu/envoy"
  envoy_source.branch = "master"
  envoy_source.commit_hash = "random_commit_hash_string"

  job_control.images.reuse_nh_images = True
  job_control.images.nighthawk_benchmark_image = \
      "envoyproxy/nighthawk-benchmark-dev:latest"
  job_control.images.nighthawk_binary_image = \
      "envoyproxy/nighthawk-dev:latest"
  job_control.images.envoy_image = \
      "envoyproxy/envoy-dev:f61b096f6a2dd3a9c74b9a9369a6ea398dbe1f0f"

  job_control.environment.variables["TMP_DIR"] = "/home/ubuntu/nighthawk_output"
  job_control.environment.test_version = job_control.environment.IPV_V4ONLY
  job_control.environment.envoy_path = "envoy"
  job_control.environment.output_dir = '/home/ubuntu/nighthawk_output'
  job_control.environment.test_dir = '/home/ubuntu/nighthawk_tests'

  # Verify that we the serialized data is json consumable
  _serialize_and_read_object(job_control)


def _test_docker_volume_generation():
  """Verify construction of the volume mount map.

  This test creates the volume and mount map we provide to a docker container.
  We verify that the structure can be serialized and read as JSON.
  """
  volume_cfg = proto_docker_volume.Volume()

  props = proto_docker_volume.VolumeProperties()
  props.bind = constants.DOCKER_SOCKET_PATH
  props.mode = 'ro'
  volume_cfg.volumes[constants.DOCKER_SOCKET_PATH].CopyFrom(props)

  props = proto_docker_volume.VolumeProperties()
  props.bind = '/home/ubuntu/nighthawk_output'
  props.mode = 'rw'
  volume_cfg.volumes['/home/ubuntu/nighthawk_output'].CopyFrom(props)

  props = proto_docker_volume.VolumeProperties()
  props.bind = constants.NIGHTHAWK_EXTERNAL_TEST_DIR
  props.mode = 'rw'
  volume_cfg.volumes[constants.NIGHTHAWK_EXTERNAL_TEST_DIR].CopyFrom(props)

  # Verify that we the serialized data is json consumable
  _serialize_and_read_object(volume_cfg)


if __name__ == '__main__':
  raise SystemExit(pytest.main(['-s', '-v', __file__]))
