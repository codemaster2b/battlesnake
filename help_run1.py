import os, subprocess,sys

firstPort = 8001

if __name__ == "__main__":
    processHandles = []
    port = firstPort
    if len(sys.argv) > 2:
        for i in range(2,len(sys.argv)):
            commands = f"py main_{sys.argv[i]}.py --port {port}"
            print(commands)
            processHandles.append(subprocess.Popen(commands, stdout=subprocess.PIPE, shell=True))
            port += 1
    else:
        commands = f"py main.py --port {port}"
        print(commands)
        processHandles.append(subprocess.Popen(commands, stdout=subprocess.PIPE, shell=True))

    for handle in processHandles:
        handle.wait()
        
    print("done")
