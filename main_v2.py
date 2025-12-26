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
    "author": "codemaster2b",
    "color": "#03c0c0",
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
  gameState["board"]["myId"] = gameState["you"]["id"]
  gameState["board"]["map"] = gameState["game"]["map"]
  results = queue.LifoQueue()
  event = threading.Event()
  thread = threading.Thread(target=make_minimax_iterating, args=(gameState, event, results))
  thread.start()
  
  sleepDivisions = 5
  sleepCount = 0
  while sleepCount < sleepDivisions and results.qsize() < 100:
    time.sleep(timeLimit / sleepDivisions)
    sleepCount += 1
  event.set() #terminate the thread

  if results.qsize() > 0:
    return results.get_nowait()
  else:
    goodMoves = []
    for move in PossibleMoves:
      next = get_next(gameState["you"]["body"][0], move)
      if avoid_walls(next, gameState["board"]["width"], gameState["board"]["height"]):
        if avoid_snakes(next, gameState["board"], gameState["you"]):
          goodMoves.append(move)
    if len(goodMoves) > 0:
      return random.choice(goodMoves)
    else:
      return random.choice(PossibleMoves)

def make_minimax_iterating(gameState, event, queue):
  depth = 2
  while not event.is_set() and depth < 100:
    myBoard = copy.deepcopy(gameState["board"])
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
  return

def minimax(event, myBoard, depth, maximizingPlayer):
  if event.is_set():
    return (0, "---")
  bestMoves = PossibleMoves
  bestValue = 0

  if depth == 0 or myBoard["end"]:
    if myBoard["end"]:
      return (myBoard["winner"], "---")      

    estimate = 0
    maxRoomScore = 15
    for snake in myBoard["snakes"]:
      if snake["id"] == myBoard["myId"]:
        estimate -= calcFoodScore(myBoard, snake)
        estimate += calcHazardScore(myBoard, snake)
        estimate += calcLengthScore(snake)
        estimate += calcRunwayScore(myBoard, snake, maxRoomScore)
      else:
        estimate += calcFoodScore(myBoard, snake)
        estimate -= calcHazardScore(myBoard, snake)
        estimate -= calcLengthScore(snake)
        estimate -= calcRunwayScore(myBoard, snake, maxRoomScore)

    return (estimate, "---")

  moveValues = {}
  for move in PossibleMoves:
    if event.is_set():
      return (0, "---")

    newBoard = {}
    newBoard["myId"] = myBoard["myId"]
    newBoard["end"] = myBoard["end"]
    newBoard["map"] = myBoard["map"]
    newBoard["winner"] = myBoard["winner"]
    newBoard["width"] = myBoard["width"]
    newBoard["height"] = myBoard["height"]
    newBoard["food"] = myBoard["food"].copy()
    newBoard["hazards"] = myBoard["hazards"].copy()
    newBoard["snakes"] = []
    for s in myBoard["snakes"]:
      newSnake = {}
      newSnake["id"] = s["id"]
      newSnake["health"] = s["health"]
      newSnake["body"] = s["body"].copy()
      newBoard["snakes"].append(newSnake)

    hitWalls = []
    hitSnakes = []
    starvedSnakes = []
    eatenSnakes = []  
    for snake in newBoard["snakes"]:
      if (maximizingPlayer and snake["id"] == newBoard["myId"]) or (not maximizingPlayer and snake["id"] != newBoard["myId"]):
        next = get_next(snake["body"][0], move)
        if not avoid_walls(next, newBoard["width"], newBoard["height"]):
          hitWalls.append(snake["id"])
        elif not avoid_snakes(next, newBoard, snake):
          hitSnakes.append(snake["id"])
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
          if snake["health"] < 1:
            starvedSnakes.append(snake["id"])

          # eat maximizing snake if possible
          # minimizing snake has not moved so cannot be eaten for certain
          if not maximizingPlayer:
            for otherSnake in newBoard["snakes"]:
              if snake["id"] == newBoard["myId"]:
                if snake["body"][0] == otherSnake["body"][0] and len(snake["body"]) >= len(otherSnake["body"]):
                  eatenSnakes.append(otherSnake["id"])

    # maximizing player loses if in any loss state
    if newBoard["end"] == False and (newBoard["myId"] in hitWalls or newBoard["myId"] in hitSnakes or newBoard["myId"] in starvedSnakes or newBoard["myId"] in eatenSnakes):
      newBoard["end"] = True
      newBoard["winner"] = SCORE_NEG_GAME_END  #minimizing player wins

    # maximizing player only wins if all opponents die
    someOpponentsLive = False
    someOpponentsDie = False
    for snake in newBoard["snakes"]:
      if snake["id"] != newBoard["myId"]:
        if snake["id"] in hitWalls or snake["id"] in hitSnakes or snake["id"] in starvedSnakes or snake["id"] in eatenSnakes:
          someOpponentsDie = True
        else:
          someOpponentsLive = True

    if someOpponentsDie and not someOpponentsLive:
      newBoard["end"] = True
      newBoard["winner"] = SCORE_GAME_END  #maximizing player wins  

    value, m = minimax(event, newBoard, depth - 1, not maximizingPlayer)
    moveValues[move] = value
    
  bigMoves = {}
  smallMoves = {}
  moderateMoves = {}
  for move in moveValues:
    if moveValues[move] > 10000:
      bigMoves[move] = moveValues[move]
    elif moveValues[move] < -10000:
      smallMoves[move] = moveValues[move]
    else:
      moderateMoves[move] = moveValues[move]

  values = []
  bestMoves = []
  if maximizingPlayer:
    bestValue = SCORE_MIN
    for move in bigMoves:
      value = bigMoves[move]
      values.append(value)
      if value == bestValue:
        bestMoves.append(move)
      elif value > bestValue:
        bestValue = value
        bestMoves = [move]
    for move in moderateMoves:
      value = moderateMoves[move]
      values.append(value)
      if value == bestValue:
        bestMoves.append(move)
      elif value > bestValue:
        bestValue = value
        bestMoves = [move]
    if len(values) == 0:
      for move in smallMoves:
        value = smallMoves[move]
        values.append(value)
        if value == bestValue:
          bestMoves.append(move)
        elif value > bestValue:
          bestValue = value
          bestMoves = [move]    
  else: # minimizing player
    bestValue = SCORE_MAX
    for move in smallMoves:
      value = smallMoves[move]
      values.append(value)
      if value == bestValue:
        bestMoves.append(move)
      elif value < bestValue:
        bestValue = value
        bestMoves = [move]
    for move in moderateMoves:
      value = moderateMoves[move]
      values.append(value)
      if value == bestValue:
        bestMoves.append(move)
      elif value < bestValue:
        bestValue = value
        bestMoves = [move]
    if len(values) == 0:
      for move in bigMoves:
        value = bigMoves[move]
        values.append(value)
        if value == bestValue:
          bestMoves.append(move)
        elif value < bestValue:
          bestValue = value
          bestMoves = [move]    

  return (np.mean(values), random.choice(bestMoves))

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
    #create snake body array to avoid
    snakeLen = 0
    for s in myBoard["snakes"]:
      snakeLen += len(s["body"])
    
    snakeBodies = [0 for i in range(snakeLen)]
    snakeCount = 0
    for s in myBoard["snakes"]:
      for part in s["body"]:
        snakeBodies[snakeCount] = part["y"]*100+part["x"]
        snakeCount += 1
  
    #create discovery nodes
    discovered = [0 for i in range(121)]
    distances = [0 for i in range(121)]
    discovered[0] = snake["body"][0]["y"]*100+snake["body"][0]["x"]
    count = 1
    
    index = 0
    while index < count and distances[count-1] < limit:
      node = discovered[index]

      node -= 100
      if node >= 0 and not node in snakeBodies and not node in discovered[:count]:
        discovered[count] = node
        distances[count] = distances[index] + 1
        count += 1
      node += 100

      node += 100
      if node//100 < myBoard["height"] and not node in snakeBodies and not node in discovered[:count]:
        discovered[count] = node
        distances[count] = distances[index] + 1
        count += 1
      node -= 100

      node -= 1
      if node%100 >= 0 and node%100 < 99 and not node in snakeBodies and not node in discovered[:count]:
        discovered[count] = node
        distances[count] = distances[index] + 1
        count += 1
      node += 1

      node += 1
      if node%100 < myBoard["width"] and not node in snakeBodies and not node in discovered[:count]:
        discovered[count] = node
        distances[count] = distances[index] + 1
        count += 1
      node -= 1

      index += 1

    return distances[count-1] * (int(25/limit) + 1)

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
