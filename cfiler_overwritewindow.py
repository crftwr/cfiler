import os
import time

import ckit
from ckit.ckit_const import *

import cfiler_misc

#--------------------------------------------------------------------

class OverWriteWindow( ckit.TextWindow ):

    RESULT_CANCEL    = 0
    RESULT_FORCE     = 1
    RESULT_TIMESTAMP = 2
    RESULT_NO        = 3
    RESULT_RENAME    = 4

    def __init__( self, x, y, parent_window, ini, src_item, dst_item, default_result=RESULT_TIMESTAMP, filename='' ):

        ckit.TextWindow.__init__(
            self,
            x=x,
            y=y,
            width=46,
            height=12,
            origin= ORIGIN_X_CENTER | ORIGIN_Y_CENTER,
            parent_window=parent_window,
            bg_color = ckit.getColor("bg"),
            cursor0_color = ckit.getColor("cursor0"),
            cursor1_color = ckit.getColor("cursor1"),
            resizable = False,
            title = '同じ名前のファイルの上書き確認',
            minimizebox = False,
            maximizebox = False,
            cursor = True,
            close_handler = self.onClose,
            keydown_handler = self.onKeyDown,
            char_handler = self.onChar,
            )

        self.setCursorPos( -1, -1 )

        self.edit = ckit.EditWidget( self, 10, 7, self.width()-12, 1, filename )

        self.src_item = src_item
        self.dst_item = dst_item
        self.select = default_result
        self.shift = False

        try:
            self.wallpaper = ckit.Wallpaper(self)
            self.wallpaper.copy( parent_window )
            self.wallpaper.adjust()
        except AttributeError:
            self.wallpaper = None

        self.paint()

    def onClose(self):
        self.select = OverWriteWindow.RESULT_CANCEL
        self.quit()

    def onKeyDown( self, vk, mod ):

        if vk==VK_UP:
            if self.select==OverWriteWindow.RESULT_TIMESTAMP:
                self.select=OverWriteWindow.RESULT_FORCE
            elif self.select==OverWriteWindow.RESULT_NO:
                self.select=OverWriteWindow.RESULT_TIMESTAMP
            elif self.select==OverWriteWindow.RESULT_RENAME:
                self.select=OverWriteWindow.RESULT_NO
            self.paint()

        elif vk==VK_DOWN:
            if self.select==OverWriteWindow.RESULT_FORCE:
                self.select=OverWriteWindow.RESULT_TIMESTAMP
            elif self.select==OverWriteWindow.RESULT_TIMESTAMP:
                self.select=OverWriteWindow.RESULT_NO
            elif self.select==OverWriteWindow.RESULT_NO:
                self.select=OverWriteWindow.RESULT_RENAME
            self.paint()

        elif vk==VK_RETURN:
            if mod==MODKEY_SHIFT:
                self.shift = True
            self.quit()

        elif vk==VK_ESCAPE:
            self.select = OverWriteWindow.RESULT_CANCEL
            self.quit()

        else:
            if self.select==OverWriteWindow.RESULT_RENAME:
                self.edit.onKeyDown( vk, mod )

    def onChar( self, ch, mod ):
        if self.select==OverWriteWindow.RESULT_RENAME:
            self.edit.onChar( ch, mod )
        else:
            ch = chr(ch).upper()
            if ch=='F':
                self.select = OverWriteWindow.RESULT_FORCE
            elif ch=='T':
                self.select = OverWriteWindow.RESULT_TIMESTAMP
            elif ch=='N':
                self.select = OverWriteWindow.RESULT_NO
            elif ch=='R':
                self.select = OverWriteWindow.RESULT_RENAME
            self.paint()

    def paint(self):

        attribute_normal = ckit.Attribute( fg=ckit.getColor("fg"))
        attribute_normal_selected = ckit.Attribute( fg=ckit.getColor("select_fg"), bg=ckit.getColor("select_bg"))

        if self.select==OverWriteWindow.RESULT_FORCE:
            attr = attribute_normal_selected
            self.setCursorPos( -1, -1 )
        else:
            attr = attribute_normal
        self.putString( 2, 1, self.width()-4, 1, attr, "F 上書き" )


        if self.select==OverWriteWindow.RESULT_TIMESTAMP:
            attr = attribute_normal_selected
            self.setCursorPos( -1, -1 )
        else:
            attr = attribute_normal
        self.putString( 2, 3, self.width()-4, 1, attr, "T 新しければ上書き" )


        if self.select==OverWriteWindow.RESULT_NO:
            attr = attribute_normal_selected
            self.setCursorPos( -1, -1 )
        else:
            attr = attribute_normal
        self.putString( 2, 5, self.width()-4, 1, attr, "N 複写しない" )


        if self.select==OverWriteWindow.RESULT_RENAME:
            attr = attribute_normal_selected
            self.setCursorPos( -1, -1 )
        else:
            attr = attribute_normal
        self.putString( 2, 7, self.width()-4, 1, attr, "R 改名" )

        self.edit.enableCursor(self.select==OverWriteWindow.RESULT_RENAME)
        self.edit.paint()

        attr = attribute_normal

        def strTime(t):
            return "%02d/%02d/%02d %02d:%02d:%02d" % ( t[0]%100, t[1], t[2], t[3], t[4], t[5] )

        self.putString( 2, 9, 18, 1, attr, "Src : %s" % ( self.src_item.getNameNfc(), ) )
        self.putString( 20, 9, self.width()-20, 1, attr, "%6s %s" % ( cfiler_misc.getFileSizeString(self.src_item.size()), strTime(self.src_item.time()) ) )

        self.putString( 2, 10, 18, 1, attr, "Dst : %s" % ( self.dst_item.getNameNfc(), ) )
        self.putString( 20, 10, self.width()-20, 1, attr, "%6s %s" % ( cfiler_misc.getFileSizeString(self.dst_item.size()), strTime(self.dst_item.time()) ) )

    def getResult(self):
        return [ self.select, self.shift, self.edit.getText() ]
