import configparser

import cfiler_error

class History:

    def __init__( self, maxnum=100 ):
        self.items = []
        self.maxnum = maxnum

    def append( self, newentry ):
    
        for i in range(len(self.items)):
            if self.items[i]==newentry:
                del self.items[i]
                break
        self.items.insert( 0, newentry )

        if len(self.items)>self.maxnum:
            self.items = self.items[:self.maxnum]

    def remove( self, entry ):
        for i in range(len(self.items)):
            if self.items[i]==entry:
                del self.items[i]
                return
        raise KeyError        

    def save( self, ini, section ):
        i=0
        while i<len(self.items):
            ini.set( section, "history_%d"%(i,), self.items[i] )
            i+=1

        while True:
            if not ini.remove_option( section, "history_%d"%(i,) ) : break
            i+=1

    def load( self, ini, section ):
        for i in range(self.maxnum):
            try:
                self.items.append( ini.get( section, "history_%d"%(i,) ) )
            except configparser.NoOptionError:
                break

    def candidateHandler( self, update_info ):

        left = update_info.text[ : update_info.selection[0] ]
        left_lower = left.lower()

        candidate_list = []

        for item in self.items:
            item_lower = item.lower()
            if item_lower.startswith(left_lower) and len(item_lower)!=len(left_lower):
                candidate_list.append( item )

        return candidate_list, 0

    def candidateRemoveHandler( self, text ):
        try:
            self.remove( text )
            return True
        except KeyError:
            pass
        return False        
