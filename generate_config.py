"""This file generates the configuration files for nginx."""

import argparse

from jinja2 import Environment
from jinja2 import FileSystemLoader

def main():
  parser = argparse.ArgumentParser()
  parser.add_argument("template_dir",
                      help="the absolute path to the template directory")
  parser.add_argument("--nginx_config_filename",
                      help="the new nginx config file name",
                      default="nginx.conf")
  # TODO(sohamcodes): later on, there could be more than one server, so this
  # parameter needs to be changed accordingly
  parser.add_argument("--server_config_filename",
                      help="the new filename for the server configuration."
                           " default: default", default="default")
  parser.add_argument("--worker_proc_count",
                      help="number of worker processes in nginx. default: 10",
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
  parser.add_argument("--nginx_port", help="nginx's responsive port number"
                                        ". default: 4500",
                      type=int, default=4500)

  args = parser.parse_args()
  if args.port_no < 1024 or args.port_no > 65535:
    parser.error("argument --port_no needs to be >= 1024 and <= 65535")

  j2_env = Environment(loader=FileSystemLoader(args.template_dir),
                       trim_blocks=True)

  with open(args.nginx_config_filename, "w") as f:
    f.write(j2_env.get_template("nginx.template.conf").render(
        no_of_worker_proc=str(args.worker_proc_count),
        worker_rlimit_nofile=str(args.worker_rlimit_nofile),
        worker_connections=str(args.worker_connections),
        keepalive_timeout=str(args.keepalive_timeout)))

  with open(args.server_config_filename, "w") as f:
    f.write(j2_env.get_template("default.template").render(
        port_no=str(args.nginx_port)))

if __name__ == "__main__":
  main()
