import pytest
from unittest import mock

import api.control_pb2 as proto_control

from src.lib import (generate_test_objects, source_manager, run_benchmark)
from src.lib.docker_management import (docker_image, docker_image_builder)
from src.lib.benchmark import (scavenging_benchmark, fully_dockerized_benchmark as full_docker,
                               binary_benchmark as binbench)

import logging
logging.basicConfig(level=logging.DEBUG)

_BUILD_ENVOY_IMAGE_FROM_SOURCE = \
    ('src.lib.docker_management.docker_image_builder.'
     'build_envoy_image_from_source')
_BUILD_NIGHTHAWK_IMAGE_FROM_SOURCE = \
    ('src.lib.docker_management.docker_image_builder.'
     'build_nighthawk_binary_image_from_source')
_BUILD_NIGHTHAWK_BENCHMARK_IMAGE_FROM_SOURCE = \
    ('src.lib.docker_management.docker_image_builder'
     '.build_nighthawk_benchmark_image_from_source')


@mock.patch('os.symlink')
@mock.patch.object(source_manager.SourceManager, 'get_envoy_hashes_for_benchmark')
def test_binary_benchmark_setup(mock_get_hashes, mock_symlink):
  """Verify that the unique methods to the binary benchmark workflow are in order"""
  job_control = proto_control.JobControl(remote=False, binary_benchmark=True)
  mock_get_hashes.return_value = ["jedi", "padawan"]
  generate_test_objects.generate_envoy_source(job_control)
  generate_test_objects.generate_nighthawk_source(job_control)

  _ = run_benchmark.BenchmarkRunner(job_control)
  mock_symlink.has_calls(
      [mock.call('source_url__padawan__master'),
       mock.call('source_url__jedi__master')])


@mock.patch('os.symlink')
@mock.patch.object(full_docker.Benchmark, 'run_image')
@mock.patch.object(full_docker.Benchmark, 'execute_benchmark')
@mock.patch.object(docker_image.DockerImage, 'pull_image')
@mock.patch.object(source_manager.SourceManager, 'have_build_options')
@mock.patch.object(source_manager.SourceManager, 'get_envoy_hashes_for_benchmark')
def test_execute_dockerized_benchmark_using_images_only(mock_hashes_for_benchmarks,
                                                        mock_have_build_options, mock_pull_image,
                                                        mock_execute, mock_run_image, mock_symlink):
  """Verify that we attempt to pull images if no sources are specified."""

  # Build a default job control object with images
  job_control = proto_control.JobControl(remote=False, dockerized_benchmark=True)
  generate_test_objects.generate_environment(job_control)
  generate_test_objects.generate_images(job_control)

  mock_run_image.return_value = b"benchmark_http_client output...."
  mock_execute.return_value = None
  mock_have_build_options.return_value = False
  mock_hashes_for_benchmarks.return_value = {'tag1', 'tag2'}

  # Instantiate the BenchmarkRunner so that it prepares the job control
  # objects for each benchmark
  benchmark = run_benchmark.BenchmarkRunner(job_control)
  benchmark.execute()

  mock_have_build_options.assert_called()
  mock_pull_image.assert_called()
  mock_symlink.assert_called()
  mock_execute.assert_has_calls([mock.call(), mock.call()])


@mock.patch('os.symlink')
@mock.patch.object(scavenging_benchmark.Benchmark, 'execute_benchmark')
@mock.patch.object(docker_image.DockerImage, 'pull_image')
@mock.patch.object(source_manager.SourceManager, 'have_build_options')
@mock.patch.object(source_manager.SourceManager, 'get_envoy_hashes_for_benchmark')
def test_execute_using_images_only(mock_hashes_for_benchmarks, mock_have_build_options,
                                   mock_pull_image, mock_execute, mock_symlink):
  """Verify that we attempt to pull images if no sources are specified."""

  # Build a default job control object with images
  job_control = generate_test_objects.generate_default_job_control()
  generate_test_objects.generate_images(job_control)

  mock_execute.return_value = None
  mock_have_build_options.return_value = False
  mock_hashes_for_benchmarks.return_value = {'tag1', 'tag2'}

  # Instantiate the BenchmarkRunner so that it prepares the job control
  # objects for each benchmark
  benchmark = run_benchmark.BenchmarkRunner(job_control)
  benchmark.execute()

  mock_have_build_options.assert_called()
  mock_pull_image.assert_called()
  mock_symlink.assert_called()
  mock_execute.assert_has_calls([mock.call(), mock.call()])


def raise_docker_pull_exception(image_name):
  raise docker_image.DockerImagePullError(f"failed to pull image: {image_name}")


@mock.patch('os.symlink')
@mock.patch.object(scavenging_benchmark.Benchmark, 'execute_benchmark')
@mock.patch(_BUILD_NIGHTHAWK_BENCHMARK_IMAGE_FROM_SOURCE)
@mock.patch(_BUILD_NIGHTHAWK_IMAGE_FROM_SOURCE)
@mock.patch(_BUILD_ENVOY_IMAGE_FROM_SOURCE)
@mock.patch.object(docker_image.DockerImage, 'pull_image')
@mock.patch.object(source_manager.SourceManager, 'have_build_options')
@mock.patch.object(source_manager.SourceManager, 'get_envoy_hashes_for_benchmark')
def test_execute_with_building_envoy_images(mock_hashes_for_benchmarks, mock_have_build_options,
                                            mock_pull_image, mock_build_envoy,
                                            mock_build_nighthawk_binary,
                                            mock_build_nighthawk_benchmark, mock_execute,
                                            mock_symlink):
  """Verify that we invoke the build methods if we are not able to pull
  the required images for a benchmark
  """
  # Build a default job control object with images
  job_control = generate_test_objects.generate_default_job_control()
  generate_test_objects.generate_images(job_control)
  generate_test_objects.generate_envoy_source(job_control)

  # mock_build_envoy.return_value = None
  mock_pull_image.side_effect = raise_docker_pull_exception
  mock_have_build_options.return_value = False
  mock_hashes_for_benchmarks.return_value = {'tag1', 'tag2'}

  # Instantiate the BenchmarkRunner so that it prepares the job control
  # objects for each benchmark
  benchmark = run_benchmark.BenchmarkRunner(job_control)
  benchmark.execute()

  mock_build_nighthawk_benchmark.assert_called()
  mock_build_nighthawk_binary.assert_called()
  mock_build_envoy.assert_called()
  mock_pull_image.assert_called()
  mock_symlink.assert_called()
  mock_execute.assert_has_calls([mock.call(), mock.call()])


def test_benchmark_failure_if_no_benchmark_selected():
  """Verify that we raise an exception if no benchmark is configured to run.
  """
  # Build a default job control object no benchmark selected
  job_control = proto_control.JobControl(remote=False)

  # Instantiate the BenchmarkRunner so that it prepares the job control
  # objects for each benchmark
  with pytest.raises(NotImplementedError) as not_implemented:
    _ = run_benchmark.BenchmarkRunner(job_control)

  assert str(not_implemented.value) == \
      "No [Unspecified Benchmark] defined"


if __name__ == '__main__':
  raise SystemExit(pytest.main(['-s', '-v', __file__]))
