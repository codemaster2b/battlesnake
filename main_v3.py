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
import queue
import numpy as np
import datetime

SCORE_DIE = -1000000
SCORE_KILL = 1000

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
    nextMove = random.choice(PossibleMoves)

  print(f"MOVE {gameState['turn']}: {nextMove}")
  return {"move": nextMove}

def make_move(gameState, results, endTime):
  depth = 2
  times = []
  times.append(datetime.datetime.now())
  while datetime.datetime.now() < endTime and depth < 100:
    value, move = minimax(endTime, copy.deepcopy(gameState["board"]), depth, True, SCORE_DIE, 3*SCORE_KILL)
    times.append(datetime.datetime.now())    
    if datetime.datetime.now() < endTime and move in PossibleMoves:
      print("iteration depth",depth,"best move",move)
      results.put(move)
    depth += 2
    if times[-1] - times[-2] >= endTime - datetime.datetime.now():
      return
  return

def minimax(endTime, myBoard, depth, maximizingPlayer, alpha, beta):
  if datetime.datetime.now() >= endTime:
    return (0, "---")
  bestMoves = PossibleMoves
  bestValue = 0

  if depth == 0:
    estimate = 0
    maxRoomScore = 10
    for snake in myBoard["snakes"]:
      if snake["id"] == myBoard["myId"]:
        if not avoid_walls(snake["body"][0], myBoard["width"], myBoard["height"]):
          estimate += SCORE_DIE
        elif not avoid_snakes(snake, myBoard):
          estimate += SCORE_DIE
        elif snake["health"] < 1:
          estimate += SCORE_DIE
        else:
          estimate -= calcFoodScore(myBoard, snake)
          estimate += calcHazardScore(myBoard, snake)
          estimate += calcLengthScore(snake)
          estimate += calcRunwayScore(myBoard, snake, maxRoomScore)
      else:
        if not avoid_walls(snake["body"][0], myBoard["width"], myBoard["height"]):
          estimate += SCORE_KILL
        elif not avoid_snakes(snake, myBoard):
          estimate += SCORE_KILL
        elif snake["health"] < 1:
          estimate += SCORE_KILL
        else:
          estimate += calcFoodScore(myBoard, snake)
          estimate -= calcHazardScore(myBoard, snake)
          estimate -= calcLengthScore(snake)
          estimate -= calcRunwayScore(myBoard, snake, maxRoomScore)

    return (estimate, "---")
  if maximizingPlayer:
    bestValue = SCORE_DIE
    bestMoves = []
    for move in PossibleMoves:
      if datetime.datetime.now() >= endTime:
        return (0, "---")
      newBoard, err = board_after_move(myBoard, move, maximizingPlayer)
      if err:
        value = SCORE_DIE
      else:
        value, m = minimax(endTime, newBoard, depth - 1, not maximizingPlayer, alpha, beta)
        
      if value == bestValue:
        bestMoves = bestMoves + [move]
      elif value > bestValue:
        bestValue = value
        bestMoves = [move]
      alpha = max(alpha, bestValue)
      if beta < alpha:
        break
  else:  # minimizing player
    bestValue = SCORE_KILL
    bestMoves = []
    for move in PossibleMoves:
      if datetime.datetime.now() >= endTime:
        return (0, "---")
      newBoard, err = board_after_move(myBoard, move, maximizingPlayer)
      if err:
        value = SCORE_KILL
      else:
        value, m = minimax(endTime, newBoard, depth - 1, not maximizingPlayer, alpha, beta)
      
      if value == bestValue:
        bestMoves = bestMoves + [move]
      elif value < bestValue:
        bestValue = value
        bestMoves = [move]
      beta = min(beta, bestValue)
      if beta < alpha:
        break

  if len(bestMoves) > 0:
    bestMove = random.choice(bestMoves)
  else:
    bestMove = random.choice(PossibleMoves)
  return (bestValue, bestMove)

def board_after_move(myBoard, move, maximizingPlayer):
  newBoard = copy.deepcopy(myBoard)
  err = False
  
  movingSnakes = []
  for snake in newBoard["snakes"]:
    if maximizingPlayer:
      if snake["id"] == newBoard["myId"]:
        movingSnakes.append(snake)
    else:
      if snake["id"] != newBoard["myId"]:
        movingSnakes.append(snake)
  
  for snake in movingSnakes:
    next = get_next(snake["body"][0], move)
    if not avoid_walls(next, newBoard["width"], newBoard["height"]):
      err = True
    elif not avoid_snakes(snake, newBoard):
      err = True
    else:
      snake["body"].insert(0, next)
      ateFood = False
      for food in newBoard["food"]:
        if food["x"] == next["x"] and food["y"] == next["y"]:
          ateFood = True
          newBoard["food"].remove(food)
          break
      if snake["health"] < 100 and newBoard["map"] != "constrictor":
        snake["body"].pop()
      snake["health"] = snake["health"] - 1
      if "hazards" in newBoard.keys():
        for hazard in newBoard["hazards"]:
          if hazard["x"] == next["x"] and hazard["y"] == next["y"]:
            snake["health"] = snake["health"] - 15
      if ateFood:
        snake["health"] = 100
  return newBoard, err

def avoid_walls(futureHead, boardWidth, boardHeight):
  x = int(futureHead["x"])
  y = int(futureHead["y"])
  if x < 0 or y < 0 or x >= boardWidth or y >= boardHeight:
    return False
  else:
    return True

def avoid_snakes(currentSnake, myBoard):
  currentSnakeLen = len(currentSnake["body"])
  currentHead = currentSnake["body"][0]
  for snake in myBoard["snakes"]:
    snakeLen = len(snake["body"])
    if currentHead in snake["body"][1:]:
      return False
    if snake["id"] != currentSnake["id"] and snakeLen >= currentSnakeLen and currentHead == snake["body"][0]:
      return False
  return True
  
def calcFoodScore(myBoard, snake):
  if snake is None:
    return 0
  else:
    foodScore = myBoard["width"] + myBoard["height"]
    head = snake["body"][0]
    for food in myBoard["food"]:
      foodScore = min(foodScore, abs(food["x"] - head["x"]) + abs(food["y"] - head["y"]))
    return foodScore

def calcHazardScore(myBoard, snake):
  if snake is None or "hazards" not in myBoard.keys():
    return 0
  else:
    next = snake["body"][0]
    for hazard in myBoard["hazards"]:
      if hazard["x"] == next["x"] and hazard["y"] == next["y"]:
        return -115
    return 0

def calcLengthScore(snake):
  if snake is None:
    return 0
  else:
    return (len(snake["body"]) + int(snake["health"] / 100)) * 25

def calcRunwayScore(myBoard, snake, limit):
  if snake is None:
    return 0
  else:
    found = []
    visited = []
    distances = [0 for i in range(121)]
      
    for s in myBoard["snakes"]:
      for part in s["body"]:
        index = part["y"]*11+part["x"]
        found.append(index)
        visited.append(index)
        distances[index] = 0
  
    #first node
    index = snake["body"][0]["y"]*11+snake["body"][0]["x"]
    found.append(index)
    limit_reached = False
    while len(found) > len(visited) and max(distances) <= limit:
      node = found[len(visited)]
      visited.append(node)
      new_nodes = [node - 11, node + 11, node - 1, node + 1]
      for new_node in new_nodes:
        if not node in found and new_node >= 0 and node%11 >= 0 and node//11 < myBoard["height"] and node%11 < myBoard["width"]:
          found.append(new_node)
          distances[new_node] = distances[node] + 1
          if distances[new_node] >= limit:
            limit_reached = True    

    return int(max(distances) * 25 / limit)
  
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
