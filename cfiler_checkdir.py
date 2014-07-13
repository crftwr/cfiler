import os
import time
import threading

import ckit

# FIXME : 実装
if os.name=="nt":
    import cfiler_native

class CheckDirThread( threading.Thread ):

    def __init__( self, path ):
        
        threading.Thread.__init__(self)
        
        self.setName(path)
        self.path = path
        self.cancel_requested = False
        self.changed = False
        self.check_dir = None

    def run(self):
        
        if os.name!="nt":
            return

        ckit.setBlockDetector()

        try:
            self.check_dir = cfiler_native.CheckDir(self.path)
        except WindowsError:
            return

        while True:
    
            if self.cancel_requested : break
            self.check_dir.wait()
            self.changed = True
            
            # 最短でもでも3秒間隔
            for i in range(30):
                if self.cancel_requested : break
                time.sleep(0.1)

    def cancel(self):
        self.cancel_requested = True
        if self.check_dir:
            self.check_dir.close()
    
    def isChanged(self):
        ret = self.changed
        self.changed = False
        return ret
