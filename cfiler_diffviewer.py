import os
import sys
import re
import math
import difflib

from PIL import Image

import ckit
from ckit.ckit_const import *

import cfiler_msgbox
import cfiler_misc
import cfiler_wallpaper
import cfiler_statusbar
import cfiler_resource
import cfiler_debug

MessageBox = cfiler_msgbox.MessageBox

## @addtogroup diffviewer
## @{

#--------------------------------------------------------------------

## テキスト差分ビューアウインドウ
#
#  テキスト差分ビューアを実現しているクラスです。\n\n
#  設定ファイル config.py の configure_DiffViewer に渡される window 引数は、DiffViewer クラスのオブジェクトです。
#
class DiffViewer( ckit.TextWindow ):

    def __init__( self, x, y, width, height, parent_window, ini, title, left_item, right_item, edit_handler=None ):

        ckit.TextWindow.__init__(
            self,
            x=x,
            y=y,
            width=width,
            height=height,
            origin= ORIGIN_X_CENTER | ORIGIN_Y_CENTER,
            parent_window=parent_window,
            bg_color = ckit.getColor("bg"),
            cursor0_color = ckit.getColor("cursor0"),
            cursor1_color = ckit.getColor("cursor1"),
            resizable = True,
            title = title,
            show = False,
            minimizebox = True,
            maximizebox = True,
            sysmenu=True,
            close_handler = self.onClose,
            size_handler = self._onSize,
            keydown_handler = self.onKeyDown,
            )

        self.command = ckit.CommandMap(self)

        class Pane:
            pass

        self.left = Pane()
        self.right = Pane()

        self.img = ckit.createThemeImage('lineno.png')
        
        client_rect = self.getClientRect()
        offset_x, offset_y = self.charToClient( 0, 0 )
        char_w, char_h = self.getCharSize()
        self.plane_statusbar = ckit.ThemePlane3x3( self, 'statusbar.png' )
        self.status_bar = cfiler_statusbar.StatusBar()
        self.status_bar_layer = cfiler_statusbar.SimpleStatusBarLayer()
        self.status_bar.registerLayer(self.status_bar_layer)

        self.job_queue = ckit.JobQueue()
        self.edit_handler = edit_handler
        
        def initializePane( pane, item ):
        
            pane.plane = ckit.ImagePlane( self, (0,0), (10,10), 1 )
            pane.plane.setImage(self.img)

            pane.item = item

            def jobLoad( job_item ):

                try:
                    pane.data = item.open().read()
                except MemoryError:
                    print( "ERROR : メモリ不足" )
                    pane.data = ""
                except Exception as e:
                    cfiler_debug.printErrorInfo()
                    print( e )
                    pane.data = ""

                text_encoding = ckit.detectTextEncoding(pane.data)
                pane.encoding = text_encoding.encoding
                if text_encoding.bom:
                    pane.data = pane.data[len(text_encoding.bom):]
                if pane.encoding==None:
                    pane.lines = []
                else:
                    unicode_data = pane.data.decode( encoding=pane.encoding, errors='replace' )
                    pane.lines = unicode_data.splitlines()

            def jobLoadFinished( job_item ):
                pass

            job_item = ckit.JobItem( jobLoad, jobLoadFinished )
            self.job_queue.enqueue(job_item)
        
            pane.scroll_info = ckit.ScrollInfo()
            pane.scroll_info.makeVisible( 0, self.height() )

            pane.diff = []

        initializePane( self.left, left_item )
        initializePane( self.right, right_item )

        try:
            self.wallpaper = cfiler_wallpaper.Wallpaper(self)
            self.wallpaper.copy( parent_window )
            self.wallpaper.adjust()
        except AttributeError:
            self.wallpaper = None

        self.load_finished = False

        def jobDiff( job_item ):

            diff_object = difflib.unified_diff( self.left.lines, self.right.lines, n=0 )
        
            color = 0

            re_pattern = re.compile( "@@ -([0-9]+)(,([0-9]+))? \+([0-9]+)(,([0-9]+))? @@" )
            for line in diff_object:
                if line.startswith("@@"):

                    re_result = re_pattern.match(line)

                    begin1 = int(re_result.group(1))
                    if not re_result.group(3):
                        delta1 = 1
                    elif re_result.group(3)=='0':
                        begin1 += 1
                        delta1 = 0
                    else:
                        delta1 = int(re_result.group(3))

                    self.left.diff.append( ( begin1, delta1, color ) )

                    begin2 = int(re_result.group(4))
                    if not re_result.group(6):
                        delta2 = 1
                    elif re_result.group(6)=='0':
                        begin2 += 1
                        delta2 = 0
                    else:
                        delta2 = int(re_result.group(6))
                        
                    self.right.diff.append( ( begin2, delta2, color ) )

                    color += 1
                    if color>=3:
                        color=0

        def jobDiffFinished( job_item ):
            if job_item.isCanceled() : return
            self.load_finished = True
            self.paint()
            
            if self.left.encoding==None or self.right.encoding==None:
                
                self.destroy()

                if self.left.data == self.right.data:
                    cfiler_msgbox.popMessageBox( parent_window, MessageBox.TYPE_OK, "ファイル比較", "ファイルの内容は同一です。" )
                else:
                    cfiler_msgbox.popMessageBox( parent_window, MessageBox.TYPE_OK, "ファイル比較", "ファイルの内容には差異があります。" )
                
            else:
                self.setTitle( "%s - [ %s : %s ]" % ( cfiler_resource.cfiler_appname, self.left.item.name, self.right.item.name ) )
                self.show(True)

        job_item = ckit.JobItem( jobDiff, jobDiffFinished )
        self.job_queue.enqueue(job_item)

        self.configure()

    def destroy(self):
        self.job_queue.cancel()
        self.job_queue.join()
        self.job_queue.destroy()
        ckit.TextWindow.destroy(self)

    ## 設定を読み込む
    #
    #  キーマップなどをリセットした上で、config,py の configure_DiffViewer() を呼び出します。
    #
    def configure(self):
        
        self.keymap = ckit.Keymap()
        self.keymap[ "Up" ] = self.command.ScrollUp
        self.keymap[ "Down" ] = self.command.ScrollDown
        self.keymap[ "PageUp" ] = self.command.PageUp
        self.keymap[ "Left" ] = self.command.PageUp
        self.keymap[ "PageDown" ] = self.command.PageDown
        self.keymap[ "Right" ] = self.command.PageDown
        self.keymap[ "C-Up" ] = self.command.DiffPrev
        self.keymap[ "C-Down" ] = self.command.DiffNext
        self.keymap[ "E" ] = self.command.Edit
        self.keymap[ "Return" ] = self.command.Close
        self.keymap[ "Escape" ] = self.command.Close

        ckit.callConfigFunc("configure_DiffViewer",self)

    def onClose(self):
        self.destroy()

    def _onSize( self, width, height ):

        if self.wallpaper:
            self.wallpaper.adjust()

        self.paint()

    def scrollSplitPos(self):
        yield ( 1, 1 )
        for i in range(len(self.left.diff)):
            yield ( self.left.diff[i][0], self.right.diff[i][0] )
            yield ( self.left.diff[i][0]+self.left.diff[i][1], self.right.diff[i][0]+self.right.diff[i][1] )
        yield ( len(self.left.lines)+1, len(self.right.lines)+1 )
    
    def scroll( self, advance ):
    
        while advance!=0:
    
            left_scroll_center = self.left.scroll_info.pos + self.height()//2
            right_scroll_center = self.right.scroll_info.pos + self.height()//2
    
            for left_split_pos, right_split_pos in self.scrollSplitPos():
        
                if left_scroll_center<left_split_pos or right_scroll_center<right_split_pos:
                
                    left_delta = left_split_pos - left_scroll_center
                    right_delta = right_split_pos - right_scroll_center

                    if advance<0:
                        if left_delta<right_delta:
                            self.left.scroll_info.pos -= 1
                        elif left_delta>right_delta:
                            self.right.scroll_info.pos -= 1
                        else:
                            self.left.scroll_info.pos -= 1
                            self.right.scroll_info.pos -= 1
                    else:
                        if left_delta>right_delta:
                            self.left.scroll_info.pos += 1
                        elif left_delta<right_delta:
                            self.right.scroll_info.pos += 1
                        else:
                            self.left.scroll_info.pos += 1
                            self.right.scroll_info.pos += 1
                    break
            else:
                if advance<0:
                    self.left.scroll_info.pos -= 1
                    self.right.scroll_info.pos -= 1
                else:
                    self.left.scroll_info.pos += 1
                    self.right.scroll_info.pos += 1

            if self.left.scroll_info.pos<0 : self.left.scroll_info.pos=0
            if self.right.scroll_info.pos<0 : self.right.scroll_info.pos=0
            if self.left.scroll_info.pos>len(self.left.lines)-1 : self.left.scroll_info.pos=len(self.left.lines)-1
            if self.right.scroll_info.pos>len(self.right.lines)-1 : self.right.scroll_info.pos=len(self.right.lines)-1
            
            advance -= int( math.copysign( 1, advance ) )

        self.paint()

    def onKeyDown( self, vk, mod ):

        try:
            func = self.keymap.table[ ckit.KeyEvent(vk,mod) ]
        except KeyError:
            return

        func( ckit.CommandInfo() )

        return True

    def paint(self):

        if not self.load_finished : return

        x=0
        y=0
        width=self.width()
        height=self.height()

        client_rect = self.getClientRect()
        offset_x, offset_y = self.charToClient( 0, 0 )
        char_w, char_h = self.getCharSize()

        keta = max( len( str(len(self.left.lines)+1) ), len(str(len(self.right.lines)+1)) )
        
        left_width = width//2

        self.left.plane.setPosition( ( 0, 0 ) )
        self.left.plane.setSize( ( int((keta+1.6)*char_w), (self.height()-1)*char_h+offset_y ) )

        self.right.plane.setPosition( ( offset_x + left_width * char_w, 0 ) )
        self.right.plane.setSize( ( int((keta+1.6)*char_w), (self.height()-1)*char_h+offset_y ) )

        self.plane_statusbar.setPosSize( 0, (self.height()-1)*char_h+offset_y, client_rect[2], client_rect[3]-(self.height()-1)*char_h+offset_y )

        attribute_normal = ckit.Attribute( fg=ckit.getColor("fg"))
        attribute_lineno = ckit.Attribute( fg=ckit.getColor("bar_fg"))
        attribute_differ = [
            ckit.Attribute( fg=ckit.getColor("fg"), bg=ckit.getColor("diff_bg1")),
            ckit.Attribute( fg=ckit.getColor("fg"), bg=ckit.getColor("diff_bg2")),
            ckit.Attribute( fg=ckit.getColor("fg"), bg=ckit.getColor("diff_bg3")),
            ]
        attribute_differ_0 = [
            ckit.Attribute( fg=ckit.getColor("fg"), line0=( LINE_BOTTOM, ckit.getColor("diff_bg1") ) ),
            ckit.Attribute( fg=ckit.getColor("fg"), line0=( LINE_BOTTOM, ckit.getColor("diff_bg2") ) ),
            ckit.Attribute( fg=ckit.getColor("fg"), line0=( LINE_BOTTOM, ckit.getColor("diff_bg3") ) ),
            ]

        def paintPane( pane, x, width ):
        
            diff_index = 0

            for i in range(height-1):

                index = pane.scroll_info.pos+i

                if index < len(pane.lines):
                    
                    attr=attribute_normal

                    while diff_index<len(pane.diff) and index+1 > pane.diff[diff_index][0] + pane.diff[diff_index][1]:
                        diff_index += 1
                        
                    if diff_index<len(pane.diff):
                    
                        d = pane.diff[diff_index]

                        if d[0] <= index+1 < d[0]+d[1]:
                            attr = attribute_differ[ d[2] ]
                        elif d[0]==index+2 and d[1]==0:
                            attr = attribute_differ_0[ d[2] ]
                        elif diff_index+1<len(pane.diff) and pane.diff[diff_index+1][0]==index+2 and pane.diff[diff_index+1][1]==0:
                            attr = attribute_differ_0[ pane.diff[diff_index+1][2] ]
                
                    str_lineno = str(index+1)
                    self.putString( x, y+i, width, 1, attribute_lineno, " "+" "*(keta-len(str_lineno))+str_lineno+" " )

                    self.putString( x+keta+2, y+i, width-keta+2, 1, attr, " " * (width-(keta+2)) )
                    self.putString( x+keta+2, y+i, width-keta+2, 1, attr, ckit.expandTab(self,pane.lines[index]) )
                else:
                    self.putString( x, y+i, width, 1, attribute_normal, " " * width )

            pane.status_message = "%d / %d : %s" % ( pane.scroll_info.pos+1, len(pane.lines), pane.encoding )
            pane.status_message = ckit.adjustStringWidth( self, pane.status_message, width, ckit.ALIGN_CENTER )

        paintPane( self.left, 0, left_width )
        paintPane( self.right, left_width, width-left_width )

        status_message = "%s%s" % ( self.left.status_message, self.right.status_message )
        self.status_bar_layer.setMessage(status_message)
        self.status_bar.paint( self, 0, height-1, width, 1 )

    #--------------------------------------------------------------------------

    def executeCommand( self, name, info ):
        try:
            command = getattr( self, "command_" + name )
        except AttributeError:
            return False

        command(info)
        return True

    def enumCommand(self):
        for attr in dir(self):
            if attr.startswith("command_"):
                yield attr[ len("command_") : ]

    #--------------------------------------------------------
    # ここから下のメソッドはキーに割り当てることができる
    #--------------------------------------------------------

    ## １行上方向にスクロールする
    def command_ScrollUp( self, info ):
        self.scroll(-1)

    ## １行下方向にスクロールする
    def command_ScrollDown( self, info ):
        self.scroll(1)

    ## １ページ上方向にスクロールする
    def command_PageUp( self, info ):
        self.scroll( -(self.height()-1) )

    ## １ページ下方向にスクロールする
    def command_PageDown( self, info ):
        self.scroll( self.height()-1 )

    ## 前の差分位置にジャンプする
    def command_DiffPrev( self, info ):
        for i in range( len(self.left.diff)-1, -1, -1 ):
            if self.left.diff[i][0]-1 < self.left.scroll_info.pos + self.height()//2:
                self.left.scroll_info.pos = self.left.diff[i][0]-1 - self.height()//2
                self.right.scroll_info.pos = self.right.diff[i][0]-1 - self.height()//2
                if self.left.scroll_info.pos<0 : self.left.scroll_info.pos=0
                if self.right.scroll_info.pos<0 : self.right.scroll_info.pos=0
                self.paint()
                break

    ## 次の差分位置にジャンプする
    def command_DiffNext( self, info ):
        for i in range(len(self.left.diff)):
            if self.left.diff[i][0]-1 > self.left.scroll_info.pos + self.height()//2:
                self.left.scroll_info.pos = self.left.diff[i][0]-1 - self.height()//2
                self.right.scroll_info.pos = self.right.diff[i][0]-1 - self.height()//2
                if self.left.scroll_info.pos<0 : self.left.scroll_info.pos=0
                if self.right.scroll_info.pos<0 : self.right.scroll_info.pos=0
                self.paint()
                break

    ## テキスト差分ビューアを閉じる
    def command_Close( self, info ):
        self.destroy()

    ## 閲覧中のファイルをエディタで編集する
    def command_Edit( self, info ):
        if self.edit_handler!=None:
            self.edit_handler()

## @} diffviewer
