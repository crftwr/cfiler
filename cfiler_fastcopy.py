import threading

# ファイルのReadとWriteを並列化することでコピーを高速化するためのクラス
class FastCopyReadThread(threading.Thread):

    data_list_max = 4

    def __init__( self, fd, read_unit=1024*1024 ):

        threading.Thread.__init__(self)

        self.cancel_requested = False

        self.lock = threading.Lock()
        self.cond_not_full = threading.Condition(self.lock)
        self.cond_not_empty = threading.Condition(self.lock)

        self.data_list = []
        self.fd = fd
        self.read_unit = read_unit

    def run(self):

        self.lock.acquire()

        try:
            while True:

                while len(self.data_list)>=FastCopyReadThread.data_list_max and not self.cancel_requested:
                    self.cond_not_full.wait()

                if self.cancel_requested : break

                self.lock.release()
                try:
                    data = self.fd.read(self.read_unit)
                finally:
                    self.lock.acquire()
                
                self.data_list.append(data)

                self.cond_not_empty.notify()

                if not data:
                    break
        finally:
            self.lock.release()

    def cancel(self):
        self.cancel_requested = True
        self.cond_not_full.notify()

    def getData(self):

        self.lock.acquire()

        try:
            
            while len(self.data_list) == 0:
                self.cond_not_empty.wait()
        
            data = self.data_list[0]
            del self.data_list[0]

            self.cond_not_full.notify()

        finally:
            self.lock.release()
        
        return data

