#this sets the nginx processes into 5 cores
#envoy into 5 cores
#h2load will be set to 5 cores for 10 clients
import sh, io, sys, shlex

nginx_start_core = 0
nginx_end_core = 4
envoy_start_core = 5
envoy_end_core = 9
h2load_start_core = 10
h2load_end_core = 14

#allocate nginx to 5 cores
buf = io.StringIO()
sh.pgrep('nginx', _out=buf)
for x in buf.getvalue().split('\n'):
    output = io.StringIO()
    if(x.strip() != ''):
        sh.sudo.taskset('-cp', str(nginx_start_core) + '-' + str(nginx_end_core), x, _out=output)

#allocate envoy to 5 cores
#./envoy-fastbuild -c envoy-configs/simple-loopback.json -l debug > out.txt 2>&1 &
envoyconfig = "-c envoy-configs/simple-loopback.json -l debug"
outfile = "out.txt"
envoy = sh.Command("./envoy-fastbuild")
#this creates the process in the background, however it'll be destroyed once the python script is finished
#if we really need envoy to keep running on background after exiting python script, then we probably should use subprocess instead of sh
run = envoy(envoyconfig.split(" "), _out = outfile, _err_to_out = True, _bg = True)
print("envoy process id is: " + str(run.pid))
sh.sudo.taskset('-cp', str(envoy_start_core) + '-' + str(envoy_end_core), str(run.pid), _out=output)

#allocate h2load to 5 cores

h2load_args = "-c " + str(h2load_start_core) + '-' + str(h2load_end_core) + " h2load https://localhost -n10000 -c100 -m10 -t10"
sh.sudo.taskset(h2load_args.split(' '), _out = "res_direct.txt")
print("h2load direct is done.")

h2load_args = "-c " + str(h2load_start_core) + '-' + str(h2load_end_core) + " h2load https://localhost:9000 -n10000 -c100 -m10 -t10"
sh.sudo.taskset(h2load_args.split(' '), _out = "res_envoy.txt")
print("h2load against envoy is done.")
