import os
import sys

import ckit
from ckit.ckit_const import *

## @addtogroup resultwindow コンソールウインドウ機能
## @{

#--------------------------------------------------------------------

class ResultWindow( ckit.TextWindow ):

    def __init__( self, x, y, width, height, parent_window, ini, title, keydown_hook=None ):

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
            minimizebox = True,
            maximizebox = True,
            close_handler = self.onClose,
            size_handler = self._onSize,
            keydown_handler = self.onKeyDown,
            )

        self.lines = [""]
        self.last_line_terminated = False

        self.keydown_hook = keydown_hook

        self.scroll_info = ckit.ScrollInfo()

        self.scroll_info.makeVisible( 0, self.height() )

        try:
            self.wallpaper = ckit.Wallpaper(self)
            self.wallpaper.copy( parent_window )
            self.wallpaper.adjust()
        except AttributeError:
            self.wallpaper = None

        self.paint()

    def onClose(self):
        self.quit()

    def _onSize( self, width, height ):

        if self.wallpaper:
            self.wallpaper.adjust()

        self.paint()

    def numLines(self):
        return len(self.lines)

    def getLine(self,lineno):
        return self.lines[lineno]

    def write( self, s, paint=True ):

        for line in s.splitlines(True):
            if self.last_line_terminated:
                if line.endswith("\n"):
                    self.lines.append(line.rstrip("\n"))
                    self.last_line_terminated = True
                else:
                    self.lines.append(line)
                    self.last_line_terminated = False
            else:
                if line.endswith("\n"):
                    self.lines[-1] += line.rstrip("\n")
                    self.last_line_terminated = True
                else:
                    self.lines[-1] += line
                    self.last_line_terminated = False
            
        if len(self.lines)>1000:
            self.lines = self.lines[-1000:]

        if paint:
            self.scroll_info.makeVisible( self.numLines()-1, self.height() )
            self.paint()

    def onKeyDown( self, vk, mod ):

        if self.keydown_hook:
            if self.keydown_hook( vk, mod ):
                return True

        if vk==VK_UP:
            self.scroll_info.pos -= 1
            if self.scroll_info.pos<0 : self.scroll_info.pos=0
            self.paint()
        elif vk==VK_DOWN:
            self.scroll_info.pos += 1
            if self.scroll_info.pos>self.numLines()-self.height() : self.scroll_info.pos=self.numLines()-self.height()
            if self.scroll_info.pos<0 : self.scroll_info.pos=0
            self.paint()
        elif vk==VK_PRIOR or vk==VK_LEFT:
            self.scroll_info.pos -= self.height()
            if self.scroll_info.pos<0 : self.scroll_info.pos=0
            self.paint()
        elif vk==VK_NEXT or vk==VK_RIGHT:
            self.scroll_info.pos += self.height()
            if self.scroll_info.pos>self.numLines()-self.height() : self.scroll_info.pos=self.numLines()-self.height()
            if self.scroll_info.pos<0 : self.scroll_info.pos=0
            self.paint()
        elif vk==VK_RETURN:
            self.quit()
        elif vk==VK_ESCAPE:
            self.quit()

    def paint(self):

        y=0
        width=self.width()
        height=self.height()

        client_rect = self.getClientRect()
        char_w, char_h = self.getCharSize()

        attribute_normal = ckit.Attribute( fg=ckit.getColor("fg"))

        for i in range(height):
            index = self.scroll_info.pos+i
            self.putString( 0, y+i, width, 1, attribute_normal, " " * width )
            if index < len(self.lines):
                self.putString( 0, y+i, width, 1, attribute_normal, self.lines[index] )


## コンソールウインドウを表示する
#
#  @param main_window    MainWindowオブジェクト
#  @param title          コンソールウインドウのタイトルバーに表示する文字列
#  @param message        メッセージ文字列
#  @param return_modkey  閉じたときのモディファイアキーの状態を取得するかどうか
#  @return               引数 return_modkey が False の場合は結果値、引数 return_modkey が True の場合は ( 結果値, モディファイアキーの状態 ) を返す
#
#  返値の結果値としては、Enter が押されたときは True、ESC が押されたときは False が返ります。
#
def popResultWindow( main_window, title, message, return_modkey=False ):

    result = [True]
    result_mod = [0]

    def onKeyDown( vk, mod ):
        if vk==VK_RETURN and mod==0:
            result[0] = True
            result_mod[0] = mod
            console_window.quit()
            return True
        elif vk==VK_ESCAPE and mod==0:
            result[0] = False
            result_mod[0] = mod
            console_window.quit()
            return True

    pos = main_window.centerOfWindowInPixel()
    console_window = ResultWindow( pos[0], pos[1], 60, 24, main_window, main_window.ini, title, onKeyDown )
    console_window.write(message)
    main_window.enable(False)
    console_window.messageLoop()
    main_window.enable(True)
    main_window.activate()
    console_window.destroy()
    
    if return_modkey:
        return result[0], result_mod[0]
    else:
        return result[0]
        
## @} resultwindow
