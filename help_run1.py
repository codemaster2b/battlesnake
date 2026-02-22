import os, subprocess, sys
from datetime import datetime

if __name__ == "__main__":
    processHandles = []
    colors = ["#03fcf4","#03c0c0","#fa003f","#06402b"]
    if len(sys.argv) > 2:
        for i in range(2,len(sys.argv)):
            commands = f"py main_{sys.argv[i]}.py --port {7999 + i} --color {colors[i-2]} --log log.{int(datetime.now().timestamp())}.snake{i-1}.{sys.argv[i]}.txt"
            print(commands)
            processHandles.append(subprocess.Popen(commands, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, shell=True))
    else:
        commands = f"py main.py --port 8001"
        print(commands)
        processHandles.append(subprocess.Popen(commands, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, shell=True))

    for handle in processHandles:
        handle.wait()
        
    print("done")
