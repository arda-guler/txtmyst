from pygame import *

def initSound():
    mixer.init()

def playSfx(track, loops=0, channel=1, volume=1):
    chn = mixer.Channel(channel)
    track_full = "data/sfx/" + str(track) + ".ogg"
    snd = mixer.Sound(track_full)
    chn.set_volume(volume)
    chn.play(snd, loops)

def playBGM(track, volume=1):
    chn = mixer.Channel(7)
    track_full = "data/bgm/" + str(track) + ".ogg"
    snd = mixer.Sound(track_full)
    chn.set_volume(volume)
    chn.play(snd, -1)

def getChannelBusy(channel):
    chn = mixer.Channel(channel)
    return chn.get_busy()

