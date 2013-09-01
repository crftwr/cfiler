import os
import sys
import re

from PIL import Image

import ckit
from ckit.ckit_const import *

import cfiler_misc
import cfiler_wallpaper
import cfiler_history
import cfiler_statusbar
import cfiler_listwindow
import cfiler_resource
import cfiler_debug

## @addtogroup textviewer
## @{

#--------------------------------------------------------------------

## テキストビューアウインドウ
#
#  テキストビューアとバイナリビューアを実現しているクラスです。\n\n
#  設定ファイル config.py の configure_TextViewer に渡される window 引数は、TextViewer クラスのオブジェクトです。
#
class TextViewer( ckit.Window ):

    def __init__( self, x, y, width, height, main_window, ini, title, item, edit_handler=None ):
    
        ckit.Window.__init__(
            self,
            x=x,
            y=y,
            width=width,
            height=height,
            origin= ORIGIN_X_CENTER | ORIGIN_Y_CENTER,
            parent_window=main_window,
            bg_color = ckit.getColor("bg"),
            cursor0_color = ckit.getColor("cursor0"),
            cursor1_color = ckit.getColor("cursor1"),
            resizable = True,
            title = title,
            minimizebox = True,
            maximizebox = True,
            sysmenu=True,
            close_handler = self.onClose,
            size_handler = self._onSize,
            keydown_handler = self.onKeyDown,
            )

        self.main_window = main_window
        self.ini = ini

        self.setTitle( "%s - [ %s ]" % ( cfiler_resource.cfiler_appname, item.name ) )

        self.img = ckit.createThemeImage('lineno.png')
        self.plane = ckit.Plane( self, (0,0), (10,10), 1 )
        self.plane.setImage(self.img)

        try:
            self.wallpaper = cfiler_wallpaper.Wallpaper(self)
            self.wallpaper.copy( main_window )
            self.wallpaper.adjust()
        except AttributeError:
            self.wallpaper = None

        client_rect = self.getClientRect()
        offset_x, offset_y = self.charToClient( 0, 0 )
        char_w, char_h = self.getCharSize()
        self.plane_statusbar = ckit.ThemePlane3x3( self, 'statusbar.png' )
        self.status_bar = cfiler_statusbar.StatusBar()
        self.status_bar_layer = cfiler_statusbar.SimpleStatusBarLayer()
        self.status_bar.registerLayer(self.status_bar_layer)

        self.job_queue = ckit.JobQueue()

        self.item = item
        self.edit_handler = edit_handler
        self.scroll_info = ckit.ScrollInfo()
        self.scroll_info.makeVisible( 0, self.height()-1 )

        self.search_pattern = ""
        self.search_regexp = False
        self.search_ignorecase = False
        self.selection = [ [0,0], [0,0] ]

        self.load()

        self.configure()

    ## テキストビューアウインドウを破棄する
    def destroy(self):
        self.job_queue.cancel()
        self.job_queue.join()
        self.job_queue.destroy()
        ckit.Window.destroy(self)

    ## 設定を読み込む
    #
    #  キーマップなどをリセットした上で、config,py の configure_TextViewer() を呼び出します。
    #
    def configure(self):
        
        self.keymap = ckit.Keymap()
        self.keymap[ "Up" ] = self.command_ScrollUp
        self.keymap[ "Down" ] = self.command_ScrollDown
        self.keymap[ "PageUp" ] = self.command_PageUp
        self.keymap[ "Left" ] = self.command_PageUp
        self.keymap[ "PageDown" ] = self.command_PageDown
        self.keymap[ "Right" ] = self.command_PageDown
        self.keymap[ "E" ] = self.command_Edit
        self.keymap[ "F" ] = self.command_Search
        self.keymap[ "Space" ] = self.command_SearchNext
        self.keymap[ "S-Space" ] = self.command_SearchPrev
        self.keymap[ "Return" ] = self.command_Close
        self.keymap[ "Escape" ] = self.command_Close
        self.keymap[ "Z" ] = self.command_ConfigMenu

        ckit.callConfigFunc("configure_TextViewer",self)

    def load( self, auto=True, encoding=None ):
    
        self.load_finished = False
        
        def jobLoad( job_item ):

            try:
                self.data = self.item.open().read()
            except MemoryError:
                print( "ERROR : メモリ不足" )
                self.data = b""
            except Exception as e:
                cfiler_debug.printErrorInfo()
                print( e )
                self.data = b""
            
            if auto:
                self.encoding = ckit.detectTextEncoding(self.data)
                if self.encoding.bom:
                    self.data = self.data[len(self.encoding.bom):]
            else:
                self.encoding = encoding
                
                if self.encoding.encoding=='utf-8':
                    if self.data[:3] == b"\xEF\xBB\xBF":
                        self.encoding.bom = b"\xEF\xBB\xBF"
                        self.data = self.data[3:]
                elif self.encoding.encoding=='utf-16-le':
                    if self.data[:2] == b"\xFF\xFE":
                        self.encoding.bom = b"\xFF\xFE"
                        self.data = self.data[2:]
                elif self.encoding.encoding=='utf-16-be':
                    if self.data[:2] == b"\xFE\xFF":
                        self.encoding.bom = b"\xFE\xFF"
                        self.data = self.data[2:]
                
            self.binary = self.encoding.encoding==None

            if self.binary:
                pass
            else:
                unicode_data = self.data.decode( encoding=self.encoding.encoding, errors='replace' )
                self.lines = unicode_data.splitlines()

        def jobLoadFinished( job_item ):
            if job_item.isCanceled() : return
            self.load_finished = True
            self.paint()

        job_item = ckit.JobItem( jobLoad, jobLoadFinished )
        self.job_queue.enqueue(job_item)
        

    def onClose(self):
        self.destroy()

    def _onSize( self, width, height ):

        if self.wallpaper:
            self.wallpaper.adjust()

        self.paint()

    def _numLines(self):
        if self.binary:
            return (len(self.data)+15)//16
        else:
            return len(self.lines)

    ## テキストビューアウインドウの中心位置を、スクリーン座標系で返す
    #
    #  @return  ( X軸座標, Y軸座標 )
    #
    def centerOfWindowInPixel(self):
        rect = self.getWindowRect()
        return ( (rect[0]+rect[2])//2, (rect[1]+rect[3])//2 )

    ## 可視領域を返す
    #
    #  @return  ( 表示範囲の先頭の行番号, 表示範囲の末尾の行番号 )
    #
    def getVisibleRegion(self):
        try:
            return ( self.scroll_info.pos+1, min( self.scroll_info.pos+self.height(), len(self.lines) )+1 )
        except Exception:
            cfiler_debug.printErrorInfo()
            return ( 0, 0 )

    def onKeyDown( self, vk, mod ):

        try:
            func = self.keymap.table[ ckit.KeyEvent(vk,mod) ]
        except KeyError:
            return

        func()

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

        attribute_normal = ckit.Attribute( fg=ckit.getColor("fg"))
        attribute_select = ckit.Attribute( fg=ckit.getColor("select_fg"), bg=ckit.getColor("select_bg"))
        attribute_lineno = ckit.Attribute( fg=ckit.getColor("bar_fg"))

        if self.binary:
        
            self.plane.setSize( ( int((8+1.6)*char_w), (self.height()-1)*char_h+offset_y ) )
            self.plane_statusbar.setPosSize( 0, (self.height()-1)*char_h+offset_y, client_rect[2], client_rect[3]-(self.height()-1)*char_h+offset_y )

            for i in range(height-1):
                index = self.scroll_info.pos+i
                if index < self._numLines():

                    self.putString( 0, y+i, width, 1, attribute_normal, " " * width )

                    str_lineno = "%08x"%(index*16)
                    self.putString( 1, y+i, width, 1, attribute_lineno, str_lineno )

                    x = 12
                    for byte in self.data[ index*16 : index*16+8 ]:
                        self.putString( x, y+i, width, 1, attribute_normal, "%02x" % byte )
                        x += 3

                    x += 1

                    for byte in self.data[ index*16+8 : index*16+16 ]:
                        self.putString( x, y+i, width, 1, attribute_normal, "%02x" % byte )
                        x += 3


                    x = 65
                    for byte in self.data[ index*16 : index*16+16 ]:
                        if byte==0:
                            c = ' '
                        elif byte>=0x20 and byte<0x7f:
                            c = "%c" % byte
                        else:
                            c = "."
                        self.putString( x, y+i, width, 1, attribute_normal, c )
                        x += 1


                else:
                    self.putString( 0, y+i, width, 1, attribute_normal, " " * width )

            status_message = "%08x / %08x  :  %s " % ( self.scroll_info.pos*16, len(self.data), "binary" )
            status_message = ckit.adjustStringWidth( self, status_message, width-2, ckit.ALIGN_RIGHT )
            self.status_bar_layer.setMessage(status_message)
            self.status_bar.paint( self, 0, height-1, width, 1 )

        else:

            str_max_lineno = str(len(self.lines)+1)
            keta = len(str_max_lineno)

            self.plane.setSize( ( int((keta+1.6)*char_w), (self.height()-1)*char_h+offset_y ) )
            self.plane_statusbar.setPosSize( 0, (self.height()-1)*char_h+offset_y, client_rect[2], client_rect[3]-(self.height()-1)*char_h+offset_y )

            for i in range(height-1):
                index = self.scroll_info.pos+i
                if index < len(self.lines):
                
                    self.putString( 0, y+i, width, 1, attribute_normal, " " * width )

                    str_lineno = str(index+1)
                    self.putString( 1, y+i, width, 1, attribute_lineno, " "*(keta-len(str_lineno))+str_lineno )

                    if index < self.selection[0][0] or index > self.selection[1][0]:
                        self.putString( keta+2, y+i, width, 1, attribute_normal, ckit.expandTab(self,self.lines[index]) )
                    elif self.selection[0][0] < index < self.selection[1][0]:
                        self.putString( keta+2, y+i, width, 1, attribute_select, ckit.expandTab(self,self.lines[index]) )
                    else:

                        offset = 0
                        sel_left = 0
                        sel_right = len(self.lines[index])
                        
                        if index == self.selection[0][0]:
                            sel_left = self.selection[0][1]
                        if index == self.selection[1][0]:
                            sel_right = self.selection[1][1]

                        s = ckit.expandTab( self, self.lines[index][ : sel_left ], offset=offset )
                        self.putString( keta+2 + offset, y+i, width, 1, attribute_normal, s )
                        
                        offset += self.getStringWidth(s)

                        s = ckit.expandTab( self, self.lines[index][ sel_left : sel_right ], offset=offset )
                        self.putString( keta+2 + offset, y+i, width, 1, attribute_select, s )

                        offset += self.getStringWidth(s)

                        s = ckit.expandTab( self, self.lines[index][ sel_right : ], offset=offset )
                        self.putString( keta+2 + offset, y+i, width, 1, attribute_normal, s )

                else:
                    self.putString( 0, y+i, width, 1, attribute_normal, " " * width )

            status_message = "%d / %d  :  %s " % ( self.scroll_info.pos+1, len(self.lines), self.encoding )
            status_message = ckit.adjustStringWidth( self, status_message, width-2, ckit.ALIGN_RIGHT )
            self.status_bar_layer.setMessage(status_message)
            self.status_bar.paint( self, 0, height-1, width, 1 )

    #--------------------------------------------------------
    # ここから下のメソッドはキーに割り当てることができる
    #--------------------------------------------------------

    ## １行上方向にスクロールする
    def command_ScrollUp(self):
        self.scroll_info.pos -= 1
        if self.scroll_info.pos<0 : self.scroll_info.pos=0
        self.paint()

    ## １行下方向にスクロールする
    def command_ScrollDown(self):
        self.scroll_info.pos += 1
        if self.scroll_info.pos>self._numLines()-1 : self.scroll_info.pos=self._numLines()-1
        self.paint()

    ## １ページ上方向にスクロールする
    def command_PageUp(self):
        self.scroll_info.pos -= self.height()-1
        if self.scroll_info.pos<0 : self.scroll_info.pos=0
        self.paint()

    ## １ページ下方向にスクロールする
    def command_PageDown(self):
        self.scroll_info.pos += self.height()-1
        if self.scroll_info.pos>self._numLines()-1 : self.scroll_info.pos=self._numLines()-1
        self.paint()

    ## 閲覧中のファイルをエディタで編集する
    def command_Edit(self):
        if self.edit_handler!=None:
            self.edit_handler()

    ## テキスト中から文字列を検索する
    def command_Search(self):
    
        if self.binary : return

        pos = self.centerOfWindowInPixel()
        search_window = TextSearchWindow( pos[0], pos[1], self, self.ini )
        self.enable(False)
        search_window.messageLoop()
        result = search_window.getResult()
        self.enable(True)
        self.activate()
        search_window.destroy()

        if result==None : return
        self.search_pattern, self.search_regexp, self.search_ignorecase = result[0], result[1], result[2]
        
        self.command_SearchNext()

    def _searchNextPrev( self, direction ):
        
        if self.binary : return

        if direction>0:
            line_index = self.selection[1][0]
            char_index = self.selection[1][1]
        else:
            line_index = self.selection[0][0]
            char_index = self.selection[0][1]
        
        if self.search_regexp:
            try:
                if self.search_ignorecase:
                    re_pattern = re.compile( self.search_pattern, re.IGNORECASE )
                else:
                    re_pattern = re.compile( self.search_pattern )

            except Exception as e:
                cfiler_debug.printErrorInfo()
                print( "正規表現のエラー :", e )
                return

        else:
            if self.search_ignorecase:
                self.search_pattern = self.search_pattern.lower()

        while True:
        
            if self.search_regexp:
                
                re_result = None
                
                if direction>0:
                    for i in re_pattern.finditer( self.lines[line_index], char_index ):
                         re_result = i
                         break
                else:
                    for i in re_pattern.finditer( self.lines[line_index], 0, char_index ):
                         re_result = i

                if re_result:
                    pos = re_result.start()
                    hit_length = re_result.end() - re_result.start()
                    break

            else:
                if self.search_ignorecase:
                    line = self.lines[line_index].lower()
                else:
                    line = self.lines[line_index]

                if direction>0:
                    pos = line.find( self.search_pattern, char_index )
                else:
                    pos = line.rfind( self.search_pattern, 0, char_index )
                
                if pos>=0:
                    hit_length = len(self.search_pattern)
                    break

            line_index += direction
            if direction>0:
                char_index = 0
            else:
                char_index = len(self.lines[line_index])

            if line_index<0 or line_index>=len(self.lines) : return
        
        self.scroll_info.makeVisible( line_index, self.height()-1, 3 )

        self.selection = [ [ line_index, pos ], [ line_index, pos + hit_length ] ]

        self.paint()

    ## 前回検索した文字列を使って次の場所を検索する
    def command_SearchNext(self):
        self._searchNextPrev(1)

    ## 前回検索した文字列を使って前の場所を検索する
    def command_SearchPrev(self):
        self._searchNextPrev(-1)
        
    ## 設定メニューをポップアップする
    def command_ConfigMenu(self):

        def loadAuto(item):
            self.load( auto=True )
            self.scroll_info.makeVisible( 0, self.height()-1 )

        def loadExplicitEncoding(item):
            self.load( auto=False, encoding=item[2] )
            self.scroll_info.makeVisible( 0, self.height()-1 )

        items = [
            ( "A : 自動判別", loadAuto ),
            ( "S : S-JIS", loadExplicitEncoding, ckit.TextEncoding("cp932") ),
            ( "E : EUC-JP", loadExplicitEncoding, ckit.TextEncoding("euc-jp") ),
            ( "J : JIS", loadExplicitEncoding, ckit.TextEncoding("iso-2022-jp") ),
            ( "U : UTF-8", loadExplicitEncoding, ckit.TextEncoding("utf-8") ),
            ( "U : UTF-16LE", loadExplicitEncoding, ckit.TextEncoding("utf-16-le") ),
            ( "U : UTF-16BE", loadExplicitEncoding, ckit.TextEncoding("utf-16-be") ),
            ( "B : バイナリ", loadExplicitEncoding, ckit.TextEncoding(None) ),
        ]

        select = cfiler_listwindow.popMenu( self, "設定メニュー", items, 0, onekey_decide=True )
        if select<0 : return

        items[select][1]( items[select] )

    ## テキストビューアを閉じる
    def command_Close(self):
        self.destroy()


#--------------------------------------------------------------------

class TextSearchWindow( ckit.Window ):

    RESULT_CANCEL = 0
    RESULT_OK     = 1

    FOCUS_PATTERN = 0
    FOCUS_REGEXP = 1
    FOCUS_IGNORECASE = 2

    def __init__( self, x, y, parent_window, ini ):

        ckit.Window.__init__(
            self,
            x=x,
            y=y,
            width=42,
            height=6,
            origin= ORIGIN_X_CENTER | ORIGIN_Y_CENTER,
            parent_window=parent_window,
            bg_color = ckit.getColor("bg"),
            cursor0_color = ckit.getColor("cursor0"),
            cursor1_color = ckit.getColor("cursor1"),
            resizable = False,
            title = 'Search',
            minimizebox = False,
            maximizebox = False,
            cursor = True,
            close_handler = self.onClose,
            keydown_handler = self.onKeyDown,
            char_handler = self.onChar,
            )

        self.setCursorPos( -1, -1 )

        self.focus = TextSearchWindow.FOCUS_PATTERN
        self.result = TextSearchWindow.RESULT_CANCEL
        self.ini = ini

        self.grep_history = cfiler_history.History()
        self.grep_history.load( self.ini, "GREP" )

        if len(self.grep_history.items)>0:
            pattern = self.grep_history.items[0]
        else:
            pattern = ""
        regexp = ini.getint( "GREP", "regexp" )
        ignorecase = ini.getint( "GREP", "ignorecase" )

        self.pattern_edit = ckit.EditWidget( self, 14, 1, self.width()-16, 1, pattern, [ 0, len(pattern) ], candidate_handler=self.grep_history.candidateHandler, candidate_remove_handler=self.grep_history.candidateRemoveHandler )
        self.regexp_checkbox = ckit.CheckBoxWidget( self, 2, 3, self.width()-4, 1, "正規表現", regexp )
        self.ignorecase_checkbox = ckit.CheckBoxWidget( self, 2, 4, self.width()-4, 1, "大文字/小文字を無視", ignorecase )

        try:
            self.wallpaper = cfiler_wallpaper.Wallpaper(self)
            self.wallpaper.copy( parent_window )
            self.wallpaper.adjust()
        except AttributeError:
            self.wallpaper = None

        self.paint()

    def saveState(self):
        self.grep_history.append(self.pattern_edit.getText())
        self.grep_history.save( self.ini, "GREP" )
        self.ini.set( "GREP", "regexp", str(int(self.regexp_checkbox.getValue())) )
        self.ini.set( "GREP", "ignorecase", str(int(self.ignorecase_checkbox.getValue())) )

    def onClose(self):
        self.result = TextSearchWindow.RESULT_CANCEL
        self.saveState()
        self.quit()

    def onEnter(self):
        self.result = TextSearchWindow.RESULT_OK
        self.saveState()
        self.quit()

    def onKeyDown( self, vk, mod ):
    
        if self.focus==TextSearchWindow.FOCUS_PATTERN and self.pattern_edit.isListOpened():
            if vk==VK_RETURN or vk==VK_ESCAPE:
                self.pattern_edit.closeList()
            else:
                self.pattern_edit.onKeyDown( vk, mod )

        elif vk==VK_UP or (vk==VK_TAB and mod==MODKEY_SHIFT):
            if self.focus==TextSearchWindow.FOCUS_REGEXP:
                self.focus=TextSearchWindow.FOCUS_PATTERN
            elif self.focus==TextSearchWindow.FOCUS_IGNORECASE:
                self.focus=TextSearchWindow.FOCUS_REGEXP
            self.paint()

        elif vk==VK_DOWN or vk==VK_TAB:
            if self.focus==TextSearchWindow.FOCUS_PATTERN:
                self.focus=TextSearchWindow.FOCUS_REGEXP
            elif self.focus==TextSearchWindow.FOCUS_REGEXP:
                self.focus=TextSearchWindow.FOCUS_IGNORECASE
            self.paint()

        elif vk==VK_RETURN:
            self.onEnter()

        elif vk==VK_ESCAPE:
            self.onClose()

        else:
            if self.focus==TextSearchWindow.FOCUS_PATTERN:
                self.pattern_edit.onKeyDown( vk, mod )
            elif self.focus==TextSearchWindow.FOCUS_REGEXP:
                self.regexp_checkbox.onKeyDown( vk, mod )
            elif self.focus==TextSearchWindow.FOCUS_IGNORECASE:
                self.ignorecase_checkbox.onKeyDown( vk, mod )

    def onChar( self, ch, mod ):
        if self.focus==TextSearchWindow.FOCUS_PATTERN:
            self.pattern_edit.onChar( ch, mod )
        else:
            pass

    def paint(self):

        if self.focus==TextSearchWindow.FOCUS_PATTERN:
            attr = ckit.Attribute( fg=ckit.getColor("select_fg"), bg=ckit.getColor("select_bg"))
        else:
            attr = ckit.Attribute( fg=ckit.getColor("fg"))
        self.putString( 2, 1, self.width()-2, 1, attr, "検索文字列" )

        self.pattern_edit.enableCursor(self.focus==TextSearchWindow.FOCUS_PATTERN)
        self.pattern_edit.paint()

        self.regexp_checkbox.enableCursor(self.focus==TextSearchWindow.FOCUS_REGEXP)
        self.regexp_checkbox.paint()

        self.ignorecase_checkbox.enableCursor(self.focus==TextSearchWindow.FOCUS_IGNORECASE)
        self.ignorecase_checkbox.paint()


    def getResult(self):
        if self.result:
            return [ self.pattern_edit.getText(), self.regexp_checkbox.getValue(), self.ignorecase_checkbox.getValue() ]
        else:
            return None

## @} textviewer
