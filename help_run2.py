import os, subprocess

firstPort = 8001

if __name__ == "__main__":
    snakes = []
    os.chdir("../../")
    for folder in os.listdir():
        if os.path.isdir(folder):
            snakes.append(folder)
    
    commands = f"battlesnake play -W 11 -H 11 --browser -g royale"
    port = firstPort
    for snake in snakes:
        commands += f" --name {snake} --url http://0.0.0.0:{port}"
        port += 1
    print(commands)
    subprocess.Popen(commands, stdout=subprocess.PIPE, shell=True).wait()
    print("done")
