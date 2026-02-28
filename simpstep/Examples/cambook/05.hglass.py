"""
Toffoli and Margolus, p. 45
"""

from simp import *
from random import randint

X,Y = [200]*2
initialize(size=[Y,X])

# -------------------------------- STATE
p = Signal(SmallUInt(2))

# -------------------------------- DYNAMICS
N,S,E,W = p[-1,0],p[1,0],p[0,1],p[0,-1]

def hglass():
    glass=(((((((E*2)+W)*2)+S)*2)+N)*2)+p


    if(glass == 0):
        p._ = 0
    elif(glass == 1):
        p._ = 1
    elif(glass == 2):
        p._ = 1
    elif(glass == 3):
        p._ = 1
    elif(glass == 4):
        p._ = 0
    elif(glass == 5):
        p._ = 0
    elif(glass == 6):
        p._ = 0
    elif(glass == 7):
        p._ = 1
    elif(glass == 8):
        p._ = 0
    elif(glass == 9):
        p._ = 0
    elif(glass == 10):
        p._ = 0
    elif(glass == 11):
        p._ = 0
    elif(glass == 12):
        p._ = 0
    elif(glass == 13):
        p._ = 1
    elif(glass == 14):
        p._ = 0
    elif(glass == 15):
        p._ = 0
    elif(glass == 16):
        p._ = 0
    elif(glass == 17):
        p._ = 0
    elif(glass == 18):
        p._ = 0
    elif(glass == 19):
        p._ = 0
    elif(glass == 20):
        p._ = 0
    elif(glass == 21):
        p._ = 0
    elif(glass == 22):
        p._ = 0
    elif(glass == 23):
        p._ = 0
    elif(glass == 24):
        p._ = 0
    elif(glass == 25):
        p._ = 1
    elif(glass == 26):
        p._ = 0
    elif(glass == 27):
        p._ = 0
    elif(glass == 28):
        p._ = 0
    elif(glass == 29):
        p._ = 1
    elif(glass == 30):
        p._ = 1
    elif(glass == 31):
        p._ = 1

# --------------------------------
white = OutSignal(UInt8)

def bw():
    white._ = p*255
rend = Renderer(Rule(bw),outputs=white)

# -------------------------------- INITIALIZE STATE
import numarray
p[:,:] = makedist(p.shape,[.5,.5])

# -------------------------------- CONSOLE
ui = Console(rend)
ui.bind("STEP",Rule(hglass))
ui.start()
