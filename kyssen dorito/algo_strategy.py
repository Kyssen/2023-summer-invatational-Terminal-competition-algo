import gamelib
import random
import math
import warnings
from sys import maxsize
import json


"""
Most of the algo code you write will be in this file unless you create new
modules yourself. Start by modifying the 'on_turn' function.

Advanced strategy tips: 

  - You can analyze action frames by modifying on_action_frame function

  - The GameState.map object can be manually manipulated to create hypothetical 
  board states. Though, we recommended making a copy of the map to preserve 
  the actual current map state.
"""

class AlgoStrategy(gamelib.AlgoCore):
    def __init__(self):
        super().__init__()
        seed = random.randrange(maxsize)
        random.seed(seed)
        gamelib.debug_write('Random seed: {}'.format(seed))

    def on_game_start(self, config):
        """ 
        Read in config and perform any initial setup here 
        """
        gamelib.debug_write('Configuring your custom algo strategy...')
        self.config = config
        global WALL, SUPPORT, TURRET, SCOUT, DEMOLISHER, INTERCEPTOR, MP, SP
        WALL = config["unitInformation"][0]["shorthand"]
        SUPPORT = config["unitInformation"][1]["shorthand"]
        TURRET = config["unitInformation"][2]["shorthand"]
        SCOUT = config["unitInformation"][3]["shorthand"]
        DEMOLISHER = config["unitInformation"][4]["shorthand"]
        INTERCEPTOR = config["unitInformation"][5]["shorthand"]
        MP = 1
        SP = 0

        # This is a good place to do initial setup
        self.scored_on_locations = []

    def on_turn(self, turn_state):
        """
        This function is called every turn with the game state wrapper as
        an argument. The wrapper stores the state of the arena and has methods
        for querying its state, allocating your current resources as planned
        unit deployments, and transmitting your intended deployments to the
        game engine.
        """
        game_state = gamelib.GameState(self.config, turn_state)
        gamelib.debug_write('Performing turn {} of your custom algo strategy'.format(game_state.turn_number))
        game_state.suppress_warnings(True)  #Comment or remove this line to enable warnings.

        self.starter_strategy(game_state)

        game_state.submit_turn()


    """
    NOTE: All the methods after this point are part of the sample starter-algo
    strategy and can safely be replaced for your custom algo.
    """

    def starter_strategy(self, game_state):
        """
        For defense we will use a spread out layout and some interceptors early on.
        We will place turrets near locations the opponent managed to score on.
        For offense we will use long range demolishers if they place stationary units near the enemy's front.
        If there are no stationary units to attack in the front, we will send Scouts to try and score quickly.
        """
        left = 1
        sp_me = game_state.get_resource(SP)
        sp_op = game_state.get_resource(SP, 1)
        mp_me = game_state.get_resource(MP)
        mp_op = game_state.get_resource(MP, 1)

        them_up = False
        gtg = False
        required = 2

        left_funnel = [[2,13], [3,12], [4,11], [5,10], [6,9], [7,8], [8,7], [9,6], [10,5], [11,4], [12,3], [13,2], [20,8], [19,7], [18,6], [17,5], [16,4], [15,3], [14,2]]
        right_funnel = [[25,13], [24,12], [23,11], [22,10], [21,9], [20,8], [19,7], [18,6], [17,5], [16,4], [15,3], [14,2],[6,9], [7,8], [8,7], [9,6], [10,5], [11,4], [12,3], [13,2]]
        left_plug = [5,8]
        right_plug = [21,8]
       
        if game_state.game_map[2,14] != [] and game_state.game_map[25,14] != []:
            if game_state.game_map[0,14] == [] or not game_state.game_map[0,14][0].upgraded:
                left = 0
            else:
                left = 2

        if game_state.game_map[2,14] != []:
            left = 0
        elif game_state.game_map[25,14] != []:
            left = 2 
        
         # If the turn is less than 5, stall with interceptors and wait to see enemy's base
        if game_state.turn_number < 1:
            game_state.attempt_spawn(INTERCEPTOR, [[7,6],[20,6]])
            
        else:
        
            cost_left = 0
            cost_right = 0
            for point in left_funnel:
                for point in left_funnel:
                    x,y = point
                if game_state.game_map[x,y] == []:
                    cost_left += 1
            for point in right_funnel:
                x,y = point
                if game_state.game_map[x,y] == []:
                    cost_right += 1
            if left == 0:
                if sp_me >= cost_left + 1:
                    gtg = True
            if left == 2:
                if sp_me >= cost_right + 1:
                    gtg = True
            
            if left == 0:
                if game_state.game_map[0,14] != []:
                    if game_state.game_map[0,14][0].upgraded:
                        them_up = True
            if left == 2:
                if game_state.game_map[27,14] != []:
                    if game_state.game_map[27,14][0].upgraded:
                        them_up = True
            if them_up:
                required = 4
            if left == 2:
                if game_state.get_attackers([26,13], 0) != []:
                    if them_up:
                        required = 6
                    else:
                        required = 4
            else:
                if game_state.get_attackers([1,13], 0) != []:
                    if them_up:
                        required = 6
                    else:
                        required = 4
            if required == 2:
                if mp_me < required + 7:
                    gtg = False
            elif required == 4:
                if mp_me < required + 10:
                    gtg = False
            elif required == 6:
                 if mp_me < required + 14:
                    gtg = False
            
            if left == 0 and gtg:
                for wall in left_funnel:
                    game_state.attempt_spawn(WALL, wall)
                game_state.attempt_spawn(WALL, right_plug)
                game_state.attempt_remove(right_plug)
                game_state.attempt_spawn(SCOUT, [14,0], required)
                game_state.attempt_spawn(SCOUT, [16,2], 1000)
            elif left == 2 and gtg:
                for wall in right_funnel:
                    game_state.attempt_spawn(WALL, wall)
                game_state.attempt_spawn(WALL, left_plug)
                game_state.attempt_remove(left_plug)
                game_state.attempt_spawn(SCOUT, [13,0], required)
                game_state.attempt_spawn(SCOUT, [11,2], 1000)

            elif left == 1:
                if mp_me > 20:
                    if sp_me >= cost_left + 1 or sp_me >= cost_right + 1:
                        if cost_left < cost_right:
                            for wall in left_funnel:
                                game_state.attempt_spawn(WALL, wall)
                            game_state.attempt_spawn(WALL, right_plug)
                            game_state.attempt_remove(right_plug)
                            game_state.attempt_spawn(DEMOLISHER, [5,8], 2)
                            game_state.attempt_spawn(SCOUT, [14,0], required)
                            game_state.attempt_spawn(SCOUT, [16,2], 1000)
                        else:
                            for wall in right_funnel:
                                game_state.attempt_spawn(WALL, wall)
                            game_state.attempt_spawn(WALL, left_plug)
                            game_state.attempt_remove(left_plug)
                            game_state.attempt_spawn(DEMOLISHER, [21,8], 2)
                            game_state.attempt_spawn(SCOUT, [13,0], required)
                            game_state.attempt_spawn(SCOUT, [11,2], 1000)
            temp = left_funnel
            temp.extend(right_funnel)
            for wall in temp:
                game_state.attempt_spawn(WALL, wall)

            front_line_tur = [[4,12],[23,12], [5,11], [22,11],[6,10],[21,10]]
            suports = [[9,7],[18,7],[10,6],[17,6],[16,6],[11,6],[16,5],[11,5],[12,5],[15,5]]
            for tur in front_line_tur:
                game_state.attempt_spawn(TURRET, tur)
                game_state.attempt_upgrade(tur)
            for sup in suports:
                game_state.attempt_spawn(SUPPORT, sup)
                game_state.attempt_upgrade(sup)
            

                        
            
            
            




if __name__ == "__main__":
    algo = AlgoStrategy()
    algo.start()
