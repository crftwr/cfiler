import os

#--------------------------------------------------------------------

lock_list = []

def lock( path ):
    path = os.path.normpath(path)
    lock_list.append( path )

def unlock( path ):
    path = os.path.normpath(path)
    lock_list.remove( path )
    
def locked( path ):
    path = os.path.normpath(path)
    for lock_item in lock_list:
        if path == lock_item : return True
        if lock_item[-1]!='\\':
            lock_item += '\\'
        if path.startswith(lock_item) : return True
    return False

# ファイルやディレクトリの変更を一時的に禁止する
class Lock:
    def __init__( self, path ):
        self.path = path
        lock(self.path)
    def __del__( self ):
        unlock(self.path)
