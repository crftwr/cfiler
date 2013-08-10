import os
import configparser

import ckit

import cfiler_error
import cfiler_debug

class Bookmark:

    def __init__(self):
        self.item_list = []
        self.item_table = {}
        self.drive_checked_table = {}

    def listDir( self, dirname ):
        dirname = dirname.lower()
        try:
            return self.item_table[dirname]
        except KeyError:
            return {}

    def getItems(self):
        return self.item_list

    def append( self, path, back=False ):
    
        path = ckit.normPath(path)
        dirname, filename = ckit.splitPath(path)
        dirname = dirname.lower()
        filename = filename.lower()

        try:
            dir_table = self.item_table[dirname]
        except KeyError:
            self.item_table[dirname] = {}
            dir_table = self.item_table[dirname]

        if filename in dir_table:
            for i in range(len(self.item_list)):
                if self.item_list[i].lower() == path.lower():
                    del self.item_list[i]
                    break
        else:
            dir_table[filename] = None

        if back:
            self.item_list.append(path)
        else:
            self.item_list.insert( 0, path )

    def remove( self, path ):
    
        path = ckit.normPath(path)
        dirname, filename = ckit.splitPath(path)
        dirname = dirname.lower()
        filename = filename.lower()

        try:
            dir_table = self.item_table[dirname]
            del dir_table[filename]
            for i in range(len(self.item_list)):
                if self.item_list[i].lower() == path.lower():
                    del self.item_list[i]
                    break
        except Exception:
            cfiler_debug.printErrorInfo()

    def removeNotExists( self, top, cache=True ):
    
        top = ckit.normPath(top)
        
        if cache and top in self.drive_checked_table:
            return
        
        def driveExistsButFileNotExists(path):

            drive, tmp = os.path.splitdrive(path)
            unc = os.path.splitunc(path)

            if not os.path.exists(path):
                if drive:
                    if os.path.exists(drive):
                        return True
                if unc[0]:
                    if os.path.exists(unc[0]):
                        return True
            return False            
    
        for path in self.item_list[:]:
            if path.startswith(top):
                if driveExistsButFileNotExists(path):
                    self.remove(path)
        
        if cache:
            self.drive_checked_table[top] = True

    def save( self, ini, section ):
        i=0
        while i<len(self.item_list):
            ini.set( section, "bookmark_%d"%(i,), self.item_list[i] )
            i+=1

        while True:
            if not ini.remove_option( section, "bookmark_%d"%(i,) ) : break
            i+=1

    def load( self, ini, section ):
        i=0
        while True:
            try:
                self.append( ckit.normPath( ini.get( section, "bookmark_%d"%(i,) )), back=True )
            except configparser.NoOptionError:
                break
            i+=1
