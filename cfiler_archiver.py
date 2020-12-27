import os
import ctypes

import ckit

import cfiler_error


class ArchiverError(Exception):
    def __init__( self, errno ):
        self.errno = errno
    def __str__(self):
        return "ArchiverError : 0x%x" % self.errno

class ArchiverNotInstalledError(Exception):
    def __init__(self):
        pass


class Archiver:

    ERROR_PASSWORD_FILE     = 0x800A
    ERROR_FILE_CRC          = 0x800C
    ERROR_ALREADY_RUNNING   = 0x801F
    ERROR_USER_CANCEL       = 0x8020
    
    instance_table = {}
    
    def __init__( self, dllname, api_prefix, wchar_api ):

        for full_dllname in (os.path.join( ckit.getAppExePath(),"lib",dllname), dllname ):
            try:
                dll = ctypes.windll.LoadLibrary(full_dllname)
                break
            except OSError:
                pass
        else:
            print( "ERROR : ライブラリがインストールされていません : %s" % dllname )
            raise ArchiverNotInstalledError

        self.dll = dll
        
        self.wchar_api = wchar_api
        if wchar_api:
            wchar_api_suffix = "W"
        else:
            wchar_api_suffix = ""
        
        self._getVersion = getattr( dll, api_prefix + "GetVersion" )
        self._getRunning = getattr( dll, api_prefix + "GetRunning" )
        self._getBackGroundMode = getattr( dll, api_prefix + "GetBackGroundMode" )
        self._setBackGroundMode = getattr( dll, api_prefix + "SetBackGroundMode" )
        self._getCursorMode = getattr( dll, api_prefix + "GetCursorMode" )
        self._setCursorMode = getattr( dll, api_prefix + "SetCursorMode" )
        self._getCursorInterval = getattr( dll, api_prefix + "GetCursorInterval" )
        self._setCursorInterval = getattr( dll, api_prefix + "SetCursorInterval" )
        self._call = getattr( dll, api_prefix + wchar_api_suffix )
        self._checkArchive = getattr( dll, api_prefix + "CheckArchive" + wchar_api_suffix )
        self._getFileCount = getattr( dll, api_prefix + "GetFileCount" + wchar_api_suffix )
        self._queryFunctionList = getattr( dll, api_prefix + "QueryFunctionList" )
        self._configDialog = getattr( dll, api_prefix + "ConfigDialog" + wchar_api_suffix )
        #self._extractMem = getattr( dll, api_prefix + "ExtractMem" + wchar_api_suffix )
        #self._compressMem = getattr( dll, api_prefix + "CompressMem" + wchar_api_suffix )
        self._openArchive = getattr( dll, api_prefix + "OpenArchive" + wchar_api_suffix )
        self._closeArchive = getattr( dll, api_prefix + "CloseArchive" )
        self._findFirst = getattr( dll, api_prefix + "FindFirst" + wchar_api_suffix )
        self._findNext = getattr( dll, api_prefix + "FindNext" + wchar_api_suffix )
        self._getArcFileName = getattr( dll, api_prefix + "GetArcFileName" + wchar_api_suffix )
        self._getArcFileSize = getattr( dll, api_prefix + "GetArcFileSize" )
        self._getArcOriginalSize = getattr( dll, api_prefix + "GetArcOriginalSize" )
        self._getArcCompressedSize = getattr( dll, api_prefix + "GetArcCompressedSize" )
        self._getArcRatio = getattr( dll, api_prefix + "GetArcRatio" )
        self._getArcDate = getattr( dll, api_prefix + "GetArcDate" )
        self._getArcTime = getattr( dll, api_prefix + "GetArcTime" )
        self._getArcOSType = getattr( dll, api_prefix + "GetArcOSType" )
        self._getFileName = getattr( dll, api_prefix + "GetFileName" + wchar_api_suffix )
        self._getMethod = getattr( dll, api_prefix + "GetMethod" + wchar_api_suffix )
        self._getOriginalSize = getattr( dll, api_prefix + "GetOriginalSize" )
        self._getCompressedSize = getattr( dll, api_prefix + "GetCompressedSize" )
        self._getRatio = getattr( dll, api_prefix + "GetRatio" )
        self._getDate = getattr( dll, api_prefix + "GetDate" )
        self._getTime = getattr( dll, api_prefix + "GetTime" )
        #self._getWriteTime = getattr( dll, api_prefix + "GetWriteTime" )
        #self._getCreateTime = getattr( dll, api_prefix + "GetCreateTime" )
        #self._getAccessTime = getattr( dll, api_prefix + "GetAccessTime" )
        self._getCRC = getattr( dll, api_prefix + "GetCRC" )
        self._getAttribute = getattr( dll, api_prefix + "GetAttribute" )
        self._getOSType = getattr( dll, api_prefix + "GetOSType" )

        self._openArchive.restype = ctypes.c_void_p
    
    def getVersion(self):
        return self._getVersion()

    def getRunning(self):
        return self._getRunning()

        """
    def getBackgroundMode(self):
        return self._getBackGroundMode()

    def setBackgroundMode(self,mode):
        return self._setBackGroundMode(mode)

    def getCursorMode(self):
        return self._getCursorMode()

    def setCursorMode(self,mode):
        return self._setCursorMode(mode)

    def getCursorInterval(self):
        return self._getCursorInterval()

    def setCursorInterval(self,interval):
        return self._setCursorInterval(interval)

    def __call__( self, hwnd, cmdline, bufsize ):
        buf = ctypes.create_string_buffer(bufsize)
        ret = self._call( hwnd, cmdline, buf, bufsize )
        if ret : raise ArchiverError(ret)
        return buf.value

    def getFileCount( self, filename ):
        ret = self._getFileCount(filename)
        if ret<0 : raise ArchiverError(ret)
        return ret

    def queryFunctionList( self, func_id ):
        return self._queryFunctionList(func_id)

    def configDialog( self, hwnd, mode ):
        buf = ctypes.create_string_buffer(513)
        ret = self._configDialog( hwnd, buf, mode )
        if not ret : raise ArchiverError(False)
        return buf.value

    def extractMem( self, hwnd, cmdline, bufsize ):
        buf = ctypes.create_string_buffer(bufsize)
        ret = self._extractMem( hwnd, cmdline, buf, bufsize, None, None, None )
        if ret : raise ArchiverError(ret)
        return buf.value

    def compressMem( self, hwnd, cmdline, buf ):
        ret = self._compress( hwnd, cmdline, buf, len(buf), None, None, None )
        if ret : raise ArchiverError(ret)
        """

    def checkArchive( self, filename, mode ):
        return self._checkArchive( filename, mode )

    def openArchive( self, hwnd, filename, mode ):

        if self.wchar_api:
            pass
        else:
            filename = filename.encode('mbcs')

        class Archive:
    
            def __init__( arc_self, harc ):
                arc_self.harc = harc
    
            def iterItems( arc_self, wildname ):

                if self.wchar_api:
                    pass
                else:
                    wildname = wildname.encode('mbcs')

                FNAME_MAX32 = 512

                if self.wchar_api:
                    class INDIVIDUALINFO(ctypes.Structure):
                        _fields_ = [("dwOriginalSize", ctypes.c_int),
                                    ("dwCompressedSize", ctypes.c_int),
                                    ("dwCRC", ctypes.c_int),
                                    ("uFlag", ctypes.c_int),
                                    ("uOSType", ctypes.c_int),
                                    ("wRatio", ctypes.c_int16),
                                    ("wDate", ctypes.c_int16),
                                    ("wTime", ctypes.c_int16),
                                    ("szFileName", ctypes.c_wchar * (FNAME_MAX32 + 1)),
                                    ("dummy1", ctypes.c_wchar * 3),
                                    ("szAttribute", ctypes.c_wchar * 8),
                                    ("szMode", ctypes.c_wchar * 8)]
                else:
                    class INDIVIDUALINFO(ctypes.Structure):
                        _fields_ = [("dwOriginalSize", ctypes.c_int),
                                    ("dwCompressedSize", ctypes.c_int),
                                    ("dwCRC", ctypes.c_int),
                                    ("uFlag", ctypes.c_int),
                                    ("uOSType", ctypes.c_int),
                                    ("wRatio", ctypes.c_int16),
                                    ("wDate", ctypes.c_int16),
                                    ("wTime", ctypes.c_int16),
                                    ("szFileName", ctypes.c_char * (FNAME_MAX32 + 1)),
                                    ("dummy1", ctypes.c_char * 3),
                                    ("szAttribute", ctypes.c_char * 8),
                                    ("szMode", ctypes.c_char * 8)]
            
                info = INDIVIDUALINFO()
                
                dirs = {}
                
                ret = self._findFirst( ctypes.c_void_p(arc_self.harc), wildname, ctypes.byref(info) )
                while ret==0:

                    name = info.szFileName

                    if not self.wchar_api:
                        name = name.decode("mbcs")

                    mtime = (
                        ((info.wDate >> 9)  & 0x3f) + 1980,
                        (info.wDate >> 5)   & 0x0f,
                        (info.wDate)        & 0x1f,
                        (info.wTime >> 11)  & 0x1f,
                        (info.wTime >> 5)   & 0x3f,
                        (info.wTime << 1)   & 0x3f
                        )

                    if name[-1]=='/' or name[-1]=='\\':
                        name = os.path.normpath(name[:-1])
                        attr = ckit.FILE_ATTRIBUTE_DIRECTORY
                    elif info.szAttribute[0]=='d':
                        name = os.path.normpath(name)
                        attr = ckit.FILE_ATTRIBUTE_DIRECTORY
                    else:
                        name = os.path.normpath(name)
                        attr = 0

                    # ディレクトリを生成する
                    d_joint = ""
                    parent, _name = os.path.split(name)
                    if parent:
                        for d in os.path.normpath(parent).split("\\"):
                            d_joint = os.path.join(d_joint,d)
                            if not d_joint in dirs:
                                dirs[d_joint] = None
                                #print( "gen", d_joint )
                                yield ( d_joint, 0, mtime, ckit.FILE_ATTRIBUTE_DIRECTORY )

                    if attr & ckit.FILE_ATTRIBUTE_DIRECTORY:
                        if not name in dirs:
                            dirs[name] = None
                            #print( "ret", name )
                            yield ( name, info.dwOriginalSize, mtime, attr )
                    else:
                        #print( "ret", name )
                        yield ( name, info.dwOriginalSize, mtime, attr )

                    ret = self._findNext( ctypes.c_void_p(arc_self.harc), ctypes.byref(info) )

            def close(arc_self):
                self._closeArchive( ctypes.c_void_p(arc_self.harc) )

        if self.getRunning():
            print( "ERROR : ライブラリを並列に使用できません." )
            raise ArchiverError(Archiver.ERROR_ALREADY_RUNNING)

        harc = self._openArchive( hwnd, filename, mode )
        if not harc:
            raise ArchiverError(0)
        return Archive(harc)

    @staticmethod
    def getInstance(archiver_class):
        try:
            instance = Archiver.instance_table[archiver_class]
        except KeyError:
            instance = archiver_class()
            Archiver.instance_table[archiver_class] = instance
        return instance


class LhaArchiver(Archiver):
    
    def __init__(self):
        Archiver.__init__( self, "unlha32.dll", "Unlha", True )
        
    def extract( self, hwnd, filename, dst_dirname, name ):
    
        dst_dirname = os.path.normpath(dst_dirname)
        if dst_dirname[-1]!="\\":
            dst_dirname += "\\"

        cmdline = 'e -+1 -n1 "%s" "%s" "%s" -p' % ( filename, dst_dirname, name )
        #print( cmdline )
        
        buf = ctypes.create_unicode_buffer(1024)
        ret = self._call( None, cmdline, buf, 1024 )
        if ret in ( Archiver.ERROR_USER_CANCEL, Archiver.ERROR_PASSWORD_FILE, Archiver.ERROR_FILE_CRC ):
            raise cfiler_error.CanceledError
        elif ret:
            raise ArchiverError(ret)

    def extractAll( self, hwnd, filename, dst_dirname ):

        dst_dirname = os.path.normpath(dst_dirname)
        if dst_dirname[-1]!="\\":
            dst_dirname += "\\"

        cmdline = 'x -+1 -m0 -jyc "%s" "%s"' % ( filename, dst_dirname )
        #print( cmdline )
        
        buf = ctypes.create_unicode_buffer(1024)
        ret = self._call( hwnd, cmdline, buf, 1024 )
        if ret in ( Archiver.ERROR_USER_CANCEL, Archiver.ERROR_PASSWORD_FILE, Archiver.ERROR_FILE_CRC ):
            raise cfiler_error.CanceledError
        elif ret:
            raise ArchiverError(ret)

    def create( self, filename, basepath, items ):
    
        basepath = os.path.normpath(basepath)
        if basepath[-1]!="\\":
            basepath += "\\"

        cmdline_items = ""
        for item in items:
            cmdline_items += ' "%s"' % item

        cmdline = 'a -+1 -x1 -r2 "%s" "%s" %s' % ( filename, basepath, cmdline_items )
        #print( cmdline )
        
        buf = ctypes.create_unicode_buffer(1024)
        ret = self._call( None, cmdline, buf, 1024 )
        if ret==Archiver.ERROR_USER_CANCEL:
            raise cfiler_error.CanceledError
        elif ret:
            raise ArchiverError(ret)


class TarBaseArchiver(Archiver):
    
    def __init__( self, mode="z" ):
        Archiver.__init__( self, "tar64.dll", "Tar", False )
        self.mode = mode

    def extract( self, hwnd, filename, dst_dirname, name ):

        dst_dirname = os.path.normpath(dst_dirname)
        if dst_dirname[-1]!="\\":
            dst_dirname += "\\"

        cmdline = '-xf "%s" -o "%s" "%s" --use-directory=0' % ( filename, dst_dirname, name )
        #print( cmdline )
        
        cmdline = cmdline.encode("mbcs")

        buf = ctypes.create_unicode_buffer(1024)
        ret = self._call( None, cmdline, buf, 1024 )
        if ret in ( Archiver.ERROR_USER_CANCEL, Archiver.ERROR_PASSWORD_FILE, Archiver.ERROR_FILE_CRC ):
            raise cfiler_error.CanceledError
        elif ret:
            raise ArchiverError(ret)

    def extractAll( self, hwnd, filename, dst_dirname ):

        dst_dirname = os.path.normpath(dst_dirname)
        if dst_dirname[-1]!="\\":
            dst_dirname += "\\"

        cmdline = '-xf "%s" -o "%s" --confirm-overwrite=1' % ( filename, dst_dirname )
        #print( cmdline )

        cmdline = cmdline.encode("mbcs")

        buf = ctypes.create_unicode_buffer(1024)
        ret = self._call( hwnd, cmdline, buf, 1024 )
        if ret in ( Archiver.ERROR_USER_CANCEL, Archiver.ERROR_PASSWORD_FILE, Archiver.ERROR_FILE_CRC ):
            raise cfiler_error.CanceledError
        elif ret:
            raise ArchiverError(ret)

    def create( self, filename, basepath, items ):

        basepath = os.path.normpath(basepath)
        if basepath[-1]!="\\":
            basepath += "\\"

        cmdline_items = ""
        for item in items:
            cmdline_items += ' "%s"' % item

        cmdline = '-c%sf "%s" "%s" %s' % ( self.mode, filename, basepath, cmdline_items )

        cmdline = cmdline.encode("mbcs")

        buf = ctypes.create_unicode_buffer(1024)
        ret = self._call( None, cmdline, buf, 1024 )
        
        if ret:
            os.unlink(filename)
        
        if ret==Archiver.ERROR_USER_CANCEL:
            raise cfiler_error.CanceledError
        elif ret:
            raise ArchiverError(ret)


class TgzArchiver(TarBaseArchiver):
    def __init__(self):
        TarBaseArchiver.__init__( self, "z" )


class Bz2Archiver(TarBaseArchiver):
    def __init__(self):
        TarBaseArchiver.__init__( self, "B" )


class RarArchiver(Archiver):
    
    def __init__(self):
        Archiver.__init__( self, "unrar32.dll", "Unrar", False )
        
    def extract( self, hwnd, filename, dst_dirname, name ):

        dst_dirname = os.path.normpath(dst_dirname)
        if dst_dirname[-1]!="\\":
            dst_dirname += "\\"

        cmdline = '-e -q "%s" "%s" "%s"' % ( filename, dst_dirname, name )
        #print( cmdline )
        
        cmdline = cmdline.encode("mbcs")

        buf = ctypes.create_string_buffer(1024)
        ret = self._call( None, cmdline, buf, 1024 )
        if ret in ( Archiver.ERROR_USER_CANCEL, Archiver.ERROR_PASSWORD_FILE, Archiver.ERROR_FILE_CRC ):
            raise cfiler_error.CanceledError
        elif ret:
            raise ArchiverError(ret)

    def extractAll( self, hwnd, filename, dst_dirname ):

        dst_dirname = os.path.normpath(dst_dirname)
        if dst_dirname[-1]!="\\":
            dst_dirname += "\\"

        cmdline = '-x "%s" "%s" *' % ( filename, dst_dirname )
        #print( cmdline )
        
        cmdline = cmdline.encode("mbcs")

        buf = ctypes.create_string_buffer(1024)
        ret = self._call( hwnd, cmdline, buf, 1024 )
        if ret in ( Archiver.ERROR_USER_CANCEL, Archiver.ERROR_PASSWORD_FILE, Archiver.ERROR_FILE_CRC ):
            raise cfiler_error.CanceledError
        elif ret:
            raise ArchiverError(ret)


class SevenZipBaseArchiver(Archiver):

    def __init__( self, mode="7z" ):
        Archiver.__init__( self, "7-zip64.dll", "SevenZip", False )
        self.mode = mode
        
    def extract( self, hwnd, filename, dst_dirname, name ):

        dst_dirname = os.path.normpath(dst_dirname)
        if dst_dirname[-1]!="\\":
            dst_dirname += "\\"

        cmdline = 'e "%s" "%s" "%s" -hide' % ( filename, dst_dirname, name )
        #print( cmdline )
        
        cmdline = cmdline.encode("mbcs")

        buf = ctypes.create_string_buffer(1024)
        ret = self._call( None, cmdline, buf, 1024 )
        if ret in ( Archiver.ERROR_USER_CANCEL, Archiver.ERROR_PASSWORD_FILE, Archiver.ERROR_FILE_CRC ):
            raise cfiler_error.CanceledError
        elif ret:
            raise ArchiverError(ret)

    def extractAll( self, hwnd, filename, dst_dirname ):

        dst_dirname = os.path.normpath(dst_dirname)
        if dst_dirname[-1]!="\\":
            dst_dirname += "\\"

        cmdline = 'x "%s" "%s" *' % ( filename, dst_dirname )
        #print( cmdline )

        cmdline = cmdline.encode("mbcs")

        buf = ctypes.create_string_buffer(1024)
        ret = self._call( hwnd, cmdline, buf, 1024 )
        if ret in ( Archiver.ERROR_USER_CANCEL, Archiver.ERROR_PASSWORD_FILE, Archiver.ERROR_FILE_CRC ):
            raise cfiler_error.CanceledError
        elif ret:
            raise ArchiverError(ret)

    def create( self, filename, basepath, items ):
    
        basepath = os.path.normpath(basepath)
        if basepath[-1]!="\\":
            basepath += "\\"

        cmdline_items = ""
        for item in items:
            cmdline_items += ' "%s"' % item

        if self.mode=="7z":
            cmdline = 'a -t7z "%s" "%s" %s -ms=off -ssw' % ( filename, basepath, cmdline_items )
        elif self.mode=="zip":
            cmdline = 'a -tzip "%s" "%s" %s -ssw' % ( filename, basepath, cmdline_items )
        #print( cmdline )
        
        cmdline = cmdline.encode("mbcs")

        buf = ctypes.create_unicode_buffer(1024)
        ret = self._call( None, cmdline, buf, 1024 )
        if ret==Archiver.ERROR_USER_CANCEL:
            raise cfiler_error.CanceledError
        elif ret:
            raise ArchiverError(ret)


class ZipArchiver(SevenZipBaseArchiver):
    def __init__(self):
        SevenZipBaseArchiver.__init__( self, "zip" )


class SevenZipArchiver(SevenZipBaseArchiver):
    def __init__(self):
        SevenZipBaseArchiver.__init__( self, "7z" )

