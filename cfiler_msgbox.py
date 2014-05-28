import ckit
from ckit.ckit_const import *

import cfiler_error

## @addtogroup msgbox
## @{

#--------------------------------------------------------------------

class MessageBox( ckit.TextWindow ):

    RESULT_CANCEL = 0
    RESULT_OK     = 1
    RESULT_YES    = 2
    RESULT_NO     = 3

    TYPE_OK    = 0
    TYPE_YESNO = 1

    BUTTON_OK  = 0
    BUTTON_YES = 1
    BUTTON_NO  = 2

    def __init__( self, x, y, parent_window, msgbox_type, title, message, return_modkey ):

        ckit.TextWindow.__init__(
            self,
            x=x,
            y=y,
            width=5,
            height=5,
            origin= ORIGIN_X_CENTER | ORIGIN_Y_CENTER,
            parent_window=parent_window,
            bg_color = ckit.getColor("bg"),
            show = False,
            resizable = False,
            title = title,
            minimizebox = False,
            maximizebox = False,
            close_handler = self.onClose,
            keydown_handler = self.onKeyDown,
            )
            
        lines = message.splitlines()
        
        self.message_width = 0
        for line in lines:
            self.message_width = max( self.message_width, self.getStringWidth(line) )

        window_width = self.message_width + 2
        if window_width<20 : window_width=20
        window_height = len(lines) + 4

        self.setPosSize(
            x=x,
            y=y,
            width=window_width,
            height=window_height,
            origin= ORIGIN_X_CENTER | ORIGIN_Y_CENTER
            )
        self.show(True)

        self.msgbox_type = msgbox_type
        self.lines = lines
        self.return_modkey = return_modkey

        if self.msgbox_type==MessageBox.TYPE_OK:
            self.focus = MessageBox.BUTTON_OK
        elif self.msgbox_type==MessageBox.TYPE_YESNO:
            self.focus = MessageBox.BUTTON_YES
        else:
            assert(False)

        self.result = MessageBox.RESULT_CANCEL
        self.result_mod = 0

        try:
            self.wallpaper = ckit.Wallpaper(self)
            self.wallpaper.copy( parent_window )
            self.wallpaper.adjust()
        except AttributeError:
            self.wallpaper = None

        self.paint()

    def onClose(self):
        self.quit()

    def onKeyDown( self, vk, mod ):
        if vk==VK_LEFT:
            if self.focus==MessageBox.BUTTON_NO:
                self.focus=MessageBox.BUTTON_YES
                self.paint()
        elif vk==VK_RIGHT:
            if self.focus==MessageBox.BUTTON_YES:
                self.focus=MessageBox.BUTTON_NO
                self.paint()
        elif vk==VK_RETURN:
            if self.focus==MessageBox.BUTTON_OK:
                self.result = MessageBox.RESULT_OK
                self.result_mod = mod
            elif self.focus==MessageBox.BUTTON_YES:
                self.result = MessageBox.RESULT_YES
                self.result_mod = mod
            elif self.focus==MessageBox.BUTTON_NO:
                self.result = MessageBox.RESULT_NO
                self.result_mod = mod
            self.quit()

        elif vk==VK_ESCAPE:
            if self.msgbox_type==MessageBox.TYPE_OK:
                self.result = MessageBox.RESULT_CANCEL
                self.result_mod = mod
                self.quit()
            elif self.msgbox_type==MessageBox.TYPE_YESNO:
                self.result = MessageBox.RESULT_CANCEL
                self.result_mod = mod
                self.quit()

    def paint(self):

        attribute_normal = ckit.Attribute( fg=ckit.getColor("fg"))
        attribute_normal_selected = ckit.Attribute( fg=ckit.getColor("select_fg"), bg=ckit.getColor("select_bg"))

        y = 1

        for line in self.lines:
            self.putString( (self.width()-self.message_width)//2, y, self.message_width, 1, attribute_normal, line )
            y += 1

        y += 1

        if self.msgbox_type==MessageBox.TYPE_OK:
            btn_string = " OK "
            btn_width = self.getStringWidth(btn_string)
            self.putString( (self.width()-btn_width)//2, y, btn_width, 1, attribute_normal_selected, btn_string )

        elif self.msgbox_type==MessageBox.TYPE_YESNO:

            btn1_string = "はい"
            btn1_width = self.getStringWidth(btn1_string)
            btn2_string = "いいえ"
            btn2_width = self.getStringWidth(btn2_string)

            if self.focus==MessageBox.BUTTON_YES:
                attr = attribute_normal_selected
            else:
                attr = attribute_normal

            self.putString( (self.width()-btn1_width-btn2_width-4)//2, y, btn1_width, 1, attr, btn1_string )

            if self.focus==MessageBox.BUTTON_NO:
                attr = attribute_normal_selected
            else:
                attr = attribute_normal

            self.putString( (self.width()+btn1_width-btn2_width+4)//2, y, btn2_width, 1, attr, btn2_string )

    def getResult(self):
        if self.return_modkey:
            return self.result, self.result_mod
        else:
            return self.result

## メッセージボックスを表示する
#
#  @param main_window    MainWindowオブジェクト
#  @param msgbox_type    メッセージボックスのタイプ
#  @param title          メッセージボックスのタイトルバーに表示する文字列
#  @param message        メッセージ文字列
#  @param return_modkey  閉じたときのモディファイアキーの状態を取得するかどうか
#  @return               引数 return_modkey が False の場合は結果値、引数 return_modkey が True の場合は ( 結果値, モディファイアキーの状態 ) を返す
#
#  引数 msgbox_type には、以下のいずれかを渡します。
#    - MessageBox.TYPE_OK \n
#       [ OK ] ボタンを１つ備えたメッセージボックス\n\n
#
#    - MessageBox.TYPE_YESNO \n
#       [はい] ボタンと [いいえ] ボタンを備えたメッセージボックス\n\n
#
#  返値の結果値としては、以下のいずれかが返ります。
#    - MessageBox.RESULT_CANCEL \n
#       キャンセルされた\n\n
#
#    - MessageBox.RESULT_OK \n
#       [ OK ]ボタンが選択された\n\n
#
#    - MessageBox.RESULT_YES \n
#       [ はい ]ボタンが選択された\n\n
#
#    - MessageBox.RESULT_NO \n
#       [ いいえ ]ボタンが選択された\n\n
#
def popMessageBox( main_window, msgbox_type, title, message, return_modkey=False ):
    pos = main_window.centerOfWindowInPixel()
    msgbox = MessageBox( pos[0], pos[1], main_window, msgbox_type, title, message, return_modkey )
    main_window.enable(False)
    msgbox.messageLoop()
    result = msgbox.getResult()
    main_window.enable(True)
    main_window.activate()
    msgbox.destroy()
    return result

## @} msgbox
