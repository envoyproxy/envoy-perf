#this sets the nginx processes into 5 cores
#envoy into 5 cores
#h2load will be set to 5 cores for 100 clients
import sh, io, sys, shlex

write_result = False

def process_h2load_output(line):
    global write_result
    if write_result:
        open("result.txt", "a+").write(line)
    if line.strip() == "progress: 100% done":
        write_result = True

nginx_start_core = 0
nginx_end_core = 9
envoy_start_core = 10
envoy_end_core = 14
h2load_start_core = 15
h2load_end_core = 19

#arguments to program
envoy_path = sys.argv[1]
envoy_config_path = sys.argv[2]

#allocate nginx to designated cores
buf = io.StringIO()
sh.pgrep('nginx', _out=buf)
for x in buf.getvalue().split('\n'):
    output = io.StringIO()
    if(x.strip() != ''):
        sh.sudo.taskset('-cp', str(nginx_start_core) + '-' + str(nginx_end_core), x, _out=output)

#allocate envoy to designated cores
#./envoy-fastbuild -c envoy-configs/simple-loopback.json -l debug > out.txt 2>&1 &
envoyconfig = "-c " + envoy_config_path + " -l debug"
outfile = "out.txt"
envoy = sh.Command(envoy_path)
#this creates the process in the background, however it'll be destroyed once the python script is finished
#if we really need envoy to keep running on background after exiting python script, then we probably should use subprocess instead of sh
run = envoy(envoyconfig.split(" "), _out = outfile, _err_to_out = True, _bg = True)
print("envoy process id is: " + str(run.pid))
sh.sudo.taskset('-cp', str(envoy_start_core) + '-' + str(envoy_end_core), str(run.pid), _out=output)

#allocate h2load to designated cores
open("result.txt", "w").write("")
write_result = False
h2load_args = "-c " + str(h2load_start_core) + '-' + str(h2load_end_core) + " h2load https://localhost -n100000 -c100 -m10 -t5"
sh.sudo.taskset(h2load_args.split(' '), _out = process_h2load_output)
print("h2load direct is done.")

write_result = False
h2load_args = "-c " + str(h2load_start_core) + '-' + str(h2load_end_core) + " h2load https://localhost:9000 -n100000 -c100 -m10 -t5"
sh.sudo.taskset(h2load_args.split(' '), _out = process_h2load_output)
print("h2load against envoy is done.")

#run.wait()
