"""this python file distributes h2load, nginx and envoy into separate cores.

it uses sh module to call shell functionalities.
"""
import io
import sys
import sh


def process_h2load_output(line):
  """process the h2load output after each line."""
  open("result.txt", "a+").write(line)

nginx_start_core = 0
nginx_end_core = 9
envoy_start_core = 10
envoy_end_core = 14
h2load_start_core = 15
h2load_end_core = 19

# arguments to program
envoy_path = sys.argv[1]
envoy_config_path = sys.argv[2]

# allocate nginx to designated cores
buf = io.StringIO()
sh.pgrep("nginx", _out=buf)
for x in buf.getvalue().split("\n"):
  output = io.StringIO()
  if x.strip():
    sh.sudo.taskset("-cp", str(nginx_start_core) +
                    "-" + str(nginx_end_core), x, _out=output)

# allocate envoy to designated cores
# following is the shell command we are trying to replicate
# ./envoy-fastbuild -c envoy-configs/simple-loopback.json\
# -l debug > out.txt 2>&1 &
envoyconfig = "-c " + envoy_config_path + " -l debug"
outfile = "out.txt"
envoy = sh.Command(envoy_path)
# this creates the process in the background, however it'll be destroyed
# once the python script is finished
# if we really need envoy to keep running on background after exiting the
# python script, then we probably should use subprocess instead of sh
run = envoy(envoyconfig.split(" "), _out=outfile, _err_to_out=True, _bg=True)
print "envoy process id is: " + str(run.pid)
sh.sudo.taskset("-cp", str(envoy_start_core) +
                "-" + str(envoy_end_core), str(run.pid), _out=output)

# allocate h2load to designated cores
open("result.txt", "w").write("")
h2load_args = "-c {}-{} h2load https://localhost -n100000 -c100 -m10 -t5".format(h2load_start_core, h2load_end_core)
sh.sudo.taskset(h2load_args.split(" "), _out=process_h2load_output)
print "h2load direct is done."

h2load_args = "-c {}-{} h2load https://localhost:9000 -n100000 -c100 -m10 -t5".format(h2load_start_core, h2load_end_core)
sh.sudo.taskset(h2load_args.split(" "), _out=process_h2load_output)
print "h2load against envoy is done."

# run.wait()
