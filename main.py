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
import queue
import numpy as np
import cProfile, pstats, io
from pstats import SortKey

RandomSeed = None
PossibleMoves = ["up", "down", "left", "right"]
BestMove = "up"
MoveLookup = {"left": -1, "right": 1, "up": 1, "down": -1}

G_END_SPAN = 100
G_END_SCORE = 100000000
SCORE_MAX = G_END_SCORE + G_END_SPAN
SCORE_MIN = -G_END_SCORE - G_END_SPAN
SCORE_GAME_END = G_END_SCORE
SCORE_NEG_GAME_END = -G_END_SCORE


# info is called when you create your Battlesnake on play.battlesnake.com
# and controls your Battlesnake's appearance
# TIP: If you open your Battlesnake URL in a browser you should see this data
def info() -> typing.Dict:
  print("INFO")
  return {
    "apiversion": "1",
    "author": "jdb1662",
    "color": "#03fcf4",
    "head": "pixel",
    "tail": "pixel",
  }


# start is called when your Battlesnake begins a game
def start(gameState: typing.Dict):
  if RandomSeed is not None:
    random.seed(RandomSeed)
  print("GAME START")


# end is called when your Battlesnake finishes a game
def end(gameState: typing.Dict):
  print("GAME OVER\n")


# move is called on every turn and returns your next move
def move(gameState: typing.Dict) -> typing.Dict:
  nextMove = make_minimax_move(gameState)
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
  futureHead = {}
  if nextMove == "left" or nextMove == "right":
    futureHead["x"] = currentHead["x"] + MoveLookup[nextMove]
    futureHead["y"] = currentHead["y"]
  elif nextMove == "up" or nextMove == "down":
    futureHead["x"] = currentHead["x"]
    futureHead["y"] = currentHead["y"] + MoveLookup[nextMove]
  return futureHead

def make_minimax_move(gameState: typing.Dict, timeLimit=0.35):
  # this code will iterate as long as there is time
  results = queue.LifoQueue()
  event = threading.Event()
  thread = threading.Thread(target=make_minimax_iterating, args=(gameState, event, results))
  thread.start()
  time.sleep(timeLimit)
  event.set()  #terminate the thread

  if results.qsize() > 0:
    return results.get_nowait()
  else:
    goodMoves = []
    for move in PossibleMoves:
      next = get_next(gameState["you"]["body"][0], move)
      if avoid_walls(next, gameState["board"]["width"], gameState["board"]["height"]):
        if avoid_snakes(next, gameState["board"]["snakes"], gameState["you"]):
          goodMoves.append(move)
    if len(goodMoves) > 0:
      return random.choice(goodMoves)
    else:
      return random.choice(PossibleMoves)


def make_minimax_iterating(gameState, event, queue):
  pr = cProfile.Profile()
  pr.enable()

  depth = 2
  while not event.is_set():
    myBoard = copy.deepcopy(gameState["board"])
    myBoard["myId"] = gameState["you"]["id"]
    myBoard["end"] = False
    myBoard["winner"] = 0  #no winner by default
    value, move = minimax(event, myBoard, depth, True)

    if not event.is_set():      
      if value <= SCORE_NEG_GAME_END: #detect a hopeless situation and exit early 
        event.set()
      else:
        print("iteration depth",depth,"best move",move)
        queue.put(move)
        depth += 2

  pr.disable()
  s = io.StringIO()
  sortby = SortKey.CUMULATIVE
  ps = pstats.Stats(pr, stream=s).sort_stats(sortby)
  ps.print_stats()
  print(s.getvalue())
  return

def minimax(event, myBoard, depth, maximizingPlayer):
  if event.is_set():
    return (0, "---")
  bestMoves = PossibleMoves
  bestValue = 0

  if depth == 0 or myBoard["end"]:
    if myBoard["end"]:
      #print("game end", depth, myBoard["winner"])
      return (myBoard["winner"], "---")      

    estimate = 0
    maxRoomScore = 10
    for snake in myBoard["snakes"]:
      if snake["id"] == myBoard["myId"]:
        estimate -= calcFoodScore(myBoard, snake)
        estimate += calcHazardScore(myBoard, snake)
        estimate += calcLengthScore(snake)
        rs1 = calcRunwayScore(myBoard, snake, maxRoomScore)
        rs2 = calcRunwayScore2(myBoard, snake, maxRoomScore)
        if rs1 != rs2:
          print("mismatched runway scores", rs1, rs2)
        estimate += rs1
      else:
        estimate += calcFoodScore(myBoard, snake)
        estimate -= calcHazardScore(myBoard, snake)
        estimate -= calcLengthScore(snake)
        rs1 = calcRunwayScore(myBoard, snake, maxRoomScore)
        rs2 = calcRunwayScore2(myBoard, snake, maxRoomScore)
        if rs1 != rs2:
          print("mismatched runway scores", rs1, rs2)
        estimate -= rs1

    return (estimate, "---")
  if maximizingPlayer:
    bestValue = SCORE_MIN
    bestMoves = []
    for move in PossibleMoves:
      if event.is_set():
        return (0, "---")
      #print("my",depth,move)
      newBoard = minimax_new_board(myBoard, move, maximizingPlayer)
      value, m = minimax(event, newBoard, depth - 1, False)
      if value == bestValue:
        bestMoves = bestMoves + [move]
      elif value > bestValue:
        bestValue = value
        bestMoves = [move]
    #print("my",depth,bestValue,bestMoves)
    return (bestValue, random.choice(bestMoves))
  else:  # minimizing player
    bestMoves = []
    qs, ps = [], []
    x, S = 0, 0
    for move in PossibleMoves:
      if event.is_set():
        return (0, "---")
      #print("other",depth,move)
      newBoard = minimax_new_board(myBoard, move, maximizingPlayer)
      value, m = minimax(event, newBoard, depth - 1, True)
      
      # if moves leads to an instant win, just take it
      if (value <= SCORE_NEG_GAME_END):
        return (value, [move])
        
      # if moves leads to instant loss, don't consider it
      elif (value >= SCORE_GAME_END):
        continue
        
      bestMoves = bestMoves + [move]
      qs.append(value)
      x += (1.01**-value)

    # if no moves are added, all lead to instant loss, so give up
    if (len(qs) == 0):
      return (SCORE_GAME_END, random.choice(PossibleMoves))
      
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

  movingSnakes = []
  for snake in newBoard["snakes"]:
    if maximizingPlayer and snake["id"] == newBoard["myId"]:
      movingSnakes.append(snake)
    elif not maximizingPlayer and snake["id"] != newBoard["myId"]:
      movingSnakes.append(snake)
  
  hitWalls = []
  hitSnakes = []
  starvedSnakes = []
  eatenSnakes = []
  
  for snake in movingSnakes:
    next = get_next(snake["body"][0], move)
    if not avoid_walls(next, newBoard["width"], newBoard["height"]):
      hitWalls.append(snake["id"])
    elif not avoid_snakes(next, newBoard["snakes"], snake):
      # modify for head collisions
      hitSnakes.append(snake["id"])
    else:
      # modify for head collisions
      snake["body"].insert(0, next)
      ateFood = False
      for food in newBoard["food"]:
        if food["x"] == next["x"] and food["y"] == next["y"]:
          ateFood = True
          newBoard["food"].remove(food)
          break
      if snake["health"] < 100:
        snake["body"].pop()
      snake["health"] = snake["health"] - 1
      if "hazards" in newBoard.keys():
        for hazard in newBoard["hazards"]:
          if hazard["x"] == next["x"] and hazard["y"] == next["y"]:
            snake["health"] = snake["health"] - 15
      if ateFood:
        snake["health"] = 100
      if snake["health"] < 1:
        starvedSnakes.append(snake["id"])

      # eat enemy snake (or be eaten) if possible
      # opponent cannot be trusted to make a wise decision, so prefer to avoid enemy
      for otherSnake in newBoard["snakes"]:
        if otherSnake["id"] != snake["id"]:
          if abs(otherSnake["body"][0]["x"] - snake["body"][0]["x"]) + abs(
              otherSnake["body"][0]["y"] - snake["body"][0]["y"]) <= 1:
            if snake["id"] == newBoard["myId"]:
              eatenSnakes.append(snake["id"])
            elif otherSnake["id"] == newBoard["myId"]:
              eatenSnakes.append(otherSnake["id"])

  # maximizing player loses if in any loss state
  if newBoard["end"] == False and newBoard["myId"] in hitWalls:
    newBoard["end"] = True
    newBoard["winner"] = SCORE_NEG_GAME_END - 10  #minimizing player wins
  if newBoard["end"] == False and newBoard["myId"] in hitSnakes:
    newBoard["end"] = True
    newBoard["winner"] = SCORE_NEG_GAME_END - 9  #minimizing player wins
  if newBoard["end"] == False and newBoard["myId"] in starvedSnakes:
    newBoard["end"] = True
    newBoard["winner"] = SCORE_NEG_GAME_END - 8  #minimizing player wins
  if newBoard["end"] == False and newBoard["myId"] in eatenSnakes:
    newBoard["end"] = True
    newBoard["winner"] = SCORE_NEG_GAME_END - 7  #minimizing player wins

  # modify to prefer killing an opponent snake if I can
  
  # maximizing player only wins if all opponents die
  someOpponentsLive = False
  someOpponentsDie = False
  for snake in newBoard["snakes"]:
    if snake["id"] != newBoard["myId"]:
      if snake["id"] in hitWalls or snake["id"] in hitSnakes or snake["id"] in starvedSnakes:
        someOpponentsDie = True
      else:
        someOpponentsLive = True

  if someOpponentsDie and not someOpponentsLive:
    newBoard["end"] = True
    newBoard["winner"] = SCORE_GAME_END  #maximizing player wins  

  return newBoard


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
        return -3
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
    discovered = [snake["body"][0]]
    distances = [0]
    index = 0
    while index < len(discovered) and distances[-1] < limit:
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

    return max(distances) * (int(25/limit) + 1)
    
def calcRunwayScore2(myBoard, snake, limit):
  if snake is None:
    return 0
  else:
    #create snake body array to avoid
    snakeLen = 0
    for s in myBoard["snakes"]:
      snakeLen += len(s["body"])
    
    snakeBodies = np.zeros((snakeLen),dtype=int)
    snakeCount = 0
    for s in myBoard["snakes"]:
      for part in s["body"]:
        snakeBodies[snakeCount] = part["y"]*100+part["x"]
        snakeCount += 1
  
    #create discovery nodes
    discovered = np.zeros((121),dtype=int)
    distances = np.zeros((121),dtype=int)
    discovered[0] = snake["body"][0]["y"]*100+snake["body"][0]["x"]
    count = 1

    index = 0
    while index < count and distances[count-1] < limit:
      node = discovered[index]

      node -= 100
      if node >= 0 and not np.any(discovered == node) and not np.any(snakeBodies == node):
        discovered[count] = node
        distances[count] = distances[index] + 1
        count += 1
      node += 100

      node += 100
      if node//100 < myBoard["height"] and not np.any(discovered == node) and not np.any(snakeBodies == node):
        discovered[count] = node
        distances[count] = distances[index] + 1
        count += 1
      node -= 100

      node -= 1
      if node%100 >= 0 and node%100 < 99 and not np.any(discovered == node) and not np.any(snakeBodies == node):
        discovered[count] = node
        distances[count] = distances[index] + 1
        count += 1
      node += 1

      node += 1
      if node%100 < myBoard["width"] and not np.any(discovered == node) and not np.any(snakeBodies == node):
        discovered[count] = node
        distances[count] = distances[index] + 1
        count += 1
      node -= 1

      index += 1
        
    return distances[count-1] * (int(25/limit) + 1)    

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
