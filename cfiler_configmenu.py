import os
import sys

import pyauto

import ckit
from ckit.ckit_const import *

import cfiler_filelist
import cfiler_listwindow
import cfiler_statusbar
import cfiler_wallpaper
import cfiler_misc
import cfiler_resource
import cfiler_error

#--------------------------------------------------------------------

def _configTheme( main_window ):

    def enumThemes():
        
        theme_list = []
        theme_parent = os.path.join( ckit.getAppExePath(), 'theme' )
        theme_dir_list = os.listdir(theme_parent)
        
        for theme_dir in theme_dir_list:
            
            if os.path.exists( os.path.join( theme_parent, theme_dir, "theme.ini" ) ):
                theme_list.append( theme_dir )
        
        return theme_list

    theme_list = enumThemes()

    current_theme_name = main_window.ini.get( "THEME", "name" )

    try:
        initial_select = theme_list.index(current_theme_name)
    except ValueError:
        initial_select = 0

    result = cfiler_listwindow.popMenu( main_window, "テーマ", theme_list, initial_select )
    if result<0 : return

    main_window.ini.set( "THEME", "name", theme_list[result] )
    
    main_window.reloadTheme()
    
    return False

def _configFontName( main_window ):
    font_list = main_window.enumFonts()

    current_font_name = main_window.ini.get( "FONT", "name" )

    try:
        initial_select = font_list.index(current_font_name)
    except ValueError:
        initial_select = 0

    select = cfiler_listwindow.popMenu( main_window, "フォント", font_list, initial_select )
    if select<0 : return

    main_window.ini.set( "FONT", "name", font_list[select] )

    main_window.setFont( main_window.ini.get("FONT","name"), main_window.ini.getint( "FONT", "size" ) )
    window_rect = main_window.getWindowRect()
    main_window.setPosSize( window_rect[0], window_rect[1], main_window.width(), main_window.height(), 0 )

def _configFontSize( main_window ):

    size_list = range(6,33)

    current_font_size = main_window.ini.getint( "FONT", "size" )

    try:
        initial_select = size_list.index(current_font_size)
    except ValueError:
        initial_select = 0

    size_list = list(map( str, size_list ))

    select = cfiler_listwindow.popMenu( main_window, "フォントサイズ", size_list, initial_select )
    if select<0 : return

    main_window.ini.set( "FONT", "size", size_list[select] )

    main_window.setFont( main_window.ini.get("FONT","name"), main_window.ini.getint( "FONT", "size" ) )
    window_rect = main_window.getWindowRect()
    main_window.setPosSize( window_rect[0], window_rect[1], main_window.width(), main_window.height(), 0 )

def _configWallpaperVisible( main_window ):

    items = []

    items.append( ( "非表示", "0" ) )
    items.append( ( "表示",   "1" ) )

    visible = main_window.ini.get( "WALLPAPER", "visible" )

    initial_select = 0
    for i in range(len(items)):
        if items[i][1]==visible:
            initial_select = i
            break

    select = cfiler_listwindow.popMenu( main_window, "壁紙の表示", items, initial_select )
    if select<0 : return

    main_window.ini.set( "WALLPAPER", "visible", items[select][1] )
    
    main_window.updateWallpaper()

def _configWallpaperStrength( main_window ):

    items = []

    items.append( ( " 10 %", "10" ) )
    items.append( ( " 20 %", "20" ) )
    items.append( ( " 30 %", "30" ) )
    items.append( ( " 40 %", "40" ) )
    items.append( ( " 50 %", "50" ) )
    items.append( ( " 60 %", "60" ) )
    items.append( ( " 70 %", "70" ) )
    items.append( ( " 80 %", "80" ) )
    items.append( ( " 90 %", "90" ) )
    items.append( ( "100 %", "100" ) )

    strength = main_window.ini.get( "WALLPAPER", "strength" )

    initial_select = 0
    for i in range(len(items)):
        if items[i][1]==strength:
            initial_select = i
            break

    select = cfiler_listwindow.popMenu( main_window, "壁紙の濃さ", items, initial_select )
    if select<0 : return

    main_window.ini.set( "WALLPAPER", "strength", items[select][1] )
    
    main_window.updateWallpaper()

def _configWallpaper( main_window ):

    select = 0
    
    while True:

        items = []

        items.append( ( "壁紙の表示の有無", _configWallpaperVisible ) )
        items.append( ( "壁紙の表示の濃さ", _configWallpaperStrength ) )

        select = cfiler_listwindow.popMenu( main_window, "壁紙オプション", items, select )
        if select<0 : return

        items[select][1]( main_window )

def _configAppName( main_window ):

    class AppNameWindow( ckit.TextWindow ):

        RESULT_CANCEL = 0
        RESULT_OK     = 1

        FOCUS_EDIT = 0

        def __init__( self, x, y, parent_window, ini ):

            ckit.TextWindow.__init__(
                self,
                x=x,
                y=y,
                width=48,
                height=3,
                origin= ORIGIN_X_CENTER | ORIGIN_Y_CENTER,
                parent_window=parent_window,
                bg_color = ckit.getColor("bg"),
                cursor0_color = ckit.getColor("cursor0"),
                cursor1_color = ckit.getColor("cursor1"),
                resizable = False,
                title = 'アプリケーション名のカスタマイズ',
                minimizebox = False,
                maximizebox = False,
                cursor = True,
                close_handler = self.onClose,
                keydown_handler = self.onKeyDown,
                char_handler = self.onChar,
                )

            self.setCursorPos( -1, -1 )

            self.focus = AppNameWindow.FOCUS_EDIT
            self.result = AppNameWindow.RESULT_CANCEL

            app_name = main_window.ini.get( "MISC", "app_name" )

            self.edit = ckit.EditWidget( self, 22, 1, self.width()-24, 1, app_name, [0,len(app_name)] )

            try:
                self.wallpaper = cfiler_wallpaper.Wallpaper(self)
                self.wallpaper.copy( parent_window )
                self.wallpaper.adjust()
            except AttributeError:
                self.wallpaper = None

            self.paint()

        def onClose(self):
            self.result = AppNameWindow.RESULT_CANCEL
            self.quit()

        def onEnter(self):
            self.result = AppNameWindow.RESULT_OK
            self.quit()

        def onKeyDown( self, vk, mod ):

            if vk==VK_RETURN:
                self.onEnter()

            elif vk==VK_ESCAPE:
                self.result = AppNameWindow.RESULT_CANCEL
                self.quit()

            else:
                if self.focus==AppNameWindow.FOCUS_EDIT:
                    self.edit.onKeyDown( vk, mod )

        def onChar( self, ch, mod ):
            if self.focus==AppNameWindow.FOCUS_EDIT:
                self.edit.onChar( ch, mod )
            else:
                pass

        def paint(self):

            if self.focus==AppNameWindow.FOCUS_EDIT:
                attr = ckit.Attribute( fg=ckit.getColor("select_fg"), bg=ckit.getColor("select_bg"))
            else:
                attr = ckit.Attribute( fg=ckit.getColor("fg"))
            self.putString( 2, 1, self.width()-2, 1, attr, "アプリケーション名" )

            self.edit.enableCursor(self.focus==AppNameWindow.FOCUS_EDIT)
            self.edit.paint()

        def getResult(self):
            if self.result:
                return [ self.edit.getText() ]
            else:
                return None

    pos = main_window.centerOfWindowInPixel()
    appname_window = AppNameWindow( pos[0], pos[1], main_window, main_window.ini )
    main_window.enable(False)
    appname_window.messageLoop()
    result = appname_window.getResult()
    main_window.enable(True)
    main_window.activate()
    appname_window.destroy()

    if result==None : return

    main_window.ini.set( "MISC", "app_name", result[0] )

    cfiler_resource.cfiler_appname = result[0]
    main_window.setTitle(cfiler_resource.cfiler_appname)
    main_window.command.About()


def _configKeymap( main_window ):

    items = []

    items.append( ( "デフォルト - 101キーボード", "101" ) )
    items.append( ( "デフォルト - 106キーボード", "106" ) )
    items.append( ( "AFX互換    - 101キーボード", "101afx" ) )
    items.append( ( "AFX互換    - 106キーボード", "106afx" ) )

    default_keymap = main_window.ini.get( "MISC", "default_keymap" )

    initial_select = 0
    for i in range(len(items)):
        if items[i][1]==default_keymap:
            initial_select = i
            break

    select = cfiler_listwindow.popMenu( main_window, "キー割り当て", items, initial_select )
    if select<0 : return

    main_window.ini.set( "MISC", "default_keymap", items[select][1] )

    main_window.configure()

def _configHotKey( main_window ):

    class HotKeyWindow( ckit.TextWindow ):

        RESULT_CANCEL = 0
        RESULT_OK     = 1

        def __init__( self, x, y, parent_window, ini ):

            ckit.TextWindow.__init__(
                self,
                x=x,
                y=y,
                width=29,
                height=2,
                origin= ORIGIN_X_CENTER | ORIGIN_Y_CENTER,
                parent_window=parent_window,
                bg_color = ckit.getColor("bg"),
                cursor0_color = ckit.getColor("cursor0"),
                cursor1_color = ckit.getColor("cursor1"),
                resizable = False,
                title = 'ホットキー',
                minimizebox = False,
                maximizebox = False,
                cursor = True,
                close_handler = self.onClose,
                keydown_handler = self.onKeyDown,
                )

            self.setCursorPos( -1, -1 )

            self.result = HotKeyWindow.RESULT_CANCEL

            activate_vk = ini.getint( "HOTKEY", "activate_vk" )
            activate_mod = ini.getint( "HOTKEY", "activate_mod" )

            self.activate_hotkey = ckit.HotKeyWidget( self, 0, 0, self.width(), 1, activate_vk, activate_mod )

            self.plane_statusbar = ckit.ThemePlane3x3( self, 'statusbar.png', 2 )
            client_rect = self.getClientRect()
            tmp, statusbar_top = self.charToClient( 0, self.height()-1 )
            self.plane_statusbar.setPosSize( 0, statusbar_top, client_rect[2]-0, client_rect[3]-statusbar_top )
            self.status_bar = cfiler_statusbar.StatusBar()
            self.status_bar_layer = cfiler_statusbar.SimpleStatusBarLayer()
            self.status_bar.registerLayer(self.status_bar_layer)

            self.updateStatusBar()

            self.paint()

        def onClose(self):
            self.result = HotKeyWindow.RESULT_CANCEL
            self.quit()

        def onEnter(self):
            self.result = HotKeyWindow.RESULT_OK
            self.quit()

        def onKeyDown( self, vk, mod ):
            if mod==0 and vk==VK_ESCAPE:
                self.result = HotKeyWindow.RESULT_CANCEL
                self.quit()
            elif mod==0 and vk==VK_RETURN:
                self.result = HotKeyWindow.RESULT_OK
                self.quit()
            else:
                self.activate_hotkey.onKeyDown( vk, mod )

        def updateStatusBar(self):
            self.status_bar_layer.setMessage("Return:決定  Esc:キャンセル")

        def paint(self):
            self.activate_hotkey.enableCursor(True)
            self.activate_hotkey.paint()

            self.status_bar.paint( self, 0, self.height()-1, self.width(), 1 )

        def getResult(self):
            if self.result:
                return [ self.activate_hotkey.getValue() ]
            else:
                return None


    pos = main_window.centerOfWindowInPixel()
    hotkey_window = HotKeyWindow( pos[0], pos[1], main_window, main_window.ini )
    main_window.enable(False)
    hotkey_window.messageLoop()
    result = hotkey_window.getResult()
    main_window.enable(True)
    main_window.activate()
    hotkey_window.destroy()

    if result==None : return

    main_window.ini.set( "HOTKEY", "activate_vk", str(result[0][0]) )
    main_window.ini.set( "HOTKEY", "activate_mod", str(result[0][1]) )

    main_window.updateHotKey()

def _configEsc( main_window ):

    items = []

    items.append( ( "何もしない", "none" ) )
    items.append( ( "非アクティブ化", "inactivate" ) )

    esc_action = main_window.ini.get( "MISC", "esc_action" )

    initial_select = 0
    for i in range(len(items)):
        if items[i][1]==esc_action :
            initial_select = i
            break

    select = cfiler_listwindow.popMenu( main_window, "Escキー動作選択", items, initial_select )
    if select<0 : return

    main_window.ini.set( "MISC", "esc_action", items[select][1] )

def _configMouse( main_window ):

    items = []

    items.append( ( "しない", "0" ) )
    items.append( ( "する", "1" ) )

    mouse_operation = main_window.ini.get( "MISC", "mouse_operation" )

    initial_select = 0
    for i in range(len(items)):
        if items[i][1]==mouse_operation:
            initial_select = i
            break

    select = cfiler_listwindow.popMenu( main_window, "マウス操作", items, initial_select )
    if select<0 : return

    main_window.ini.set( "MISC", "mouse_operation", items[select][1] )

def _configDelete( main_window ):

    items = []

    items.append( ( "デフォルトで%sの削除機能を使用する" % cfiler_resource.cfiler_appname, "builtin" ) )
    items.append( ( "デフォルトでOSのごみ箱を使用する", "recycle_bin" ) )

    delete_behavior = main_window.ini.get( "MISC", "delete_behavior" )

    initial_select = 0
    for i in range(len(items)):
        if items[i][1]==delete_behavior:
            initial_select = i
            break

    select = cfiler_listwindow.popMenu( main_window, "削除動作選択", items, initial_select )
    if select<0 : return

    main_window.ini.set( "MISC", "delete_behavior", items[select][1] )

def _configCompareTime( main_window ):

    items = []

    items.append( ( "1秒の差を無視する", "1" ) )
    items.append( ( "1秒の差を無視しない", "0" ) )

    ignore_1second = main_window.ini.get( "MISC", "ignore_1second" )

    initial_select = 0
    for i in range(len(items)):
        if items[i][1]==ignore_1second:
            initial_select = i
            break

    select = cfiler_listwindow.popMenu( main_window, "日時の比較動作選択", items, initial_select )
    if select<0 : return

    main_window.ini.set( "MISC", "ignore_1second", items[select][1] )

    cfiler_misc.ignore_1second = ( items[select][1] != "0" )


def _configISearch( main_window ):

    items = []

    items.append( ( "厳密     : ABC*", "strict" ) )
    items.append( ( "部分一致 : *ABC*", "partial" ) )
    items.append( ( "あいまい : *A*B*C*", "inaccurate" ) )
    items.append( ( "Migemo   : *AIUEO*", "migemo" ) )

    isearch_type = main_window.ini.get( "MISC", "isearch_type" )

    initial_select = 0
    for i in range(len(items)):
        if items[i][1]==isearch_type:
            initial_select = i
            break

    select = cfiler_listwindow.popMenu( main_window, "インクリメンタルサーチ動作選択", items, initial_select )
    if select<0 : return

    main_window.ini.set( "MISC", "isearch_type", items[select][1] )

def _configConfirm( main_window ):

    class ConfigConfirmWindow( ckit.TextWindow ):

        RESULT_CANCEL = 0
        RESULT_OK     = 1

        FOCUS_COPY = 0
        FOCUS_MOVE = 1
        FOCUS_EXTRACT = 2
        FOCUS_QUIT = 3

        def __init__( self, x, y, parent_window, ini ):

            ckit.TextWindow.__init__(
                self,
                x=x,
                y=y,
                width=22,
                height=6,
                origin= ORIGIN_X_CENTER | ORIGIN_Y_CENTER,
                parent_window=parent_window,
                bg_color = ckit.getColor("bg"),
                cursor0_color = ckit.getColor("cursor0"),
                cursor1_color = ckit.getColor("cursor1"),
                resizable = False,
                title = '確認の有無のカスタマイズ',
                minimizebox = False,
                maximizebox = False,
                cursor = True,
                close_handler = self.onClose,
                keydown_handler = self.onKeyDown,
                )

            self.setCursorPos( -1, -1 )

            self.focus = ConfigConfirmWindow.FOCUS_COPY
            self.result = ConfigConfirmWindow.RESULT_CANCEL

            confirm_copy = main_window.ini.getint( "MISC", "confirm_copy" )
            confirm_move = main_window.ini.getint( "MISC", "confirm_move" )
            confirm_extract = main_window.ini.getint( "MISC", "confirm_extract" )
            confirm_quit = main_window.ini.getint( "MISC", "confirm_quit" )

            self.confirm_copy_checkbox    = ckit.CheckBoxWidget( self, 2, 1, self.width()-4, 1, "コピー",         confirm_copy )
            self.confirm_move_checkbox    = ckit.CheckBoxWidget( self, 2, 2, self.width()-4, 1, "移動",           confirm_move )
            self.confirm_extract_checkbox = ckit.CheckBoxWidget( self, 2, 3, self.width()-4, 1, "アーカイブ展開", confirm_extract )
            self.confirm_quit_checkbox    = ckit.CheckBoxWidget( self, 2, 4, self.width()-4, 1, "終了",           confirm_quit )

            try:
                self.wallpaper = cfiler_wallpaper.Wallpaper(self)
                self.wallpaper.copy( parent_window )
                self.wallpaper.adjust()
            except AttributeError:
                self.wallpaper = None

            self.paint()

        def onClose(self):
            self.result = ConfigConfirmWindow.RESULT_CANCEL
            self.quit()

        def onEnter(self):

            main_window.ini.set( "MISC", "confirm_copy", str(int(self.confirm_copy_checkbox.getValue())) )
            main_window.ini.set( "MISC", "confirm_move", str(int(self.confirm_move_checkbox.getValue())) )
            main_window.ini.set( "MISC", "confirm_extract", str(int(self.confirm_extract_checkbox.getValue())) )
            main_window.ini.set( "MISC", "confirm_quit", str(int(self.confirm_quit_checkbox.getValue())) )

            self.result = ConfigConfirmWindow.RESULT_OK
            self.quit()

        def onKeyDown( self, vk, mod ):

            if vk==VK_RETURN:
                self.onEnter()

            elif vk==VK_ESCAPE:
                self.result = ConfigConfirmWindow.RESULT_CANCEL
                self.quit()

            if vk==VK_UP:
                if self.focus==ConfigConfirmWindow.FOCUS_MOVE:
                    self.focus=ConfigConfirmWindow.FOCUS_COPY
                elif self.focus==ConfigConfirmWindow.FOCUS_EXTRACT:
                    self.focus=ConfigConfirmWindow.FOCUS_MOVE
                elif self.focus==ConfigConfirmWindow.FOCUS_QUIT:
                    self.focus=ConfigConfirmWindow.FOCUS_EXTRACT
                self.paint()

            elif vk==VK_DOWN:
                if self.focus==ConfigConfirmWindow.FOCUS_COPY:
                    self.focus=ConfigConfirmWindow.FOCUS_MOVE
                elif self.focus==ConfigConfirmWindow.FOCUS_MOVE:
                    self.focus=ConfigConfirmWindow.FOCUS_EXTRACT
                elif self.focus==ConfigConfirmWindow.FOCUS_EXTRACT:
                    self.focus=ConfigConfirmWindow.FOCUS_QUIT
                self.paint()

            else:
                if self.focus==ConfigConfirmWindow.FOCUS_COPY:
                    self.confirm_copy_checkbox.onKeyDown( vk, mod )
                elif self.focus==ConfigConfirmWindow.FOCUS_MOVE:
                    self.confirm_move_checkbox.onKeyDown( vk, mod )
                elif self.focus==ConfigConfirmWindow.FOCUS_EXTRACT:
                    self.confirm_extract_checkbox.onKeyDown( vk, mod )
                elif self.focus==ConfigConfirmWindow.FOCUS_QUIT:
                    self.confirm_quit_checkbox.onKeyDown( vk, mod )

        def paint(self):

            self.confirm_copy_checkbox.enableCursor(self.focus==ConfigConfirmWindow.FOCUS_COPY)
            self.confirm_copy_checkbox.paint()

            self.confirm_move_checkbox.enableCursor(self.focus==ConfigConfirmWindow.FOCUS_MOVE)
            self.confirm_move_checkbox.paint()

            self.confirm_extract_checkbox.enableCursor(self.focus==ConfigConfirmWindow.FOCUS_EXTRACT)
            self.confirm_extract_checkbox.paint()

            self.confirm_quit_checkbox.enableCursor(self.focus==ConfigConfirmWindow.FOCUS_QUIT)
            self.confirm_quit_checkbox.paint()

        def getResult(self):
            return self.result

    pos = main_window.centerOfWindowInPixel()
    config_confirm_window = ConfigConfirmWindow( pos[0], pos[1], main_window, main_window.ini )
    main_window.enable(False)
    config_confirm_window.messageLoop()
    main_window.enable(True)
    main_window.activate()
    config_confirm_window.destroy()

def _configDirectorySeparator( main_window ):

    items = []

    items.append( ( "スラッシュ       : / ",  "slash" ) )
    items.append( ( "バックスラッシュ : \\ ", "backslash" ) )

    directory_separator = main_window.ini.get( "MISC", "directory_separator" )

    initial_select = 0
    for i in range(len(items)):
        if items[i][1]==directory_separator:
            initial_select = i
            break

    select = cfiler_listwindow.popMenu( main_window, "ディレクトリ区切り文字", items, initial_select )
    if select<0 : return

    main_window.ini.set( "MISC", "directory_separator", items[select][1] )

    if items[select][1]=="slash":
        ckit.setPathSlash(True)
    else:
        ckit.setPathSlash(False)

def _configDriveCase( main_window ):

    items = []

    items.append( ( "気にしない", "nocare" ) )
    items.append( ( "大文字", "upper" ) )
    items.append( ( "小文字", "lower" ) )

    drive_case = main_window.ini.get( "MISC", "drive_case" )

    initial_select = 0
    for i in range(len(items)):
        if items[i][1]==drive_case:
            initial_select = i
            break

    select = cfiler_listwindow.popMenu( main_window, "ドライブ文字の大文字/小文字", items, initial_select )
    if select<0 : return

    main_window.ini.set( "MISC", "drive_case", items[select][1] )

    if items[select][1]=="upper":
        ckit.setPathDriveUpper(True)
    elif items[select][1]=="lower":
        ckit.setPathDriveUpper(False)
    else:    
        ckit.setPathDriveUpper(None)

def _configNetworkUpdate( main_window ):

    items = []

    items.append( ( "無効",                        0 ) )
    items.append( ( "有効 (起動時毎回)",           1 ) )
    items.append( ( "有効 (1日に1回チェック)",     1000000 ) )
    items.append( ( "有効 (1週間に1回チェック)",   7000000 ) )

    check_frequency = main_window.ini.getint( "UPDATE", "check_frequency" )

    initial_select = 0
    for i in range(len(items)):
        if items[i][1]==check_frequency:
            initial_select = i
            break

    select = cfiler_listwindow.popMenu( main_window, "ネットワークアップデート機能", items, initial_select )
    if select<0 : return

    main_window.ini.set( "UPDATE", "check_frequency", str(items[select][1]) )

def _editConfigFile( main_window ):

    if callable(main_window.editor):
        location, filename = os.path.split(main_window.config_filename)
        item = cfiler_filelist.item_Default(
            location,
            filename
            )
        main_window.subThreadCall( main_window.editor, ( item, (1,1), location ) )
    else:
        main_window.subThreadCall( pyauto.shellExecute, ( None, main_window.editor, '"%s"' % main_window.config_filename, os.path.split(main_window.config_filename)[0] ) )

    return False

def _reloadConfigFile( main_window ):
    main_window.command.Reload()
    return False

def _configAppearance( main_window ):

    select = 0
    
    while True:

        items = []

        items.append( ( "テーマ", _configTheme ) )
        items.append( ( "フォント名", _configFontName ) )
        items.append( ( "フォントサイズ", _configFontSize ) )
        items.append( ( "壁紙オプション", _configWallpaper ) )
        items.append( ( "アプリケーション名", _configAppName ) )
        items.append( ( "ディレクトリ区切り文字", _configDirectorySeparator ) )
        items.append( ( "ドライブ文字", _configDriveCase ) )

        select = cfiler_listwindow.popMenu( main_window, "表示オプション", items, select )
        if select<0 : return

        items[select][1]( main_window )


def doConfigMenu( main_window ):

    def _showHiddenFile( main_window, item ):
        main_window.showHiddenFile( True )

    def _hideHiddenFile( main_window, item ):
        main_window.showHiddenFile( False )

    def _configItemString( main_window, item ):
        main_window.setItemFormat( item[2] )

    items = []

    if main_window.isHiddenFileVisible():
        items.append( ( "H : 隠しファイル    ON ⇒ OFF", _hideHiddenFile ) )
    else:
        items.append( ( "H : 隠しファイル   OFF ⇒ ON", _showHiddenFile ) )
    
    for itemformat_item in main_window.itemformat_list:
        items.append( ( itemformat_item[0], _configItemString, itemformat_item[1] ) )

    select = cfiler_listwindow.popMenu( main_window, "設定メニュー", items, 0, onekey_decide=True )
    if select<0 : return

    items[select][1]( main_window, items[select] )

def doConfigMenu2( main_window ):

    select = 0
    
    while True:

        items = []

        items.append( ( "表示オプション", _configAppearance ) )
        items.append( ( "キー割り当て", _configKeymap ) )
        items.append( ( "ホットキー設定", _configHotKey ) )
        items.append( ( "Escキー動作選択", _configEsc ) )
        items.append( ( "マウス操作", _configMouse ) )
        items.append( ( "削除動作選択", _configDelete ) )
        items.append( ( "日時の比較動作選択", _configCompareTime ) )
        items.append( ( "I-Search動作選択", _configISearch ) )
        items.append( ( "確認の有無", _configConfirm ) )
        items.append( ( "ネットワークアップデート", _configNetworkUpdate ) )
        items.append( ( "config.py を編集", _editConfigFile ) )
        items.append( ( "config.py をリロード", _reloadConfigFile ) )

        select = cfiler_listwindow.popMenu( main_window, "設定メニュー2", items, select )
        if select<0 : return

        loop_continue = items[select][1]( main_window )
        if loop_continue==False:
            return
