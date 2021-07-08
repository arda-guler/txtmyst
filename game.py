import pygame
from pygame.locals import *
from os import system
import keyboard
import random

from sound import *

current_episode = "E1"
current_episode_keys = []
current_map_name = None
current_message = None
current_message_timer = 0
lightning = False

# this is so that we don't read property lines as data
# when loading new maps
map_property_lines = 3 + 1

class gameMap:
    def __init__(self, data, name, size, east, west, north, south,
                 key_east, key_west, key_north, key_south, dark):
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

class player:
    def __init__(self, pos, inventory):
        self.pos = pos
        self.inventory = inventory

current_map = gameMap(None, None, None, None, None, None,\
                      None, None, None, None, None, False)
player = player([0,0], [])

# read map data and properties

def loadMap(e, m):
    
    map_path = "data/" + e + "/" + m + ".map"
    map_file = open(map_path, "r")
    map_lines = map_file.readlines()

    loaded_map = []
    map_size = [len(map_lines) - map_property_lines, len(map_lines[0]) - 1]

    # have a clean and sized map
    for y in range(map_size[0]):
        loaded_map.append([])
        for x in range(map_size[1]):
            loaded_map[y].append(".")

    # fill map with stuff
    for y in range(map_size[0]):
        for x in range(map_size[1]):
                loaded_map[y][x] = map_lines[y][x]

    # when you add a new PROPERTY line, please re-check list indices
    directions = map_lines[-3].split("-")
    loaded_map_east = directions[0]
    loaded_map_west = directions[1]
    loaded_map_north = directions[2]
    loaded_map_south = directions[3][0:-1] # do the slicing because of newline

    keys = map_lines[-2].split("-")
    loaded_map_key_east = keys[0]
    loaded_map_key_west = keys[1]
    loaded_map_key_north = keys[2]
    loaded_map_key_south = keys[3][0:-1] # do the slicing because of newline

    loaded_map_dark = bool(int(map_lines[-1][0:-1]))

    loaded_map_name = m

    return loaded_map, loaded_map_name, map_size, loaded_map_east,\
           loaded_map_west, loaded_map_north, loaded_map_south,\
           loaded_map_key_east, loaded_map_key_west,\
           loaded_map_key_north, loaded_map_key_south, loaded_map_dark

#-----------------------
# MOVING THROUGH DOORS
#-----------------------

# basically, load in the new map and place player next to appropriate door

def goEast():
    global current_map, player
    playSfx("door", channel=1)

    door_num = 0

    for line in current_map.data:
        if ("e" in line) or ("E" in line):
            door_num += 1
    
    current_map.data, current_map.name, current_map.size, current_map.east, current_map.west,\
                      current_map.north, current_map.south, current_map.key_east, current_map.key_west,\
                      current_map.key_north, current_map.key_south, current_map.dark = loadMap(current_episode, current_map.east)

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

    for line in current_map.data:
        if ("w" in line) or ("W" in line):
            door_num += 1
            
    current_map.data, current_map.name, current_map.size, current_map.east, current_map.west,\
                      current_map.north, current_map.south, current_map.key_east, current_map.key_west,\
                      current_map.key_north, current_map.key_south, current_map.dark = loadMap(current_episode, current_map.west)

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
                      current_map.key_north, current_map.key_south, current_map.dark = loadMap(current_episode, current_map.north)

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
                      current_map.key_north, current_map.key_south, current_map.dark = loadMap(current_episode, current_map.south)

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

# just check the player's keys before letting them move to nearby maps

def goEastLocked():
    global current_map, player, current_message, current_message_timer

    if current_map.key_east in player.inventory:
        goEast()
    else:
        playSfx("locked", channel=1)
        current_message = "LOCKED."
        current_message_timer = 15

def goWestLocked():
    global current_map, player, current_message, current_message_timer

    if current_map.key_west in player.inventory:
        goWest()
    else:
        playSfx("locked", channel=1)
        current_message = "LOCKED."
        current_message_timer = 15

def goNorthLocked():
    global current_map, player, current_message, current_message_timer

    if current_map.key_north in player.inventory:
        goNorth()
    else:
        playSfx("locked", channel=1)
        current_message = "LOCKED."
        current_message_timer = 15

def goSouthLocked():
    global current_map, player, current_message, current_message_timer

    if current_map.key_south in player.inventory:
        goSouth()
    else:
        playSfx("locked", channel=1)
        current_message = "LOCKED."
        current_message_timer = 15
            
#-----------------

# new episode, yay!
def loadEpisode(e):
    global current_map, player, current_episode, current_episode_keys

    current_episode_keys = []

    keys_path = "data/" + e + "/episode.keys"
    keys_file = open(keys_path, "r")
    keys_lines = keys_file.readlines()

    for line in keys_lines:
        current_episode_keys.append(line[0:-1])
    
    current_map.data, current_map.name, current_map.size, current_map.east, current_map.west,\
                      current_map.north, current_map.south, current_map.key_east, current_map.key_west,\
                      current_map.key_north, current_map.key_south, current_map.dark = loadMap(e, "ENTRY")

    for y in range(current_map.size[0]):
        for x in range(current_map.size[1]):
            if current_map.data[y][x] == "P":
                player.pos = [y, x]
                break

# print loaded map, player, items, decorations, everything

def updateMap():
    global current_map, player

    print(current_map.name + "\n")
    
    for y in range(current_map.size[0]):
        line = ""
        for x in range(current_map.size[1]):
            this_char = current_map.data[y][x]
            if not (current_map.dark and ((player.pos[0] - y)**2 + (player.pos[1] - x)**2)**0.5 > 4):

                # pass-below chars
                if this_char == "o":
                    line += "O"
                elif this_char == "i":
                    line += "I"
                elif this_char == "t":
                    line += "T"

                # player
                elif [y,x] == player.pos:
                    line += "#"

                # keys
                elif this_char == "1" or this_char == "2" or this_char == "3" or this_char == "4":
                    if not (this_char in player.inventory):
                        line += "+"
                    else:
                        line += "."

                # regular floor
                elif this_char == "." or this_char == "P":
                    line += "."

                # obstacles
                elif this_char == "O":
                    line += "O"
                elif this_char == "I":
                    line += "I"
                elif this_char == "T":
                    line += "T"
                elif this_char == " ":
                    line += " "

                # doors
                elif (this_char == "N" or this_char == "S"
                      or this_char == "n" or this_char == "s"):
                    line += "_"
                elif (this_char == "W" or this_char == "E"
                      or this_char == "w" or this_char == "e"):
                    line += "|"

                # everything else used for aesthetics
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

def main():
    global current_map, player, current_message, current_message_timer
    
    loadEpisode("E1")

    initSound()
    playBGM("bgm1")
    playSfx("thunder", -1, 6, 0.3)
    
    while True:
        frame_up_cmd = False
        frame_down_cmd = False
        frame_right_cmd = False
        frame_left_cmd = False
        
        if keyboard.is_pressed("w"):
            frame_up_cmd = True
        if keyboard.is_pressed("s"):
            frame_down_cmd = True
        if keyboard.is_pressed("d"):
            frame_right_cmd = True
        if keyboard.is_pressed("a"):
            frame_left_cmd = True

        frame_movement = [0, 0] # y, x
        next_char = None

        # what characters we can move through is quite specific
        if frame_up_cmd:
            next_char = current_map.data[player.pos[0] - 1][player.pos[1]]
            if (next_char == "." or next_char == "P" or next_char == "i" or next_char == "t" or
                next_char == "1" or next_char == "2" or next_char == "3" or next_char == "4" or
                next_char == "o" or next_char == "H" or next_char == "-"):
                frame_movement[0] -= 1
                
            elif next_char == "N":
                goNorth()
            elif next_char == "n":
                goNorthLocked()

        if frame_down_cmd:
            next_char = current_map.data[player.pos[0] + 1][player.pos[1]]
            if (next_char == "." or next_char == "P" or next_char == "i" or next_char == "t" or
                next_char == "1" or next_char == "2" or next_char == "3" or next_char == "4" or
                next_char == "o" or next_char == "H" or next_char == "-"):
                frame_movement[0] += 1
                
            elif next_char == "S":
                goSouth()
            elif next_char == "s":
                goSouthLocked()

        if frame_right_cmd:
            next_char = current_map.data[player.pos[0]][player.pos[1] + 1]
            if (next_char == "." or next_char == "P" or next_char == "i" or next_char == "t" or
                next_char == "1" or next_char == "2" or next_char == "3" or next_char == "4" or
                next_char == "o" or next_char == "H" or next_char == "-"):
                frame_movement[1] += 1
                
            elif next_char == "E":
                goEast()
            elif next_char == "e":
                goEastLocked()

        if frame_left_cmd:
            next_char = current_map.data[player.pos[0]][player.pos[1] - 1]
            if (next_char == "." or next_char == "P" or next_char == "i" or next_char == "t" or
                next_char == "1" or next_char == "2" or next_char == "3" or next_char == "4" or
                next_char == "o" or next_char == "H" or next_char == "-"):
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
                next_char == "o" or next_char == "H" or next_char == "-"):
                frame_movement = [0, 0]
            
        player.pos[0] += frame_movement[0]
        player.pos[1] += frame_movement[1]

        # is the player on a key?
        player_on = current_map.data[player.pos[0]][player.pos[1]]

        if (player_on == "1" or player_on == "2" or player_on == "3" or player_on == "4"):
            if not (player_on in player.inventory):
                playSfx("pickup", channel=1)
                player.inventory.append(player_on)
                current_message = "You got " + current_episode_keys[int(player_on) - 1] + "!"
                current_message_timer = 25

        system("cls")
        lightningStrike()
        updateMap()
        updateMessage()
        pygame.time.wait(100)

    pygame.time.wait(10000)
    pygame.quit()

main()




