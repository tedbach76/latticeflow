"""
A little module that gathers system information relevant to SIMP
"""

# the system information string
info = ""


# fill out various pieces of information

# -------------------------------- GET INFO FROM SYS
import time
info+="ctime"+"\t"+ time.ctime()+"\n"
info+="gmtime"+"\t"+ `time.gmtime()`+"\n"
import socket
try:    info+="hostname"+"\t"+socket.gethostname()+"\n"
except: info+="hostname"+"\t"+"\n"

import sys
info+="python\t"+sys.version+"\n"


import sys
sys.version

modules = ["simp","pygame","Numeric","numarray"]

for mod in modules:
    info+=mod+"\t"
    try:
        mod = __import__(mod)
        info+=mod.__version__+"\n"
    except ImportError: info+="\n"
    except AttributeError: pass
        
info
