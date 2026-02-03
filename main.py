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
from datetime import datetime, timedelta

possible_moves = ["up", "down", "left", "right"]

def print_and_log(text):
    print(text)
    #with open("output.log", "a") as f:
    #    f.write(f"{text}\n")

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

# info is called when you create your Battlesnake on play.battlesnake.com
# and controls your Battlesnake's appearance
# TIP: If you open your Battlesnake URL in a browser you should see this data
def info() -> typing.Dict:
    print_and_log("INFO")
    return {
        "apiversion": "1",
        "author": "codemaster2b",
        "color": "#03fcf4",
        "head": "pixel",
        "tail": "pixel",
    }

# start is called when your Battlesnake begins a game
def start(gameState: typing.Dict):
    print_and_log("GAME START")

# end is called when your Battlesnake finishes a game
def end(gameState: typing.Dict):
    print_and_log("GAME OVER\n")

# move is called on every turn and returns your next move
def move(gameState: typing.Dict) -> typing.Dict:
    gameState["board"]["myId"] = gameState["you"]["id"]
    gameState["board"]["map"] = gameState["game"]["map"]
    results = queue.LifoQueue()
    end_time = datetime.now() + timedelta(seconds=0.35)
    move_iterating(gameState, results, end_time)
  
    next_move = random.choice(possible_moves)
    if results.qsize() > 0:
        next_move = results.get_nowait()
    print_and_log(f"MOVE {gameState['turn']}: {next_move}")
    return {"move": next_move}

def move_iterating(gameState, queue, end_time):
    max_depth = 1
    times = []
    times.append(datetime.now())
    while datetime.now() < end_time and max_depth < 51:
        value, move = minimax(end_time, gameState["board"], 0, max_depth, True, -2000000, 2000000)
        times.append(datetime.now())    
        if datetime.now() < end_time:
            if value <= -1000000: #detect a hopeless situation and exit early 
                return
            elif move in possible_moves:
                print_and_log(f"iteration depth{max_depth} best move{move}")
                queue.put(move)

        max_depth += 1
        if times[-1] - times[-2] >= end_time - datetime.now():
            return
    return

def minimax(end_time, myBoard, depth, max_depth, maximizingPlayer, alpha, beta):
    if datetime.now() >= end_time:
        return (0, "---")
    bestMoves = []
    bestValue = 0

    if depth == max_depth:
        estimate = end_score(myBoard, depth)
        return (estimate, "---")
    if maximizingPlayer:
        bestValue = -2000000
        for move in possible_moves:
            if datetime.now() >= end_time:
                return (0, "---")
            newBoard = copy_board(myBoard)
            immediate_score = move_and_score(newBoard, move, maximizingPlayer, depth, max_depth)
            print_and_log(f"move={move} depth={depth} isMax={maximizingPlayer} immediate_score={immediate_score}")
            if immediate_score > -500000:
                value, m = minimax(end_time, newBoard, depth, max_depth, not maximizingPlayer, alpha, beta)
                value = round(value * 0.99 + immediate_score,2)
                value = min(max(value, -1000000),1000000)
                print_and_log(f"move={move} isMax={maximizingPlayer} value={value}")
                if value == bestValue:
                    bestMoves = bestMoves + [move]
                elif value > bestValue:
                    bestValue = value
                    bestMoves = [move]
                alpha = max(alpha, bestValue)
                if beta < alpha:
                    break
    else:  # minimizing player
        bestValue = 2000000
        for move in possible_moves:
            if datetime.now() >= end_time:
                return (0, "---")
            newBoard = copy_board(myBoard)
            immediate_score = move_and_score(newBoard, move, maximizingPlayer, depth, max_depth)
            print_and_log(f"move={move} depth={depth} isMax={maximizingPlayer} immediate_score={immediate_score}")
            if immediate_score < 500000:
                value, m = minimax(end_time, newBoard, depth + 1, max_depth, not maximizingPlayer, alpha, beta)
                value = round(value * 0.99 + immediate_score,2)
                value = min(max(value, -1000000),1000000)
                print_and_log(f"move={move} isMax={maximizingPlayer} value={value}")
                if value == bestValue:
                    bestMoves = bestMoves + [move]
                elif value < bestValue:
                    bestValue = value
                    bestMoves = [move]
                beta = min(beta, bestValue)
                if beta < alpha:
                    break

    if len(bestMoves) > 0:
        return bestValue, random.choice(bestMoves)
    else:
        return bestValue, "---"

def copy_board(myBoard):
  newBoard = myBoard.copy()
  newBoard["food"] = myBoard["food"].copy()
  newBoard["hazards"] = myBoard["hazards"].copy()
  newBoard["snakes"] = []
  for s in myBoard["snakes"]:
    newSnake = s.copy()
    newSnake["body"] = s["body"].copy()
    newBoard["snakes"].append(newSnake)
  return newBoard
  
def end_score(myBoard, depth):
    estimate = 0
    for snake in myBoard["snakes"]:
        f = food_score(myBoard, snake)
        h = hazard_score(myBoard, snake)
        l = length_score(snake)
        p = path_score(myBoard, snake, snake["body"][0])
        snake_score = f + h + l + p
        if snake["id"] == myBoard["myId"]:
            estimate += snake_score
        else:
            estimate -= snake_score
    return estimate

def move_and_score(newBoard, move, maximizingPlayer, depth, max_depth):
    estimate = 0

    my_snake = {}
    moving_snakes = []
    for snake in newBoard["snakes"]:
        if snake["id"] == newBoard["myId"]:
            my_snake = snake
            if maximizingPlayer:
				estimate = -1000000
                moving_snakes.append(snake)
        elif not maximizingPlayer and snake["id"] != newBoard["myId"]:
            moving_snakes.append(snake)
			estimate = 1000000
        
    for snake in moving_snakes:
        next = get_next(snake["body"][0], move)
        snake_score = avoid_snakes(next, newBoard, snake, depth)
        
        if not avoid_walls(next, newBoard["width"], newBoard["height"]):
            snake_score = -1000000 #wall
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
                        snake["health"] = snake["health"] - 14
            if ateFood:
                snake["health"] = 100
            if snake["health"] < 1:
                snake_score = -1000000 #health

        if snake["id"] == newBoard["myId"]:
            estimate = snake_score
        else:
            estimate = min(estimate, snake_score)
    return estimate

def avoid_walls(futureHead, boardWidth, boardHeight):
    x = int(futureHead["x"])
    y = int(futureHead["y"])
    if x < 0 or y < 0 or x >= boardWidth or y >= boardHeight:
        return False
    else:
        return True

def avoid_snakes(futureHead, newBoard, currentSnake, depth):
    currentSnakeLen = len(currentSnake["body"])
    for snake in newBoard["snakes"]:
        snakeLen = len(snake["body"])
        if depth < snakeLen - 2 and futureHead in snake["body"][depth+1:-1]:
            return -1000000 #dead if hit snake body
        elif futureHead in snake["body"][1:-1]:
            return -100 #avoid hitting possible snake body
        
        if snake["id"] != currentSnake["id"]:
            dx0 = abs(snake["body"][0]["x"]-futureHead["x"])
            dy0 = abs(snake["body"][0]["y"]-futureHead["y"])
            dx1 = abs(snake["body"][1]["x"]-currentSnake["body"][0]["x"])
            dy1 = abs(snake["body"][1]["y"]-currentSnake["body"][0]["y"])

            dx2 = abs(snake["body"][1]["x"]-futureHead["x"])
            dy2 = abs(snake["body"][1]["y"]-futureHead["y"])
            dx3 = abs(snake["body"][2]["x"]-currentSnake["body"][0]["x"])
            dy3 = abs(snake["body"][2]["y"]-currentSnake["body"][0]["y"])
            
            if (snake["health"] == 100 or newBoard["map"] == "constrictor" or snake["id"] == newBoard["myId"]) and futureHead == snake["body"][-1]:
                return -1000000
            elif snake["id"] == newBoard["myId"] and snakeLen >= currentSnakeLen:
                #avoid connecting with another snake head that is >= my length and has moved already    
                if dx0 + dy0 == 0:
                    return -100
                #avoid a stalker snake that is >= my length and has moved already    
                elif dx2 + dy2 == 2 and dx3 + dy3 == 2:
                    return -100
            elif snakeLen >= currentSnakeLen:
                #avoid being within 1 of another snake head that is >= my length and has not moved yet
                if dx0 + dy0 == 1:
                    return -100
                #avoid a stalker snake that is >= my length and has not moved yet    
                elif dx0 + dy0 == 2 and dx1 + dy1 == 2:
                    return -100
    return 0

def food_score(myBoard, snake):
    score = myBoard["width"] + myBoard["height"]
    head = snake["body"][0]
    for food in myBoard["food"]:
        score = min(score, abs(food["x"] - head["x"]) + abs(food["y"] - head["y"]))
    return -1 * score

def hazard_score(myBoard, snake):
    return int(-500 / (min(snake["health"],1)))

def length_score(snake):
    return (len(snake["body"]) + int(snake["health"] / 100)) * 25 + snake["health"]

def path_score(myBoard, current_snake, move):
    width = myBoard["width"]
    height = myBoard["height"]
    max_cost = current_snake["health"] - 1
    
    #make a cost map including hazards
    costs = [1 for i in range(121)]
    if "hazards" in myBoard.keys():
        for hazard in myBoard["hazards"]:
            hazard_index = hazard["y"] * 11 + hazard["x"]
            costs[hazard_index] += 14
    
    #find more runway for the snake to avoid early death
    found = []
    visited = []
    found_h = []
    visited_h = []
    distances = [0 for i in range(121)]
    
    #snakes are already visited
    for snake in myBoard["snakes"]:
        for part in snake["body"]:
            if move != current_snake["body"][0]: #works with both immediate and depth=0 cases
                part_index = part["y"] * 11 + part["x"]
                found.append(part_index)
                visited.append(part_index)
                distances[part_index] = 0
    
    pre_visited = len(visited)
    
    #begin at the move node
    move_index = move["y"] * 11 + move["x"]
    
    #invalid start for the search
    if move["x"] < 0 or move["y"] < 0 or move["x"] >= width or move["y"] >= height or move_index in visited: 
        return 0
    else:
        found.append(move_index)
        distances[move_index] = 1
        
        while len(found) > len(visited) or len(found_h) > len(visited_h):
            if len(found) > len(visited):
                node = found[len(visited)]
                visited.append(node)
            else:
                node = found_h[len(visited_h)]
                visited_h.append(node)
                
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
                cost = distances[node] + costs[neighbor]
                if cost <= max_cost:
                    add = False
                    if neighbor in found:
                        if cost < distances[neighbor]:
                            add = True
                            found.remove(neighbor)
                            if neighbor in visited:
                                visited.remove(neighbor)
                    elif neighbor in found_h:
                        if cost < distances[neighbor]:
                            add = True
                            found_h.remove(neighbor)
                            if neighbor in visited_h:
                                visited_h.remove(neighbor)
                    else:
                        add = True

                    if add:
                        distances[neighbor] = cost
                        if costs[neighbor] > 1:
                            found_h.append(neighbor)
                        else:
                            found.append(neighbor)
    
    visited_nodes = len(visited) - pre_visited
    sum_dist = 0
    for node in visited:
        sum_dist += distances[node]
    
    #return visited_nodes * 5 - (sum_dist / visited_nodes)
    return -1000/(visited_nodes - (0.2 * sum_dist / visited_nodes))

# Start server when `python main.py` is run
if __name__ == "__main__":
  from server import run_server

  port = "8000"
  for i in range(len(sys.argv) - 1):
    if sys.argv[i] == '--port':
      port = sys.argv[i + 1]
    elif sys.argv[i] == '--seed':
      random_seed = int(sys.argv[i + 1])
  run_server({"info": info, "start": start, "move": move, "end": end, "port": port})
