import numarray

parity3dresults = [

    [[[1,0,0],
      [0,0,0],
      [0,0,0]],
     [[0,0,0],
      [0,0,0],
      [0,0,0]],     
     [[0,0,0],
      [0,0,0],
      [0,0,0]]],     

    [[[1,1,1],
      [1,0,0],
      [1,0,0]],
     [[1,0,0],
      [0,0,0],
      [0,0,0]],     
     [[1,0,0],
      [0,0,0],
      [0,0,0]]],     

    [[[1,1,1],
      [1,0,0],
      [1,0,0]],
     [[1,0,0],
      [0,0,0],
      [0,0,0]],     
     [[1,0,0],
      [0,0,0],
      [0,0,0]]]]     

for i in xrange(len(parity3dresults)):
    parity3dresults[i] = numarray.array(parity3dresults[i])


parity2dresults = [

     [[1,0,0],
      [0,0,0],
      [0,0,0]],
     
     [[1,1,1],
      [1,0,0],
      [1,0,0]],
     
     [[1,1,1],
      [1,0,0],
      [1,0,0]]]     

for i in xrange(len(parity2dresults)):
    parity2dresults[i] = numarray.array(parity2dresults[i])


