import sys
import os

from PIL import Image

import ckit
from ckit.ckit_const import *

import cfiler_misc
import cfiler_statusbar
import cfiler_resource
import cfiler_debug

## @addtogroup imageviewer
## @{

#--------------------------------------------------------------------

## 画像ビューアウインドウ
#
#  画像ビューアを実現しているクラスです。\n\n
#  設定ファイル config.py の configure_ImageViewer に渡される window 引数は、ImageViewer クラスのオブジェクトです。
#
class ImageViewer( ckit.Window ):

    move_speed = 30
    zoom_speed = 1.2

    def __init__( self, x, y, width, height, parent_window, ini, title, items, selection, cursor_handler, select_handler ):

        ckit.Window.__init__(
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
            sysmenu = True,
            close_handler = self.onClose,
            size_handler = self.onSize,
            keydown_handler = self.onKeyDown,
            )

        self.ini = ini

        client_rect = self.getClientRect()
        offset_x, offset_y = self.charToClient( 0, 0 )
        char_w, char_h = self.getCharSize()
        self.plane_statusbar = ckit.ThemePlane3x3( self, 'statusbar.png' )
        self.status_bar = cfiler_statusbar.StatusBar()
        self.status_bar_layer = cfiler_statusbar.SimpleStatusBarLayer()
        self.status_bar.registerLayer(self.status_bar_layer)

        self.job_queue = ckit.JobQueue()
        self.items = items
        self.cursor = selection
        self.plane = None
        self.img = None
        self.zoom_policy = self.ini.get( "IMAGEVIEWER", "zoom_policy" ).lower()
        if self.zoom_policy=="fit":
            self.fit = True
        else:
            self.fit = False
        self.pos = [0,0]
        
        self.cursor_handler = cursor_handler
        self.select_handler = select_handler

        self.configure()

        self.decode()

    def destroy(self):
        self.job_queue.cancel()
        self.job_queue.join()
        self.job_queue.destroy()
        ckit.Window.destroy(self)

    def configure(self):
        
        self.keymap = ckit.Keymap()

        self.keymap[ "Return" ] = self.command_Close
        self.keymap[ "Escape" ] = self.command_Close
        self.keymap[ "A-Return" ] = self.command_ToggleMaximize
        self.keymap[ "F" ] = self.command_ToggleMaximize
        self.keymap[ "Space" ] = self.command_SelectDown
        self.keymap[ "S-Space" ] = self.command_SelectUp
        self.keymap[ "S-Left" ] = self.command_ScrollLeft
        self.keymap[ "S-Right" ] = self.command_ScrollRight
        self.keymap[ "S-Up" ] = self.command_ScrollUp
        self.keymap[ "S-Down" ] = self.command_ScrollDown
        self.keymap[ "Up" ] = self.command_CursorUp
        self.keymap[ "Down" ] = self.command_CursorDown
        self.keymap[ "PageUp" ] = self.command_CursorPageUp
        self.keymap[ "PageDown" ] = self.command_CursorPageDown
        self.keymap[ "Delete" ] = self.command_ZoomIn
        self.keymap[ "Insert" ] = self.command_ZoomOut
        self.keymap[ "End" ] = self.command_ZoomPolicyFit
        self.keymap[ "Home" ] = self.command_ZoomPolicyOriginal

        ckit.callConfigFunc("configure_ImageViewer",self)

    def onClose(self):
        self.destroy()

    def onSize( self, width, height ):

        if self.zoom_policy=="fit" and self.fit:
            self.reset()

        self.paint()

    def onKeyDown( self, vk, mod ):

        try:
            func = self.keymap.table[ ckit.KeyEvent(vk,mod) ]
        except KeyError:
            return

        func()

        return True

    def saveini(self):
        self.ini.set( "IMAGEVIEWER", "zoom_policy", self.zoom_policy )

    def decode(self):
    
        item = self.items[self.cursor]
        info = [None]
        img = [None]

        def jobDecode( job_item ):
            try:
                pil_img = Image.open( item.open() )
                info[0] = "%d x %d  :  %s  :  %s " % (pil_img.size[0], pil_img.size[1], pil_img.format, pil_img.mode )
                pil_img = pil_img.convert( "RGBA" )
                img[0] = ckit.Image.fromString( pil_img.size, pil_img.tostring(), None, True )
            except Exception as e:
                cfiler_debug.printErrorInfo()
                print( "ERROR : 画像デコード失敗 : %s : %s" % ( e, item.getName() ) )
                info[0] = None
                img[0] = ckit.Image.fromString( (0,0), "" )

        def jobDecodeFinished( job_item ):
            if job_item.isCanceled() : return
            self.info = info[0]
            self.img = img[0]
            self.reset()
            self.paint()

        job_item = ckit.JobItem( jobDecode, jobDecodeFinished )
        self.job_queue.enqueue(job_item)

    def reset(self):

        if self.zoom_policy=="original":
        
            self._zoom = 1.0
            self.fit = False
            self.pos = [0,0]
        
        elif self.zoom_policy=="fit":

            self._zoom = 1.0
            if self.img:
                img_size = self.img.getSize()

                client_rect = self.getClientRect()
                offset_x, offset_y = self.charToClient( 0, 0 )
                char_w, char_h = self.getCharSize()
            
                area_size = ( client_rect[2]-client_rect[0], (self.height()-1)*char_h+offset_y )

                if img_size[1]>0 and area_size[1]>0:
                    if float(img_size[0])/float(img_size[1]) > float(area_size[0])/float(area_size[1]):
                        self._zoom = float(area_size[0])/float(img_size[0])
                    else:
                        self._zoom = float(area_size[1])/float(img_size[1])

            self.fit = True
            self.pos = [0,0]

    def move( self, xx, yy ):

        self.pos[0] += xx
        self.pos[1] += yy
        
        img_size = self.img.getSize()
        plane_size = ( int(img_size[0]*self._zoom), int(img_size[1]*self._zoom) )

        client_rect = self.getClientRect()
        offset_x, offset_y = self.charToClient( 0, 0 )
        char_w, char_h = self.getCharSize()
        
        area_size = ( client_rect[2]-client_rect[0], (self.height()-1)*char_h+offset_y )

        plane_topleft = [ (area_size[0]-plane_size[0])//2+self.pos[0], (area_size[1]-plane_size[1])/2+self.pos[1] ]

        if plane_size[0]<=area_size[0] : self.pos[0] = 0
        elif plane_topleft[0]>0 : self.pos[0] = -(area_size[0]-plane_size[0])//2
        elif plane_topleft[0]+plane_size[0]<area_size[0] : self.pos[0] = (area_size[0]-plane_size[0])//2

        if plane_size[1]<=area_size[1] : self.pos[1] = 0
        elif plane_topleft[1]>0 : self.pos[1]=-(area_size[1]-plane_size[1])//2
        elif plane_topleft[1]+plane_size[1]<area_size[1] : self.pos[1] = (area_size[1]-plane_size[1])//2

    def zoom( self, _zoom ):

        self._zoom *= _zoom
        if self._zoom < 0.1 : self._zoom = 0.1
        if self._zoom > 8.0 : self._zoom = 8.0
        
        self.fit = False
        
        self.pos[0] = int(self.pos[0] * _zoom)
        self.pos[1] = int(self.pos[1] * _zoom)

    def paint(self):

        width = self.width()
        height = self.height()

        client_rect = self.getClientRect()
        offset_x, offset_y = self.charToClient( 0, 0 )
        char_w, char_h = self.getCharSize()

        area_size = ( client_rect[2]-client_rect[0], (height-1)*char_h+offset_y )
        
        if not self.img : return

        img_size = self.img.getSize()
        plane_size = ( int(img_size[0]*self._zoom), int(img_size[1]*self._zoom) )
        plane_topleft = [ (area_size[0]-plane_size[0])//2+self.pos[0], (area_size[1]-plane_size[1])//2+self.pos[1] ]

        if self.plane:
            self.plane.destroy()

        self.plane = ckit.Plane( self, plane_topleft, plane_size, 4 )
        self.plane.setImage(self.img)

        self.setTitle( "%s - [ %s ]" % ( cfiler_resource.cfiler_appname, self.items[self.cursor].name ) )

        attribute_normal = ckit.Attribute( fg=ckit.getColor("fg"))
        for i in range(height-1):
            self.putString( 0, i, width, 1, attribute_normal, " " * width )

        self.plane_statusbar.setPosSize( 0, (height-1)*char_h+offset_y, client_rect[2], client_rect[3]-(height-1)*char_h+offset_y )
        
        if self.info:
            status_message_right = ":  %d%%  :  %s-mode  :  %s" % ( self._zoom*100, self.zoom_policy, self.info )
            error = False
        else:
            status_message_right = ": デコードエラー"
            error = True
        status_message_left = "[%d/%d]  %s" % ( self.cursor+1, len(self.items), self.items[self.cursor].name )
        status_message_left = ckit.adjustStringWidth( self, status_message_left, width-2-self.getStringWidth(status_message_right), ckit.ALIGN_LEFT, ckit.ELLIPSIS_RIGHT )
        self.status_bar_layer.setMessage( status_message_left + status_message_right, error )
        self.status_bar.paint( self, 0, height-1, width, 1 )

    #--------------------------------------------------------
    # ここから下のメソッドはキーに割り当てることができる
    #--------------------------------------------------------

    ## メインウインドウで、閲覧中のファイルを選択する
    def command_Select(self):
        if self.select_handler:
            self.select_handler(self.items[self.cursor])

    ## プレイリスト中の１つ次の画像を表示する
    def command_CursorDown(self):
        if self.job_queue.numItems()>0 : return
        if self.cursor+1>len(self.items)-1 : return
        self.cursor += 1
        if self.cursor_handler : self.cursor_handler(self.items[self.cursor])
        self.decode()

    ## プレイリスト中の１つ前の画像を表示する
    def command_CursorUp(self):
        if self.job_queue.numItems()>0 : return
        if self.cursor-1<0 : return
        self.cursor -= 1
        if self.cursor_handler : self.cursor_handler(self.items[self.cursor])
        self.decode()

    ## プレイリスト中の10個次の画像を表示する
    def command_CursorPageUp(self):
        if self.job_queue.numItems()>0 : return
        if self.cursor-1<0 : return
        self.cursor -= 10
        if self.cursor<0 : self.cursor=0
        if self.cursor_handler : self.cursor_handler(self.items[self.cursor])
        self.decode()

    ## プレイリスト中の10個前の画像を表示する
    def command_CursorPageDown(self):
        if self.job_queue.numItems()>0 : return
        if self.cursor+1>len(self.items)-1 : return
        self.cursor += 10
        if self.cursor>len(self.items)-1 : self.cursor=len(self.items)-1
        if self.cursor_handler : self.cursor_handler(self.items[self.cursor])
        self.decode()

    ## ファイルを選択して、１つ次の画像を表示する
    def command_SelectDown(self):
        self.command_Select()
        self.command_CursorDown()

    ## ファイルを選択して、１つ前の画像を表示する
    def command_SelectUp(self):
        self.command_Select()
        self.command_CursorUp()

    ## 左方向にスクロールする
    def command_ScrollLeft(self):
        self.move( ImageViewer.move_speed, 0 )
        self.paint()

    ## 右方向にスクロールする
    def command_ScrollRight(self):
        self.move( -ImageViewer.move_speed, 0 )
        self.paint()

    ## 上方向にスクロールする
    def command_ScrollUp(self):
        self.move( 0, ImageViewer.move_speed )
        self.paint()

    ## 下方向にスクロールする
    def command_ScrollDown(self):
        self.move( 0, -ImageViewer.move_speed )
        self.paint()

    ## ズームインする
    def command_ZoomIn(self):
        self.zoom(ImageViewer.zoom_speed)
        self.move(0,0)
        self.paint()

    ## ズームアウトする
    def command_ZoomOut(self):
        self.zoom(1/ImageViewer.zoom_speed)
        self.move(0,0)
        self.paint()

    ## ズームポリシーを [original] モードに設定する
    #
    #  [original]モードでは、画像を拡大縮小せずに、元々のサイズで表示します。
    #
    def command_ZoomPolicyOriginal(self):
        self.zoom_policy = "original"
        self.saveini()
        self.reset()
        self.paint()

    ## ズームポリシーを [fit] モードに設定する
    #
    #  [fit]モードでは、ウインドウに収まるように、画像を拡大縮小して表示します。
    #
    def command_ZoomPolicyFit(self):
        self.zoom_policy = "fit"
        self.saveini()
        self.reset()
        self.paint()

    ## 画像ビューアウインドウの最大化状態を切り替える
    def command_ToggleMaximize(self):
        if self.isMaximized():
            self.restore()
        else:
            self.maximize()

    ## 画像ビューアを閉じる
    def command_Close(self):
        self.destroy()

## @} imageviewer
