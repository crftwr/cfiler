import os
import threading

import ckit
from ckit.ckit_const import *

import cfiler_wallpaper
import cfiler_history

#--------------------------------------------------------------------

class GrepWindow( ckit.Window ):

    RESULT_CANCEL = 0
    RESULT_OK     = 1

    FOCUS_PATTERN = 0
    FOCUS_RECURSIVE = 1
    FOCUS_REGEXP = 2
    FOCUS_IGNORECASE = 3

    def __init__( self, x, y, parent_window, ini ):

        ckit.Window.__init__(
            self,
            x=x,
            y=y,
            width=42,
            height=7,
            origin= ORIGIN_X_CENTER | ORIGIN_Y_CENTER,
            parent_window=parent_window,
            bg_color = ckit.getColor("bg"),
            cursor0_color = ckit.getColor("cursor0"),
            cursor1_color = ckit.getColor("cursor1"),
            resizable = False,
            title = 'Grep',
            minimizebox = False,
            maximizebox = False,
            cursor = True,
            close_handler = self.onClose,
            keydown_handler = self.onKeyDown,
            char_handler = self.onChar,
            )

        self.setCursorPos( -1, -1 )

        self.focus = GrepWindow.FOCUS_PATTERN
        self.result = GrepWindow.RESULT_CANCEL
        self.ini = ini

        self.grep_history = cfiler_history.History()
        self.grep_history.load( self.ini, "GREP" )

        if len(self.grep_history.items)>0:
            pattern = self.grep_history.items[0]
        else:
            pattern = ""
        recursive = ini.getint( "GREP", "recursive" )
        regexp = ini.getint( "GREP", "regexp" )
        ignorecase = ini.getint( "GREP", "ignorecase" )

        self.pattern_edit = ckit.EditWidget( self, 14, 1, self.width()-16, 1, pattern, [ 0, len(pattern) ], candidate_handler=self.grep_history.candidateHandler, candidate_remove_handler=self.grep_history.candidateRemoveHandler )
        self.recursive_checkbox = ckit.CheckBoxWidget( self, 2, 3, self.width()-4, 1, "サブディレクトリ", recursive )
        self.regexp_checkbox = ckit.CheckBoxWidget( self, 2, 4, self.width()-4, 1, "正規表現", regexp )
        self.ignorecase_checkbox = ckit.CheckBoxWidget( self, 2, 5, self.width()-4, 1, "大文字/小文字を無視", ignorecase )

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
        self.ini.set( "GREP", "recursive", str(int(self.recursive_checkbox.getValue())) )
        self.ini.set( "GREP", "regexp", str(int(self.regexp_checkbox.getValue())) )
        self.ini.set( "GREP", "ignorecase", str(int(self.ignorecase_checkbox.getValue())) )

    def onClose(self):
        self.result = GrepWindow.RESULT_CANCEL
        self.saveState()
        self.quit()

    def onEnter(self):
        self.result = GrepWindow.RESULT_OK
        self.saveState()
        self.quit()

    def onKeyDown( self, vk, mod ):
    
        if self.focus==GrepWindow.FOCUS_PATTERN and self.pattern_edit.isListOpened():
            if vk==VK_RETURN or vk==VK_ESCAPE:
                self.pattern_edit.closeList()
            else:
                self.pattern_edit.onKeyDown( vk, mod )

        elif vk==VK_UP or (vk==VK_TAB and mod==MODKEY_SHIFT):
            if self.focus==GrepWindow.FOCUS_RECURSIVE:
                self.focus=GrepWindow.FOCUS_PATTERN
            elif self.focus==GrepWindow.FOCUS_REGEXP:
                self.focus=GrepWindow.FOCUS_RECURSIVE
            elif self.focus==GrepWindow.FOCUS_IGNORECASE:
                self.focus=GrepWindow.FOCUS_REGEXP
            self.paint()

        elif vk==VK_DOWN or vk==VK_TAB:
            if self.focus==GrepWindow.FOCUS_PATTERN:
                self.focus=GrepWindow.FOCUS_RECURSIVE
            elif self.focus==GrepWindow.FOCUS_RECURSIVE:
                self.focus=GrepWindow.FOCUS_REGEXP
            elif self.focus==GrepWindow.FOCUS_REGEXP:
                self.focus=GrepWindow.FOCUS_IGNORECASE
            self.paint()

        elif vk==VK_RETURN:
            self.onEnter()

        elif vk==VK_ESCAPE:
            self.onClose()

        else:
            if self.focus==GrepWindow.FOCUS_PATTERN:
                self.pattern_edit.onKeyDown( vk, mod )
            elif self.focus==GrepWindow.FOCUS_RECURSIVE:
                self.recursive_checkbox.onKeyDown( vk, mod )
            elif self.focus==GrepWindow.FOCUS_REGEXP:
                self.regexp_checkbox.onKeyDown( vk, mod )
            elif self.focus==GrepWindow.FOCUS_IGNORECASE:
                self.ignorecase_checkbox.onKeyDown( vk, mod )

    def onChar( self, ch, mod ):
        if self.focus==GrepWindow.FOCUS_PATTERN:
            self.pattern_edit.onChar( ch, mod )
        else:
            pass

    def paint(self):

        if self.focus==GrepWindow.FOCUS_PATTERN:
            attr = ckit.Attribute( fg=ckit.getColor("select_fg"), bg=ckit.getColor("select_bg"))
        else:
            attr = ckit.Attribute( fg=ckit.getColor("fg"))
        self.putString( 2, 1, self.width()-2, 1, attr, "検索文字列" )

        self.pattern_edit.enableCursor(self.focus==GrepWindow.FOCUS_PATTERN)
        self.pattern_edit.paint()

        self.recursive_checkbox.enableCursor(self.focus==GrepWindow.FOCUS_RECURSIVE)
        self.recursive_checkbox.paint()

        self.regexp_checkbox.enableCursor(self.focus==GrepWindow.FOCUS_REGEXP)
        self.regexp_checkbox.paint()

        self.ignorecase_checkbox.enableCursor(self.focus==GrepWindow.FOCUS_IGNORECASE)
        self.ignorecase_checkbox.paint()


    def getResult(self):
        if self.result:
            return [ self.pattern_edit.getText(), self.recursive_checkbox.getValue(), self.regexp_checkbox.getValue(), self.ignorecase_checkbox.getValue() ]
        else:
            return None
