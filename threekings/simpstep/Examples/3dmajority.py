"""Siple 3d majority rule with 3d z-buffer based rendering all
programmed in SIMP.

Mon Sep 19 23:28:34 EDT 2005

This example needs work, but is functional. 
"""

from simp import *
from random import randint

#X,Y,Z = [70]*3
X,Y,Z = [100,100,50]
initialize(size=[Z,Y,X])

# -------------------------------- STATE
p = Signal(SmallUInt(2))
r = Signal(SmallUInt(2))

zlight = Signal(UInt8,[Z,1,1]) # z moving light
dlight = Signal(UInt8,[Z,1,1]) # diagonal moving light
screen = Signal(UInt8,[Z,1,1]) # visible screen
white = OutSignal(UInt8,[Z,1,1]) # visible screen


# -------------------------------- DYNAMICS
N,S,E,W,U,D = p[0,-1,0],p[0,1,0],p[0,0,1],p[0,0,-1],p[-1,0,0],p[1,0,0]

def majority():
    sum = p+N+S+E+W+U+D+(r*2)
    if sum<=4: p._ = 0
    elif sum>=5: p._ = 1 

# --------------------------------
white = OutSignal(UInt8)

def bw():
    white._ = p*255
rend = Renderer(Rule(bw),outputs=white)


def render_slice():
    if zlight>0 and p==1:
        screen._=zlight+dlight
    if p==1:
        dlight._=0;
        zlight._=0;
    else:
        if dlight>0:  dlight._=dlight # grow dimmer
        else: dlight._=0
        if zlight>0:  zlight._=zlight-1
        else: zlight._=0    

render_slice = Rule(render_slice,[Z,1,1])


reset_seq = Sequence([SetCoset({render_slice:[0,0,0]}),
              Write(subscr[:,:,:],[zlight,dlight,screen],[127,128,0])])

z_rend = Sequence([render_slice,
                   Shift({render_slice:[1,0,0],zlight:[0,0,0],
                          dlight:[0,1,1],screen:[0,0,0]})])

def background():
    """Cast shadows onto a dim background"""
    if zlight>0:
        screen._=(dlight)/4        

z_rend = Sequence([render_slice,render_slice,
                   Shift({render_slice:[1,0,0],
                          dlight:[0,1,1],
#                          zlight:[0,-1,-1],
#                          screen:[0,-1,-1]
                          }),
                   render_slice,
                   Shift({render_slice:[1,0,0]})] )

render_seq = Sequence([reset_seq]+([z_rend]*(Z/2))+[Rule(background,[Z,1,1])])
 
class Render3D(Renderer):
    def __call__(self,out=None):
        render_seq()
        return Renderer.__call__(self,out)

def rend_screen():
    white._ = screen
rend_screen = Rule(rend_screen,[Z,1,1])

    
rend_3d = Render3D(rend_screen,outputs=white)


# -------------------------------- INITIALIZE STATE
p[:,:,:] = makedist(p.shape,[.50,.50])
r[:,:,:] = makedist(r.shape,[.50,.50])

p[-5:5,:,:] = 0



# -------------------------------- CONSOLE
dynamics = Sequence([Rule(majority),Shuffle([r])])

print rend_3d().shape

ui = Console([rend_3d,rend])

for i in range(40):
    print "iteration i",i
    dynamics()

ui.bind("I",reset_seq)
ui.bind("R",render_seq)

ui.bind("Z",z_rend)

    
ui.bind("STEP",dynamics)
ui.start()
