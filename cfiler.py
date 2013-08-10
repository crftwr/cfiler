from ckit import *

from pyauto import shellExecute

from cfiler_mainwindow import *
from cfiler_filelist import *
from cfiler_listwindow import *
from cfiler_msgbox import *
from cfiler_consolewindow import *
from cfiler_filecmp import *
from cfiler_archiver import *
from cfiler_misc import *
from cfiler_error import *
from cfiler_native import *

"""
## @mainpage 内骨格APIリファレンス
#
#  内骨格のカスタマイズや機能拡張をするためのリファレンスです。\n
#  \n
#  内骨格のオフィシャルサイトはこちらです。\n
#  http://sites.google.com/site/craftware/cfiler/ \n
#  \n
#  @par クラス
#  @ref cfiler_mainwindow.MainWindow        "MainWindow クラス"             \n
#  \n
#  @ref cfiler_filelist.FileList            "FileList クラス"               \n
#  \n
#  @ref cfiler_filelist.item_Default        "item_Default クラス"           \n
#  @ref cfiler_filelist.item_Archive        "item_Archive クラス"           \n
#  \n
#  @ref cfiler_filelist.filter_Default      "filter_Default クラス"         \n
#  @ref cfiler_filelist.filter_Bookmark     "filter_Bookmark クラス"        \n
#  \n
#  @ref cfiler_filelist.sorter_ByName       "sorter_ByName クラス"          \n
#  @ref cfiler_filelist.sorter_ByExt        "sorter_ByExt クラス"           \n
#  @ref cfiler_filelist.sorter_BySize       "sorter_BySize クラス"          \n
#  @ref cfiler_filelist.sorter_ByTimeStamp  "sorter_ByTimeStamp クラス"     \n
#  \n
#  @ref cfiler_textviewer.TextViewer        "TextViewer クラス"             \n
#  @ref cfiler_diffviewer.DiffViewer        "DiffViewer クラス"             \n
#  @ref cfiler_imageviewer.ImageViewer      "ImageViewer クラス"            \n
#  \n
#  @ref cfiler_listwindow.ListWindow        "ListWindow クラス"             \n
#  @ref cfiler_listwindow.ListItem          "ListItem クラス"               \n
#  \n
#  @ref cfiler_error.Error                  "Error クラス"                  \n
#  @ref cfiler_error.NotExistError          "NotExistError クラス"          \n
#  @ref cfiler_error.CanceledError          "CanceledError クラス"          \n
#  \n
#  @ref ckit.ckit_threadutil.JobItem        "JobItem クラス"                \n
#  @ref ckit.ckit_threadutil.JobQueue       "JobQueue クラス"               \n
#  @ref ckit.ckit_threadutil.SyncCall       "SyncCall クラス"               \n
#  \n
#  @ref ckit.ckit_widget.Widget             "Widget クラス"                 \n
#  @ref ckit.ckit_widget.ButtonWidget       "ButtonWidget クラス"           \n
#  @ref ckit.ckit_widget.CheckBoxWidget     "CheckBoxWidget クラス"         \n
#  @ref ckit.ckit_widget.ChoiceWidget       "ChoiceWidget クラス"           \n
#  @ref ckit.ckit_widget.ColorWidget        "ColorWidget クラス"            \n
#  @ref ckit.ckit_widget.EditWidget         "EditWidget クラス"             \n
#  @ref ckit.ckit_widget.HotKeyWidget       "HotKeyWidget クラス"           \n
#  @ref ckit.ckit_widget.ProgressBarWidget  "ProgressBarWidget クラス"      \n
#  @ref ckit.ckit_widget.TimeWidget         "TimeWidget クラス"             \n
#  \n
#  @par グローバル関数
#  @ref shellExecute()              "shellExecute()"                \n
#  \n
#  @ref popMenu()                   "popMenu()"                     \n
#  @ref popMessageBox()             "popMessageBox()"               \n
#  @ref popConsoleWindow()          "popConsoleWindow()"            \n
#  \n
#  @ref getClipboardText()          "getClipboardText()"            \n
#  @ref setClipboardText()          "setClipboardText()"            \n
#  \n
#  @ref compareFile()               "compareFile()"                 \n
#  \n
#  @ref joinPath()                  "joinPath()"                    \n
#  @ref splitPath()                 "splitPath()"                   \n
#  @ref rootPath()                  "rootPath()"                    \n
#  @ref normPath()                  "normPath()"                    \n
#
"""
