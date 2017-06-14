**Pre-requisite:**

1. python2
2. gcloud

Follow these set-up before running the benchmarking script.

1. Keep your envoy-binary in an accessible location, `$ENVOY_BINARY`
2. Keep all the scripts, Makefiles in a directory, `$SCRIPTS`
3. Keep all the Envoy configurations in a directory, `$ENVOY_CONFIG`
4. Select a directory in which you want to keep the result, `$RESULT`

Install the following packages (possibly running the below commands): `sh`, `pexpect`

1. `sudo pip install pexpect sh`

Run the benchmarking script, as follows with python2:

	python2 benchmark.py $VM_NAME $ENVOY_BINARY $SCRIPTS $ENVOY_CONFIG $RESULT $USERNAME

The above command will create a VM on the `us-east1-b` zone with the name, `$VM_NAME`. The VM will have `20 CPUs`, `76GB RAM` and run `Ubuntu 16.04 LTS` under `envoy-ci` project. All the output and errors will be written in a file, named `logfile.log`. You can change these default settings by providing the following arguments to the above python script:


	  --zone            the zone where you want to create the VM. default: us-
	                        east1-b
	  --cpu             number of CPU cores. default: 20
	  --ram             amount of ram in the VM in MB. default: 76 MB
	  --os_img_family
	           			the os in which you want the benchmark. default:
	                        ubuntu-1604-lts
	  --os_img_project
	                 	the project in which the oscan be found. default:
	                        ubuntu-os-cloud
	  --project     	the project namedefault: envoy-ci
	  --logfile     	the local log file for this script. default:
	                        logfile.log
	                        