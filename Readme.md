**Pre-requisite:**

1. python2
2. gcloud

Follow these set-up before running the benchmarking script.

1. Keep your envoy-binary in an accessible location, `$ENVOY_BINARY`.
2. Keep all the scripts, Makefiles in a directory, `$SCRIPTS`. The scripts, Makefiles refer to the same files that are included in this benchmarking package.
3. Keep all the Envoy configurations in a directory, `$ENVOY_CONFIG`.
4. Select a directory in which you want to keep the result, `$RESULT`.

Google Cloud-related setup:
1. Create a Service Account.
2. Grant proper roles to the newly created Service Account, such as roles/owner.

Install the following packages (possibly running the below commands): `pexpect` `python-matplotlib`

1. `sudo pip install pexpect`
2. `sudo apt-get install python-matplotlib`

Run the benchmarking script, as follows with python2:

	python2 benchmark.py --local_envoy_binary_path $ENVOY_BINARY --scripts_path $SCRIPTS --envoy_config_path $ENVOY_CONFIG --result_dir $RESULT --username $USERNAME

The above command will create a VM in the `us-east1-b` zone (default) with the name, `envoy-vm`. The VM will have, by default, 20 CPUs, 76GB RAM and run Ubuntu 16.04 LTS under `envoy-ci` project. All the output and errors will be written in a file, named `benchmark.log`. You can change these default settings by providing the following arguments to the above Python script:

	  --vm_name		name of the virtual machine that you want to create
		                (default: envoy-vm)
	  --local_envoy_binary_path
		                local relative path of the envoy binary (default:
		                ./envoy-fastbuild)
	  --scripts_path	local relative path to the directory of all helper
		                scripts and configs (default: ./)
	  --envoy_config_path
		                local relative path to the directory of the envoy
		                configs (default: ./envoy-configs)
	  --result_dir
		                local relative path to the directory of the
		                benchmarking result file (default: ./)
	  --username   		username on the VM in the cloud-platform (default:
		                envoy)
	  --zone            the zone where you want to create the VM. (default:
		                us-east1-b)
	  --cpu             number of CPU cores. (default: 20)
	  --ram             amount of ram in the VM in MB. (default: 76)
	  --os_img_family
		                the OS in which you want the benchmark. (default:
		                ubuntu-1604-lts)
	  --os_img_project
		                the project in which the OS can be found. (default:
		                ubuntu-os-cloud)
	  --project     	the project name. (default: envoy-ci)
	  --logfile     	the local log file for this script. New log messages 
		                are appended to this file. (default: benchmark.log)
	 --num_retries      the number of retries for a single command. (default:
                        15)
	  --sleep_between_retry
		                number of seconds to sleep between each retry.
		                (default: 5)
	  --create_delete       if you want to create/delete new VM. (default: True)
	  --no-create_delete
	  --setup               if you want to run setup. (default: True)
	  --no-setup
	                        