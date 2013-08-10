import os
import sys
import re
import time
import threading

import ckit
from ckit.ckit_const import *

import cfiler_native
import cfiler_wallpaper
import cfiler_statusbar
import cfiler_consolewindow

#--------------------------------------------------------------------

class RenameWindow( ckit.Window ):

    RESULT_CANCEL = 0
    RESULT_OK     = 1

    FOCUS_FILENAME = 0
    FOCUS_TIMESTAMP = 1
    FOCUS_READONLY = 2
    FOCUS_SYSTEM = 3
    FOCUS_HIDDEN = 4
    FOCUS_ARCHIVE = 5

    def __init__( self, x, y, parent_window, ini, item ):

        ckit.Window.__init__(
            self,
            x=x,
            y=y,
            width=42,
            height=10,
            origin= ORIGIN_X_CENTER | ORIGIN_Y_CENTER,
            parent_window=parent_window,
            bg_color = ckit.getColor("bg"),
            cursor0_color = ckit.getColor("cursor0"),
            cursor1_color = ckit.getColor("cursor1"),
            resizable = False,
            title = 'ファイル情報の変更',
            minimizebox = False,
            maximizebox = False,
            cursor = True,
            close_handler = self.onClose,
            keydown_handler = self.onKeyDown,
            char_handler = self.onChar,
            )

        self.setCursorPos( -1, -1 )

        self.item = item
        self.focus = RenameWindow.FOCUS_FILENAME
        self.result = RenameWindow.RESULT_CANCEL

        basename = os.path.basename( item.getName() )

        last_period_pos = basename.rfind(".")
        if last_period_pos>0 and last_period_pos>=len(basename)-5:
            selection = [ last_period_pos, last_period_pos ]
        else:
            selection = None

        self.filename_edit = ckit.EditWidget( self, 8, 1, self.width()-10, 1, basename, selection )

        self.timestamp_edit = ckit.TimeWidget( self, 18, 3, item.time() )

        self.original_attribute = item.attr()
        self.readonly_checkbox = ckit.CheckBoxWidget( self, 2, 5, self.width()-4, 1, "Read Only", self.original_attribute & ckit.FILE_ATTRIBUTE_READONLY )
        self.system_checkbox = ckit.CheckBoxWidget(   self, 2, 6, self.width()-4, 1, "System   ", self.original_attribute & ckit.FILE_ATTRIBUTE_SYSTEM )
        self.hidden_checkbox = ckit.CheckBoxWidget(   self, 2, 7, self.width()-4, 1, "Hidden   ", self.original_attribute & ckit.FILE_ATTRIBUTE_HIDDEN )
        self.archive_checkbox = ckit.CheckBoxWidget(  self, 2, 8, self.width()-4, 1, "Archive  ", self.original_attribute & ckit.FILE_ATTRIBUTE_ARCHIVE )

        try:
            self.wallpaper = cfiler_wallpaper.Wallpaper(self)
            self.wallpaper.copy( parent_window )
            self.wallpaper.adjust()
        except AttributeError:
            self.wallpaper = None

        self.paint()

    def onClose(self):
        self.result = RenameWindow.RESULT_CANCEL
        self.quit()

    def onEnter(self):
        self.result = RenameWindow.RESULT_OK
        self.quit()

    def onKeyDown( self, vk, mod ):

        if vk==VK_UP:
            if self.focus==RenameWindow.FOCUS_TIMESTAMP:
                self.focus=RenameWindow.FOCUS_FILENAME
            elif self.focus==RenameWindow.FOCUS_READONLY:
                self.focus=RenameWindow.FOCUS_TIMESTAMP
            elif self.focus==RenameWindow.FOCUS_SYSTEM:
                self.focus=RenameWindow.FOCUS_READONLY
            elif self.focus==RenameWindow.FOCUS_HIDDEN:
                self.focus=RenameWindow.FOCUS_SYSTEM
            elif self.focus==RenameWindow.FOCUS_ARCHIVE:
                self.focus=RenameWindow.FOCUS_HIDDEN
            self.paint()

        elif vk==VK_DOWN:
            if self.focus==RenameWindow.FOCUS_FILENAME:
                self.focus=RenameWindow.FOCUS_TIMESTAMP
            elif self.focus==RenameWindow.FOCUS_TIMESTAMP:
                self.focus=RenameWindow.FOCUS_READONLY
            elif self.focus==RenameWindow.FOCUS_READONLY:
                self.focus=RenameWindow.FOCUS_SYSTEM
            elif self.focus==RenameWindow.FOCUS_SYSTEM:
                self.focus=RenameWindow.FOCUS_HIDDEN
            elif self.focus==RenameWindow.FOCUS_HIDDEN:
                self.focus=RenameWindow.FOCUS_ARCHIVE
            self.paint()

        elif vk==VK_RETURN:
            self.onEnter()

        elif vk==VK_ESCAPE:
            self.result = RenameWindow.RESULT_CANCEL
            self.quit()

        else:
            if self.focus==RenameWindow.FOCUS_FILENAME:
                self.filename_edit.onKeyDown( vk, mod )
            elif self.focus==RenameWindow.FOCUS_TIMESTAMP:
                self.timestamp_edit.onKeyDown( vk, mod )
            elif self.focus==RenameWindow.FOCUS_READONLY:
                self.readonly_checkbox.onKeyDown( vk, mod )
            elif self.focus==RenameWindow.FOCUS_SYSTEM:
                self.system_checkbox.onKeyDown( vk, mod )
            elif self.focus==RenameWindow.FOCUS_HIDDEN:
                self.hidden_checkbox.onKeyDown( vk, mod )
            elif self.focus==RenameWindow.FOCUS_ARCHIVE:
                self.archive_checkbox.onKeyDown( vk, mod )

    def onChar( self, ch, mod ):
        if self.focus==RenameWindow.FOCUS_FILENAME:
            self.filename_edit.onChar( ch, mod )
        elif self.focus==RenameWindow.FOCUS_TIMESTAMP:
            self.timestamp_edit.onChar( ch, mod )
        else:
            pass

    def paint(self):

        attribute_normal = ckit.Attribute( fg=ckit.getColor("fg"))
        attribute_normal_selected = ckit.Attribute( fg=ckit.getColor("select_fg"), bg=ckit.getColor("select_bg"))

        if self.focus==RenameWindow.FOCUS_FILENAME:
            attr = attribute_normal_selected
        else:
            attr = attribute_normal
        self.putString( 2, 1, self.width()-2, 1, attr, "名前" )

        self.filename_edit.enableCursor(self.focus==RenameWindow.FOCUS_FILENAME)
        self.filename_edit.paint()


        if self.focus==RenameWindow.FOCUS_TIMESTAMP:
            attr = attribute_normal_selected
        else:
            attr = attribute_normal
        self.putString( 2, 3, self.width()-2, 1, attr, "タイムスタンプ" )

        self.timestamp_edit.enableCursor(self.focus==RenameWindow.FOCUS_TIMESTAMP)
        self.timestamp_edit.paint()

        self.readonly_checkbox.enableCursor(self.focus==RenameWindow.FOCUS_READONLY)
        self.readonly_checkbox.paint()

        self.system_checkbox.enableCursor(self.focus==RenameWindow.FOCUS_SYSTEM)
        self.system_checkbox.paint()

        self.hidden_checkbox.enableCursor(self.focus==RenameWindow.FOCUS_HIDDEN)
        self.hidden_checkbox.paint()

        self.archive_checkbox.enableCursor(self.focus==RenameWindow.FOCUS_ARCHIVE)
        self.archive_checkbox.paint()

    def getResult(self):
        if self.result:
            new_filename = self.filename_edit.getText()
            new_timestamp = self.timestamp_edit.getValue()
            new_attribute = (
                ( ckit.FILE_ATTRIBUTE_READONLY if self.readonly_checkbox.getValue() else 0 ) |
                ( ckit.FILE_ATTRIBUTE_SYSTEM if self.system_checkbox.getValue() else 0 ) |
                ( ckit.FILE_ATTRIBUTE_HIDDEN if self.hidden_checkbox.getValue() else 0 ) |
                ( ckit.FILE_ATTRIBUTE_ARCHIVE if self.archive_checkbox.getValue() else 0 )
                )
            return [ new_filename, new_timestamp, new_attribute ]
        else:
            return None


#--------------------------------------------------------------------

class MultiRenameWindow( ckit.Window ):

    RESULT_CANCEL = 0
    RESULT_OK     = 1

    FOCUS_RECURSIVE = 0
    FOCUS_TIMESTAMP = 1
    FOCUS_ALLCASE = 2
    FOCUS_EXTCASE = 3
    FOCUS_READONLY = 4
    FOCUS_SYSTEM = 5
    FOCUS_HIDDEN = 6
    FOCUS_ARCHIVE = 7

    def __init__( self, x, y, parent_window, ini, items ):

        self.ini = ini

        ckit.Window.__init__(
            self,
            x=x,
            y=y,
            width=44,
            height=13,
            origin= ORIGIN_X_CENTER | ORIGIN_Y_CENTER,
            parent_window=parent_window,
            bg_color = ckit.getColor("bg"),
            cursor0_color = ckit.getColor("cursor0"),
            cursor1_color = ckit.getColor("cursor1"),
            resizable = False,
            title = 'ファイル情報の一括変更',
            minimizebox = False,
            maximizebox = False,
            cursor = True,
            close_handler = self.onClose,
            keydown_handler = self.onKeyDown,
            char_handler = self.onChar,
            )

        self.setCursorPos( -1, -1 )

        self.focus = MultiRenameWindow.FOCUS_RECURSIVE
        self.result = MultiRenameWindow.RESULT_CANCEL

        self.recursive_checkbox = ckit.CheckBoxWidget( self, 2, 1, self.width()-4, 1, "Recursive", True )

        timestamp = time.localtime( time.time() )[:6]
        self.timestamp_checkbox = ckit.CheckBoxWidget( self, 2, 3, self.width()-4, 1, "タイムスタンプ", False )
        self.timestamp_edit = ckit.TimeWidget( self, 20, 3, timestamp )

        self.allcase_choice  = ckit.ChoiceWidget( self, 2,  5, self.width()-4, 1, "全体     ", [ "小文字", "変更なし", "大文字" ], 1 )
        self.extcase_choice  = ckit.ChoiceWidget( self, 2,  6, self.width()-4, 1, "拡張子   ", [ "小文字", "変更なし", "大文字" ], 1 )
        self.readonly_choice = ckit.ChoiceWidget( self, 2,  8, self.width()-4, 1, "Read Only   ", [ "OFF", "変更なし", "ON" ], 1 )
        self.system_choice   = ckit.ChoiceWidget( self, 2,  9, self.width()-4, 1, "System      ", [ "OFF", "変更なし", "ON" ], 1 )
        self.hidden_choice   = ckit.ChoiceWidget( self, 2, 10, self.width()-4, 1, "Hidden      ", [ "OFF", "変更なし", "ON" ], 1 )
        self.archive_choice  = ckit.ChoiceWidget( self, 2, 11, self.width()-4, 1, "Archive     ", [ "OFF", "変更なし", "ON" ], 1 )

        self.items = items

        try:
            self.wallpaper = cfiler_wallpaper.Wallpaper(self)
            self.wallpaper.copy( parent_window )
            self.wallpaper.adjust()
        except AttributeError:
            self.wallpaper = None

        self.paint()

    def centerOfWindowPixel(self):
        rect = self.getWindowRect()
        return ( (rect[0]+rect[2])//2, (rect[1]+rect[3])//2 )

    def onClose(self):
        self.result = MultiRenameWindow.RESULT_CANCEL
        self.quit()

    def onEnter(self):
        self.result = MultiRenameWindow.RESULT_OK
        self.quit()

    def onKeyDown( self, vk, mod ):

        if vk==VK_UP:
            if self.focus==MultiRenameWindow.FOCUS_TIMESTAMP:
                self.focus=MultiRenameWindow.FOCUS_RECURSIVE
            elif self.focus==MultiRenameWindow.FOCUS_ALLCASE:
                self.focus=MultiRenameWindow.FOCUS_TIMESTAMP
            elif self.focus==MultiRenameWindow.FOCUS_EXTCASE:
                self.focus=MultiRenameWindow.FOCUS_ALLCASE
            elif self.focus==MultiRenameWindow.FOCUS_READONLY:
                self.focus=MultiRenameWindow.FOCUS_EXTCASE
            elif self.focus==MultiRenameWindow.FOCUS_SYSTEM:
                self.focus=MultiRenameWindow.FOCUS_READONLY
            elif self.focus==MultiRenameWindow.FOCUS_HIDDEN:
                self.focus=MultiRenameWindow.FOCUS_SYSTEM
            elif self.focus==MultiRenameWindow.FOCUS_ARCHIVE:
                self.focus=MultiRenameWindow.FOCUS_HIDDEN
            self.paint()

        elif vk==VK_DOWN:
            if self.focus==MultiRenameWindow.FOCUS_RECURSIVE:
                self.focus=MultiRenameWindow.FOCUS_TIMESTAMP
            elif self.focus==MultiRenameWindow.FOCUS_TIMESTAMP:
                self.focus=MultiRenameWindow.FOCUS_ALLCASE
            elif self.focus==MultiRenameWindow.FOCUS_ALLCASE:
                self.focus=MultiRenameWindow.FOCUS_EXTCASE
            elif self.focus==MultiRenameWindow.FOCUS_EXTCASE:
                self.focus=MultiRenameWindow.FOCUS_READONLY
            elif self.focus==MultiRenameWindow.FOCUS_READONLY:
                self.focus=MultiRenameWindow.FOCUS_SYSTEM
            elif self.focus==MultiRenameWindow.FOCUS_SYSTEM:
                self.focus=MultiRenameWindow.FOCUS_HIDDEN
            elif self.focus==MultiRenameWindow.FOCUS_HIDDEN:
                self.focus=MultiRenameWindow.FOCUS_ARCHIVE
            self.paint()

        elif vk==VK_RETURN:
            self.onEnter()

        elif vk==VK_ESCAPE:
            self.result = MultiRenameWindow.RESULT_CANCEL
            self.quit()

        else:
            if self.focus==MultiRenameWindow.FOCUS_RECURSIVE:
                self.recursive_checkbox.onKeyDown( vk, mod )
            elif self.focus==MultiRenameWindow.FOCUS_TIMESTAMP:
                if vk==VK_SPACE:
                    self.timestamp_checkbox.onKeyDown( vk, mod )
                    self.paint()
                elif self.timestamp_checkbox.getValue():
                    self.timestamp_edit.onKeyDown( vk, mod )
            elif self.focus==MultiRenameWindow.FOCUS_ALLCASE:
                self.allcase_choice.onKeyDown( vk, mod )
            elif self.focus==MultiRenameWindow.FOCUS_EXTCASE:
                self.extcase_choice.onKeyDown( vk, mod )
            elif self.focus==MultiRenameWindow.FOCUS_READONLY:
                self.readonly_choice.onKeyDown( vk, mod )
            elif self.focus==MultiRenameWindow.FOCUS_SYSTEM:
                self.system_choice.onKeyDown( vk, mod )
            elif self.focus==MultiRenameWindow.FOCUS_HIDDEN:
                self.hidden_choice.onKeyDown( vk, mod )
            elif self.focus==MultiRenameWindow.FOCUS_ARCHIVE:
                self.archive_choice.onKeyDown( vk, mod )

    def onChar( self, ch, mod ):
        if self.focus==MultiRenameWindow.FOCUS_TIMESTAMP:
            self.timestamp_edit.onChar( ch, mod )
        else:
            pass

    def paint(self):

        self.recursive_checkbox.enableCursor(self.focus==MultiRenameWindow.FOCUS_RECURSIVE)
        self.recursive_checkbox.paint()

        self.timestamp_checkbox.enableCursor(self.focus==MultiRenameWindow.FOCUS_TIMESTAMP)
        self.timestamp_checkbox.paint()

        self.timestamp_edit.enableCursor( self.focus==MultiRenameWindow.FOCUS_TIMESTAMP and self.timestamp_checkbox.getValue() )
        self.timestamp_edit.paint()

        self.allcase_choice.enableCursor(self.focus==MultiRenameWindow.FOCUS_ALLCASE)
        self.allcase_choice.paint()

        self.extcase_choice.enableCursor(self.focus==MultiRenameWindow.FOCUS_EXTCASE)
        self.extcase_choice.paint()

        self.readonly_choice.enableCursor(self.focus==MultiRenameWindow.FOCUS_READONLY)
        self.readonly_choice.paint()

        self.system_choice.enableCursor(self.focus==MultiRenameWindow.FOCUS_SYSTEM)
        self.system_choice.paint()

        self.hidden_choice.enableCursor(self.focus==MultiRenameWindow.FOCUS_HIDDEN)
        self.hidden_choice.paint()

        self.archive_choice.enableCursor(self.focus==MultiRenameWindow.FOCUS_ARCHIVE)
        self.archive_choice.paint()

    def getResult(self):
        if self.result:
            recursive = self.recursive_checkbox.getValue()
            if self.timestamp_checkbox.getValue():
                new_timestamp = self.timestamp_edit.getValue()
            else:
                new_timestamp = None
            new_case = [
                self.allcase_choice.getValue(),
                self.extcase_choice.getValue(),
                ]
            new_attribute = [ 
                self.readonly_choice.getValue(),
                self.system_choice.getValue(),
                self.hidden_choice.getValue(),
                self.archive_choice.getValue()
                ]
            return [ recursive, new_timestamp, new_case, new_attribute ]
            
        else:
            return None
#--------------------------------------------------------------------

class BatchRenameWindow( ckit.Window ):

    RESULT_CANCEL = 0
    RESULT_OK     = 1

    FOCUS_OLD = 0
    FOCUS_NEW = 1
    FOCUS_REGEXP = 2
    FOCUS_IGNORECASE = 3

    def __init__( self, x, y, parent_window, ini, items ):

        self.ini = ini

        ckit.Window.__init__(
            self,
            x=x,
            y=y,
            width=42,
            height=9,
            origin= ORIGIN_X_CENTER | ORIGIN_Y_CENTER,
            parent_window=parent_window,
            bg_color = ckit.getColor("bg"),
            cursor0_color = ckit.getColor("cursor0"),
            cursor1_color = ckit.getColor("cursor1"),
            resizable = False,
            title = 'ファイル名の一括変換',
            minimizebox = False,
            maximizebox = False,
            cursor = True,
            close_handler = self.onClose,
            keydown_handler = self.onKeyDown,
            char_handler = self.onChar,
            )

        self.setCursorPos( -1, -1 )

        self.items = items
        self.focus = BatchRenameWindow.FOCUS_OLD
        self.result = BatchRenameWindow.RESULT_CANCEL

        old = ini.get( "BATCHRENAME", "old" )
        new = ini.get( "BATCHRENAME", "new" )
        regexp = ini.getint( "BATCHRENAME", "regexp" )
        ignorecase = ini.getint( "BATCHRENAME", "ignorecase" )

        self.old_edit = ckit.EditWidget( self, 10, 1, self.width()-12, 1, old, [ 0, len(old) ] )
        self.new_edit = ckit.EditWidget( self, 10, 3, self.width()-12, 1, new, [ 0, len(new) ] )
        self.regexp_checkbox = ckit.CheckBoxWidget( self, 2, 5, self.width()-4, 1, "正規表現", regexp )
        self.ignorecase_checkbox = ckit.CheckBoxWidget( self, 2, 6, self.width()-4, 1, "大文字/小文字を無視", ignorecase )

        client_rect = self.getClientRect()
        offset_x, offset_y = self.charToClient( 0, 0 )
        char_w, char_h = self.getCharSize()
        self.plane_statusbar = ckit.ThemePlane3x3( self, 'statusbar.png' )
        self.plane_statusbar.setPosSize( 0, (self.height()-1)*char_h+offset_y, client_rect[2], client_rect[3]-(self.height()-1)*char_h+offset_y )
        self.status_bar = cfiler_statusbar.StatusBar()
        self.status_bar_layer = cfiler_statusbar.SimpleStatusBarLayer()
        self.status_bar.registerLayer(self.status_bar_layer)

        self.updateStatusBar()

        try:
            self.wallpaper = cfiler_wallpaper.Wallpaper(self)
            self.wallpaper.copy( parent_window )
            self.wallpaper.adjust()
        except AttributeError:
            self.wallpaper = None

        self.paint()

    def onClose(self):
        self.result = BatchRenameWindow.RESULT_CANCEL
        self.quit()

    def onEnter(self):
        self.result = BatchRenameWindow.RESULT_OK
        self.quit()

    def onKeyDown( self, vk, mod ):

        if vk==VK_UP:
            if self.focus==BatchRenameWindow.FOCUS_NEW:
                self.focus=BatchRenameWindow.FOCUS_OLD
            elif self.focus==BatchRenameWindow.FOCUS_REGEXP:
                self.focus=BatchRenameWindow.FOCUS_NEW
            elif self.focus==BatchRenameWindow.FOCUS_IGNORECASE:
                self.focus=BatchRenameWindow.FOCUS_REGEXP
            self.updateStatusBar()
            self.paint()

        elif vk==VK_DOWN:
            if self.focus==BatchRenameWindow.FOCUS_OLD:
                self.focus=BatchRenameWindow.FOCUS_NEW
            elif self.focus==BatchRenameWindow.FOCUS_NEW:
                self.focus=BatchRenameWindow.FOCUS_REGEXP
            elif self.focus==BatchRenameWindow.FOCUS_REGEXP:
                self.focus=BatchRenameWindow.FOCUS_IGNORECASE
            self.updateStatusBar()
            self.paint()

        elif vk==VK_RETURN:
            self.onEnter()

        elif vk==VK_ESCAPE:
            self.result = BatchRenameWindow.RESULT_CANCEL
            self.quit()

        else:
            if self.focus==BatchRenameWindow.FOCUS_OLD:
                self.old_edit.onKeyDown( vk, mod )
            elif self.focus==BatchRenameWindow.FOCUS_NEW:
                self.new_edit.onKeyDown( vk, mod )
            elif self.focus==BatchRenameWindow.FOCUS_REGEXP:
                self.regexp_checkbox.onKeyDown( vk, mod )
            elif self.focus==BatchRenameWindow.FOCUS_IGNORECASE:
                self.ignorecase_checkbox.onKeyDown( vk, mod )

    def onChar( self, ch, mod ):
        if self.focus==BatchRenameWindow.FOCUS_OLD:
            self.old_edit.onChar( ch, mod )
        elif self.focus==BatchRenameWindow.FOCUS_NEW:
            self.new_edit.onChar( ch, mod )

    def updateStatusBar(self):
        if self.focus==BatchRenameWindow.FOCUS_OLD:
            if self.regexp_checkbox.getValue():
                self.status_bar_layer.setMessage("ファイル名全体に一致する正規表現")
            else:
                self.status_bar_layer.setMessage("ファイル名の一部に一致する文字列")
        elif self.focus==BatchRenameWindow.FOCUS_NEW:
            if self.regexp_checkbox.getValue():
                self.status_bar_layer.setMessage("\\0:全体 \\1～\\9:部分 \\d:連番")
            else:
                self.status_bar_layer.setMessage("ファイル名の一部を置き換える文字列")
        elif self.focus==BatchRenameWindow.FOCUS_REGEXP:
            self.status_bar_layer.setMessage("正規表現のOn/Off")
        elif self.focus==BatchRenameWindow.FOCUS_IGNORECASE:
            self.status_bar_layer.setMessage("")

    def paint(self):

        attribute_normal = ckit.Attribute( fg=ckit.getColor("fg"))
        attribute_normal_selected = ckit.Attribute( fg=ckit.getColor("select_fg"), bg=ckit.getColor("select_bg"))

        if self.focus==BatchRenameWindow.FOCUS_OLD:
            attr = attribute_normal_selected
        else:
            attr = attribute_normal
        self.putString( 2, 1, self.width()-2, 1, attr, "置換前" )

        self.old_edit.enableCursor(self.focus==BatchRenameWindow.FOCUS_OLD)
        self.old_edit.paint()


        if self.focus==BatchRenameWindow.FOCUS_NEW:
            attr = attribute_normal_selected
        else:
            attr = attribute_normal
        self.putString( 2, 3, self.width()-2, 1, attr, "置換後" )

        self.new_edit.enableCursor(self.focus==BatchRenameWindow.FOCUS_NEW)
        self.new_edit.paint()

        self.regexp_checkbox.enableCursor(self.focus==BatchRenameWindow.FOCUS_REGEXP)
        self.regexp_checkbox.paint()

        self.ignorecase_checkbox.enableCursor(self.focus==BatchRenameWindow.FOCUS_IGNORECASE)
        self.ignorecase_checkbox.paint()

        self.status_bar.paint( self, 0, self.height()-1, self.width(), 1 )

    def getResult(self):
        if self.result:
            return [ self.old_edit.getText(), self.new_edit.getText(), self.regexp_checkbox.getValue(), self.ignorecase_checkbox.getValue() ]
        else:
            return None

    def centerOfWindowInPixel(self):
        rect = self.getWindowRect()
        return ( (rect[0]+rect[2])//2, (rect[1]+rect[3])//2 )

