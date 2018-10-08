"""This file generates the configuration files for nginx."""

import argparse

from jinja2 import Environment
from jinja2 import FileSystemLoader

import utils


def main():
  parser = argparse.ArgumentParser(
      formatter_class=argparse.ArgumentDefaultsHelpFormatter)
  parser.add_argument("template_dir",
                      help="the absolute path to the template directory")
  parser.add_argument("--nginx_config_filename",
                      help="the new nginx config file name",
                      default="nginx.conf")
  # TODO(sohamcodes): later on, there could be more than one server, so this
  # parameter needs to be changed accordingly
  parser.add_argument("--server_config_filename",
                      help="the new filename for the server configuration.",
                      default="default")
  parser.add_argument("--worker_proc_count",
                      help="number of worker processes in nginx.",
                      type=int, default=10)
  parser.add_argument("--worker_rlimit_nofile",
                      help="maximum number of open files for worker processes.",
                      type=int, default=200000)
  parser.add_argument("--worker_connections",
                      help="maximum number of simultaneous open connections"
                      " by a worker processes.",
                      type=int, default=35000)
  parser.add_argument("--keepalive_timeout",
                      help="timeout for keepalive connections.",
                      type=int, default=2000)
  parser.add_argument("--nginx_port", help="nginx's responsive port number.",
                      type=int, default=4500)
  utils.CreateBooleanArgument(parser, "ssl",
                              ("turn on if you want"
                               " to enable ssl on Nginx"),
                              ssl=True)
  utils.CreateBooleanArgument(parser, "h1",
                              ("turn on if you want"
                               " to enable HTTP1.1, instead of default h2"),
                              h1=False)

  args = parser.parse_args()
  if args.nginx_port < 1024 or args.nginx_port > 65535:
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
        port_no=str(args.nginx_port),
        ssl=("ssl " if args.ssl else ""),
        http2=("" if args.h1 else "http2 ")))

if __name__ == "__main__":
  main()
