import pygame
from pygame.locals import *
from os import system
import keyboard
import random

from sound import *

# WARNING: WINDOWS-ONLY SYSTEM CALLS!
#
# For Linux friendly experience:
#
# 1a) Remove command line color switching calls
# 1b) Inhibit lightningStrike() function
# 2) Replace system("cls") with system("clear")

#-----------------------------------
#  INITIALIZATION AND DEFINITIONS
#-----------------------------------

# message that appears below map
current_message = None
current_message_timer = 0

# light blue flash
lightning = False

# cheats :)
invulnerability = False
no_locks = False
night_vision = False

frame_clock = 0

# this is so that we don't read property lines as data
# when loading new maps
map_property_lines = 4 + 1

class gameEpisode:
    def __init__(self, name, keys, backstory, ending, map_start, map_finish):
        self.name = name
        self.keys = keys
        
        self.backstory = backstory
        self.ending = ending
        
        self.map_start = map_start
        self.map_finish = map_finish
        
class gameMap:
    def __init__(self, data, name, size, east, west, north, south,
                 key_east, key_west, key_north, key_south, dark, desc):
        self.data = data
        self.name = name
        self.size = size
        
        self.east = east
        self.west = west
        self.north = north
        self.south = south
        
        self.key_east = key_east
        self.key_west = key_west
        self.key_north = key_north
        self.key_south = key_south

        self.dark = dark

        self.desc = desc

class player:
    def __init__(self, pos, inventory, health):
        self.pos = pos
        self.inventory = inventory
        self.health = 100

class enemy:
    def __init__(self, pos, dormant):
        self.pos = pos
        self.dormant = dormant

# these guys track you
class ghost(enemy):
    def __init__(self, pos, dormant, damage):
        super().__init__(pos, dormant)
        self.damage = damage

# these guys teleport around you
# trust me, I'm an expert, they do that
class doll(enemy):
    def __init__(self, pos, dormant, damage, tp_chance):
        super().__init__(pos, dormant)
        self.damage = damage
        self.tp_chance = tp_chance

# these guys are moving obstacles
class statue(enemy):
    def __init__(self, pos, dormant, move_rate):
        super().__init__(pos, dormant)
        self.move_rate = move_rate

# lets get the instances ready

current_episode = gameEpisode(None, [], "", "", "", "")

current_map = gameMap(None, None, None, None, None, None,\
                      None, None, None, None, None, False, None)

player = player([0,0], [], 100)

ghost_a = ghost([-1, -1], True, 10)
doll_a = doll([-1, -1], True, 10, 5)
statue_a = statue([-5, -5], True, 0.2)
statue_b = statue([-5, -5], True, 0.2)
statue_c = statue([-5, -5], True, 0.2)
statue_d = statue([-5, -5], True, 0.2)

statues = [statue_a, statue_b, statue_c, statue_d]

def sign(number):
    if number >= 0:
        return 1
    else:
        return -1

#-----------------------------------
#            MAP LOADER
#-----------------------------------

def loadMap(m):

    global current_episode, ghost_a, statues

    # if the player reached the ending, don't bother loading
    # just show the ending instead
    if m == current_episode.map_finish:
        gameOver("ending")
        return
    
    map_path = "data/" + current_episode.name + "/" + m + ".map"
    map_file = open(map_path, "r")
    map_lines = map_file.readlines()

    loaded_map = []
    map_size = [len(map_lines) - map_property_lines, len(map_lines[0]) - 1]

    has_ghost, num_of_statues = False, 0
    statue_positions = []

    # have a clean and sized map
    for y in range(map_size[0]):
        loaded_map.append([])
        for x in range(map_size[1]):
            loaded_map[y].append(".")

    # fill map with stuff
    for y in range(map_size[0]):
        for x in range(map_size[1]):
            loaded_map[y][x] = map_lines[y][x]
            if map_lines[y][x] == "A":
                has_ghost = True
                ghost_a.pos = [y,x]
                ghost_a.dormant = False
            elif map_lines[y][x] == "!":
                num_of_statues += 1
                statue_positions.append([y,x])

    if not has_ghost:
        ghost_a.dormant = True

    for i in range(4):
        if num_of_statues > 0:
            statues[i].dormant = False
            statues[i].pos = statue_positions[i]
        else:
            statues[i].dormant = True
        num_of_statues -= 1

    # when you add a new PROPERTY line, please re-check list indices
    directions = map_lines[-map_property_lines+1].split("-")
    loaded_map_east = directions[0]
    loaded_map_west = directions[1]
    loaded_map_north = directions[2]
    loaded_map_south = directions[3][0:-1]

    keys = map_lines[-map_property_lines+2].split("-")
    loaded_map_key_east = keys[0]
    loaded_map_key_west = keys[1]
    loaded_map_key_north = keys[2]
    loaded_map_key_south = keys[3][0:-1]

    loaded_map_dark = bool(int(map_lines[-map_property_lines+3][0:-1]))

    loaded_map_name = m

    loaded_map_desc = map_lines[-map_property_lines+4][0:-1]

    return loaded_map, loaded_map_name, map_size, loaded_map_east,\
           loaded_map_west, loaded_map_north, loaded_map_south,\
           loaded_map_key_east, loaded_map_key_west,\
           loaded_map_key_north, loaded_map_key_south, loaded_map_dark,\
           loaded_map_desc

#-----------------------
# MOVING THROUGH DOORS
#-----------------------

# basically, load in the new map and place player next to appropriate door

# NOTE: There may be more than one door going in and out of the same room
# so you need to check which door the player went through

def goEast():
    global current_map, player
    playSfx("door", channel=1)

    door_num = 0

    for y in range(len(current_map.data)):
        if (("e" in current_map.data[y]) or ("E" in current_map.data[y])) and y <= player.pos[0]:
            door_num += 1
    
    current_map.data, current_map.name, current_map.size, current_map.east, current_map.west,\
                      current_map.north, current_map.south, current_map.key_east, current_map.key_west,\
                      current_map.key_north, current_map.key_south, current_map.dark, current_map.desc = loadMap(current_map.east)

    search_num = 0

    for y in range(current_map.size[0]):
        for x in range(current_map.size[1]):
            if current_map.data[y][x] == "W" or current_map.data[y][x] == "w":
                search_num += 1
                if search_num == door_num:
                    player.pos = [y, x+1]
                    break

def goWest():
    global current_map, player
    playSfx("door", channel=1)

    door_num = 0

    for y in range(len(current_map.data)):
        if (("w" in current_map.data[y]) or ("W" in current_map.data[y])) and y <= player.pos[0]:
            door_num += 1
            
    current_map.data, current_map.name, current_map.size, current_map.east, current_map.west,\
                      current_map.north, current_map.south, current_map.key_east, current_map.key_west,\
                      current_map.key_north, current_map.key_south, current_map.dark, current_map.desc  = loadMap(current_map.west)

    search_num = 0

    for y in range(current_map.size[0]):
        for x in range(current_map.size[1]):
            if current_map.data[y][x] == "E" or current_map.data[y][x] == "e":
                search_num += 1
                if search_num == door_num:
                    player.pos = [y, x-1]
                    break

def goNorth():
    global current_map, player
    playSfx("door", channel=1)

    door_num = 0

    for char in range(len(current_map.data[player.pos[0]-1])):
        if (current_map.data[player.pos[0]-1][char] == "n" or current_map.data[player.pos[0]-1][char] == "N") and char <= player.pos[1]:
            door_num += 1
    
    current_map.data, current_map.name, current_map.size, current_map.east, current_map.west,\
                      current_map.north, current_map.south, current_map.key_east, current_map.key_west,\
                      current_map.key_north, current_map.key_south, current_map.dark, current_map.desc = loadMap(current_map.north)

    search_num = 0

    for y in range(current_map.size[0]):
        for x in range(current_map.size[1]):
            if current_map.data[y][x] == "S" or current_map.data[y][x] == "s":
                search_num += 1
                if search_num == door_num:
                    player.pos = [y-1, x]
                    break

def goSouth():
    global current_map, player
    playSfx("door", channel=1)

    door_num = 0

    for char in range(len(current_map.data[player.pos[0]+1])):
        if (current_map.data[player.pos[0]+1][char] == "s" or current_map.data[player.pos[0]+1][char] == "S") and char <= player.pos[1]:
            door_num += 1
    
    current_map.data, current_map.name, current_map.size, current_map.east, current_map.west,\
                      current_map.north, current_map.south, current_map.key_east, current_map.key_west,\
                      current_map.key_north, current_map.key_south, current_map.dark, current_map.desc = loadMap(current_map.south)

    search_num = 0

    for y in range(current_map.size[0]):
        for x in range(current_map.size[1]):
            if current_map.data[y][x] == "N" or current_map.data[y][x] == "n":
                search_num += 1
                if search_num == door_num:
                    player.pos = [y+1, x]
                    break

#-----------------------------
# MOVING THROUGH LOCKED DOORS
#-----------------------------

# just check the player's keys before letting them move through locked doors

def goEastLocked():
    global current_map, player, current_message, current_message_timer,\
           no_locks

    if (current_map.key_east in player.inventory) or no_locks:
        goEast()
    else:
        playSfx("locked", channel=1)
        current_message = "LOCKED."
        current_message_timer = 15

def goWestLocked():
    global current_map, player, current_message, current_message_timer,\
           no_locks

    if (current_map.key_west in player.inventory) or no_locks:
        goWest()
    else:
        playSfx("locked", channel=1)
        current_message = "LOCKED."
        current_message_timer = 15

def goNorthLocked():
    global current_map, player, current_message, current_message_timer,\
           no_locks

    if (current_map.key_north in player.inventory) or no_locks:
        goNorth()
    else:
        playSfx("locked", channel=1)
        current_message = "LOCKED."
        current_message_timer = 15

def goSouthLocked():
    global current_map, player, current_message, current_message_timer,\
           no_locks

    if (current_map.key_south in player.inventory) or no_locks:
        goSouth()
    else:
        playSfx("locked", channel=1)
        current_message = "LOCKED."
        current_message_timer = 15
            
#-------------------
#  EPISODE LOADER
#-------------------

# new episode, yay!
def loadEpisode(e):
    global current_map, player, current_episode

    current_episode.name = e

    # read backstory, ending, start and finish maps
    # from episode.story file
    story_path = "data/" + current_episode.name + "/episode.story"
    story_file = open(story_path, "r")
    story_lines = story_file.readlines()

    i = 0
    for line in story_lines:
        i += 1
        if line[0:10] == "MAP_START:":
            current_episode.map_start = line[10:-1]
        elif line[0:11] == "MAP_FINISH:":
            current_episode.map_finish = line[11:-1]
        elif line[0:-1] == "BACKSTORY":
            episode_backstory_start = i
        elif line[0:-1] == "END_BACKSTORY":
            episode_backstory_end = i
        elif line[0:-1] == "ENDING":
            episode_ending_start = i
        elif line[0:-1] == "END_ENDING":
            episode_ending_end = i

    current_episode.backstory = ""
    for i in range(len(story_lines[episode_backstory_start:episode_backstory_end-1])):
        current_episode.backstory += story_lines[episode_backstory_start + i]

    current_episode.ending = ""
    for i in range(len(story_lines[episode_ending_start:episode_ending_end-1])):
        current_episode.ending += story_lines[episode_ending_start + i]

    # read keys from episode.keys file
    current_episode.keys = []

    keys_path = "data/" + current_episode.name + "/episode.keys"
    keys_file = open(keys_path, "r")
    keys_lines = keys_file.readlines()

    for line in keys_lines:
        current_episode.keys.append(line[0:-1])

    # show controls and backstory
    # also show controls
    system("cls")
    print(current_episode.backstory)
    pygame.time.wait(3000)
    input("Press Enter to proceed.")
    system("cls")
    print("Controls: WASD to move, t to enter command.\n\nEnter command 'help' to learn more.\n")
    input("Press enter to begin.")
    system("cls")
    
    # place player in starting map
    current_map.data, current_map.name, current_map.size, current_map.east, current_map.west,\
                      current_map.north, current_map.south, current_map.key_east, current_map.key_west,\
                      current_map.key_north, current_map.key_south, current_map.dark, current_map.desc = loadMap(current_episode.map_start)

    for y in range(current_map.size[0]):
        for x in range(current_map.size[1]):
            if current_map.data[y][x] == "P":
                player.pos = [y, x]
                break

def updateEnemies():
    global current_map, player, ghost_a, doll_a, statues

    # --- GHOST MECHANICS ---

    # ghost is not dormant and player is not hiding
    if (ghost_a.dormant == False and not
        current_map.data[player.pos[0]][player.pos[1]] == "t"):
        if (abs(ghost_a.pos[0] - player.pos[0]) > 1 and
            random.uniform(0,10) > 3): # stall the ghost randomly so player has a chance to escape

            if player.pos[0] > ghost_a.pos[0]: 
                ghost_a.pos[0] += 1
            else:
                ghost_a.pos[0] -= 1

        if (abs(ghost_a.pos[1] - player.pos[1]) > 1 and
            random.uniform(0,10) > 3): # stall the ghost randomly so player has a chance to escape

            if player.pos[1] > ghost_a.pos[1]: 
                ghost_a.pos[1] += 1
            else:
                ghost_a.pos[1] -= 1

    # player is hidden
    elif (ghost_a.dormant == False and current_map.data[player.pos[0]][player.pos[1]] == "t" and
          random.uniform(0,10) > 3):
        # random y movement
        if ghost_a.pos[0] <= 0:
            ghost_a.pos[0] += random.randint(0,1)
        elif ghost_a.pos[0] >= current_map.size[0]:
            ghost_a.pos[0] += random.randint(-1, 0)
        else:
            ghost_a.pos[0] += random.randint(-1, 1)

        # random x movement
        if ghost_a.pos[1] <= 0:
            ghost_a.pos[1] += random.randint(0,1)
        elif ghost_a.pos[1] >= current_map.size[0]:
            ghost_a.pos[1] += random.randint(-1, 0)
        else:
            ghost_a.pos[1] += random.randint(-1, 1)

    # --- STATUE MECHANICS ---
    
    for statue in statues:
        if (statue.dormant == False and not
            current_map.data[player.pos[0]][player.pos[1]] == "t" and
            (frame_clock % 4) == 0): # these guys are rather slow

            statue_movement = [0, 0]
            
            if (abs(statue.pos[0] - player.pos[0]) > 1):
                statue_next_char = (current_map.data[statue.pos[0] - sign(statue.pos[0] - player.pos[0])][statue.pos[1]])
                if (statue_next_char == "." or statue_next_char == "." or statue_next_char == "o" or statue_next_char == "i" or
                    statue_next_char == "P" or statue_next_char == "A"):
                    statue_movement[0] = - sign(statue.pos[0] - player.pos[0])
            if (abs(statue.pos[1] - player.pos[1]) > 1):
                statue_next_char = current_map.data[statue.pos[0]][statue.pos[1] - sign(statue.pos[1] - player.pos[1])]
                if (statue_next_char == "." or statue_next_char == "." or statue_next_char == "o" or statue_next_char == "i" or
                    statue_next_char == "P" or statue_next_char == "A"):
                    statue_movement[1] = - sign(statue.pos[1] - player.pos[1])

            if (not statue_movement[0] == 0) and (not statue_movement[1] == 0):
                statue_next_char = current_map.data[statue.pos[0] + statue_movement[0]][statue.pos[1] + statue_movement[1]]
                if not (statue_next_char == "." or statue_next_char == "." or statue_next_char == "o" or statue_next_char == "i" or
                    statue_next_char == "P" or statue_next_char == "A"):
                    statue_movement = [0, 0]

            # don't move onto other statues
            for s in statues:
                if not s == statue and not statue.dormant:
                    if s.pos[0] == statue.pos[0] + statue_movement[0] and s.pos[1] == statue.pos[1] + statue_movement[1]:
                        statue_movement = [0, 0]

            statue.pos[0] += statue_movement[0]
            statue.pos[1] += statue_movement[1]

            # they can get blocked by obstacles, that's on purpose

    playerDamage()

def gameOver(ending):

    global current_episode

    if ending == "death":
        system("cls")
        system("color 4c")
        playBGM("death")
        print("\n\n  YOU DIED.  \n")
        pygame.time.wait(1000)
        flush_input()
        input("Your last words?: ")
        pygame.time.wait(1000)
        pygame.quit()
        exit()

    elif ending == "ending":
        system("cls")
        #playBGM("ending")
        print(current_episode.ending)
        pygame.time.wait(1000)
        flush_input()
        input("What is the code for next episode?: ")
        pygame.time.wait(1000)
        pygame.quit()
        exit()

# damage player from every possible cause
# because there is no rest for the living

def playerDamage():
    global player, ghost_a, doll_a, frame_clock

    if frame_clock % 5 == 0:

        # ghost damage
        if (abs(player.pos[0] - ghost_a.pos[0]) <= 1 and abs(player.pos[1] - ghost_a.pos[1]) <= 1 and
            not ghost_a.dormant):
            player.health -= ghost_a.damage
            system("color 4")
            playSfx("ghost", channel=2)

        # doll damage
        if (abs(player.pos[0] - doll_a.pos[0]) <= 1 and abs(player.pos[1] - doll_a.pos[1]) <= 1 and
            not doll_a.dormant):
            player.health -= doll_a.damage
            system("color 4")

        # note: statues don't deal damage

    if player.health <= 0:
        gameOver("death")

# print loaded map, player, items, decorations, everything

def updateMap():
    global current_map, player, ghost_a, doll_a, night_vision, statues

    updateEnemies()

    print(current_map.name + "\n")
    
    for y in range(current_map.size[0]):
        line = ""
        for x in range(current_map.size[1]):
            this_char = current_map.data[y][x]
            if not (current_map.dark and ((player.pos[0] - y)**2 + (player.pos[1] - x)**2)**0.5 > 4) or night_vision:

                # pass-below chars
                if this_char == "o":
                    line += "O"
                elif this_char == "i":
                    line += "I"
                elif this_char == "t":
                    line += "T"
                
                # enemies
                    # ghost
                elif [y,x] == ghost_a.pos and not ghost_a.dormant:
                    line += "*"

                    #statue
                elif [y,x] == statues[0].pos and not statues[0].dormant:
                    line += "I"
                elif [y,x] == statues[1].pos and not statues[1].dormant:
                    line += "I"
                elif [y,x] == statues[2].pos and not statues[2].dormant:
                    line += "I"
                elif [y,x] == statues[3].pos and not statues[3].dormant:
                    line += "I"
                        
                # player
                elif [y,x] == player.pos:
                    line += "#"

                # keys
                elif (this_char == "1" or this_char == "2" or this_char == "3" or this_char == "4" or
                      this_char == "5" or this_char == "6" or this_char == "7" or this_char == "8"):
                    if not (this_char in player.inventory):
                        line += "+"
                    else:
                        line += "."

                # regular floor
                elif this_char == "." or this_char == "P":
                    line += "."

                # doors
                elif (this_char == "N" or this_char == "S"
                      or this_char == "n" or this_char == "s"):
                    line += "_"
                elif (this_char == "W" or this_char == "E"
                      or this_char == "w" or this_char == "e"):
                    line += "|"

                # enemy spawns
                elif this_char == "A" or this_char == "!":
                    line += "."

                # everything else used for aesthetics and obstacles
                else:
                    line += this_char
            else:
                line += " "
        print(line)

# print current message until timer ends (if any)

def updateMessage():
    global current_message, current_message_timer
    if current_message and current_message_timer > 0:
        current_message_timer -= 1
        print("\n" + current_message)
    elif current_message and current_message_timer <= 0:
        current_message = None
        current_message_timer = 0

def lightningStrike():
    global lightning
    
    if not lightning:
        if random.uniform(0, 10) > 9.5:
            lightning = not lightning
            system("color b")
    else:
        lightning = not lightning
        system("color 7")

def flush_input():
    try:
        import msvcrt
        while msvcrt.kbhit():
            msvcrt.getch()
    except ImportError:
        import sys, termios    #for linux/unix
        termios.tcflush(sys.stdin, termios.TCIOFLUSH)

def main():
    global current_map, player, current_message, current_message_timer, frame_clock,\
           invulnerability, no_locks, night_vision, statues
    
    while True:
        frame_up_cmd = False
        frame_down_cmd = False
        frame_right_cmd = False
        frame_left_cmd = False
        frame_cmd = False

        if not invulnerability:
            frame_clock += 1
        
        if keyboard.is_pressed("w"):
            frame_up_cmd = True
        if keyboard.is_pressed("s"):
            frame_down_cmd = True
        if keyboard.is_pressed("d"):
            frame_right_cmd = True
        if keyboard.is_pressed("a"):
            frame_left_cmd = True
        if keyboard.is_pressed("t"):
            frame_cmd = True

        frame_movement = [0, 0] # y, x
        next_char = None

        # what characters we can move through is quite specific
        if frame_up_cmd:
            next_char = current_map.data[player.pos[0] - 1][player.pos[1]]
            if (next_char == "." or next_char == "P" or next_char == "i" or next_char == "t" or
                next_char == "1" or next_char == "2" or next_char == "3" or next_char == "4" or
                next_char == "5" or next_char == "6" or next_char == "7" or next_char == "8" or
                next_char == "o" or next_char == "H" or next_char == "-" or next_char == "A" or
                next_char == "!"):
                frame_movement[0] -= 1
                
            elif next_char == "N":
                goNorth()
            elif next_char == "n":
                goNorthLocked()

        if frame_down_cmd:
            next_char = current_map.data[player.pos[0] + 1][player.pos[1]]
            if (next_char == "." or next_char == "P" or next_char == "i" or next_char == "t" or
                next_char == "1" or next_char == "2" or next_char == "3" or next_char == "4" or
                next_char == "5" or next_char == "6" or next_char == "7" or next_char == "8" or
                next_char == "o" or next_char == "H" or next_char == "-" or next_char == "A" or
                next_char == "!"):
                frame_movement[0] += 1
                
            elif next_char == "S":
                goSouth()
            elif next_char == "s":
                goSouthLocked()

        if frame_right_cmd:
            next_char = current_map.data[player.pos[0]][player.pos[1] + 1]
            if (next_char == "." or next_char == "P" or next_char == "i" or next_char == "t" or
                next_char == "1" or next_char == "2" or next_char == "3" or next_char == "4" or
                next_char == "5" or next_char == "6" or next_char == "7" or next_char == "8" or
                next_char == "o" or next_char == "H" or next_char == "-" or next_char == "A" or
                next_char == "!"):
                frame_movement[1] += 1
                
            elif next_char == "E":
                goEast()
            elif next_char == "e":
                goEastLocked()

        if frame_left_cmd:
            next_char = current_map.data[player.pos[0]][player.pos[1] - 1]
            if (next_char == "." or next_char == "P" or next_char == "i" or next_char == "t" or
                next_char == "1" or next_char == "2" or next_char == "3" or next_char == "4" or
                next_char == "5" or next_char == "6" or next_char == "7" or next_char == "8" or
                next_char == "o" or next_char == "H" or next_char == "-" or next_char == "A" or
                next_char == "!"):
                frame_movement[1] -= 1
                
            elif next_char == "W":
                goWest()
            elif next_char == "w":
                goWestLocked()

        # this is to prevent the edge case where you can walk into corners of obstacles
        if not frame_movement[0] == 0 and not frame_movement[1] == 0:
            next_char = current_map.data[player.pos[0] + frame_movement[0]][player.pos[1] + frame_movement[1]]
            if not (next_char == "." or next_char == "P" or next_char == "i" or next_char == "t" or
                next_char == "1" or next_char == "2" or next_char == "3" or next_char == "4" or
                next_char == "5" or next_char == "6" or next_char == "7" or next_char == "8" or
                next_char == "o" or next_char == "H" or next_char == "-" or next_char == "A" or
                next_char == "!"):
                frame_movement = [0, 0]

        # player can't get past statues directly, but he can squish through corners
        if not statues[0].dormant:
            for statue in statues:
                if not statue.dormant:
                    if statue.pos[0] == player.pos[0] + frame_movement[0] and statue.pos[1] == player.pos[1] + frame_movement[1]:
                        frame_movement = [0, 0]
            
        player.pos[0] += frame_movement[0]
        player.pos[1] += frame_movement[1]

        # is the player on a key?
        player_on = current_map.data[player.pos[0]][player.pos[1]]

        if (player_on == "1" or player_on == "2" or player_on == "3" or player_on == "4" or
            player_on == "5" or player_on == "6" or player_on == "7" or player_on == "8"):
            if not (player_on in player.inventory):
                playSfx("pickup", channel=1)
                player.inventory.append(player_on)
                current_message = "You got " + current_episode.keys[int(player_on) - 1] + "!"
                current_message_timer = 25

        system("cls")
        lightningStrike()
        updateMap()
        updateMessage()

        # player wants to enter a command
        if frame_cmd:
            flush_input()
            cmd = input("\n > ")
            
            if cmd == "examine" or cmd == "e":
                p_desc = ""
                for char in current_map.desc:
                    if not char == "\\":
                        p_desc += char
                    else:
                        p_desc += "\n"
                        
                print("\n" + p_desc + "\n")
                input("Press Enter to continue...")

            elif cmd == "inventory" or cmd == "i":
                inv_list = []
                for item in player.inventory:
                    if (item == "1" or item == "2" or item == "3" or item == "4" or
                        item == "5" or item == "6" or item == "7" or item == "8"):
                        inv_list.append(current_episode.keys[int(item) - 1])
                    else:
                        inv_list.append(item)
                        
                print("\nYou have", inv_list, "in your inventory.")
                input("Press Enter to continue...")

            elif cmd == "help" or cmd == "h":
                print("\nCOMMANDS: (h)elp, (e)xamine, (i)nventory, (q)uit")
                print("\nCONTROLS: WASD to move, t to enter command.")
                input("\n\nPress Enter to continue...")

            elif cmd == "agdqd":
                invulnerability = not invulnerability
                frame_clock = 1
                print("\n:)")
                pygame.time.wait(1000)

            elif cmd == "agkfa":
                no_locks = not no_locks
                print("\n:)")
                pygame.time.wait(1000)

            elif cmd == "agbehold":
                night_vision = not night_vision
                print("\nB)")
                pygame.time.wait(1000)

            elif cmd == "quit" or cmd == "q":
                print("\nQuitting...")
                pygame.time.wait(1000)
                pygame.quit()
                break
            
        pygame.time.wait(100)

    pygame.time.wait(3000)
    pygame.quit()

def startGame():
    
    initSound()
    playSfx("thunder", -1, 6, 0.3)
    loadEpisode("E1")
    playBGM("bgm1")

    main()

startGame()
