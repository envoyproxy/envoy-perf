**Pre-requisite:**

1. python2
2. gcloud

Follow these set-up before running the benchmarking script.

1. Keep all the scripts, Makefiles in a single folder.
2. Keep all the envoy-configs in a single folder.
3. Keep your envoy-binary in an accessible location

Install the following packages (possibly running the below commands): `sh`, `pexpect`

1. `sudo pip install pexpect sh`

Run as follows with python2:

	usage: benchmark.py [-h] [--zone ZONE] [--cpu CPU] [--ram RAM]
	                    [--os_img_family OS_IMG_FAMILY]
	                    [--os_img_project OS_IMG_PROJECT] [--project PROJECT]
	                    [--logfile LOGFILE]
	                    vm_name local_envoy_binary_path scripts_path
	                    envoy_config_path result_dir username
	
	positional arguments:
	  vm_name               name of the virtual machine that you want to create
	  local_envoy_binary_path
	                        local abosolute path of the envoy binary
	  scripts_path          local absolute path to the directory of all helper
	                        scripts and configs
	  envoy_config_path     local absolute path to the directory of the envoy
	                        configs
	  result_dir            local absolute path to the directory of the
	                        benchmarking result file
	  username              username on the VM in the cloud-platform
	
	optional arguments:
	  -h, --help            show this help message and exit
	  --zone ZONE           the zone where you want to create the VM. default: us-
	                        east1-b
	  --cpu CPU             number of CPU cores. default: 20
	  --ram RAM             amount of ram in the VM in MB. default: 76 MB
	  --os_img_family OS_IMG_FAMILY
	                        the os in which you want the benchmark. default:
	                        ubuntu-1604-lts
	  --os_img_project OS_IMG_PROJECT
	                        the project in which the oscan be found. default:
	                        ubuntu-os-cloud
	  --project PROJECT     the project namedefault: envoy-ci
	  --logfile LOGFILE     the local log file for this script. default:
	                        logfile.log

