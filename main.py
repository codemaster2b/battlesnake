import typing
from math import inf
from timeit import default_timer
from sys import argv
from copy import deepcopy

move_start = default_timer()


# info is called when you create your Battlesnake on play.battlesnake.com
# and controls your Battlesnake's appearance
# TIP: If you open your Battlesnake URL in a browser you should see this data

def info() -> typing.Dict:
    print("INFO")

    return {
        "apiversion": "1",
        "author": "CAJ",  # TODO: Your Battlesnake Username
        "color": "#336699",  # TODO: Choose color
        "head": "shades",  # TODO: Choose head
        "tail": "mlh-gene",  # TODO: Choose tail
    }


# start is called when your Battlesnake begins a game
def start(game_state: typing.Dict):
    print("GAME START")


# end is called when your Battlesnake finishes a game
def end(game_state: typing.Dict):
    print("GAME OVER\n")


# move is called on every turn and returns your next move
# Valid moves are "up", "down", "left", or "right"
# See https://docs.battlesnake.com/api/example-move for available data
def move(game_state: typing.Dict) -> typing.Dict:
    # inputing "down" does not affect minmax unless depth is zero. Ignore it
    global move_start
    move_start = default_timer()
    # print("Original Body: ", game_state['you']['body'])
    score, move = minimax(game_state, 4, "down", True, -inf, inf)
    if move == "None":
        #print("Panic Mode")
        move = panic_move(game_state)

    move_end = default_timer()
    move_time = (move_end - move_start)
    #print("Turn: ", game_state["turn"])
    #print("Total Calc Time: ", move_time)
    #print("Score of move: ", score)
    #print("Move: ", move, "\n")
    return {"move": move}


# maxer is a boolean representing if current player is the maximixing player
# Tweak based on the specifics of how evaluation is implemented
# Might need to add in Neighbors (as generated in the move function) as a parameter here.
# It might be ok though, since this function should only be called within the move function anyway,
# and the scope might be ok with that in Python.
def minimax(state: typing.Dict, depth, move, maxer, alpha, beta):
    # If the depth is 0 or this state is an end state (win or loss)
    move_time = measure_time(depth)

    # simulates and tests for death

    death = is_terminal(state, move)
    # tests if bottom reached, someone died, or running out of time
    if (depth == 0) or (death == True) or move_time > 0.38:

        try:
            return evaluate(state, move), move
        except:
            return inf, move

    # try to give same depths equal time
    if depth == 1 and move_time > 0.41:
        print("Equal time stop, depth: ", depth)
        try:
            return evaluate(state, move), move
        except:
            return inf, move

    # try to give same depths equal time
    if depth == 2 and move_time > 0.45:
        print("Equal time stop, depth: ", depth)
        try:
            return evaluate(state, move), move
        except:
            return inf, move

    # Max player
    elif maxer == True:
        maxer = False
        value = -inf
        best_move = "None"
        Neighbors = ["up", "down", "left", "right"]

        # Find best move
        for option in Neighbors:
            # update snakes
            new_state = simulate(deepcopy(state), option)
            test_val, test_move = minimax(deepcopy(new_state), (depth - 1), option, maxer, alpha, beta)

            #To see if eating is done on depth
            if new_state["you"]["health"] == 100:
                test_val += 107
                if len(new_state["board"]["food"]) == 0:
                    #print("Last food boost")
                    #print("Option: ", option, "value: ", test_val)
                    test_val += 80

                # sees if enemy snake head is right by this depth
                test_val += is_near(new_state)


            alpha = max(test_val, alpha)
            if test_val > value:
                # print(str(test_val) + " > " + str(value))
                value = test_val
                best_move = option
            # print("\n")
            if test_val > beta:
                #print("beta prune: ", test_val, " > ", beta)
                break

        #print("This is move chosen by max call: " + str(best_move))
        #print("value: ", value, "prev  enemy move: ", move, " depth: ", depth, "\n")

        return value, best_move



    # Min player
    elif maxer == False:
        maxer = True
        value = inf
        best_move = "None"
        Neighbors = ["up", "down", "left", "right"]

        for option in Neighbors:
            new_state = simulate_opponent(state, option)
            test_val, test_move = minimax(deepcopy(new_state), (depth - 1), option, maxer, alpha, beta)

            if test_val < value:
                # print(str(test_val) + " < " + str(value))
                value = test_val
                best_move = option

            if test_val < alpha:
                #print("alpha prune: ", test_val, " < ", alpha)
                break
            beta = min(test_val, beta)
        #print("This is move chosen by min call: " + str(best_move))
        #print("value", value, "prev my move: ", move, " depth: ", depth)

        return value, best_move

def is_near(state):
    try:
        my_body = state["you"]["body"]
        my_head = my_body[0]
        is_near = 0
        x = my_head["x"]
        y = my_head["y"]
        my_length = state["you"]["length"]
        snakeid = state["you"]["id"]
        allsnakes = state['board']['snakes']
        # designed for 1v1's only
        for snake in allsnakes:
            if snake["id"] != snakeid:
                opponent = snake
                opponent_body = opponent["body"]
                opponent_head = opponent_body[0]
                enemy_x, enemy_y = opponent_head["x"], opponent_head["y"]
                enemy_length = opponent["length"]

        if [x + 1, y] == [enemy_x, enemy_y]:
            is_near = 1
        elif [x - 1, y] == [enemy_x, enemy_y]:
            is_near = 1
        elif [x, y + 1] == [enemy_x, enemy_y]:
            is_near = 1
        elif [x, y - 1] == [enemy_x, enemy_y]:
            is_near = 1

        if my_length > enemy_length + 1:
            value = is_near * 220
        elif my_length < enemy_length + 1:
            value = is_near * -800
        else:
            value = 0
    except:
        return 0

    return value

def panic_move(old_state):
    all_moves = ["up", "down", "left", "right"]
    board_width = old_state["board"]["width"]
    board_height = old_state["board"]["height"]

    for option in all_moves:
        evaluationValue = 0
        state = simulate(deepcopy(old_state), option)
        new_move = "right"
        new_eval = -9999
        my_body = state["you"]["body"]
        my_health = state["you"]["health"]
        my_head = my_body[0]
        snakeid = state["you"]["id"]
        allsnakes = state['board']['snakes']
        obstacles = []
        my_length = state["you"]["length"]
        # designed for 1v1's only
        for snake in allsnakes:
            if snake["id"] != snakeid:
                opponent = snake
                opponent_body = opponent["body"]
                opponent_head = opponent_body[0]
                enemy_x = opponent_head["x"]
                enemy_y = opponent_head["y"]
                enemy_length = opponent["length"]

        count = 0
        for i in my_body:
            x = i["x"]
            y = i["y"]
            if (count != 0):  # tested in seperate case
                obstacles.append([x, y])
            count += 1

        try:
            count = 0
            for k in opponent_body:
                enemy_x = k["x"]
                enemy_y = k["y"]
                if (count != 0):
                    obstacles.append([enemy_x, enemy_y])
            count += 1

            if (x >= board_width) or (x < 0):
                # print("eval snake out of x bounds")
                evaluationValue = -9999  # we lose

            elif (y >= board_height) or (y < 0):
                # print("eval snake out of y bounds")
                evaluationValue = -9999  # we lose

            elif (enemy_x >= board_width) or (enemy_x < 0):
                # print("eval enemy snake out of x bounds")
                evaluationValue = 9999  # we win

            elif (enemy_y >= board_height) or (enemy_y < 0):
                # print("eval enemy snake out of y bounds")
                evaluationValue = 9999  # we win

            elif ([enemy_x, enemy_y] in obstacles):
                # print("eval enemy snake in obstacles")
                # print("enemy head:", opponent_head)
                # print("enemy calc head: ", [enemy_x, enemy_y])
                evaluationValue = 9999

            elif ([x, y] in obstacles):
                # print("eval snake in obstacles")
                evaluationValue = -9999

            elif ([x, y] == [enemy_x, enemy_y]):

                if my_length > enemy_length:
                    print("eval head on win")
                    evaluationValue = 9999
                elif my_length < enemy_length:
                    print("eval head on lose")
                    # not -inf so that snake does not give up
                    # enemy could mess up
                    evaluationValue = -600
                elif my_length == enemy_length:
                    print("eval head on tie")
                    evaluationValue = 0

            elif (my_health == 0):
                evaluationValue = -999

            else:
                x = my_head["x"]
                y = my_head["y"]
                enemy_x = opponent_head["x"]
                enemy_y = opponent_head["y"]
                dist = abs(x - enemy_x) + abs(y - enemy_y)
                evaluationValue += dist
        except:
            return "right"

        if evaluationValue > new_eval:
            new_move = option
            new_eval = evaluationValue

    return new_move

def measure_time(depth):
    move_end = default_timer()
    global move_start
    move_time = move_end - move_start
    if move_time > 0.4:
        print("Time stop, depth of: ", depth)
    return move_time


def is_terminal(state: typing.Dict, move_choice):
    # terminal_start = default_timer()
    dead = False

    my_body = state["you"]["body"]
    my_head = my_body[0]
    my_health = state["you"]["health"]
    snakeid = state["you"]["id"]
    allsnakes = state['board']['snakes']
    board_width = state["board"]["width"]
    board_height = state["board"]["height"]
    obstacles = []

    for snake in allsnakes:
        if snake["id"] != snakeid:
            opponent = snake
            opponent_body = opponent["body"]
            opponent_head = opponent_body[0]

    count = 0
    for i in my_body:
        x = i["x"]
        y = i["y"]
        if (count != 0):  # tested in seperate case
            obstacles.append([x, y])
        count += 1

    try:
        count = 0
        for k in opponent_body:
            enemy_x = k["x"]
            enemy_y = k["y"]
            if (count != 0):
                obstacles.append([enemy_x, enemy_y])
            count += 1

        enemy_x, enemy_y = opponent_head["x"], opponent_head["y"]
        x, y = my_head["x"], my_head["y"]

        # test for death of either snake
        if (x >= board_width) or (x <= -1):
            # print(my_head["x"])
            dead = True
            # print("snake out of x bounds")
        elif (y >= board_height) or (y <= -1):
            dead = True
            # print("snake out of y bounds")
        elif (enemy_x >= board_width) or (enemy_x <= -1):
            dead = True
            # print("enemy snake out of x bounds")
        elif (enemy_y >= board_height) or (enemy_y <= -1):
            dead = True
            # print("ememy snake out of y bounds")
        elif ([x, y] in obstacles):
            dead = True
            # print("head in obstacles")
        elif ([enemy_x, enemy_y] in obstacles):
            dead = True
            # print("enemy head in obstacles")
        elif [x, y] == [enemy_x, enemy_y]:
            dead = True
            # print("head on collision")
        elif (my_health == 0):
            dead = True
    except:
        pass

    # terminal_end = default_timer()
    # time = (terminal_end - terminal_start) * 1000
    # print("is terminal run time: ", time)
    return dead



# evaluates current state
def evaluate(state, move_choice):  # move choice is a string
    # eval_start = default_timer()

    evaluationValue = 0  # this determines how likely we are to win positive is good
    my_body = state["you"]["body"]
    my_head = my_body[0].copy()
    x, y = my_head["x"], my_head["y"]  # this one
    obstacles = []
    snakeid = state["you"]["id"]

    allsnakes = state['board']['snakes']

    # designed for 1v1's only
    for snake in allsnakes:
        if snake["id"] != snakeid:
            opponent = snake
            opponent_body = opponent["body"]
            opponent_head = opponent_body[0]
            enemy_x, enemy_y = opponent_head["x"], opponent_head["y"]
            enemy_length = opponent["length"]

    count = 0
    for i in my_body:
        x = i["x"]
        y = i["y"]
        if (count != 0):  # tested in seperate case
            obstacles.append([x, y])
        count += 1

    try:
        count = 0
        for k in opponent_body:
            enemy_x = k["x"]
            enemy_y = k["y"]
            if (count != 0):
                obstacles.append([enemy_x, enemy_y])
            count += 1

    except:
        pass

    board_height = state["board"]["height"]
    board_width = state["board"]["width"]
    my_health = state["you"]["health"]

    my_length = state["you"]["length"]
    ate_food = 0  # Boolean to see if we ate food

    flood_obstacles = deepcopy(obstacles)
    flood_head = deepcopy(my_head)
    # Calculate availible space for both snakes
    #c_space is choice space
    #c_space = close_fill(board_width, board_height, flood_head, flood_obstacles)
    #enemy_c_space = close_fill(board_width, board_height, flood_head, flood_obstacles)

    freespace = flood_fill(board_width, board_height, flood_head, flood_obstacles)

    enemy_flood_obstacles = deepcopy(obstacles)

    enemy_flood_head = deepcopy(opponent_head)

    enemy_freespace = flood_fill(board_width, board_height, enemy_flood_head, enemy_flood_obstacles)
    #print("free space: ", freespace)

    enemy_x = opponent_head["x"]
    enemy_y = opponent_head["y"]

    x = my_head["x"]
    y = my_head["y"]

    # print("My head: ", my_head)
    # print("My body: ", my_body)
    # print("Obstacles: ", obstacles)
    # Giant series of tests
    if my_health == 100:
        ate_food = 1

    if freespace < (my_length * enemy_length) + 2:
        # we are trapped
        evaluationValue -= 750

    if enemy_freespace < (my_length * enemy_length) + 2:
        # enemy is trapped
        evaluationValue += 750
    if freespace <= 5:
        evaluationValue += -705

    if enemy_freespace <= 5:
        evaluationValue += 705

    if (freespace <= 10) and (freespace == enemy_freespace) and my_length > enemy_length + 1:
        evaluationValue += 507

    if my_health < 10:
        # need to eat
        evaluationValue += (ate_food * 201)
        food_dist = food_find(state, obstacles, my_head)
        evaluationValue += (25 - food_dist) * 5

    if my_length > enemy_length:
        x_dist = abs(x - enemy_x)
        y_dist = abs(y - enemy_y)
        evaluationValue += (25 - (x_dist + y_dist)) * 8

    else:
        x_dist = abs(x - enemy_x)
        y_dist = abs(y - enemy_y)
        if x_dist >= 2 or y_dist >= 2:
            evaluationValue += 7
        evaluationValue += (x_dist + y_dist) * 2
        if (x == board_width - 1) or (y == board_height - 1):
            evaluationValue += -50
        elif (x == 1) or (y == 1):
            evaluationValue += -50

    if my_length <= 17 and ((my_length - enemy_length) <= 2):
        if ate_food:
            evaluationValue += 106
        food_dist = food_find(state, obstacles, my_head)

        evaluationValue += (25 - food_dist) * 4

    if (x == board_width - 1) or (y == board_height - 1):
        x_dist = abs(x - enemy_x)
        y_dist = abs(y - enemy_y)
        evaluationValue += (x_dist + y_dist) * 2

    elif (x == 1) or (y == 1):
        x_dist = abs(x - enemy_x)
        y_dist = abs(y - enemy_y)
        evaluationValue += (x_dist + y_dist) * 2

    x_dist = x - 5
    y_dist = y - 5
    center_dist = (15 - abs(x_dist + y_dist)) * 2
    evaluationValue += center_dist

    #Worth more at longer lengths
    if (my_length >= 18) and (enemy_length >= 18):
        evaluationValue += ((freespace - enemy_freespace) * 6)

    # death testing
    if (x >= board_width) or (x < 0):
        # print("eval snake out of x bounds")
        evaluationValue = -(inf)  # we lose

    elif (y >= board_height) or (y < 0):
        # print("eval snake out of y bounds")
        evaluationValue = -(inf)  # we lose

    elif (enemy_x >= board_width) or (enemy_x < 0):
        # print("eval enemy snake out of x bounds")
        evaluationValue = inf  # we win

    elif (enemy_y >= board_height) or (enemy_y < 0):
        # print("eval enemy snake out of y bounds")
        evaluationValue = inf  # we win

    elif ([enemy_x, enemy_y] in obstacles):
        # print("eval enemy snake in obstacles")
        # print("enemy head:", opponent_head)
        # print("enemy calc head: ", [enemy_x, enemy_y])
        evaluationValue = inf

    elif ([x, y] in obstacles):
        # print("eval snake in obstacles")
        evaluationValue = -(inf)

    elif ([x, y] == [enemy_x, enemy_y]):

        if my_length > enemy_length:
            #print("eval head on win")
            evaluationValue = inf
        elif my_length < enemy_length:
            #print("eval head on lose")
            #not -inf so that snake does not give up
            #enemy could mess up
            evaluationValue = -999999
        elif my_length == enemy_length:
            #print("eval head on tie")
            evaluationValue = 0
    elif (my_health == 0):
        evaluationValue = -inf

    else:
        evaluationValue += (((freespace - enemy_freespace) * 12) + (ate_food * 50))


    #print("Evaluation value: " + str(evaluationValue))
    #print("Evaluation move: ", move_choice)
    # print("Enemy body: ", opponent_body)
    # eval_end = default_timer()
    # time = (eval_end - eval_start) * 1000
    # print("eval run time: ", time)
    return evaluationValue

def food_find(state, obstacles, my_head):
    food = state['board']['food']
    food_dist = 25
    head_x = my_head["x"]
    head_y = my_head["y"]

    for i in food:
        food_x = i["x"]
        food_y = i["y"]
        dist = (abs(head_x - food_x) + abs(head_y - food_y))
        if [food_x, food_y] not in obstacles:
            if dist < food_dist:
                food_dist = dist

    return food_dist


def flood_fill(board_width, board_height, my_head, obstacles):

    flood_obstacles = obstacles
    move_area = 0
    move_queue = []
    x = my_head["x"]
    y = my_head["y"]

    move_queue.append([x, y])  # starting point

    while move_queue:  # while it's not empty
        n = move_queue[-1]
        move_queue.pop()
        x = n[0]
        y = n[1]
        if board_width > x >= 0:
            if board_height > y >= 0:
                if [x, y] not in flood_obstacles:
                    flood_obstacles.append([x, y])  # makes sure not counting it twice

                    move_area += 1  # counting total number of free spaces

                    move_queue.append([x + 1, y])  # adding possible free spaces
                    move_queue.append([x, y + 1])
                    move_queue.append([x - 1, y])
                    move_queue.append([x, y - 1])

    return move_area



# Code for simulating a snake's move
# by Charles Raines

# Function to take a snake head and move it to a new coordinate
def move_snake_head(current_head: typing.Dict, move):
    new_head = deepcopy(current_head)

    if move == "up":
        new_head["y"] += 1
    elif move == "down":
        new_head["y"] -= 1
    elif move == "left":
        new_head["x"] -= 1
    elif move == "right":
        new_head["x"] += 1

    return new_head


# Function to take a snake's new head and body and adjust the values
def move_snake(new_head: typing.Dict, snake_body: typing.Dict, ate_food):
    new_body = deepcopy(snake_body)

    n = len(new_body) - 1
    while n > 0:
        new_body[n] = new_body[n - 1]
        n -= 1

    new_body[0] = new_head

    if ate_food:
        tail = snake_body[-1]
        new_body.append(tail)

    return new_body


# This function will take in a state and a move and return a new state
# for my snake
def simulate(state: typing.Dict, move):
    # sim_start = timeit.default_timer()
    # Variable Assignments
    new_state = deepcopy(state)
    my_body = state["you"]["body"]
    head = deepcopy(my_body[0])
    food_index = 0

    # Static Adjusted Values
    new_state["turn"] += 1
    new_state["you"]["health"] -= 1

    new_head = move_snake_head(deepcopy(head), move)

    # Boolean Objects
    ate_food = 0

    for i in range(len(new_state["board"]["food"])):
        if new_state["board"]["food"][i] == new_head:
            food_index = i
            ate_food = 1

    if ate_food:
        new_state["board"]["food"].pop(food_index)
        new_state["you"]["length"] += 1
        new_state["you"]["health"] = 100

    new_state["you"]["body"] = move_snake(deepcopy(new_head), deepcopy(my_body), ate_food)

    # sim_end = timeit.default_timer()
    # sim_time = (sim_end - sim_start) * 1000
    # print("simulation time: ", sim_time)
    return new_state


# This function is exactly identical to the simulate function, but this
# will be used to evaluate from the opponent's point of view
def simulate_opponent(state: typing.Dict, move):
    # en_sim_start = timeit.default_timer()
    # Variable Assignments
    new_state = deepcopy(state)

    snakeid = state["you"]["id"]

    # figure out the opponent's body (should be index 0, but sanity check)
    for i in range(len(new_state["board"]["snakes"])):
        if new_state["board"]["snakes"][i]["id"] != snakeid:
            snake_index = i

    # Continued Variable Assignments
    try:
        head = deepcopy(state["board"]["snakes"][snake_index]["body"][0])
    except:
        pass
    food_index = 0

    # Static Adjusted Values
    new_state["turn"] += 1
    try:
        new_state["board"]["snakes"][snake_index]["health"] -= 1
        new_head = move_snake_head(head, move)
    except:
        pass

    # Boolean Objects
    ate_food = 0
    try:
        for i in range(len(new_state["board"]["food"])):
            if new_state["board"]["food"][i] == new_head:
                food_index = i
                ate_food = 1

        if ate_food:
            new_state["board"]["food"].pop(food_index)
            new_state["board"]["snakes"][snake_index]["length"] += 1
            new_state["board"]["snakes"][snake_index]["health"] = 100

        new_state["board"]["snakes"][snake_index]["body"] = move_snake(deepcopy(new_head), deepcopy(
            state["board"]["snakes"][snake_index]["body"]), ate_food)


    except:
        pass

    # en_sim_end = timeit.default_timer()
    # en_sim_time = (en_sim_end - en_sim_start) * 1000
    # print("enemy simulation time: ", en_sim_time)
    return new_state

# Start server when `python main.py` is run
if __name__ == "__main__":
    from server import run_server

    port = "8000"
    for i in range(len(argv) - 1):
        if argv[i] == '--port':
            port = argv[i + 1]
        elif argv[i] == '--seed':
            random_seed = int(argv[i + 1])
    run_server({"info": info, "start": start, "move": move, "end": end, "port": port})
