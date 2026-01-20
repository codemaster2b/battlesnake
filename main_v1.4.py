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
  nextMove = make_minimax_move(gameState, endTime)
  print(f"MOVE {gameState['turn']}: {nextMove}")
  return {"move": nextMove}

possible_moves = ["up", "down", "left", "right"]
def get_next(origin, move):
    next_loc = origin.copy()
    if move == "left":
        next_loc["x"] -= 1
    elif move == "right":
        next_loc["x"] += 1
    elif move == "down":
        next_loc["y"] -= 1
    elif move == "up":
        next_loc["y"] += 1
    return next_loc


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
      return False #dead if hit snake body, but this needs to care about future body differently
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

def make_minimax_move(gameState: typing.Dict, endTime):
  # this code will iterate as long as there is time
  gameState["board"]["myId"] = gameState["you"]["id"]
  gameState["board"]["map"] = gameState["game"]["map"]
  results = queue.LifoQueue()
  make_minimax_iterating(gameState, results, endTime)
  
  if results.qsize() > 0:
    return results.get_nowait()
  else:
    goodMoves = []
    for move in possible_moves:
      next = get_next(gameState["you"]["body"][0], move)
      if avoid_walls(next, gameState["board"]["width"], gameState["board"]["height"]):
        if avoid_snakes(next, gameState["board"], gameState["you"]):
          goodMoves.append(move)
    if len(goodMoves) > 0:
      return random.choice(goodMoves)
    else:
      return random.choice(possible_moves)

def make_minimax_iterating(gameState, queue, endTime):
  depth = 2
  times = []
  times.append(datetime.datetime.now())
  while datetime.datetime.now() < endTime and depth < 100:
    myBoard = copy.deepcopy(gameState["board"])
    myBoard["myId"] = gameState["you"]["id"]
    myBoard["map"] = gameState["game"]["map"]
    myBoard["end"] = False
    myBoard["winner"] = 0  #no winner by default
    value, move = minimax(endTime, myBoard, depth, True, -2000000, 2000000)
    times.append(datetime.datetime.now())
    
    if datetime.datetime.now() < endTime:
      if value <= -1000000: #detect a hopeless situation and exit early 
        return
      elif move in possible_moves:
        print("iteration depth",depth,"best move",move)
        queue.put(move)
    
    depth += 2
    if times[-1] - times[-2] >= endTime - datetime.datetime.now():
      return

  return

def minimax(endTime, myBoard, depth, maximizingPlayer, alpha, beta):
  if datetime.datetime.now() >= endTime:
    return (0, "---")
  bestMoves = possible_moves
  bestValue = 0

  if depth == 0 or myBoard["end"]:
    if myBoard["end"]:
      return (myBoard["winner"], "---")      

    estimate = 0
    maxRoomScore = 10
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
  if maximizingPlayer:
    bestValue = -2000000
    bestMoves = []
    for move in possible_moves:
      if datetime.datetime.now() >= endTime:
        return (0, "---")
      newBoard = minimax_new_board(myBoard, move, maximizingPlayer)
      value, m = minimax(endTime, newBoard, depth - 1, not maximizingPlayer, alpha, beta)
      if value == bestValue:
        bestMoves = bestMoves + [move]
      elif value > bestValue:
        bestValue = value
        bestMoves = [move]
      alpha = max(alpha, bestValue)
      if beta < alpha:
        break
    return (bestValue, random.choice(bestMoves))
  else:  # minimizing player
    bestValue = 2000000
    bestMoves = []
    qs, ps = [], []
    x, S = 0, 0
    for move in possible_moves:
      if datetime.datetime.now() >= endTime:
        return (0, "---")
      newBoard = minimax_new_board(myBoard, move, maximizingPlayer)
      value, m = minimax(endTime, newBoard, depth - 1, not maximizingPlayer, alpha, beta)
      if value == bestValue:
        bestMoves = bestMoves + [move]
      elif value < bestValue:
        bestValue = value
        bestMoves = [move]
      beta = min(beta, bestValue)
      if beta < alpha:
        break

    return (bestValue, random.choice(bestMoves))

# Make a board move
def minimax_new_board(myBoard, move, maximizingPlayer):
  newBoard = copyBoard(myBoard)

  alreadyMovedSnakes = []
  notAlreadyMovedSnakes = []
  movingSnakes = []
  for snake in newBoard["snakes"]:
    if maximizingPlayer:
      if snake["id"] == newBoard["myId"]:
        movingSnakes.append(snake)
        notAlreadyMovedSnakes.append(snake.copy())
      else:
        notAlreadyMovedSnakes.append(snake.copy())
    else:
      if snake["id"] == newBoard["myId"]:
        alreadyMovedSnakes.append(snake)
      else:
        movingSnakes.append(snake)
        notAlreadyMovedSnakes.append(snake.copy())
  
  hitWalls = []
  hitSnakes = []
  starvedSnakes = []
  eatenSnakes = []
  
  for snake in movingSnakes:
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
        for otherSnake in alreadyMovedSnakes:
          if snake["body"][0] == otherSnake["body"][0] and len(snake["body"]) >= len(otherSnake["body"]):
            eatenSnakes.append(otherSnake["id"])

  # maximizing player loses if in any loss state
  if newBoard["end"] == False and newBoard["myId"] in hitWalls:
    newBoard["end"] = True
    newBoard["winner"] = -1000000 #minimizing player wins
  if newBoard["end"] == False and newBoard["myId"] in hitSnakes:
    newBoard["end"] = True
    newBoard["winner"] = -1000000 #minimizing player wins
  if newBoard["end"] == False and newBoard["myId"] in starvedSnakes:
    newBoard["end"] = True
    newBoard["winner"] = -1000000 #minimizing player wins
  if newBoard["end"] == False and newBoard["myId"] in eatenSnakes:
    newBoard["end"] = True
    newBoard["winner"] = -1000000 #minimizing player wins

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
    newBoard["winner"] = 1000000  #maximizing player wins  

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

def minimax2(game_state, results, end_time, depth, isMaxPlayer):
    bestValue = 0
    bestMoves = []
    
    if datetime.now() >= end_time:
        return 0, "---"
    
    if depth == 0:
        #score has to be built differently, since move is already done
        #score all snakes
        my_snake = game_state["you"]
        bestValue = 0
        for snake in game_state["board"]["snakes"]:
            w = wall_score(game_state, snake, snake["body"][0]) #works
            a = avoid_score(game_state, snake, snake["body"][0]) #maybe works
            h = health_score(game_state, snake, snake["body"][0]) #works
            p = path_score(game_state, snake, snake["body"][0]) #maybe works
            f = food_score(game_state, snake, snake["body"][0]) #works
            snakeValue = w + a + h + p + f
            if snake["id"] == my_snake["id"]:
                bestValue += snakeValue
            else:
                bestValue -= snakeValue
    elif isMaxPlayer:
        bestValue = DIE_SCORE
        for move in possible_moves:
            if datetime.now() >= end_time:
                return 0, "---"
            #make changes
            new_game_state, err = game_state_after_move(game_state, move, isMaxPlayer)
            if not err:
                #call minimax recursively
                value, m = minimax(new_game_state, results, end_time, depth - 1, not isMaxPlayer)
                print(f"move={move} isMax={isMaxPlayer} value={value}")
                if value > bestValue:
                    bestValue = value
                    bestMoves = [move]
                elif value == bestValue:
                    bestMoves.append(move)
    else: #one or more opponents
        bestValue = KILL_SCORE
        for move in possible_moves:
            if datetime.now() >= end_time:
                return 0, "---"
            #make changes
            new_game_state, err = game_state_after_move(game_state, move, isMaxPlayer)
            if not err:
                #call minimax recursively
                value, m = minimax(new_game_state, results, end_time, depth - 1, not isMaxPlayer)
                print(f"move={move} isMax={isMaxPlayer} value={value}")
                if value < bestValue:
                    bestValue = value
                    bestMoves = [move]
                elif value == bestValue:
                    bestMoves.append(move)

    if len(bestMoves) > 0:
        return bestValue, random.choice(bestMoves)
    else:
        return bestValue, "---"

def game_state_after_move(game_state, move, isMaxPlayer):
    error = False
    new_game_state = copy.deepcopy(game_state)
    my_snake = new_game_state["you"]
    
    #move snake; which snake? why not all snakes?
    snakesToMove = []
    for snake in new_game_state["board"]["snakes"]:
        if isMaxPlayer and snake["id"] == my_snake["id"]:
            snakesToMove.append(snake)
        elif not isMaxPlayer and snake["id"] != my_snake["id"]:
            snakesToMove.append(snake)
            
    for snake in snakesToMove:
        next_loc = get_next(move, snake["body"][0])
        #do i care if the snake dies immediately? yes, to avoid overlooking death
        if wall_score(new_game_state, snake, next_loc) == DIE_SCORE:
            error = True
        elif avoid_score(new_game_state, snake, next_loc) == DIE_SCORE:
            error = True
        else:
            snake["body"].insert(0, next_loc)
            snake["body"].pop()
            #what about eating food?
            snake["health"] = snake["health"] - 1
    return new_game_state, error

def wall_score(game_state, current_snake, move):
    width = game_state["board"]["width"]
    height = game_state["board"]["height"]
    if move["x"] < 0 or move["y"] < 0 or move["x"] >= width or move["y"] >= height:
        return DIE_SCORE
    return 0

def avoid_score(game_state, current_snake, move):
    #avoid all snakes
    for snake in game_state["board"]["snakes"]:
        if move in snake["body"][1:]: #avoid body
            return DIE_SCORE
        #can eat a shorter snake, so do not avoid
        elif move == snake["body"][0] and snake["id"] != current_snake["id"] and len(snake["body"]) >= len(current_snake["body"]):
            return DIE_SCORE
        #adjacent can lead to death, but maybe not
        elif abs(move["x"]-snake["body"][0]["x"]) + abs(move["y"]-snake["body"][0]["y"]) == 1 and snake["id"] != current_snake["id"] and len(snake["body"]) >= len(current_snake["body"]):
            return DIE_SCORE / 2
    return 0

def health_score(game_state, current_snake, move):
    if move in game_state["board"]["food"]:
        return 100    
    elif current_snake["health"] < 1:
        return DIE_SCORE
    else:
        return current_snake["health"]
        
def path_score(game_state, current_snake, move):
    width = game_state["board"]["width"]
    height = game_state["board"]["height"]
    
    #find more runway for the snake to avoid early death
    #node search for distance
    found = []
    visited = []
    distance = [0 for i in range(121)]
    
    #snakes are already visited
    for snake in game_state["board"]["snakes"]:
        for part in snake["body"]:
            if move != current_snake["body"][0]: #works with both immediate and depth=0 cases
                part_index = part["y"] * 11 + part["x"]
                found.append(part_index)
                visited.append(part_index)
                distance[part_index] = 0    
    
    #begin at the move node
    move_index = move["y"] * 11 + move["x"]
    
    #invalid start for the search
    if move["x"] < 0 or move["y"] < 0 or move["x"] >= width or move["y"] >= height or move_index in visited: 
        return 0
    else:
        found.append(move["y"] * 11 + move["x"])
        
        while len(found) > len(visited):
            node = found[len(visited)]
            #print(f"visited={node}")
            visited.append(node)
            
            neighbors = []
            if node // 11 < height - 1:
                neighbors.append(node + 11)
            if node // 11 >0:
                neighbors.append(node - 11)
            if node % 11 < width - 1:
                neighbors.append(node + 1)
            if node % 11 > 0:
                neighbors.append(node - 1)
            
            for neighbor in neighbors:
                if not neighbor in found:
                    found.append(neighbor)
                    distance[neighbor] = distance[node] + 1
        
        #how important is the path score?
        #health changes by 1 each time
        path_to_health_ratio = 5
        return len(visited) * path_to_health_ratio

def food_score(game_state, current_snake, move):
    width = game_state["board"]["width"]
    height = game_state["board"]["height"]
    distance = width + height
    for food in game_state["board"]["food"]:
        dx = abs(food["x"] - move["x"])
        dy = abs(food["y"] - move["y"])
        distance = min(distance, dx + dy)
    return distance * -1

def copyBoard(myBoard):
  newBoard = myBoard.copy()
  newBoard["food"] = myBoard["food"].copy()
  newBoard["hazards"] = myBoard["hazards"].copy()
  newBoard["snakes"] = []
  for s in myBoard["snakes"]:
    newSnake = s.copy()
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
