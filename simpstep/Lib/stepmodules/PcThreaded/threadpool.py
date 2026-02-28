# threadpool.py
# modified by tbach
#   removed error and output handling
#   made it compatible with python2.2

# based on 
#   http://aspn.activestate.com/ASPN/Cookbook/Python/Recipe/303108

#   I am trying to show how to have a thread pool building on the recipe
#   in http://aspn.activestate.com/ASPN/Cookbook/Python/Recipe/302746.
#   This is a python class that essentially makes a thread pool for a
#   function you define. Like the earlier example, I want to show off the
#   power of having a thread pool that you can stop and start at
#   will. Interestingly, you can mimic more standard thread use with the
#   pool -- which I show off in as little as 3 lines of simple code.

import threading,Queue,time,sys,traceback

import sys # close threads on system exit...

class easy_pool:
    def __init__(self,func):
        self.Qin   = Queue.Queue()
        self.npending = 0 # number of pending jobs
        self.npending_lock = threading.Lock() # lock to protect it
        self.Pool = []   
        self.Func=func

        # make sure the threads stop at system exit ...
        oldexitfunc = sys.exitfunc
        def cleanup(self=self,last_exit=oldexitfunc):
          self.stop_threads()
          last_exit()
        sys.exitfunc = cleanup
        
    def process_queue(self):
        flag='ok'
        while flag !='stop':
            flag,item=self.Qin.get() #will wait here!
            if flag=='ok':
                try: self.Func(item)
                finally: # update the number of pending items
                   self.npending_lock.acquire(); self.npending-=1
                   self.npending_lock.release()

    def start_threads(self,num_threads=5):
        for i in range(num_threads):
             thread = threading.Thread(target=self.process_queue)
             thread.start()
             self.Pool.append(thread)
             
    def put(self,data,flag='ok'):
        self.npending_lock.acquire(); self.npending+=1
        self.npending_lock.release()
        self.Qin.put([flag,data]) 
        
    def stop_threads(self):
        for i in range(len(self.Pool)):
            self.Qin.put(('stop',None))
        while self.Pool:
            time.sleep(0.01)
            for index in xrange(len(self.Pool)):
                the_thread  = self.Pool[index]
                if the_thread.isAlive():
                    continue
                else:
                    del self.Pool[index]
                break
    
    def wait_for_idle(self):
        while self.Pool:
            if (self.Qin.empty() and self.npending==0):
                return
            time.sleep(0.001) # don't busy wait!

# ---------------------------------------------------------------- TEST
if __name__=="__main__":
  def work1(item):
#      time.sleep(0.1)      
      print 'hi '+item
      return 'hi '+item

  t=easy_pool(work1)    
  t.start_threads(2)

  t0 = time.time()  
  for i in ('a','b'): t.put(i)
  print "yo"
  t.wait_for_idle()
  print "idle"  
  print time.time()-t0
  t.stop_threads()
