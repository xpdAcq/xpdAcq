import numpy as np
from time import sleep


class mock_shutter():
    def put(self,value):
        pass
    def get(self,status=1):
        # this will keep returning 0 or 1 until the calling program is satisfied
        callback = round(np.random.rand())
        sleep(0.1)
        return callback

