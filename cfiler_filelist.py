import os
import stat
import gc
import copy
import shutil
import fnmatch
import time
import io
import threading
import functools
import unicodedata

import ckit
from ckit.ckit_const import *

import cfiler_native
import cfiler_misc
import cfiler_fileoplock
import cfiler_mainwindow
import cfiler_checkdir
import cfiler_archiver
import cfiler_error
import cfiler_debug

## @addtogroup filelist
## @{

#--------------------------------------------------------------------

## アイテムのリストアップ機能のベースクラス
class lister_Base:

    def __init__(self):
        pass
    
    def destroy(self):
        pass

    def __call__( self ):
        return []

    def cancel(self):
        pass

    def __str__(self):
        return ""
    
    def getLocation(self):
        return ""

    def isLazy(self):
        return True

    def isChanged(self):
        return False

    def getCopy( self, name ):
        return ( lister_Base(), name )

    def getChild( self, name ):
        return lister_Base()

    def getParent(self):
        return ( lister_Base(), "" )

    def getRoot(self):
        return lister_Base()

    def locked(self):
        return False

## アイテムのベースクラス
class item_Base:

    def __init__(self):
        pass

    def __str__(self):
        return ""

    def getName(self):
        return ""

    def time(self):
        return (0,0,0,0,0,0)

    def size(self):
        return 0

    def attr(self):
        return 0

    def isdir(self):
        return False

    def ishidden(self):
        return False

    def _select( self, sel=None ):
        pass

    def selected(self):
        return False

    def bookmark(self):
        return False

    def setTextPoint( self, text_point ):
        self.text_point = text_point

    def getTextPoint( self ):
        try:
            return self.text_point
        except AttributeError:
            return (1,1)

    def paint( self, window, x, y, width, cursor, itemformat, userdata ):
        pass


# 空のファイルリストを表示する機能
class lister_Empty(lister_Base):

    def __init__(self):
        lister_Base.__init__(self)


# [ - no item - ] を表示するための特別なアイテム
class item_Empty(item_Base):

    def __init__( self, location ):
        self.location = location
        self.name = ""

    def __str__(self):
        return os.path.join( self.location, self.name )

    def getName(self):
        return self.name

    def paint( self, window, x, y, width, cursor, itemformat, userdata ):
        if cursor:
            line0=( LINE_BOTTOM, ckit.getColor("file_cursor") )
        else:
            line0=None

        attr = ckit.Attribute( fg=ckit.getColor("error_file_fg"), line0=line0 )

        s = "- no item -"
        s = ckit.adjustStringWidth(window,s,width,ckit.ALIGN_CENTER)
        window.putString( x, y, width, 1, attr, s )


# ファイルのレンダリング処理
class item_CommonPaint(item_Base):

    def paint( self, window, x, y, width, cursor, itemformat, userdata ):

        if self.isdir():
            if self.ishidden():
                attr_fg=ckit.getColor("hidden_dir_fg")
            else:
                attr_fg=ckit.getColor("dir_fg")
        else:
            if self.ishidden():
                attr_fg=ckit.getColor("hidden_file_fg")
            else:
                attr_fg=ckit.getColor("file_fg")

        if self.selected():
            attr_bg_gradation=( ckit.getColor("select_file_bg1"), ckit.getColor("select_file_bg2"), ckit.getColor("select_file_bg1"), ckit.getColor("select_file_bg2"))
        elif self.bookmark():
            attr_bg_gradation=( ckit.getColor("bookmark_file_bg1"), ckit.getColor("bookmark_file_bg2"), ckit.getColor("bookmark_file_bg1"), ckit.getColor("bookmark_file_bg2"))
        else:
            attr_bg_gradation = None

        if cursor:
            line0=( LINE_BOTTOM, ckit.getColor("file_cursor") )
        else:
            line0=None
        
        attr = ckit.Attribute( fg=attr_fg, bg_gradation=attr_bg_gradation, line0=line0 )

        s = itemformat( window, self, width, userdata )
        window.putString( x, y, width, 1, attr, s )

## 通常のファイルアイテム
#
#  通常の実在するファイルやディレクトリを意味するクラスです。\n\n
#
#  内骨格では、ファイルリストに表示されるアイテムを item_Xxxx という名前のクラスのオブジェクトで表現します。\n
#  
#  @sa item_Archive
#
class item_Default(item_CommonPaint):

    def __init__( self, location, name, info=None, bookmark=False ):
    
        self.location = location
        self.name = name

        if info==None:
            
            if os.name=="nt":
                info_list = cfiler_native.findFile( os.path.join(self.location,self.name) )
            else:
                # FIXME : 属性をちゃんとする
                info_list = []
                # FIXME : try - catch して info_list を空のまま抜ける
                s = os.stat( os.path.join(self.location,self.name) )
                attr = 0
                if stat.S_ISDIR(s.st_mode): attr |= ckit.FILE_ATTRIBUTE_DIRECTORY
                info_list.append( (self.name,s.st_size,time.localtime(s.st_mtime)[:6],attr) )
        
            if info_list:
                info = info_list[0]
            else:
                raise IOError( "file does not exist. [%s]" % self.name )

        self._size = info[1]
        self._mtime = info[2]
        self._attr = info[3]

        self._selected = False
        self._bookmark = bookmark

        # Macの濁点変換
        # FIXME : 変換の場所が適切か要検討。表示とキャレットの移動に関してのみ、変換をするべきかも。
        self.name = unicodedata.normalize( "NFC", self.name )

    def __str__(self):
        return os.path.join( self.location, self.name )

    def getName(self):
        return self.name

    def getFullpath(self):
        return os.path.join( self.location, self.name )

    def time(self):
        assert( type(self._mtime)==tuple )
        return self._mtime

    def utime( self, time ):
        if os.name=="nt":
            cfiler_native.setFileTime( os.path.join(self.location,self.name), time )
        else:
            # FIXME : 実装
            pass
            #os.utime( os.path.join(self.location,self.name), (t,t) )

    def size(self):
        return self._size

    def attr(self):
        return self._attr

    def uattr( self, attr ):
        if os.name=="nt":
            ckit.setFileAttribute( os.path.join( self.location, self.name ), attr )
            self._attr = attr
        else:
            # FIXME : 実装
            pass

    def isdir(self):
        return self._attr & ckit.FILE_ATTRIBUTE_DIRECTORY

    def ishidden(self):
        return self._attr & ckit.FILE_ATTRIBUTE_HIDDEN

    def _select( self, sel=None ):
        if sel==None:
            self._selected = not self._selected
        else:
            self._selected = sel;

    def selected(self):
        return self._selected

    def bookmark(self):
        return self._bookmark

    def lock(self):
        return cfiler_fileoplock.Lock( os.path.join(self.location,self.name) )

    def walk( self, topdown=True ):

        class packItem:

            def __init__( self, location, dirname ):

                self.location = location
                self.dirname = ckit.replacePath(dirname)

            def __call__( self, filename ):

                try:
                    item = item_Default(
                        self.location,
                        ckit.joinPath( self.dirname, filename )
                        )
                    return item
                except Exception:
                    cfiler_debug.printErrorInfo()
                    return None

        fullpath = os.path.join( self.location, self.name )
        for root, dirs, files in os.walk( fullpath, topdown ):
            root = ckit.replacePath(root)
            dirname = root[len(self.location):].lstrip('\\/')
            yield dirname, filter( lambda item:item, map( packItem(self.location,dirname), dirs )), filter( lambda item:item, map( packItem(self.location,dirname), files ))

    def delete( self, recursive, item_filter, schedule_handler, log_writer=None ):

        if not log_writer:
            def logWriter(s) : pass
            log_writer = logWriter

        def remove_file( filename ):
            log_writer( 'ファイル削除 : %s …' % filename )
            try:
                # READONLY属性を落とさないと削除できない
                attr = ckit.getFileAttribute(filename)
                if attr & ckit.FILE_ATTRIBUTE_READONLY:
                    attr &= ~ckit.FILE_ATTRIBUTE_READONLY
                    ckit.setFileAttribute(filename,attr)
                # 削除
                os.unlink(filename)
            except Exception as e:
                cfiler_debug.printErrorInfo()
                log_writer( '失敗\n' )
                log_writer( "  %s\n" % str(e) )
            else:
                log_writer( '完了\n' )

        def remove_dir( filename ):
            log_writer( 'ディレクトリ削除 : %s …' % filename )

            if len(os.listdir(filename))>0:
                log_writer( '空ではない\n' )
                return

            try:
                # READONLY属性を落とさないと削除できない
                attr = ckit.getFileAttribute(filename)
                if attr & ckit.FILE_ATTRIBUTE_READONLY:
                    attr &= ~ckit.FILE_ATTRIBUTE_READONLY
                    ckit.setFileAttribute(filename,attr)
                # 削除
                os.rmdir(filename)
            except Exception as e:
                cfiler_debug.printErrorInfo()
                log_writer( '失敗\n' )
                log_writer( "  %s\n" % str(e) )
            else:
                log_writer( '完了\n' )

        fullpath = ckit.joinPath( self.location, self.name )
        if self.isdir():
            if recursive:
                for root, dirs, files in os.walk( fullpath, False ):
                    if schedule_handler(): return
                    root = ckit.replacePath(root)
                    for name in files:
                        if schedule_handler(): return
                        if item_filter==None or item_filter( item_Default(root,name) ):
                            remove_file( ckit.joinPath(root, name) )
                    if schedule_handler(): return
                    remove_dir(root)
            else:
                remove_dir(fullpath)
        else:
            remove_file(fullpath)

    def open(self):
        return open( os.path.join( self.location, self.name ), "rb" )

    def rename( self, name ):
        src = os.path.join(self.location,self.name)
        dst = os.path.join(self.location,name)
        os.rename( src, dst )
        self.name = name

    def getLink(self):
        if not self.isdir():
            ext = os.path.splitext(self.name)[1].lower()
            if ext in (".lnk",".pif"):
                program, param, directory, swmode = cfiler_native.getShellLinkInfo(self.getFullpath())
                link = item_Default(
                    self.location,
                    program
                    )
                return link
        return None            


# ローカルファイルシステム上のリスト機能
class lister_LocalFS(lister_Base):

    def __init__( self, main_window, location ):
        self.main_window = main_window
        self.location = ckit.normPath(location)

    def getLocation(self):
        return self.location

    def locked(self):
        return cfiler_fileoplock.locked(self.location)

    def exists( self, name ):
        fullpath = os.path.join( self.location, name )
        if os.path.exists( os.path.join( self.location, name ) ):
            item = item_Default(
                self.location,
                name
                )
            return item
        return None

    def mkdir( self, name, log_writer=None ):

        if not log_writer:
            def logWriter(s) : pass
            log_writer = logWriter

        fullpath = ckit.joinPath( self.location, name )
        log_writer( 'ディレクトリ作成 : %s …' % fullpath )
        if os.path.exists(fullpath) and os.path.isdir(fullpath):
            log_writer( 'すでに存在\n' )
            return
        try:
            os.makedirs(fullpath)
        except Exception as e:
            cfiler_debug.printErrorInfo()
            log_writer( '失敗\n' )
            log_writer( "  %s\n" % str(e) )
        else:
            log_writer( '完了\n' )

    def getCopyDst( self, name ):

        fullpath = os.path.join( self.location, name )

        try:
            dirname = os.path.split(fullpath)[0]
            os.makedirs(dirname)
        except FileExistsError:
            pass

        # READONLY属性を落とさないと上書きできない
        attr = ckit.getFileAttribute(fullpath)
        if attr & ckit.FILE_ATTRIBUTE_READONLY:
            attr &= ~ckit.FILE_ATTRIBUTE_READONLY
            ckit.setFileAttribute(fullpath,attr)

        return open( fullpath, "wb" )

    def getRoot(self):
        dirname = self.location
        root = ckit.rootPath( self.location )
        return lister_Default(self.main_window,root)


# 標準的なディレクトリのリストアップ機能
class lister_Default(lister_LocalFS):

    def __init__( self, main_window, location ):
        lister_LocalFS.__init__( self, main_window, location )
        self.check_thread = cfiler_checkdir.CheckDirThread(self.location)
        self.check_thread.start()
        
    def destroy(self):
        self.check_thread.cancel()
        self.check_thread.join()
        lister_LocalFS.destroy(self)

    def __call__( self ):

        def packListItem( fileinfo ):

            item = item_Default(
                self.location,
                fileinfo[0],
                fileinfo,
                bookmark = fileinfo[0].lower() in bookmark_items
                )

            return item

        bookmark_items = self.main_window.bookmark.listDir(self.location)

        cfiler_misc.checkNetConnection(self.location)


        if os.name=="nt":
            fileinfo_list = cfiler_native.findFile( os.path.join(self.location,"*") )
        else:
            # FIXME : 属性をちゃんとする
            fileinfo_list = []
            for name in os.listdir(self.location):
                s = os.stat( os.path.join(self.location,name) )
                attr = 0
                if stat.S_ISDIR(s.st_mode): attr |= ckit.FILE_ATTRIBUTE_DIRECTORY
                fileinfo_list.append( (name,s.st_size,time.localtime(s.st_mtime)[:6],attr) )

        items = list(map( packListItem, fileinfo_list ))

        return items

    def cancel(self):
        pass

    def __str__(self):
        return self.location

    def isLazy(self):
        return False

    def isChanged(self):
        return self.check_thread.isChanged()

    def getCopy( self, name ):
        return ( lister_Default( self.main_window, self.location ), name )

    def getChild( self, name ):
        return lister_Default( self.main_window, os.path.join( self.location, name ) )

    def getParent(self):
        parent, name = ckit.splitPath( self.location )
        if not name:
            raise cfiler_error.NotExistError
        return ( lister_Default(self.main_window,parent), name )

    def touch( self, name ):

        fullpath = os.path.join( self.location, name )

        if not os.path.exists(fullpath):
            fd = open( fullpath, "wb" )
            del fd

        item = item_Default(
            self.location,
            name
            )
        return item

    def unlink( self, name ):
        fullpath = os.path.join( self.location, name )

        # READONLY属性を落とさないと削除できない
        attr = ckit.getFileAttribute(fullpath)
        if attr & ckit.FILE_ATTRIBUTE_READONLY:
            attr &= ~ckit.FILE_ATTRIBUTE_READONLY
            ckit.setFileAttribute(fullpath,attr)

        os.unlink( fullpath )

    def canRenameFrom( self, other ):
        if not isinstance( other, lister_Default ) : return False
        return os.path.splitdrive(self.location)[0].lower()==os.path.splitdrive(other.location)[0].lower()

    def rename( self, src_item, dst_name ):
        dst_fullpath = os.path.join( self.location, dst_name )
        os.rename( src_item.getFullpath(), dst_fullpath )

    def popupContextMenu( self, window, x, y, items=None ):
        if items==None:
            directory, name = ckit.splitPath(os.path.normpath(self.location))
            if name:
                return cfiler_native.popupContextMenu( window.getHWND(), x, y, directory, [name] )
            else:
                return cfiler_native.popupContextMenu( window.getHWND(), x, y, "", [directory] )
        else:
            filename_list = list(map( lambda item : os.path.normpath(item.getName()), items ))
            return cfiler_native.popupContextMenu( window.getHWND(), x, y, os.path.normpath(self.location), filename_list )


# アーカイブファイルの中のファイルをツリー構造で管理するためのノード
class ArchiveNode:
    def __init__( self, info ):
        #print( "ArchiveNode.__init__", info )
        self.info = info
        if self.info[3] & ckit.FILE_ATTRIBUTE_DIRECTORY:
            self.children = {}
        else:
            self.children = None


## コモンアーカイバライブラリでサポートされているアーカイブファイルの仮想ディレクトリ中のファイルを表すアイテム
#
#  コモンアーカイバライブラリでサポートされているアーカイブファイルの仮想ディレクトリ中のファイルやディレクトリを意味するクラスです。\n\n
#
#  内骨格では、ファイルリストに表示されるアイテムを item_Xxxx という名前のクラスのオブジェクトで表現します。\n
#  
#  @sa item_Default
#
class item_Archive(item_CommonPaint):

    def __init__( self, archiver, arc_filename, arc_dir, name, node ):

        self.archiver = archiver
        self.arc_filename = arc_filename
        self.arc_dir = arc_dir
        self.name = name
        self.node = node
        
        self._selected = False

    def __str__(self):
        return "%s:%s" % ( self.arc_filename, os.path.join( self.arc_dir, self.name ) )

    def getName(self):
        return self.name

    def time(self):
        assert( type(self.node.info[2])==tuple )
        return self.node.info[2]

    def size(self):
        return self.node.info[1]

    def attr(self):
        return 0

    def isdir(self):
        return self.node.info[3] & ckit.FILE_ATTRIBUTE_DIRECTORY

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
        return cfiler_fileoplock.Lock(self.arc_filename)
        
    def walk( self, topdown=True ):

        class packItem:

            def __init__( packer_self, dirname ):
                self.dirname = dirname

            def __call__( packer_self, node ):

                item = item_Archive(
                    self.archiver,
                    self.arc_filename,
                    self.arc_dir,
                    os.path.join(self.dirname,node.info[0]).replace("\\","/"),
                    node
                    )

                return item

        def walkRecursive( root, node ):

            dirs = []
            files = []

            for child in node.children.values():
                if child.info[3] & ckit.FILE_ATTRIBUTE_DIRECTORY:
                    dirs.append(child)
                else:
                    files.append(child)

            if topdown:
                yield root, map( packItem(root), dirs ), map( packItem(root), files )

            for child_node in dirs:
                for ret in walkRecursive( os.path.join(root,child_node.info[0]).replace("\\","/"), child_node ):
                    yield ret

            if not topdown:
                yield root, map( packItem(root), dirs ), map( packItem(root), files )

        for ret in walkRecursive( self.name, self.node ):
            yield ret
        
    def open(self):
    
        tmp_dir_path = ckit.makeTempDir( "archive_" )
        tmp_dir_path = os.path.abspath( os.path.normpath(tmp_dir_path) )
        tmp_file_path = os.path.join(tmp_dir_path,os.path.split(self.name)[1])

        if self.node.info[1]>0:
            self.archiver.extract( None, self.arc_filename, tmp_dir_path, os.path.join(self.arc_dir,self.name) )
        else:
            fd = open( tmp_file_path, "wb" )
            del fd

        fd = io.BytesIO( open(tmp_file_path,"rb").read() )

        shutil.rmtree(tmp_dir_path,ignore_errors=True)

        return fd

# アーカイブファイルの中のファイルをリストアップする機能
class lister_Archive(lister_Base):

    def __init__( self, main_window, archiver, arc_filename, arc_dir, arc_tree=None ):

        self.main_window = main_window
        self.archiver = archiver
        self.arc_filename = ckit.normPath(arc_filename)
        self.arc_dir = arc_dir
        self.arc_tree = arc_tree
        self.cancel_requested = False
        
    def __call__( self ):

        # まだアーカイブをオープンしていなかったらオープンする
        if self.arc_tree==None:
            arc_tree = ArchiveNode( ( "", 0, (0,0,0,0,0,0), ckit.FILE_ATTRIBUTE_DIRECTORY ) )
            arc_obj = self.archiver.openArchive( self.main_window.getHWND(), self.arc_filename, 0 )
            try:
                for info in arc_obj.iterItems("*"):
                    if self.cancel_requested:
                        raise cfiler_error.CanceledError
                    name = info[0]
                    current_node = arc_tree
                    names = name.split("\\")
                    for i in range( len(names)-1 ):
                        #print( "name[%d]=%s" % (i,names[i]) )
                        if not names[i] in current_node.children:
                            child = ArchiveNode( ( names[i], 0, info[2], ckit.FILE_ATTRIBUTE_DIRECTORY ) )
                            current_node.children[ names[i] ] = child
                        current_node = current_node.children[ names[i] ]
                    if names[-1]:
                        #print( "name[%d]=%s" % (-1,names[-1]) )
                        child = ArchiveNode( ( names[-1], info[1], info[2], info[3] ) )
                        current_node.children[ names[-1] ] = child
                self.arc_tree = arc_tree
            finally:
                arc_obj.close()

        items = []
        
        current_node = self.arc_tree
        if self.arc_dir:
            for name in os.path.normpath(self.arc_dir).split("\\"):
                #print( name )
                current_node = current_node.children[name]
        
        for node in current_node.children.values():

            #print( node.info )

            item = item_Archive(
                self.archiver,
                self.arc_filename,
                self.arc_dir,
                node.info[0],
                node,
                )

            items.append(item)

        return items

    def cancel(self):
        self.cancel_requested = True

    def __str__(self):
        return "%s:%s" % ( self.arc_filename, self.arc_dir )

    def getLocation(self):
        return "%s:%s" % ( self.arc_filename, self.arc_dir )

    def isLazy(self):
        return False

    def isChanged(self):
        return False

    def getCopy( self, name ):
        return ( lister_Archive( self.main_window, self.archiver, self.arc_filename, self.arc_dir, self.arc_tree ), name )

    def getChild( self, name ):
        return lister_Archive( self.main_window, self.archiver, self.arc_filename, ckit.normPath(os.path.join(self.arc_dir,name)), self.arc_tree )

    def getParent(self):
        if self.arc_dir:
            parent, name = os.path.split(self.arc_dir)
            return ( lister_Archive( self.main_window, self.archiver, self.arc_filename, parent, self.arc_tree ), name )
        else:
            parent, name = os.path.split(self.arc_filename)
            return ( lister_Default(self.main_window,parent), name )

    def getRoot(self):
        return lister_Archive( self.main_window, self.archiver, self.arc_filename, "", self.arc_tree )

    def locked(self):
        return cfiler_fileoplock.locked(self.arc_filename)


# 外部からアイテムリストを受け取る機能
class lister_Custom(lister_LocalFS):

    def __init__( self, main_window, prefix, location, items ):
        lister_LocalFS.__init__(self,main_window,location)
        self.prefix = prefix
        self.items = items

    def destroy(self):
        lister_LocalFS.destroy(self)

    def __call__( self ):
        items = []
        for item in self.items:
            items.append( copy.copy(item) )
        return items

    def cancel(self):
        pass

    def __str__(self):
        return self.prefix + self.location

    def isLazy(self):
        return True

    def isChanged(self):
        return False

    def getCopy( self, name ):
        path = ckit.joinPath( self.location, name )
        dirname, filename = ckit.splitPath(path)
        return ( lister_Default( self.main_window, dirname ), filename )

    def getChild( self, name ):
        return lister_Default( self.main_window, os.path.join( self.location, name ) )

    def getParent(self):
        return ( lister_Default(self.main_window,self.location), "" )

#--------------------------------------------------------------------

## 標準的なアイテムの表示形式
def itemformat_Name_Ext_Size_YYMMDD_HHMMSS( window, item, width, userdata ):

    if item.isdir():
        str_size = "<DIR>"
    else:
        str_size = "%6s" % cfiler_misc.getFileSizeString(item.size())

    t = item.time()
    str_time = "%02d/%02d/%02d %02d:%02d:%02d" % ( t[0]%100, t[1], t[2], t[3], t[4], t[5] )

    str_size_time = "%s %s" % ( str_size, str_time )

    width = max(40,width)
    filename_width = width-len(str_size_time)

    if item.isdir():
        body, ext = item.name, None
    else:
        body, ext = ckit.splitExt(item.name)

    if ext:
        body_width = min(width,filename_width-6)
        return ( ckit.adjustStringWidth(window,body,body_width,ckit.ALIGN_LEFT,ckit.ELLIPSIS_RIGHT)
               + ckit.adjustStringWidth(window,ext,6,ckit.ALIGN_LEFT,ckit.ELLIPSIS_NONE)
               + str_size_time )
    else:
        return ( ckit.adjustStringWidth(window,body,filename_width,ckit.ALIGN_LEFT,ckit.ELLIPSIS_RIGHT)
               + str_size_time )

## 秒を省いたアイテムの表示形式
def itemformat_Name_Ext_Size_YYMMDD_HHMM( window, item, width, userdata ):

    if item.isdir():
        str_size = "<DIR>"
    else:
        str_size = "%6s" % cfiler_misc.getFileSizeString(item.size())

    t = item.time()
    str_time = "%02d/%02d/%02d %02d:%02d" % ( t[0]%100, t[1], t[2], t[3], t[4] )

    str_size_time = "%s %s" % ( str_size, str_time )

    width = max(40,width)
    filename_width = width-len(str_size_time)

    if item.isdir():
        body, ext = item.name, None
    else:
        body, ext = ckit.splitExt(item.name)

    if ext:
        body_width = min(width,filename_width-6)
        return ( ckit.adjustStringWidth(window,body,body_width,ckit.ALIGN_LEFT,ckit.ELLIPSIS_RIGHT)
               + ckit.adjustStringWidth(window,ext,6,ckit.ALIGN_LEFT,ckit.ELLIPSIS_NONE)
               + str_size_time )
    else:
        return ( ckit.adjustStringWidth(window,body,filename_width,ckit.ALIGN_LEFT,ckit.ELLIPSIS_RIGHT)
               + str_size_time )

## ファイル名だけを表示するアイテムの表示形式
def itemformat_NameExt( window, item, width, userdata ):
    return ckit.adjustStringWidth(window,item.name,width,ckit.ALIGN_LEFT,ckit.ELLIPSIS_RIGHT)


#--------------------------------------------------------------------

## ワイルドカードを使ったフィルタ機能
#
#  ワイルドカードを使った標準的なフィルタ機能です。\n\n
#
#  内骨格では、フィルタと呼ばれるオブジェクトを使って、ファイルリストのアイテムを絞り込んで表示することが出来ます。\n
#  フィルタは filter_Xxxx という名前のクラスのオブジェクトで表現します。\n
#  
#  @sa filter_Bookmark
#
class filter_Default:

    def __init__( self, pattern="*", dir_policy=True ):
        self.pattern = pattern
        self.pattern_list = pattern.split()
        self.dir_policy = dir_policy

    def __call__( self, item ):

        if self.dir_policy!=None and item.isdir() : return self.dir_policy

        for pattern in self.pattern_list:
            if fnmatch.fnmatch( item.name, pattern ) : return True
        return False

    def __str__(self):
        if self.pattern=='*' : return ""
        return self.pattern

    def canRenameDir(self):
        return (self.pattern=="*")

## ブックマークを使ったフィルタ機能
#
#  ブックマークに登録されているアイテムのみを表示するためのフィルタ機能です。\n\n
#
#  内骨格では、フィルタと呼ばれるオブジェクトを使って、ファイルリストのアイテムを絞り込んで表示することが出来ます。\n
#  フィルタは filter_Xxxx という名前のクラスのオブジェクトで表現します。\n
#  
#  @sa filter_Default
#
class filter_Bookmark:

    def __init__( self, dir_policy=True ):
        self.dir_policy = dir_policy

    def __call__( self, item ):
        if self.dir_policy!=None and item.isdir() : return self.dir_policy
        return item.bookmark()

    def __str__(self):
        return "[bookmark]"

#--------------------------------------------------------------------

## ファイルの名前を使ってソートする機能
#
#  ファイル名を使ってアイテムをソートするための機能です。\n\n
#
#  内骨格では、ソータと呼ばれるオブジェクトを使って、ファイルリストのアイテムを並べ替えて表示することが出来ます。\n
#  ソータは sorter_Xxxx という名前のクラスのオブジェクトで表現します。\n
#  
#  @sa sorter_ByExt
#  @sa sorter_BySize
#  @sa sorter_ByTimeStamp
#
class sorter_ByName:

    ## コンストラクタ
    #  @param self  -
    #  @param order 並びの順序。1=昇順、-1=降順
    def __init__( self, order=1 ):
        self.order = order

    def __call__( self, items ):
        if self.order==1:
            key = lambda item : ( not item.isdir(), item.name.lower() )
            reverse = False
        else:
            key = lambda item : ( item.isdir(), item.name.lower() )
            reverse = True
        items.sort( key=key, reverse=reverse )

## ファイルの拡張子を使ってソートする機能
#
#  ファイルの拡張子を使ってアイテムをソートするための機能です。\n\n
#
#  内骨格では、ソータと呼ばれるオブジェクトを使って、ファイルリストのアイテムを並べ替えて表示することが出来ます。\n
#  ソータは sorter_Xxxx という名前のクラスのオブジェクトで表現します。\n
#  
#  @sa sorter_ByName
#  @sa sorter_BySize
#  @sa sorter_ByTimeStamp
#
class sorter_ByExt:

    ## コンストラクタ
    #  @param self  -
    #  @param order 並びの順序。1=昇順、-1=降順
    def __init__( self, order=1 ):
        self.order = order

    def __call__( self, items ):
        if self.order==1:
            key = lambda item : ( not item.isdir(), os.path.splitext(item.name)[1].lower() )
            reverse = False
        else:
            key = lambda item : ( item.isdir(), os.path.splitext(item.name)[1].lower() )
            reverse = True
        items.sort( key=key, reverse=reverse )

## ファイルのサイズを使ってソートする機能
#
#  ファイルのサイズを使ってアイテムをソートするための機能です。\n\n
#
#  内骨格では、ソータと呼ばれるオブジェクトを使って、ファイルリストのアイテムを並べ替えて表示することが出来ます。\n
#  ソータは sorter_Xxxx という名前のクラスのオブジェクトで表現します。\n
#  
#  @sa sorter_ByName
#  @sa sorter_ByExt
#  @sa sorter_ByTimeStamp
#
class sorter_BySize:

    ## コンストラクタ
    #  @param self  -
    #  @param order 並びの順序。1=昇順、-1=降順
    def __init__( self, order=1 ):
        self.order = order

    def __call__( self, items ):
        if self.order==1:
            key = lambda item : ( not item.isdir(), item.size() )
            reverse = False
        else:
            key = lambda item : ( item.isdir(), item.size() )
            reverse = True
        items.sort( key=key, reverse=reverse )

## ファイルのタイムスタンプを使ってソートする機能
#
#  ファイルのタイムスタンプを使ってアイテムをソートするための機能です。\n\n
#
#  内骨格では、ソータと呼ばれるオブジェクトを使って、ファイルリストのアイテムを並べ替えて表示することが出来ます。\n
#  ソータは sorter_Xxxx という名前のクラスのオブジェクトで表現します。\n
#  
#  @sa sorter_ByName
#  @sa sorter_ByExt
#  @sa sorter_BySize
#
class sorter_ByTimeStamp:

    ## コンストラクタ
    #  @param self  -
    #  @param order 並びの順序。1=昇順、-1=降順
    def __init__( self, order=1 ):
        self.order = order

    def __call__( self, items ):
        if self.order==1:
            key = lambda item : ( not item.isdir(), item.time() )
            reverse = False
        else:
            key = lambda item : ( item.isdir(), item.time() )
            reverse = True
        items.sort( key=key, reverse=reverse )

#--------------------------------------------------------------------

class compare_Default:

    def __init__( self, cmp_size=None, cmp_timestamp=None ):
        self.cmp_size = cmp_size
        self.cmp_timestamp = cmp_timestamp

    @staticmethod
    def _compare( left, right ):
        if left<right: return -1
        elif left>right: return 1
        else: return 0

    def __call__( self, active_item, inactive_item ):

        if self.cmp_size!=None:
            if compare_Default._compare(active_item.size(),inactive_item.size())!=self.cmp_size : return False

        if self.cmp_timestamp!=None:
            if cfiler_misc.compareTime(active_item.time(),inactive_item.time())!=self.cmp_timestamp : return False

        return True

class compare_Selected:

    def __init__(self):
        pass

    def __call__( self, active_item, inactive_item ):
        return inactive_item.selected()

#--------------------------------------------------------------------

## ファイルリスト
#
#  ファイルアイテムの列挙、フィルタリング、ソート、という一連の操作を実行し、アイテムのリストを管理するクラスです。\n
#  MainWindow.activeFileList() などで取得されるのが FileList オブジェクトです。
#
class FileList:

    def __init__( self, main_window, lister, item_filter=filter_Default( "*", dir_policy=True ), sorter=sorter_ByName() ):

        self.main_window = main_window

        self.lister = lister
        self.item_filter = item_filter
        self.sorter = sorter
        self.disk_size_info = None
        self.disk_size_string = ""
        self.job_queue = ckit.JobQueue()
        self.job_item = None
        self.lock = threading.RLock()

        self.original_items = [] # 作成中のアイテムリスト(列挙直後)
        self.back_items = []     # 作成中のアイテムリスト(フィルタ/ソート適用後)
        self.items = []          # 完成済みのアイテムリスト
        self.applyItems()

    def destroy(self):
        self.lister.destroy()
        self.job_queue.cancel()
        self.job_queue.join()
        self.job_queue.destroy()

    def __str__(self):
        return " %s %s " % ( self.lister, self.item_filter )

    def _callLister( self, manual, keep_selection=False ):

        if not manual and self.lister.isLazy() : return

        if keep_selection:
            old_items = dict( map( lambda item : [ item.name, item ], self.original_items ) )

        self.main_window.setStatusMessage( "List ..." )
        try:
            self.original_items = self.lister()
        finally:
            self.main_window.clearStatusMessage()

        if keep_selection:
            for item in self.original_items:
                try:
                    if old_items[item.name].selected():
                        item._select(True)
                except KeyError:
                    continue

        self.delayedUpdateInfo()

    def _callFilterAndSorter(self):

        if self.item_filter:
            self.back_items = list( filter( self.item_filter, self.original_items ) )
        else:
            self.back_items = self.original_items[:]

        if not self.main_window.isHiddenFileVisible():
            def isNotHidden(item):
                return not item.ishidden()
            self.back_items = list( filter( isNotHidden, self.back_items ) )

        if self.sorter:
            self.sorter(self.back_items)

    def delayedUpdateInfo(self):

        def jobUpdateInfo(job_item):
            self.lock.acquire()
            try:
                self.disk_size_info = ckit.getDiskSize( os.path.splitdrive(self.getLocation())[0] )
            finally:
                self.lock.release()

        def jobUpdateInfoFinished(job_item):
            if job_item.isCanceled() : return
            self.main_window.paint( cfiler_mainwindow.PAINT_LEFT_FOOTER | cfiler_mainwindow.PAINT_RIGHT_FOOTER )

        self.lock.acquire()
        try:
            self.disk_size_info = None
            if self.job_item:
                self.job_item.cancel()
                self.job_item = None
            self.job_item = ckit.JobItem( jobUpdateInfo, jobUpdateInfoFinished )
            self.job_queue.enqueue(self.job_item)
        finally:
            self.lock.release()

    def _updateInfo(self):

        self.num_file = 0
        self.num_dir = 0
        self.num_file_selected = 0
        self.num_dir_selected = 0
        self.selected_size = 0

        for item in self.items:
            isdir = item.isdir()
            if isdir:
                self.num_dir += 1
                if item.selected():
                    self.num_dir_selected += 1
            else:
                self.num_file += 1
                if item.selected():
                    self.num_file_selected += 1
                    self.selected_size += item.size()

    def selectItem( self, i, sel=None ):

        item = self.items[i]
        sel_prev = self.items[i].selected()
        item._select(sel)

        if item.selected() != sel_prev:
            if item.selected():
                if item.isdir():
                    self.num_dir_selected += 1
                else:
                    self.num_file_selected += 1
                    self.selected_size += item.size()
            else:
                if item.isdir():
                    self.num_dir_selected -= 1
                else:
                    self.num_file_selected -= 1
                    self.selected_size -= item.size()

    def isChanged(self):
        return self.lister.isChanged()

    def refresh( self, manual=False, keep_selection=False ):
        self._callLister(manual,keep_selection)
        self._callFilterAndSorter()

    def setLister( self, lister ):
        old_lister = self.lister
        self.lister = lister
        try:
            self._callLister(True)
            self._callFilterAndSorter()
        except Exception:
            cfiler_debug.printErrorInfo()
            self.lister.destroy()
            self.lister = old_lister
            raise
        old_lister.destroy()    
        del old_lister
        gc.collect()

    def getLister(self):
        return self.lister

    def getLocation(self):
        return self.lister.getLocation()

    def setFilter( self, new_filter ):
        self.item_filter = new_filter
        self._callFilterAndSorter()

    def getFilter(self):
        return self.item_filter

    def setSorter( self, new_sorter ):
        self.sorter = new_sorter
        self._callFilterAndSorter()

    def getSorter(self):
        return self.sorter

    def applyItems(self):

        self.items = self.back_items

        if len(self.items)==0:
            self.items.append( item_Empty(str(self.lister)) )

        self._updateInfo()

    def getHeaderInfo(self):

        if self.num_dir_selected==0 and self.num_file_selected==0 : return ""

        if self.num_dir_selected==0:
            str_dir = ""
        elif self.num_dir_selected==1:
            str_dir = "%d Dir " % self.num_dir_selected
        else:
            str_dir = "%d Dirs " % self.num_dir_selected

        if self.num_file_selected==0:
            str_file = ""
        elif self.num_file_selected==1:
            str_file = "%d File " % self.num_file_selected
        else:
            str_file = "%d Files " % self.num_file_selected

        if self.selected_size==0:
            str_size = ""
        else:
            str_size = cfiler_misc.getFileSizeString( self.selected_size ) + " "

        return "%s%s%sMarked" % ( str_dir, str_file, str_size )

    def getFooterInfo(self):

        self.lock.acquire()
        try:
            if self.disk_size_info:
                if self.num_dir<=1:
                    str_dir = "%d Dir" % self.num_dir
                else:
                    str_dir = "%d Dirs" % self.num_dir

                if self.num_file<=1:
                    str_file = "%d File" % self.num_file
                else:
                    str_file = "%d Files" % self.num_file

                self.disk_size_string = "%s  %s  %s (%s)" % ( str_dir, str_file, cfiler_misc.getFileSizeString(self.disk_size_info[1]), cfiler_misc.getFileSizeString(self.disk_size_info[0]) )

            return self.disk_size_string

        finally:
            self.lock.release()

    def numItems(self):
        return len(self.items)

    def getItem(self,index):
        return self.items[index]

    def indexOf(self,filename):
        for i in range(len(self.items)):
            if self.items[i].name == filename:
                return i
        return -1

    def selected(self):
        for item in self.items:
            if item.selected():
                return True
        return False

## @} filelist
