# Welcome to
# __________         __    __  .__                               __
# \______   \_____ _/  |__/  |_|  |   ____   ______ ____ _____  |  | _____
#  |    |  _/\__  \\   __\   __\  | _/ __ \ /  ___//    \\__  \ |  |/ // __ \
#  |    |   \ / __ \|  |  |  | |  |_\  ___/ \___ \|   |  \/ __ \|    <\  ___/
#  |________/(______/__|  |__| |____/\_____>______>___|__(______/__|__\\_____>
#
# This file can be a nice home for your Battlesnake logic and helper functions.
#
# To get you started we've included code to prevent your Battlesnake from moving backwards.
# For more info see docs.battlesnake.com

import random
import typing
import sys
import copy
import time
import threading

RandomSeed = None
PossibleMoves = ["up", "down", "left", "right"]
BestMove = "up"
MoveLookup = {"left": -1, "right": 1, "up": 1, "down": -1}
GAME_END = 100000000
x = 0


# info is called when you create your Battlesnake on play.battlesnake.com
# and controls your Battlesnake's appearance
# TIP: If you open your Battlesnake URL in a browser you should see this data
def info() -> typing.Dict:
  print("INFO")
  return {
    "apiversion": "1",
    "author": "mcr460",
    "color": "#ff0000",
    "head": "tiger-king",
    "tail": "curled",
  }


# start is called when your Battlesnake begins a game
def start(gameState: typing.Dict):
  global x
  x = 0
  if RandomSeed is not None:
    random.seed(RandomSeed)
  print("GAME START")


# end is called when your Battlesnake finishes a game
def end(gameState: typing.Dict):
  print("GAME OVER\n")


# move is called on every turn and returns your next move
def move(gameState: typing.Dict) -> typing.Dict:
  global x
  start = time.time()
  nextMove = make_minimax_move(gameState, 5)
  end = time.time()
  print("Time taken this move:", int(1000 * (end - start)), "ms")
  x += 1000*(end-start)
  print("Average time so far:", x/(gameState['turn']+1))
  print(f"MOVE {gameState['turn']}: {nextMove}")
  return {"move": nextMove}


def avoid_walls(futureHead, boardWidth, boardHeight):
  x = int(futureHead["x"])
  y = int(futureHead["y"])
  if x < 0 or y < 0 or x >= boardWidth or y >= boardHeight:
    return False
  else:
    return True


def avoid_snakes(futureHead, snakes, currentSnake):
  for snake in snakes:
    snakeLen = len(snake["body"])
    currentSnakeLen = len(currentSnake["body"])
    if futureHead == snake["body"][0] and snakeLen <= currentSnakeLen:
      return False
    elif futureHead in snake["body"][:-1]:
      return False
    elif snake["health"] == 100 and futureHead in snake["body"]:
      return False
    elif futureHead == snake["body"][0] and len(
        snake["body"]) >= currentSnakeLen:
      return False
  return True


def get_next(currentHead, nextMove):
  futureHead = currentHead.copy()
  if nextMove in ["left", "right"]:
    futureHead["x"] = currentHead["x"] + MoveLookup[nextMove]
  elif nextMove in ["up", "down"]:
    futureHead["y"] = currentHead["y"] + MoveLookup[nextMove]
  return futureHead


def make_minimax_move(gameState: typing.Dict, depth) -> typing.Dict:
  myBoard = copy.deepcopy(gameState["board"])
  myBoard["myId"] = gameState["you"]["id"]
  myBoard["end"] = False
  myBoard["winner"] = 0  #no winner by default

  value, nextMove = minimax(myBoard, depth, True)
  return nextMove


def minimax(myBoard, depth, maximizingPlayer):
  bestMoves = PossibleMoves
  bestValue = 0

  if depth == 0 or myBoard["end"]:
    if myBoard["end"]:
      #print("game end", myBoard["winner"])
      return (myBoard["winner"], "---")

    estimate = 0
    for snake in myBoard["snakes"]:
      #calculate food score
      foodScore = myBoard["width"] + myBoard["height"]
      head = snake["body"][0]
      for food in myBoard["food"]:
        foodScore = min(
          foodScore,
          abs(food["x"] - head["x"]) + abs(food["y"] - head["y"]))
      if snake["id"] == myBoard["myId"]:
        estimate -= foodScore
      else:
        estimate += foodScore

      #calculate length score
      if snake["id"] == myBoard["myId"]:
        estimate += (len(snake["body"]) + int(snake["health"] / 100)) * 25
      else:
        estimate -= (len(snake["body"]) + int(snake["health"] / 100)) * 25

      #calculate future room score
      maxRoomScore = 10
      discovered = [snake["body"][0]]
      distances = [0]
      index = 0
      while index < len(discovered) and distances[-1] < maxRoomScore:
        origin = discovered[index]

        originUp = get_next(origin, "up")
        if originUp not in discovered and avoid_walls(
            originUp, myBoard["width"], myBoard["height"]):
          good = True
          for s in myBoard["snakes"]:
            if originUp in s["body"]:
              good = False
          if good:
            discovered.append(originUp)
            distances.append(distances[index] + 1)

        originDown = get_next(origin, "down")
        if originDown not in discovered and avoid_walls(
            originDown, myBoard["width"], myBoard["height"]):
          good = True
          for s in myBoard["snakes"]:
            if originDown in s["body"]:
              good = False
          if good:
            discovered.append(originDown)
            distances.append(distances[index] + 1)

        originLeft = get_next(origin, "left")
        if originLeft not in discovered and avoid_walls(
            originLeft, myBoard["width"], myBoard["height"]):
          good = True
          for s in myBoard["snakes"]:
            if originLeft in s["body"]:
              good = False
          if good:
            discovered.append(originLeft)
            distances.append(distances[index] + 1)

        originRight = get_next(origin, "right")
        if originRight not in discovered and avoid_walls(
            originRight, myBoard["width"], myBoard["height"]):
          good = True
          for s in myBoard["snakes"]:
            if originRight in s["body"]:
              good = False
          if good:
            discovered.append(originRight)
            distances.append(distances[index] + 1)
        index += 1

      if snake["id"] == myBoard["myId"]:
        estimate += max(distances)
      else:
        estimate -= max(distances)

      #calculate collision score
      for otherSnake in myBoard["snakes"]:
        if otherSnake["id"] != snake["id"]:
          otherHead = otherSnake["body"][0]
          distance = abs(otherHead["x"] - head["x"]) + abs(otherHead["y"] -
                                                           head["y"])
          #print("distance", distance,head["x"],head["y"],otherHead["x"],otherHead["y"],snake["health"],otherSnake["health"])
          if distance <= 2 and len(
              snake["body"]) > len(otherSnake["body"]) - 1:
            if snake["id"] == myBoard["myId"]:
              estimate += 100
            else:
              estimate -= 100

    return (estimate, "---")
  if maximizingPlayer:
    bestValue = GAME_END * -10
    bestMoves = []
    for move in PossibleMoves:
      newBoard = minimax_new_board(myBoard, move, maximizingPlayer)
      value, m = minimax(newBoard, depth - 1, False)
      if value == bestValue:
        bestMoves = bestMoves + [move]
      elif value > bestValue:
        bestValue = value
        bestMoves = [move]
    return (bestValue, random.choice(bestMoves))
  else:  # minimizing player
    bestMoves = []
    qs, ps = [], []
    x, S = 0, 0
    for move in PossibleMoves:
      newBoard = minimax_new_board(myBoard, move, maximizingPlayer)
      value, m = minimax(newBoard, depth - 1, True)

      # if moves leads to an instant win, just take it
      if (value < -10000):
        return (value, [move])

      # if moves leads to instant loss, don't consider it
      elif (value > 10000):
        continue

      bestMoves = bestMoves + [move]
      qs.append(value)
      x += (1.01**-value)

    # if no moves are added, all lead to instant loss, so give up
    if (len(qs) == 0):
      return (GAME_END, random.choice(PossibleMoves))

    # if length is one, then there is only one option
    elif (len(qs) == 1):
      return (qs[0], bestMoves[0])

    # probability is calculated with a bias for negative numbers
    for i in range(len(qs)):
      ps.append((1.01**-qs[i]) / x)
      S += ps[i] * qs[i]
    if (len(qs) == 2):
      return (S, random.choices(bestMoves, weights=[ps[0], ps[1]])[0])
    elif (len(qs) == 3):
      return (S, random.choices(bestMoves, weights=[ps[0], ps[1], ps[2]])[0])
    else:
      return (S, random.choice(PossibleMoves))


# Make a board move
def minimax_new_board(myBoard, move, maximizingPlayer):
  newBoard = copyBoard(myBoard)

  # this part does not really handle 3+ snakes
  mySnake = None
  notMySnake = None
  for snake in newBoard["snakes"]:
    if snake["id"] == newBoard["myId"]:
      mySnake = snake
    else:
      notMySnake = snake

  snake = None
  if maximizingPlayer:
    snake = mySnake
  elif notMySnake is not None:
    snake = notMySnake

  if snake is not None:
    next = get_next(snake["body"][0], move)
    if not avoid_walls(next, newBoard["width"], newBoard["height"]):
      newBoard["end"] = True
      if snake["id"] == newBoard["myId"]:
        newBoard["winner"] = -GAME_END - 10  #minimizing player wins
      else:
        newBoard["winner"] = GAME_END + 10  #maximizing player wins
    elif not avoid_snakes(next, newBoard["snakes"], snake):
      newBoard["end"] = True
      if snake["id"] == newBoard["myId"]:
        newBoard["winner"] = -GAME_END - 9  #minimizing player wins
      else:
        newBoard["winner"] = GAME_END + 9  #maximizing player wins
    else:
      # move snake
      snake["body"].insert(0, next)
      # eat food if any
      ateFood = False
      for food in newBoard["food"]:
        if food["x"] == next["x"] and food["y"] == next["y"]:
          ateFood = True
          newBoard["food"].remove(food)
          break
      if snake["health"] < 100:
        snake["body"].pop()
      snake["health"] = snake["health"] - 1
      if ateFood:
        snake["health"] = 100

      if snake["health"] < 1:
        if snake["id"] == newBoard["myId"]:
          newBoard["winner"] = -GAME_END - 8  #minimizing player wins
        else:
          newBoard["winner"] = GAME_END + 8  #maximizing player wins

      # eat enemy snake (or be eaten) if possible
      # opponent cannot be trusted to make a wise decision, so prefer to avoid enemy
      for otherSnake in newBoard["snakes"]:
        if otherSnake["id"] != snake["id"]:
          if abs(otherSnake["body"][0]["x"] - snake["body"][0]["x"]) + abs(
              otherSnake["body"][0]["y"] - snake["body"][0]["y"]) <= 1:
            newBoard["end"] = True
            if snake["id"] == newBoard["myId"]:
              newBoard["winner"] = -GAME_END - 4  #minimizing player wins
            elif otherSnake["id"] == newBoard["myId"]:
              newBoard["winner"] = -GAME_END - 4  #minimizing player wins

  return newBoard

def copyBoard(myBoard):
  newBoard = {}
  newBoard["myId"] = myBoard["myId"]
  newBoard["end"] = myBoard["end"]
  newBoard["winner"] = myBoard["winner"]
  newBoard["width"] = myBoard["width"]
  newBoard["height"] = myBoard["height"]
  newBoard["food"] = myBoard["food"].copy()
  newBoard["snakes"] = []
  for s in myBoard["snakes"]:
    newSnake = {}
    newSnake["id"] = s["id"]
    newSnake["health"] = s["health"]
    newSnake["body"] = s["body"].copy()
    newBoard["snakes"].append(newSnake)
  return newBoard

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