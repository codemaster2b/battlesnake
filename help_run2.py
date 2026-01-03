import os, subprocess, sys

firstPort = 8001

if __name__ == "__main__":
    snakes = ["main"]
    if len(sys.argv) > 2:
        for i in range(2,len(sys.argv)):
            snakes = sys.argv[2:]

    game_type = "solo"
    if len(snakes) > 1:
        game_type = "royale"

    commands = f"battlesnake play -W 11 -H 11 --browser -g {game_type}"
    port = firstPort
    for snake in snakes:
        commands += f" --name {snake} --url http://0.0.0.0:{port}"
        port += 1
    print(commands)
    subprocess.Popen(commands, stdout=subprocess.PIPE, shell=True).wait()
    print("done")
