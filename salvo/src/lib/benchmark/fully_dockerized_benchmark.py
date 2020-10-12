"""
This module contains the methods to perform a fully dockerized benchmark as
documented in the NightHawk repository:

https://github.com/envoyproxy/nighthawk/blob/master/benchmarks/README.md
"""

import logging

from lib.benchmark.base_benchmark import BaseBenchmark

log = logging.getLogger(__name__)

class Benchmark(BaseBenchmark):
    def __init__(self, **kwargs):
        super(Benchmark, self).__init__(**kwargs)

    def validate(self):
        """
        Validate that all data required for running the scavenging
        benchmark is defined and or accessible
        """
        verify_source = False
        images = self.get_images()

        # Determine whether we need to build the images from source
        # If so, verify that the required source data is defined
        verify_source = images is None or \
            not images.nighthawk_benchmark_image or \
            not images.nighthawk_binary_image  or \
            not images.envoy_image

        log.debug(f"Source verification needed: {verify_source}")
        if verify_source:
            self._verify_sources(images)

        return

    def _verify_sources(self, images):
        """
        Validate that sources are defined from which we can build a missing image
        """
        source = self.get_source()
        if not source:
            raise Exception("No source configuration specified")

        can_build_envoy = False
        can_build_nighthawk = False

        for source_def in source:
            # Cases:
            # Missing envoy image -> Need to see an envoy source definition
            # Missing at least one nighthawk image -> Need to see a nighthawk source

            if not images.envoy_image \
                and source_def.envoy and (source_def.location or source_def.url):
                can_build_envoy = True

            if (not images.nighthawk_benchmark_image or not images.nighthawk_binary_image) \
                and source_def.nighthawk and (source_def.location or source_def.url):
                can_build_nighthawk = True

            if (not images.envoy_image and not can_build_envoy) or \
                (not images.nighthawk_benchmark_image or \
                 not images.nighthawk_binary_image) and not can_build_nighthawk:

                # If the Envoy image is specified, then the validation failed for NightHawk and vice versa
                msg = "No source specified to build undefined {image} image".format(
                    image="NightHawk" if images.envoy_image else "Envoy")
                raise Exception(msg)

    def execute_benchmark(self):
        """
        Prepare input artifacts and run the benchmark
        """
        if self.is_remote():
            raise NotImplementedError("Local benchmarks only for the moment")

        # pull in environment and set values
        output_dir = self._control.environment.output_dir
        test_dir = self._control.environment.test_dir
        images = self.get_images()
        log.debug(f"Images: {images.nighthawk_benchmark_image}")

        # 'TMPDIR' is required for successful operation.
        image_vars = {
            'NH_DOCKER_IMAGE': images.nighthawk_binary_image,
            'ENVOY_DOCKER_IMAGE_TO_TEST': images.envoy_image,
            'TMPDIR': output_dir
        }
        log.debug(f"Using environment: {image_vars}")

        volumes = self.get_docker_volumes(output_dir, test_dir)
        log.debug(f"Using Volumes: {volumes}")
        self.set_environment_vars()

        # Explictly pull the images that are defined.  If this fails or does not work
        # our only option is to build things. The specified images are pulled when we
        # run them, so this step is not absolutely required
        if not images.reuse_nh_images:
            pulled_images = self.pull_images()
            if not pulled_images or len(pulled_images) != 3:
                raise NotImplementedError(("Unable to retrieve all images. ",
                                           "Building from source is not yet implemented"))

        kwargs = {}
        kwargs['environment'] = image_vars
        kwargs['command'] = ['./benchmarks', '--log-cli-level=info', '-vvvv']
        kwargs['volumes'] = volumes
        kwargs['network_mode'] = 'host'
        kwargs['tty'] = True

        # TODO: We need to capture stdout and stderr to a file to catch docker invocation issues
        #       This may help with the escaping that we see happening on an successful invocation
        result = ''
        try:
            result = self.run_image(images.nighthawk_benchmark_image, **kwargs)
        except Exception as e:
            log.exception(f"Exception occured {e}")

        # FIXME: result needs to be unescaped. We don't use this data and the same content
        #        is available in the nighthawk-human.txt file.
        log.debug(f"Output: {len(result)} bytes")

        log.info(f"Benchmark output: {output_dir}")

        return

#  vim: set ts=4 sw=4 tw=0 et :
