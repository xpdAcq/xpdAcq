import numpy as np
from time import sleep

class mock_shutter():
    def put(self,value):
        pass
    def get(self,status=1):
        # this will keep returning 0 or 1 until the calling program is satisfied
        callback = np.random.randint(2)
        #sleep(0.1)
        return callback

class mock_livetable():
    def __init__(self,mylist):
    	self.mylist = mylist


