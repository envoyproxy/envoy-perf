#!/bin/bash

set -e

# Required tokens, see:
# https://github.com/envoyproxy/envoy-perf/blob/main/salvo-remote/azure-pipelines/README.md
export AWS_ACCESS_KEY_ID=${AWS_ACCESS_KEY_ID:-}
export AWS_SECRET_ACCESS_KEY=${AWS_SECRET_ACCESS_KEY:-}

# The name of the salvo-remote ASG (Auto Scaling Group) this script controls.
export SALVO_REMOTE_ASG="salvo-azp-agent-vm-x64_salvo-control_pool"

# The region Salvo resources run in.
export AWS_REGION="us-west-1"

# Sets the capacity of the salvo-remote ASG.
# Arguments:
#   An integer, the desired capacity.
function set_salvo_asg_capacity() {
	local desired_capacity="$1"

  aws autoscaling update-auto-scaling-group \
    --region "${AWS_REGION}" \
    --auto-scaling-group-name "${SALVO_REMOTE_ASG}" \
    --min-size "${desired_capacity}" \
    --desired-capacity "${desired_capacity}"
}

# Configure the salvo-remote ASG to have at least one instance to process jobs.
function preheat_salvo_asg() {
  echo "Preheating the salvo-remote ASG."
  set_salvo_asg_capacity 1

  # Give the VM enough time to start up and register with AZP.
  local sleep_time=150
  echo "Sleeping for ${sleep_time} seconds to give the ASG time to setup a VM."
  sleep ${sleep_time}
}

# Configure the salvo-remote ASG to have zero instance.
function cooldown_salvo_asg() {
  echo "Cooling the salvo-remote ASG."
  set_salvo_asg_capacity 0
}


# Set the action to perform.
# If no parameters are defined, print out the help text.
action=${1:-}

case "${action}" in
  "preheat")
    preheat_salvo_asg
    ;;
  "cooldown")
    cooldown_salvo_asg
    ;;
  *)
    echo "usage: asg_control.sh {action}, the action must be one of [preheat, cooldown]"
    exit 1
    ;;
esac

exit 0
