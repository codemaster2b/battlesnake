# Welcome to
# __________         __    __  .__                               __
# \______   \_____ _/  |__/  |_|  |   ____   ______ ____ _____  |  | _____
#  |    |  _/\__  \\   __\   __\  | _/ __ \ /  ___//    \\__  \ |  |/ // __ \
#  |    |   \ / __ \|  |  |  | |  |_\  ___/ \___ \|   |  \/ __ \|    <\  ___/
#  |________/(______/__|  |__| |____/\_____>______>___|__(______/__|__\\_____>
#
# For more info see docs.battlesnake.com

import random
import typing
import sys
import copy
import time
import threading
import queue
import numpy as np
import datetime

PossibleMoves = ["up", "down", "left", "right"]
def get_next(currentHead, nextMove):
  futureHead = {}
  match nextMove:
    case "left":
      futureHead["x"] = currentHead["x"] - 1
      futureHead["y"] = currentHead["y"]
    case "right":
      futureHead["x"] = currentHead["x"] + 1
      futureHead["y"] = currentHead["y"]
    case "up":
      futureHead["x"] = currentHead["x"]
      futureHead["y"] = currentHead["y"] + 1
    case "down":
      futureHead["x"] = currentHead["x"]
      futureHead["y"] = currentHead["y"] - 1    
  return futureHead

# info is called when you create your Battlesnake on play.battlesnake.com
# and controls your Battlesnake's appearance
# TIP: If you open your Battlesnake URL in a browser you should see this data
def info() -> typing.Dict:
  print("INFO")
  return {
    "apiversion": "1",
    "author": "codemaster2b",
    "color": "#03c0c0",
    "head": "pixel",
    "tail": "pixel",
  }

# start is called when your Battlesnake begins a game
def start(gameState: typing.Dict):
  print("GAME START")

# end is called when your Battlesnake finishes a game
def end(gameState: typing.Dict):
  print("GAME OVER\n")

# move is called on every turn and returns your next move
def move(gameState: typing.Dict) -> typing.Dict:
  endTime = datetime.datetime.now() + datetime.timedelta(seconds=0.4)
  gameState["board"]["myId"] = gameState["you"]["id"]
  gameState["board"]["map"] = gameState["game"]["map"]
  results = queue.LifoQueue()
  make_move(gameState, results, endTime)

  if results.qsize() > 0:
    nextMove = results.get_nowait()
  else:
    goodMoves = []
    for move in PossibleMoves:
      next = get_next(gameState["you"]["body"][0], move)
      if avoid_walls(next, gameState["board"]["width"], gameState["board"]["height"]):
        if avoid_snakes(next, gameState["board"], gameState["you"]):
          goodMoves.append(move)
    if len(goodMoves) > 0:
      nextMove = random.choice(goodMoves)

  print(f"MOVE {gameState['turn']}: {nextMove}")
  return {"move": nextMove}

def make_move(gameState, results, endTime):
    goodMoves = []
    for move in PossibleMoves:
      next = get_next(gameState["you"]["body"][0], move)
      if avoid_walls(next, gameState["board"]["width"], gameState["board"]["height"]):
        if avoid_snakes(next, gameState["board"], gameState["you"]):
          goodMoves.append(move)
    if len(goodMoves) > 0:
      results.put(random.choice(goodMoves))
    else:
      results.put(random.choice(PossibleMoves))
    return

def avoid_walls(futureHead, boardWidth, boardHeight):
  x = int(futureHead["x"])
  y = int(futureHead["y"])
  if x < 0 or y < 0 or x >= boardWidth or y >= boardHeight:
    return False
  else:
    return True

def avoid_snakes(futureHead, newBoard, currentSnake):
  currentSnakeLen = len(currentSnake["body"])
  for snake in newBoard["snakes"]:
    snakeLen = len(snake["body"])    
    if futureHead in snake["body"][1:-1]:
      return False
    if snake["id"] != currentSnake["id"]:
      if (snake["health"] == 100 or newBoard["map"] != "constrictor" or snake["id"] == newBoard["myId"]) and futureHead == snake["body"][-1]:
        return False
      elif snake["id"] == newBoard["myId"] and snakeLen >= currentSnakeLen:
        #avoid connecting with another snake head that is >= my length and has moved already
        if futureHead == snake["body"][0]:
          return False
      elif snakeLen >= currentSnakeLen:
        #avoid being within 1 of another snake head that is >= my length and has not moved yet
        if abs(snake["body"][0]["x"]-futureHead["x"]) + abs(snake["body"][0]["y"]-futureHead["y"]) == 1:
          return False
  return True
  
# Start server when `python main.py` is run
if __name__ == "__main__":
  from server import run_server

  port = "8000"
  for i in range(len(sys.argv) - 1):
    if sys.argv[i] == '--port':
      port = sys.argv[i + 1]
    elif sys.argv[i] == '--seed':
      random_seed = int(sys.argv[i + 1])
  run_server({
    "info": info,
    "start": start,
    "move": move,
    "end": end,
    "port": port
  })
