#this sets the nginx processes into 5 cores
#envoy into 1 core
#h2load will be set to 5 cores for 10 clients
import sh, io

buf = io.StringIO()
sh.pgrep('nginx', _out=buf)

for x in buf.getvalue().split('\n'):
    if(x.strip() != ''):
        sh.sudo.taskset('-cp', '0-4', x, _fg=True)
