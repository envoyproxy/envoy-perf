"""
Common object generation methods shared by tests
"""
from src.lib import constants

import api.control_pb2 as proto_control
import api.image_pb2 as proto_image
import api.env_pb2 as proto_environ
import api.source_pb2 as proto_source


def generate_images(job_control: proto_control.JobControl) -> proto_image.DockerImages:
  """Generate a default images specification for a control object.

  Returns:
    a DockerImages object populated with a default set of data
  """
  generated_images = job_control.images
  generated_images.reuse_nh_images = True
  generated_images.nighthawk_benchmark_image = \
      "envoyproxy/nighthawk-benchmark-dev:random_benchmark_image_tag"
  generated_images.nighthawk_binary_image = \
      "envoyproxy/nighthawk-dev:random_binary_image_tag"
  generated_images.envoy_image = \
      "envoyproxy/envoy-dev:random_envoy_image_hash"

  return generated_images


def generate_environment(job_control: proto_control.JobControl) -> proto_environ.EnvironmentVars:
  """Generate a default set of environment variables for a control object.

  Returns:
    an EnvironmentVars object containing varibles used by benchmarks.
  """
  generated_environment = job_control.environment
  generated_environment.variables["TMP_DIR"] = "/home/ubuntu/nighthawk_output"
  generated_environment.test_version = generated_environment.IPV_V4ONLY
  generated_environment.envoy_path = "envoy"

  return generated_environment


def generate_envoy_source(job_control: proto_control.JobControl) -> proto_source.SourceRepository:
  """Generate a default Envoy SourceRepository in the control object.

  Returns:
    a SourceRepository object defining the location of the Envoy source.
  """
  envoy_source = job_control.source.add(
      identity=proto_source.SourceRepository.SourceIdentity.SRCID_ENVOY,
      source_url=constants.ENVOY_GITHUB_REPO,
      branch="master",
      commit_hash="hash_doesnt_really_matter_here")

  return envoy_source


def generate_nighthawk_source(
    job_control: proto_control.JobControl) -> proto_source.SourceRepository:
  """Generate a default NightHawk SourceRepository in the control object.

  Returns:
    a SourceRepository object defining the location of the NightHawk source.
  """
  nighthawk_source = job_control.source.add(
      identity=proto_source.SourceRepository.SourceIdentity.SRCID_NIGHTHAWK,
      source_url=constants.NIGHTHAWK_GITHUB_REPO)

  return nighthawk_source


def generate_default_job_control() -> proto_control.JobControl:
  """Generate a default job control object used in tests."""
  job_control = proto_control.JobControl(remote=False, scavenging_benchmark=True)
  return job_control
