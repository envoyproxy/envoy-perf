"""This file generates the configuration files for nginx."""

import argparse

from jinja2 import Environment
from jinja2 import FileSystemLoader

# TODO(sohamcodes): Need to do templating for nginx.conf, default
# also add a call this python script in the main scripting


def main():
  parser = argparse.ArgumentParser()
  parser.add_argument("template_dir",
                      help="the absolute path to the template directory")
  parser.add_argument("--nginx_config_filename",
                      help="the generated nginx config file name",
                      default="nginx.conf")
  parser.add_argument("--no_of_worker_proc",
                      help="no of worker processes in nginx. default: 10",
                      type=int, default=10)
  parser.add_argument("--worker_rlimit_nofile",
                      help="maximum number of open files for worker processes"
                      ". default: 100000",
                      type=int, default=100000)
  parser.add_argument("--worker_connections",
                      help="maximum number of simultaneous open connections"
                      " by a worker processes. default: 4000",
                      type=int, default=4000)
  parser.add_argument("--keepalive_timeout",
                      help="timeout for keepalive connections"
                      ". default: 250",
                      type=int, default=250)

  args = parser.parse_args()
  j2_env = Environment(loader=FileSystemLoader(args.template_dir),
                       trim_blocks=True)

  with open(args.nginx_config_filename, "w") as f:
    f.write(j2_env.get_template("nginx.template.conf").render(
        no_of_worker_proc=str(args.no_of_worker_proc),
        worker_rlimit_nofile=str(args.worker_rlimit_nofile),
        worker_connections=str(args.worker_connections),
        keepalive_timeout=str(args.keepalive_timeout)))

if __name__ == "__main__":
  main()
