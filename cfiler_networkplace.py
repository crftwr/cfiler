import os
import time
import shutil
import datetime
import urlparse
import comtypes.client

import ckit

import cfiler_filelist
import cfiler_fileoplock
import cfiler_misc
import cfiler_error
import cfiler_debug

#--------------------------------------------------------------------

# FTP/WebDav上のファイルを表すアイテム
class item_NetworkPlace(cfiler_filelist.item_CommonPaint):

    def __init__( self, location, username, password, name, obj ):

        self.location = location
        self.username = username
        self.password = password
        self.name = name
        self.obj = obj

        self._size = obj.Size
        mtime = datetime.datetime( 1900, 1, 1 ) + datetime.timedelta( obj.ModifyDate )
        self._mtime = [ mtime.year, mtime.month, mtime.day, mtime.hour, mtime.minute, mtime.second ]

        self._selected = False

    def __str__(self):
        return urlparse.urljoin( self.location + "/", self.name )

    def getName(self):
        return self.name

    def time(self):
        assert( type(self._mtime)==tuple )
        return self._mtime

    def size(self):
        return self._size

    def attr(self):
        return 0

    def isdir(self):
        return self.obj.IsFolder

    def ishidden(self):
        return False

    def _select( self, sel=None ):
        if sel==None:
            self._selected = not self._selected
        else:
            self._selected = sel;

    def selected(self):
        return self._selected

    def bookmark(self):
        return False

    def lock(self):
        return cfiler_fileoplock.Lock( os.path.join(self.location,self.name) )

    def walk( self, topdown=True ):

        location = self.location
        username = self.username
        password = self.password

        class packItem:

            def __init__( self, dirname ):
                self.dirname = dirname

            def __call__( self, item ):

                filename = item.Name

                item = item_NetworkPlace(
                    location,
                    username,
                    password,
                    os.path.join( self.dirname, filename ),
                    item
                    )

                return item

        def walkRecursive( dirname, parent ):
            
            dirs = []
            files = []

            for item in parent.GetFolder.Items():

                if item.IsFolder:
                    dirs.append(item)
                else:
                    files.append(item)

            if topdown:
                yield dirname, map(packItem(dirname),dirs), map(packItem(dirname),files)

            for item in dirs:
                for ret in walkRecursive( os.path.join(dirname,item.Name), item ):
                    yield ret

            if not topdown:
                yield dirname, map(packItem(dirname),dirs), map(packItem(dirname),files)

        for ret in walkRecursive( self.obj.Name, self.obj ):
            yield ret

    def delete( self, recursive, item_filter, schedule_handler, log_writer=None ):

        comtypes.CoInitializeEx(comtypes.COINIT_MULTITHREADED)
        try:
            if not log_writer:
                def logWriter(s) : pass
                log_writer = logWriter

            def remove_file( filename, item ):
                log_writer( 'ファイル削除 : %s …' % filename )
                try:
                    for i in item.Verbs():
                        if i.Name.find("&D")>=0:
                            item.InvokeVerb(i.Name)
                            break
                except Exception as e:
                    cfiler_debug.printErrorInfo()
                    log_writer( '失敗\n' )
                    log_writer( "  %s\n" % str(e) )
                else:
                    log_writer( '完了\n' )

            def remove_dir( filename, item ):
            
                log_writer( 'ディレクトリ削除 : %s …' % filename )

                if len(item.GetFolder.Items())>0:
                    log_writer( '空ではない\n' )
                    return

                try:
                    for i in item.Verbs():
                        if i.Name.find("&D")>=0:
                            item.InvokeVerb(i.Name)
                            break
                except Exception as e:
                    cfiler_debug.printErrorInfo()
                    log_writer( '失敗\n' )
                    log_writer( "  %s\n" % str(e) )
                else:
                    log_writer( '完了\n' )

            if self.obj.IsFolder:

                if recursive:

                    def walk( dirname, parent ):
                
                        dirs = []
                        files = []
                
                        for item in parent.GetFolder.Items():

                            if item.IsFolder:
                        
                                for i in walk( os.path.join(dirname,item.Name), item ):
                                    yield i
                        
                                dirs.append(item)
                            else:
                                files.append(item)
                    
                        yield dirname, parent, dirs, files

                    for dirname, parent, dirs, files in walk( os.path.join(self.location,self.obj.Name), self.obj ):
                        if schedule_handler(): return
                        for item in files:
                            if schedule_handler(): return
                            if item_filter==None or item_filter( item_NetworkPlace(dirname,self.username,self.password,item.Name,item) ):
                                remove_file( os.path.join(dirname,item.Name), item )
                        if schedule_handler(): return
                        remove_dir( dirname, parent )

                else:
                    remove_dir( urlparse.urljoin(self.location+"/",self.name), self.obj )

            else:
                remove_file( urlparse.urljoin(self.location+"/",self.name), self.obj )

        finally:
            comtypes.CoUninitialize()

    def open(self):
    
        class File:
            def __init__( self, buf ):
                self.buf = buf
                self.pos = 0

            def seek( self, offset ):
                self.pos = offset

            def tell(self):
                return self.pos

            def read( self, size=-1 ):
                if size>=0:
                    buf = self.buf[ self.pos : self.pos + size ]
                    self.pos += size
                else:
                    buf = self.buf[ self.pos : ]
                    self.pos = len(self.buf)
                return buf

            def close( self ):
                del self.buf
                self.pos = 0
    
        
        comtypes.CoInitializeEx(comtypes.COINIT_MULTITHREADED)
        try:
            tmp_dir_path = ckit.makeTempDir( "networkplace_" )
            path = os.path.abspath( os.path.normpath(tmp_dir_path) )
            shell_app = comtypes.client.CreateObject("Shell.Application")

            tmp_folder = shell_app.NameSpace(path)
    
            tmp_folder.CopyHere(self.obj)
            path = os.path.join( path, os.path.split(self.name)[1] )

            # FTP/WebDAV の CopyHere は非同期なので、コピー完了まで待つ
            while 1:
                if os.path.exists(path):
                    if os.path.getsize(path)>=self.obj.Size : break
                time.sleep(0.1)
    
            fd = File( open(path,"rb").read() )
            shutil.rmtree(tmp_dir_path,ignore_errors=True)
            return fd
        
        finally:
            comtypes.CoUninitialize()

# FTP/WebDavのディレクトリのリストアップ機能
class lister_NetworkPlace(cfiler_filelist.lister_Base):

    def __init__( self, main_window, location, username, password ):
        self.main_window = main_window
        self.location = location
        self.username = username
        self.password = password
        
        shell_app = comtypes.client.CreateObject("Shell.Application")
        self.folder_obj = shell_app.NameSpace(self._url())
        
    def __call__( self ):

        def packListItem( fileinfo ):

            item = item_NetworkPlace(
                self.location,
                self.username,
                self.password,
                fileinfo.Name,
                fileinfo,
                )

            return item

        items = map( packListItem, self.folder_obj.Items() )

        return items

    def cancel(self):
        pass

    def _url(self):
        parsed_url = list( urlparse.urlparse(self.location) )
        parsed_url[1] = "%s:%s@%s" % ( self.username, self.password, parsed_url[1] )
        return urlparse.urlunparse(parsed_url)

    def __str__(self):
        return self.location

    def getLocation(self):
        return self.location

    def isLazy(self):
        return False

    def isChanged(self):
        return False

    def getCopy( self, name ):
        return ( lister_NetworkPlace( self.main_window, self.location, self.username, self.password ), name )

    def getChild( self, name ):
        parsed_url = list(urlparse.urlparse(self.location))
        parsed_url[2] = os.path.join( parsed_url[2], name )
        parsed_url[2] = parsed_url[2].replace("\\","/")
        new_location = urlparse.urlunparse(parsed_url)
        return lister_NetworkPlace( self.main_window, new_location, self.username, self.password )

    def getParent(self):
        parsed_url = list(urlparse.urlparse(self.location))
        parent, name = os.path.split(parsed_url[2])
        if not name:
            raise cfiler_error.NotExistError
        parsed_url[2] = parent
        new_location = urlparse.urlunparse(parsed_url)
        return ( lister_NetworkPlace( self.main_window, new_location, self.username, self.password ), name )

    def getRoot(self):
        parsed_url = list(urlparse.urlparse(self.location))
        parsed_url[2] = "/"
        new_location = urlparse.urlunparse(parsed_url)
        return lister_NetworkPlace( self.main_window, new_location, self.username, self.password )

    def mkdir( self, name, log_writer=None ):

        comtypes.CoInitializeEx(comtypes.COINIT_MULTITHREADED)
        try:
            if not log_writer:
                def logWriter(s) : pass
                log_writer = logWriter

            fullpath = ckit.joinPath( self.location, name )
            log_writer( 'ディレクトリ作成 : %s …' % fullpath )

            if self.exists(name):
                log_writer( 'すでに存在\n' )
                return

            dirs = []
            for i in name.split("\\"):
                dirs += i.split("/")

            folder_obj = self.folder_obj
            for dirname in dirs:
        
                already_exist = False
                for i in folder_obj.Items():
                    if i.Name.lower()==dirname.lower():
                        already_exist = True
                        break

                if not already_exist:
                
                    # NewFolder は サポートされていないので、CopyHereをつかってディレクトリ作成を模倣する
                    tmp_dir_path = cfiler_misc.makeTempDir( "networkplace_" )
                    tmp_dir_path2 = os.path.join( tmp_dir_path, dirname )
                    os.mkdir(tmp_dir_path2)
                    tmp_dir_path2 = os.path.abspath( os.path.normpath(tmp_dir_path2) )
       
                    result = folder_obj.CopyHere(tmp_dir_path2)

                    # CopyHere は非同期なので、実際にコピーが完了するまで待つ
                    while 1:
                        exist = False
                        for i in folder_obj.Items():
                            if i.Name.lower()==dirname.lower():
                                exist = True
                                break
                        if exist : break
                        time.sleep(0.1)

                    # CopyHere が実際に完了するタイミングがわからないので、ここで削除しない
                    #shutil.rmtree(tmp_dir_path,ignore_errors=True)
            
                    if result : break

                for i in folder_obj.Items():
                    if i.Name.lower()==dirname.lower():
                        folder_obj = i.GetFolder
                        break
        
            if result:
                log_writer( '失敗\n' )
            else:
                log_writer( '完了\n' )

        finally:
            comtypes.CoUninitialize()

    def exists( self, name ):

        comtypes.CoInitializeEx(comtypes.COINIT_MULTITHREADED)
        try:
            parsed_url = list( urlparse.urlparse(self.location) )
            parsed_url[1] = "%s:%s@%s" % ( self.username, self.password, parsed_url[1] )
            parsed_url[2] = os.path.join( parsed_url[2], os.path.split(name)[0] )
            url = urlparse.urlunparse(parsed_url)

            shell_app = comtypes.client.CreateObject("Shell.Application")
            folder_obj = shell_app.NameSpace(url)
        
            for i in folder_obj.Items():
                if i.Name.lower() == os.path.split(name)[1].lower():
                    item = item_NetworkPlace(
                        self.location,
                        self.username,
                        self.password,
                        name,
                        i,
                        )
                    return item

            return None
        
        finally:
            comtypes.CoUninitialize()

    def locked(self):
        return cfiler_fileoplock.locked(self.location)

    def unlink( self, name ):
        dir_obj, file_obj = self._step(self.folder_obj,name)
        if file_obj:
            file_obj.InvokeVerb("&Delete")
        else:
            raise IOError( "file does not exist. [%s]" % name )

    def getCopyDst( self, name ):
    
        class File:

            def __init__( self, folder_obj, name ):
                self.folder_obj = folder_obj
                self.tmp_dir_path = cfiler_misc.makeTempDir( "networkplace_" )
                self.path = os.path.join( self.tmp_dir_path, name )
                self.fd = open( self.path, "wb" )
        
            def write( self, buf ):
                self.fd.write(buf)
        
            def close(self):

                self.fd.close()
                path = os.path.abspath( os.path.normpath(self.path) )
                self.folder_obj.CopyHere(path)

                # CopyHere は非同期なので、実際にコピーが完了するまで待つ
                while 1:
                    done = False
                    for i in self.folder_obj.Items():
                        if i.Name.lower()==os.path.split(self.path)[1].lower():
                            if i.Size==os.path.getsize(path):
                                done = True
                                break
                    if done : break
                    time.sleep(0.1)

                # CopyHere が実際に完了するタイミングがわからないので、ここで削除しない
                #shutil.rmtree(self.tmp_dir_path,ignore_errors=True)

        # FIXME : 深い場所    
        #folder_obj, file_obj = self._step( self.folder_obj, name )

        return File( self.folder_obj, os.path.split(name)[1] )
