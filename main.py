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
snake_color = "#03fcf4"
log_file_name = "output.log"
logs = []

def print_and_log(text):
    logs.append(text)
    return

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
    print_and_log("INFO\n")
    return {
        "apiversion": "1",
        "author": "codemaster2b",
        "color": snake_color,
        "head": "pixel",
        "tail": "pixel",
    }

# start is called when your Battlesnake begins a game
def start(gameState: typing.Dict):
    print_and_log("GAME START\n")

# end is called when your Battlesnake finishes a game
def end(gameState: typing.Dict):
    print_and_log("GAME OVER\n")
    #with open(log_file_name, "a") as f:
    #    for text in logs:
    #        f.write(f"{text}")
    for block in [logs[i:i + 100] for i in range(0, len(logs), 100)]:
        print(" ".join(block))
        time.sleep(0.1) #max 500 logs/sec
    logs.clear()

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
    print_and_log(f"MOVE {gameState['turn']}: {next_move}\n")
    return {"move": next_move}

def move_iterating(gameState, queue, end_time):
    max_depth = 1
    times = []
    times.append(datetime.now())
    while datetime.now() < end_time and max_depth < 3:
        value, move = minimax(end_time, gameState["board"], 0, max_depth, True, -1000000, 1000000)
        times.append(datetime.now())    
        if datetime.now() < end_time:
            if value <= -1000000: #detect a hopeless situation and exit early 
                return
            elif move in possible_moves:
                print_and_log(f"d={max_depth} best={move}\n")
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
        bestValue = -1000000
        for move in possible_moves:
            newBoard = copy_board(myBoard)
            print_and_log(f"<< d={depth} max={maximizingPlayer} {move}: ")
            immediate_score = move_and_score(newBoard, move, maximizingPlayer, depth, max_depth)
            if immediate_score > -500000:
                value, m = minimax(end_time, newBoard, depth, max_depth, not maximizingPlayer, alpha, beta)
                if datetime.now() >= end_time:
                    return (0, "---")
                value = round(value * 0.99 + immediate_score,2)
                value = min(max(value, -1000000),1000000)
                if value == bestValue:
                    bestMoves = bestMoves + [move]
                elif value > bestValue:
                    bestValue = value
                    bestMoves = [move]
                alpha = max(alpha, bestValue)
                print_and_log(f"final d={depth} max={maximizingPlayer} {move}: value={value} alpha={alpha} >>\n")
                if beta < alpha:
                    break
            else:
                print_and_log(f"final d={depth} max={maximizingPlayer} {move}: immediate={immediate_score} >>\n")
    else:  # minimizing player
        bestValue = 1000000
        for move in possible_moves:
            newBoard = copy_board(myBoard)
            print_and_log(f"<< d={depth} max={maximizingPlayer} {move}: ")
            immediate_score = move_and_score(newBoard, move, maximizingPlayer, depth, max_depth)
            if immediate_score < 500000:
                value, m = minimax(end_time, newBoard, depth + 1, max_depth, not maximizingPlayer, alpha, beta)
                if datetime.now() >= end_time:
                    return (0, "---")
                value = round(value * 0.99 + immediate_score,2)
                value = min(max(value, -1000000),1000000)
                if value == bestValue:
                    bestMoves = bestMoves + [move]
                elif value < bestValue:
                    bestValue = value
                    bestMoves = [move]
                beta = min(beta, bestValue)
                print_and_log(f"final d={depth} max={maximizingPlayer} {move}: value={value} beta={beta} >>\n")
                if beta < alpha:
                    break
            else:
                print_and_log(f"final d={depth} max={maximizingPlayer} {move}: immediate={immediate_score} >>\n")
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
        maximizingPlayer = snake["id"] == myBoard["myId"]
        print_and_log(f"[max={maximizingPlayer} f={f} h={h} l={l} p={p}] ")
        if snake["id"] == myBoard["myId"]:
            estimate += snake_score
        else:
            estimate -= snake_score
    return estimate

def move_and_score(newBoard, move, maximizingPlayer, depth, max_depth):
    estimate = 1000000
    if maximizingPlayer:
        estimate = -1000000

    for snake in newBoard["snakes"]:
        if (snake["id"] == newBoard["myId"] and maximizingPlayer) or (snake["id"] != newBoard["myId"] and not maximizingPlayer):
            next = get_next(snake["body"][0], move)
            snake_score = avoid_snakes(next, newBoard, snake, depth)
            if not avoid_walls(next, newBoard["width"], newBoard["height"]):
                snake_score = -1000000
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
                estimate = min(estimate, -1*snake_score)
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
    value = 0
    for snake in newBoard["snakes"]:
        snakeLen = len(snake["body"])
        #if snake is currentSnake, then I chose this path
        if depth < snakeLen - 2 and futureHead in snake["body"][depth+1:-1]:
            value = min(value, -1000000) #dead if hit snake body
        elif futureHead in currentSnake["body"][1:-1]:
            value = min(value, -1000000) #dead if hit my snake body
        elif futureHead in snake["body"][1:-1]:
            #i should not return with just -100 if it could be worse!
            value = min(value, -100) #avoid hitting possible snake body
        
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
                value = min(value, -1000000)
            elif snake["id"] == newBoard["myId"] and snakeLen >= currentSnakeLen:
                #avoid connecting with another snake head that is >= my length and has moved already    
                if dx0 + dy0 == 0:
                    value = min(value, -100)
                #avoid a stalker snake that is >= my length and has moved already    
                elif dx2 + dy2 == 2 and dx3 + dy3 == 2:
                    value = min(value, -100)
            elif snakeLen >= currentSnakeLen:
                #avoid being within 1 of another snake head that is >= my length and has not moved yet
                if dx0 + dy0 == 1:
                    value = min(value, -100)
                #avoid a stalker snake that is >= my length and has not moved yet    
                elif dx0 + dy0 == 2 and dx1 + dy1 == 2:
                    value = min(value, -100)
    return value

def food_score(myBoard, snake):
    score = myBoard["width"] + myBoard["height"]
    head = snake["body"][0]
    for food in myBoard["food"]:
        score = min(score, abs(food["x"] - head["x"]) + abs(food["y"] - head["y"]))
    return -1 * score

def hazard_score(myBoard, snake):
    return round(-500 / (max(snake["health"],1)), 3)

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
    visits = [0 for i in range(121)]
    distances = [0 for i in range(121)]
    
    #snakes are already visited
    for snake in myBoard["snakes"]:
        for part in snake["body"]:
            if part != current_snake["body"][0]: #works with both immediate and depth=0 cases
                part_index = part["y"] * 11 + part["x"]
                visits[part_index] = 3
                distances[part_index] = 100
    
    #begin at the move node
    move_index = move["y"] * 11 + move["x"]
    
    #invalid start for the search
    if move["x"] < 0 or move["y"] < 0 or move["x"] >= width or move["y"] >= height or visits[move_index] > 0: 
        return 0
    else:
        visits[move_index] = 1
        distances[move_index] = 1
        
        while 1 in visits:
            #find next lowest number
            sorted_idx = np.argsort(distances) #list of all indexes
            filter_idx = list(filter(lambda i: visits[i] == 1, sorted_idx))
            
            node = filter_idx[0]
            visits[node] = 2
                
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
                if cost <= max_cost and visits[neighbor] < 1:
                    distances[neighbor] = cost
                    visits[neighbor] = 1
    
    #score is the sum of each discovered node (100-dist)
    visited_nodes = 0
    for i in range(121):
        if visits[i] == 2:
            visited_nodes += 1 - 0.01 * distances[i]
    
    return round(-1000/visited_nodes, 3)

# Start server when `python main.py` is run
if __name__ == "__main__":
    from server import run_server

    port = "8000"
    for i in range(len(sys.argv) - 1):
        if sys.argv[i] == '--port':
            port = sys.argv[i + 1]
        elif sys.argv[i] == '--seed':
            random_seed = int(sys.argv[i + 1])
        elif sys.argv[i] == '--color':
            snake_color = sys.argv[i + 1]
        elif sys.argv[i] == '--log':
            log_file_name = sys.argv[i + 1]

    run_server({"info": info, "start": start, "move": move, "end": end, "port": port})
