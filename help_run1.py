import os, subprocess

firstPort = 8001

if __name__ == "__main__":
    processHandles = []
    snakes = []
    port = firstPort
    os.chdir("../../")
    for folder in os.listdir():
        if os.path.isdir(folder):
            commands = f"cd {folder} & py main.py --port {port}"
            print(commands)
            processHandles.append(subprocess.Popen(commands, stdout=subprocess.PIPE, shell=True))
            port += 1
            snakes.append(folder)

    for handle in processHandles:
        handle.wait()
        
    print("done")
