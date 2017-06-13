"""This file generates some scripts, Makefiles."""

import argparse

from jinja2 import Environment
from jinja2 import FileSystemLoader


def main():
  parser = argparse.ArgumentParser()
  parser.add_argument("template_dir",
                      help="the absolute path to the template directory")
  parser.add_argument("username",
                      help="your username on the VM in the cloud-platform")
  parser.add_argument("--script_name",
                      help="don't change this. This is kept"
                           " for future-exptentsion. default: Makefile",
                      default="Makefile")

  args = parser.parse_args()

  j2_env = Environment(loader=FileSystemLoader(args.template_dir),
                       trim_blocks=True)
                       
  with open(args.script_name, "w") as f:
    f.write(j2_env.get_template("Makefile.template").render(
        username=str(args.username)))

if __name__ == "__main__":
  main()
