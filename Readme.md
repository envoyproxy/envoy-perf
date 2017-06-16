**Pre-requisite:**

1. python2
2. gcloud

Follow these set-up before running the benchmarking script.

1. Keep your envoy-binary in an accessible location, `$ENVOY_BINARY`.
2. Keep all the scripts, Makefiles in a directory, `$SCRIPTS`. The scripts and Makefiles refer to the same files that are included in this benchmarking package.
3. Keep all the Envoy configurations in a directory, `$ENVOY_CONFIG`.
4. Select a directory in which you want to keep the result, `$RESULT`.

Install the following packages (possibly running the below commands): `pexpect`

1. `sudo pip install pexpect`

Run the benchmarking script, as follows with python2:

	python2 benchmark.py $VM_NAME $ENVOY_BINARY $SCRIPTS $ENVOY_CONFIG $RESULT $USERNAME

The above command will create a VM in the `us-east1-b` zone (default) with the name, `envoy-vm`. The VM will have, by default, 20 CPUs, 76GB RAM and run Ubuntu 16.04 LTS under `envoy-ci` project. All the output and errors will be written in a file, named `benchmark.log`. You can change these default settings by providing the following arguments to the above Python script:

	  --vm_name		name of the virtual machine that you want to create
		                (default: envoy-vm)
	  --local_envoy_binary_path
		                local absolute path of the envoy binary (default:
		                ./envoy-fastbuild)
	  --scripts_path	local absolute path to the directory of all helper
		                scripts and configs (default: ./)
	  --envoy_config_path
		                local absolute path to the directory of the envoy
		                configs (default: ./envoy-configs)
	  --result_dir
		                local absolute path to the directory of the
		                benchmarking result file (default: ./)
	  --username   		username on the VM in the cloud-platform (default:
		                envoy)
	  --zone            the zone where you want to create the VM. (default:
		                us-east1-b)
	  --cpu             number of CPU cores. (default: 20)
	  --ram             amount of ram in the VM in MB. (default: 76)
	  --os_img_family
		                the os in which you want the benchmark. (default:
		                ubuntu-1604-lts)
	  --os_img_project
		                the project in which the os can be found. (default:
		                ubuntu-os-cloud)
	  --project     	the project name. (default: envoy-ci)
	  --logfile     	the local log file for this script. New log will
		                beappended to this file. (default: benchmark.log)
	  --create_delete
		                Do you want to create/delete a VM? (yes/no) (default:
		                yes)
	  --skip_setup
		                Do you want to skip the setup?(yes/no) (default: yes)
	                        