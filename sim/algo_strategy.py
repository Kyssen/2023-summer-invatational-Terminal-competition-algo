import gamelib
import random
import math
import warnings
from sys import maxsize
import json
from gamelib.game_state import GameState
from gamelib.unit import GameUnit
from gamelib.game_map import GameMap
import copy



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
        friendly_edges = game_state.game_map.get_edge_locations(game_state.game_map.BOTTOM_LEFT) + game_state.game_map.get_edge_locations(game_state.game_map.BOTTOM_RIGHT)
        # First, place basic defenses
        self.bd(game_state)
        # Now build reactive defenses based on where the enemy scored
        self.build_reactive_defense(game_state)

        # If the turn is less than 5, stall with interceptors and wait to see enemy's base

        # Now let's analyze the enemy base to see where their defenses are concentrated.
        # If they have many units in the front we can build a line for our demolishers to attack them at long range.
            # They don't have many units in the front so lets figure out their least defended area and send Scouts there.

            # Only spawn Scouts every other turn
            # Sending more at once is better since attacks can only hit a single scout at a time
        if game_state.turn_number % 2 == 1:
            # To simplify we will just check sending them from back left and right
            scout_spawn_location_options = self.filter_blocked_locations(friendly_edges, game_state)
            best_location = self.least_damage_spawn_location(game_state, scout_spawn_location_options)
            game_state.attempt_spawn(SCOUT, best_location, 1000)

    def build_reactive_defense(self, game_state):
        if len(self.scored_on_locations) > 0:
            game_state.attempt_spawn(INTERCEPTOR, self.scored_on_locations[-1])

    def bd(self, game_state):
        mid_up = False
        tur_upgraded = False

        # get resources
        sp_me = game_state.get_resource(SP)
        sp_op = game_state.get_resource(SP, 1)
        mp_me = game_state.get_resource(MP)
        mp_op = game_state.get_resource(MP, 1)

        # how to use the first 40 SP
        starting_turrets = [[1,12],[6,12],[25,12],[21,11],[18,9]]
        starting_supports = [[5,8],[6,8]]
        starting_walls = [[0,13],[1,13],[2,13],[3,13],[4,13],[5,13],[6,13],[27,13],[26,13],[25,13], [18,10],[19,11],[20,12]]
        starting_INTERCEPTOR = [[6,7]]
        starting_scout = [[6,7],[6,7],[6,7],[6,7],[6,7]]
        
        # defence sections
        mid_wall = [[7,12],[7,11],[7,10],[8,9],[9,8],[10,8],[11,8],[12,8],[13,8],[14,8],[15,8],[16,8],[17,8]]
        right_corner_walls = [[24,12],[24,11],[23,10]]
        final_turrets = [[25,11],[20,10],[3,12],[23,9]]
        final_walls = [[18,10],[2,12],[4,12],[5,12],[22,12]]
        upgrade_walls = [[2,13],[3,13],[6,13],[24,13],[21,12],[20,11]]

        # determine cost of upkeeping starting essentials
        initial_cost = 0 
        for wall in starting_walls:
            x,y = wall
            if game_state.game_map[x,y] == []:
                initial_cost += 1
        for tur in starting_turrets:
            x,y = tur
            if game_state.game_map[x,y] == []:
                initial_cost += 4

        # determine cost to erect mid wall
        mid_wall_cost = 0
        for wall in mid_wall:
            x,y = wall
            if game_state.game_map[x,y] == []:
                mid_wall_cost += 1

        # deploy start setup on first step
        if game_state.turn_number == 0:
            game_state.attempt_spawn(TURRET, starting_turrets)
            game_state.attempt_spawn(SUPPORT, starting_supports)
            game_state.attempt_spawn(WALL, starting_walls)
            game_state.attempt_spawn(SCOUT, starting_scout)
            game_state.attempt_spawn(INTERCEPTOR, starting_INTERCEPTOR)

        # defence placement logic sequence
        else:
            for t in starting_turrets:
                game_state.attempt_spawn(TURRET, t)
            for w in starting_walls:
                game_state.attempt_spawn(WALL, w)
            for s in starting_supports:
                game_state.attempt_spawn(SUPPORT, s)
            if sp_me - initial_cost >= mid_wall_cost:
                mid_up = True
                for wall in mid_wall:
                    game_state.attempt_spawn(WALL, wall)
            for wall in right_corner_walls:
                game_state.attempt_spawn(WALL, wall)
            game_state.attempt_spawn(TURRET, [24,10])
            game_state.attempt_spawn(WALL, [22,9])
            game_state.attempt_spawn(WALL, [21,8])

            if mid_up:
                for tur in final_turrets:
                    game_state.attempt_spawn(TURRET, tur)

                game_state.attempt_spawn(SUPPORT,[4,9])
                game_state.attempt_spawn(SUPPORT,[5,9])
                for wall in final_walls:
                    game_state.attempt_spawn(WALL, wall)

                # upgrade defences
                tur_upgraded = True
                for tur in starting_turrets:
                    game_state.attempt_upgrade(tur)
                    if not self.is_upgraded(game_state,tur):
                            tur_upgraded = False
                if tur_upgraded:
                    for wall in upgrade_walls:
                        game_state.attempt_upgrade(wall)
                    for sup in starting_supports:
                        game_state.attempt_upgrade(sup)
            
        return mid_up

    def is_upgraded(self,game_state, unit):
        x = unit[0]
        y = unit[1]
        return len(game_state.game_map[x,y]) and game_state.game_map[x,y][0].upgraded

    def demolisher_line_strategy(self, game_state):
        """
        Build a line of the cheapest stationary unit so our demolisher can attack from long range.
        """
        # First let's figure out the cheapest unit
        # We could just check the game rules, but this demonstrates how to use the GameUnit class
        stationary_units = [WALL, TURRET, SUPPORT]
        cheapest_unit = WALL
        for unit in stationary_units:
            unit_class = gamelib.GameUnit(unit, game_state.config)
            if unit_class.cost[game_state.MP] < gamelib.GameUnit(cheapest_unit, game_state.config).cost[game_state.MP]:
                cheapest_unit = unit

        # Now let's build out a line of stationary units. This will prevent our demolisher from running into the enemy base.
        # Instead they will stay at the perfect distance to attack the front two rows of the enemy base.
        for x in range(27, 5, -1):
            game_state.attempt_spawn(cheapest_unit, [x, 11])

        # Now spawn demolishers next to the line
        # By asking attempt_spawn to spawn 1000 units, it will essentially spawn as many as we have resources for
        game_state.attempt_spawn(DEMOLISHER, [24, 10], 1000)

    def least_damage_spawn_location(self, game_state, location_options):
        """
        This function will help us guess which location is the safest to spawn moving units from.
        It gets the path the unit will take then checks locations on that path to 
        estimate the path's damage risk.
        """
        damages = []
        # Get the damage estimate each path will take
        for location in location_options:
            path = game_state.find_path_to_edge(location)
            damage = 0
            for path_location in path:
                # Get number of enemy turrets that can attack each location and multiply by turret damage
                damage += len(game_state.get_attackers(path_location, 0)) * gamelib.GameUnit(TURRET, game_state.config).damage_i
            damages.append(damage)
        
        # Now just return the location that takes the least damage
        return location_options[damages.index(min(damages))]

    def detect_enemy_unit(self, game_state, unit_type=None, valid_x = None, valid_y = None):
        total_units = 0
        for location in game_state.game_map:
            if game_state.contains_stationary_unit(location):
                for unit in game_state.game_map[location]:
                    if unit.player_index == 1 and (unit_type is None or unit.unit_type == unit_type) and (valid_x is None or location[0] in valid_x) and (valid_y is None or location[1] in valid_y):
                        total_units += 1
        return total_units
        
    def filter_blocked_locations(self, locations, game_state):
        filtered = []
        for location in locations:
            if not game_state.contains_stationary_unit(location):
                filtered.append(location)
        return filtered

    def on_action_frame(self, turn_string):
        """
        This is the action frame of the game. This function could be called 
        hundreds of times per turn and could slow the algo down so avoid putting slow code here.
        Processing the action frames is complicated so we only suggest it if you have time and experience.
        Full doc on format of a game frame at in json-docs.html in the root of the Starterkit.
        """
        # Let's record at what position we get scored on
        state = json.loads(turn_string)
        events = state["events"]
        breaches = events["breach"]
        for breach in breaches:
            location = breach[0]
            unit_owner_self = True if breach[4] == 1 else False
            # When parsing the frame data directly, 
            # 1 is integer for yourself, 2 is opponent (StarterKit code uses 0, 1 as player_index instead)
            if not unit_owner_self:
                gamelib.debug_write("Got scored on at: {}".format(location))
                self.scored_on_locations.append(location)
                gamelib.debug_write("All locations: {}".format(self.scored_on_locations))


    def sim(self, game_state: GameState, dep: list[list[str, list[int,int]]]):
        """
        Deployments are of form [[type, spawn_location],...]
        """
        stationaries_hit = []
        scoured_on_op = 0
        scoured_on_me = 0
        dmg_on_op = 0
        dmg_on_me = 0
        sim = copy.deepcopy(game_state)
        active = []
        for unit in dep:
            if unit[1][1] <= 13:
                player = 0
            else: 
                player = 1
            new = GameUnit.__init__(unit[0], sim.game_map.config, player, unit[1][0], unit[1][1])
            active.append((new, 100, [], sim.get_target_edge([unit[0].y, unit[0].y])))

            if not new.stationary:
                sim.game_map.__map[x][y].append(new)
            else:
                sim.game_map.__map[x][y] = [new]

        while active != []:
            locations = []
            for nub in active:
                nub[1] += 1
                locations.append([nub[0].x,nub[0].y])
            locations = set(locations)

            for loc in locations:
                # upraded supports grand shielding
                for point in sim.game_map.get_locations_in_range(loc, 10):
                    if not point in nub[2]:
                        x,y = point
                        units = sim.game_map[x,y]
                        is_up_sup = False
                        for u in units:
                            if u.unit_type == SUPPORT and u.upgraded:
                                is_up_sup == True
                        if is_up_sup:
                            nub[2].append(point)
                            nub[0].health += 6 + (0.3 * y)
                # unupgradded supports grant shielding
                for point in sim.game_map.get_locations_in_range(loc, 4.5):
                    if not point in nub[2]:
                        x,y = point
                        units = sim.game_map[x,y]
                        is_sup = False
                        for u in units:
                            if u.unit_type == SUPPORT and not u.upgraded:
                                is_sup == True
                        if is_sup:
                            nub[2].append(point)
                            nub[0].health += 3
            # move
            for nub in active:
                if nub[1] >= nub[0].speed:
                    next_move = sim.find_path_to_edge([nub[0].x, nub[0].y], nub[3])
 

                    if next_move is None:
                        nub[0].health = 0
                    elif len(next_move == 1):
                        # blocked or on edge
                        nub[0].health = 0
                        x,y = nub[0].x, nub[0].y
                        if [x,y] in sim.game_map.get_edge_locations(nub[3]):
                            if nub[0].player_index == 0:
                                scoured_on_op += 1
                            else:
                                scoured_on_me += 1
                            
                    else:
                        nub[0].x = next_move[1][0]
                        nub[0].y = next_move[1][1]
                    nub[1] = 0
            # mobile attack
            for nub in active:
                targ = sim.get_target(nub[0])
                if not targ is None:
                    if targ.stationary:
                        stationaries_hit.append(targ)
                        targ.health -= nub[0].damage_f
                        if nub[0].player_index == 0:
                            dmg_on_op += nub[0].damage_f
                        else:
                            dmg_on_me += nub[0].damage_f
                    else:
                        targ.health -= nub[0].damage_i
            # sattionary attack
            attackers = [] 
            for nub in active:
                attackers.extend(sim.get_attackers([nub[0].x, nub[0].y], nub[0].player_index))
            attackers = set(attackers)
            for att in attackers:
                sim.get_target(att).health -= att.damage_i
            # remove dead mobile
            for nub in active:
                if nub[0].health <= 0:
                    active.remove(nub)
                    sim.game_map.__map.remove(nub[0])
            #remove dead stationary
            for defence in stationaries_hit:
                if defence.health <= 0:
                    sim.game_map.remove_unit([defence.x, defence.y])
        return scoured_on_op, scoured_on_me, dmg_on_op, dmg_on_me
            
if __name__ == "__main__":
    algo = AlgoStrategy()
    algo.start()
