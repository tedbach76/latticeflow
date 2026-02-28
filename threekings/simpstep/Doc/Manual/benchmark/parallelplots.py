#    CPU time   :    907.79 sec.
#    Max Memory :       251 MB
#    Max Swap   :       251 MB
#
#    Max Processes  :         3
#    Max Threads    :       379
# pobo.bu.edu (p4-mp32)



import os
fname = "parallelperformance.eps"

def dummy(): pass
curdir = os.path.split(os.path.realpath(dummy.func_code.co_filename))[0]


data = [(1, 3.8395762658183231e-08), (2, 1.9505117165863341e-08), (3,
         1.3215350236350788e-08), (4, 1.0041898690360541e-08), (5,
         8.1796173390102925e-09), (6, 6.942110530872014e-09), (7,
         6.0128215295662806e-09), (8, 5.4064450694113475e-09), (9,
         4.9791879064287061e-09), (10, 4.6286913857329638e-09), (11,
         4.235708672695182e-09), (12, 4.1316774002098102e-09), (13,
         3.8893311682386408e-09), (14, 3.6563193361871527e-09), (15,
         3.6179656603962937e-09), (16, 3.3048685565972844e-09)]

data = data + \
        [(17,      3.39859127507e-09),
         (18,      3.41160273365e-09),
         (19,      3.36365388875e-09),
         (20,      3.20679234278e-09)]

#         (21,      3.19722559539e-09)]
#         (22,      3.00469338299e-09),
#         (23,      2.93840329846e-09),
#         (24,      3.01131350966e-09),
#         (25,      3.25918776412e-09),
#         (26,      3.19101189916e-09),
#         (27,      3.24854809719e-09),
#         (28,      2.9257254397e-09 ),
#         (29,      3.16017860769e-09),
#         (30,      3.00138012221e-09),
#         (31,      2.87957035994e-09)]


import pyx
# -------------------------------- 
# Performance plot
# --------------------------------
performance = []
ideal = []
i1,t1 = data[0]
Msite1 = (1/t1)/10**6
for i,t in data:
    Msite = (1/t)/10**6
    performance.append((i,Msite)) # Msite/sec
    ideal.append((i,Msite1*i))

d = pyx.graph.data.list(performance,x=0,y=1,
                        title="Parallel performance",addlinenumbers=0)
g = pyx.graph.graphxy(width=6) # rng[1]-1
g.plot(d) # use x marks
g.plot(d,[pyx.graph.style.line()]) # make lines

# plot ideal speedup too...
d = pyx.graph.data.list(ideal,x=0,y=1,
                        title="Ideal speedup",addlinenumbers=0)
g.plot(d,[pyx.graph.style.line()]) # make lines


g.writeEPSfile(os.path.join(curdir,fname))


# -------------------------------- 
# Speedup plot
fname = "parallelspeedup.eps"

speedup = []; t_cpu = data[0][1]
ideal = []
for i,t in data:
    speedup.append((i,t_cpu/t))
    ideal.append((i,i))
    
    
d = pyx.graph.data.list(speedup,x=0,y=1,
                        title="Parallel speedup",addlinenumbers=0)
g = pyx.graph.graphxy(width=6) # rng[1]-1
g.plot(d) # use x marks
g.plot(d,[pyx.graph.style.line()]) # make lines

# plot ideal speedup too...
d = pyx.graph.data.list(ideal,x=0,y=1,
                        title="Ideal speedup",addlinenumbers=0)
g.plot(d,[pyx.graph.style.line()]) # make lines
g.writeEPSfile(os.path.join(curdir,fname))

