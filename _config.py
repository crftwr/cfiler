import os
import sys
import io
import urllib
import functools
import xml.etree.ElementTree

from cfiler import *


# 設定処理
def configure(window):

    # --------------------------------------------------------------------
    # F1 キーでヘルプファイルを表示する

    def command_Help(info):
        print( "Helpを起動 :" )
        help_path = os.path.join( getAppExePath(), 'doc\\index.html' )
        shellExecute( None, help_path, "", "" )
        print( "Done.\n" )

    window.keymap[ "F1" ] = command_Help

    # --------------------------------------------------------------------
    # F5 キーであふを起動する

    def command_LaunchAFX(info):
        print( "あふを起動 :" )
        left_location = os.path.join( window.leftFileList().getLocation(), "" )
        right_location = os.path.join( window.rightFileList().getLocation(), "" )
        print( "  Left  :", left_location )
        print( "  Right :", right_location )
        shellExecute( None, "c:/ols/afx/afx.exe", '-L"%s" -R"%s"' % (left_location,right_location), "" )
        print( "Done.\n" )

    window.keymap[ "F5" ] = command_LaunchAFX

    # --------------------------------------------------------------------
    # Shift-X キーでプログラム起動メニューを表示する

    def command_ProgramMenu(info):

        def launch_InternetExplorer():
            shellExecute( None, r"C:\Program Files\Internet Explorer\iexplore.exe", "", "" )

        def launch_CommandPrompt():
            shellExecute( None, r"cmd.exe", "", window.activeFileList().getLocation() )

        items = [
            ( "Internet Explorer", launch_InternetExplorer ),
            ( "Command Prompt",    launch_CommandPrompt )
        ]

        result = popMenu( window, "プログラム", items, 0 )
        if result<0 : return
        items[result][1]()

    window.keymap[ "S-X" ] = command_ProgramMenu

    # --------------------------------------------------------------------
    # Enter キーを押したときの動作をカスタマイズするためのフック

    def hook_Enter():

        if 0:
            print( "hook_Enter" )
            pane = window.activePane()
            item = pane.file_list.getItem(pane.cursor)

            # hook から True を返すと、デフォルトの動作がスキップされます
            return True

    window.enter_hook = hook_Enter

    # --------------------------------------------------------------------
    # テキストエディタを設定する

    if 1: # プログラムのファイルパスを設定 (単純な使用方法)
        window.editor = "notepad.exe"

    if 0: # 呼び出し可能オブジェクトを設定 (高度な使用方法)
        def editor( item, region, location ):
            shellExecute( None, "notepad.exe", '"%s"'% item.getFullpath(), location )
        window.editor = editor

    # --------------------------------------------------------------------
    # テキスト差分エディタを設定する
    #
    #   この例では外部テキストマージツールとして、WinMerge( http://winmerge.org/ )
    #   を使用しています。
    #   必要に応じてインストールしてください。

    if 0: # プログラムのファイルパスを設定 (単純な使用方法)
        window.diff_editor = "c:\\ols\\winmerge\\WinMergeU.exe"

    if 0: # 呼び出し可能オブジェクトを設定 (高度な使用方法)
        def diffEditor( left_item, right_item, location ):
            shellExecute( None, "c:\\ols\\winmerge\\WinMergeU.exe", '"%s" "%s"'% ( left_item.getFullpath(), right_item.getFullpath() ), location )
        window.diff_editor = diffEditor

    # --------------------------------------------------------------------
    # J キーで表示されるジャンプリスト

    window.jump_list += [
        ( "OLS",       "c:\\ols" ),
        ( "PROJECT",   "c:\\project" ),
        ( "MUSIC",     "e:\\music" ),
    ]

    # --------------------------------------------------------------------

    # ; キーで表示されるフィルタリスト
    window.filter_list += [
        ( "ALL",               filter_Default( "*" ) ),
        ( "SOURCE",            filter_Default( "*.cpp *.c *.h *.cs *.py *.pyw *.fx" ) ),
        ( "BOOKMARK",          filter_Bookmark() ),
    ]

    # --------------------------------------------------------------------
    # " キーで表示されるフィルタ選択リスト

    window.select_filter_list += [
        ( "SOURCE",        filter_Default( "*.cpp *.c *.h *.cs *.py *.pyw *.fx", dir_policy=None ) ),
        ( "BOOKMARK",      filter_Bookmark(dir_policy=None) ),
    ]

    # --------------------------------------------------------------------
    # アーカイブファイルのファイル名パターンとアーカイバの関連付け

    window.archiver_list = [
        ( "*.zip *.jar *.apk",  ZipArchiver ),
        ( "*.7z",               SevenZipArchiver ),
        ( "*.tgz *.tar.gz",     TgzArchiver ),
        ( "*.tbz2 *.tar.bz2",   Bz2Archiver ),
        ( "*.lzh",              LhaArchiver ),
        ( "*.rar",              RarArchiver ),
    ]

    # --------------------------------------------------------------------
    # ソースファイルでEnterされたときの関連付け処理

    def association_Video(item):
        shellExecute( None, r"wmplayer.exe", '/prefetch:7 /Play "%s"' % item.getFullpath(), "" )

    window.association_list += [
        ( "*.mpg *.mpeg *.avi *.wmv", association_Video ),
    ]


    # --------------------------------------------------------------------
    # ファイルアイテムの表示形式

    # 昨日以前については日時、今日については時間、を表示するアイテムの表示形式
    #
    #   引数:
    #       window   : メインウインドウ
    #       item     : アイテムオブジェクト
    #       width    : 表示領域の幅
    #       userdata : ファイルリストの描画中に一貫して使われるユーザデータオブジェクト
    #
    def itemformat_Name_Ext_Size_YYYYMMDDorHHMMSS( window, item, width, userdata ):

        if item.isdir():
            str_size = "<DIR>"
        else:
            str_size = "%6s" % getFileSizeString(item.size())

        if not hasattr(userdata,"now"):
            userdata.now = time.localtime()

        t = item.time()
        if t[0]==userdata.now[0] and t[1]==userdata.now[1] and t[2]==userdata.now[2]:
            str_time = "  %02d:%02d:%02d" % ( t[3], t[4], t[5] )
        else:
            str_time = "%04d/%02d/%02d" % ( t[0]%10000, t[1], t[2] )

        str_size_time = "%s %s" % ( str_size, str_time )

        width = max(40,width)
        filename_width = width-len(str_size_time)

        if item.isdir():
            body, ext = item.name, None
        else:
            body, ext = splitExt(item.name)

        if ext:
            body_width = min(width,filename_width-6)
            return ( adjustStringWidth(window,body,body_width,ALIGN_LEFT,ELLIPSIS_RIGHT)
                   + adjustStringWidth(window,ext,6,ALIGN_LEFT,ELLIPSIS_NONE)
                   + str_size_time )
        else:
            return ( adjustStringWidth(window,body,filename_width,ALIGN_LEFT,ELLIPSIS_RIGHT)
                   + str_size_time )

    # Z キーで表示されるファイル表示形式リスト
    window.itemformat_list = [
        ( "1 : 全て表示 : filename  .ext  99.9K YY/MM/DD HH:MM:SS", itemformat_Name_Ext_Size_YYMMDD_HHMMSS ),
        ( "2 : 秒を省略 : filename  .ext  99.9K YY/MM/DD HH:MM",    itemformat_Name_Ext_Size_YYMMDD_HHMM ),
        ( "3 : 日 or 時 : filename  .ext  99.9K YYYY/MM/DD",        itemformat_Name_Ext_Size_YYYYMMDDorHHMMSS ),
        ( "0 : 名前のみ : filename.ext",                            itemformat_NameExt ),
    ]
    
    # 表示形式の初期設定
    window.itemformat = itemformat_Name_Ext_Size_YYYYMMDDorHHMMSS

    # --------------------------------------------------------------------
    # "Google" コマンド
    #   Google でキーワードを検索します

    def command_Google(info):
        if len(info.args)>=1:
            keyword = ' '.join(info.args)
            keyword = urllib.quote_plus(keyword)
        else:
            keyword = ""
        url = "http://www.google.com/search?ie=utf8&q=%s" % keyword
        shellExecute( None, url, "", "" )

    # --------------------------------------------------------------------
    # "Eijiro" コマンド 
    #   英辞郎 on the WEB で日本語/英語を相互に検索します

    def command_Eijiro(info):
        if len(args)>=1:
            keyword = ' '.join(info.args)
            keyword = urllib.quote_plus(keyword)
        else:
            keyword = ""
        url = "http://eow.alc.co.jp/%s/UTF-8/" % keyword
        shellExecute( None, url, "", "" )

    # --------------------------------------------------------------------
    # "Subst" コマンド 
    #   任意のパスにドライブを割り当てるか、ドライブの解除を行います。
    #    subst;H;C:\dirname  : C:\dirname を Hドライブに割り当てます
    #    subst;H             : Hドライブの割り当てを解除します

    def command_Subst(info):
        
        if len(info.args)>=1:
            drive_letter = info.args[0]
            if len(info.args)>=2:
                path = info.args[1]
                if window.subProcessCall( [ "subst", drive_letter+":", os.path.normpath(path) ], cwd=None, env=None, enable_cancel=False )==0:
                    print( "%s に %sドライブを割り当てました。" % ( path, drive_letter ) )
            else:
                if window.subProcessCall( [ "subst", drive_letter+":", "/D" ], cwd=None, env=None, enable_cancel=False )==0:
                    print( "%sドライブの割り当てを解除しました。" % ( drive_letter ) )
        else:
            print( "ドライブの割り当て : Subst;<ドライブ名>;<パス>" )
            print( "ドライブの解除     : Subst;<ドライブ名>" )
            raise TypeError

    # --------------------------------------------------------------------
    # "NetDrive" コマンド
    #   ネットワークドライブを割り当てるか解除を行います。
    #    NetDrive;L;\\server\share : \\machine\public を Lドライブに割り当てます
    #    NetDrive;L                : Lドライブの割り当てを解除します

    def command_NetDrive(info):
        
        if len(info.args)>=1:
            drive_letter = info.args[0]
            if len(info.args)>=2:
                path = info.args[1]
                checkNetConnection(path)
                if window.subProcessCall( [ "net", "use", drive_letter+":", os.path.normpath(path), "/yes" ], cwd=None, env=None, enable_cancel=False )==0:
                    print( "%s に %sドライブを割り当てました。" % ( path, drive_letter ) )
            else:
                if window.subProcessCall( [ "net", "use", drive_letter+":", "/D" ], cwd=None, env=None, enable_cancel=False )==0:
                    print( "%sドライブの割り当てを解除しました。" % ( drive_letter ) )
        else:
            print( "ドライブの割り当て : NetDrive;<ドライブ名>;<パス>" )
            print( "ドライブの解除     : NetDrive;<ドライブ名>" )
            raise TypeError


    # --------------------------------------------------------------------
    # "CheckEmpty" コマンド 
    #   ファイルが入っていない空のディレクトリを検索します。
    #   ディレクトリが入っていても、ファイルが入っていない場合は空とみなします。

    def command_CheckEmpty(info):
        
        pane = window.activePane()
        location = window.activeFileList().getLocation()
        items = window.activeItems()

        result_items = []
        message = [""]

        def jobCheckEmpty( job_item ):

            def printBoth(s):
                print( s )
                message[0] += s + "\n"

            def appendResult(item):
                result_items.append(item)
                printBoth( '   %s' % item.getName() )

            printBoth( '空のディレクトリを検索 :' )

            # ビジーインジケータ On
            window.setProgressValue(None)

            for item in items:
                
                if not item.isdir() : continue
                
                if job_item.isCanceled(): break
                if job_item.waitPaused():
                    window.setProgressValue(None)
                
                empty = True
                
                for root, dirs, files in item.walk(False):

                    if job_item.isCanceled(): break
                    if job_item.waitPaused():
                        window.setProgressValue(None)

                    if not empty : break
                    for file in files:
                        empty = False
                        break
                
                if empty:
                    appendResult(item)

            message[0] += '\n'
            message[0] += '検索結果をファイルリストに反映しますか？(Enter/Esc):\n'
                
        def jobCheckEmptyFinished( job_item ):
        
            # ビジーインジケータ Off
            window.clearProgress()

            if job_item.isCanceled():
                print( '中断しました.\n' )
            else:
                print( 'Done.\n' )

            if job_item.isCanceled(): return

            result = popResultWindow( window, "検索完了", message[0] )
            if not result: return

            window.jumpLister( pane, lister_Custom( window, "[empty] ", location, result_items ) )

        job_item = ckit.JobItem( jobCheckEmpty, jobCheckEmptyFinished )
        window.taskEnqueue( job_item, "CheckEmpty" )


    # --------------------------------------------------------------------
    # "CheckDuplicate" コマンド
    #   左右のペイン両方のアイテムを通して、内容が重複するファイルを検索します。
    #   ファイルのサイズが一致するものについて、より詳細に比較を行います。

    def command_CheckDuplicate(info):
        
        left_pane = window.leftPane()
        right_pane = window.rightPane()

        left_location = window.leftFileList().getLocation()
        right_location = window.rightFileList().getLocation()

        left_items = window.leftItems()
        right_items = window.rightItems()
        
        items = []
        for item in left_items:
            if not item.isdir() and hasattr(item,"getFullpath"):
                items.append( [ item, None, False ] )
        for item in right_items:
            if not item.isdir() and hasattr(item,"getFullpath"):
                items.append( [ item, None, False ] )
                
        if len(items)<=1:
            return

        result_left_items = set()
        result_right_items = set()
        message = [""]

        def jobCheckDuplicate( job_item ):

            def printBoth(s):
                print( s )
                message[0] += s + "\n"

            def appendResult(item):
                if item in left_items:
                    result_left_items.add(item)
                    printBoth( '   Left: %s' % item.getName() )
                else:
                    result_right_items.add(item)
                    printBoth( '  Right: %s' % item.getName() )

            def leftOrRight(item):
                if item in left_items:
                    return 'Left'
                else:
                    return 'Right'

            printBoth( '重複するファイルを検索 :' )

            # ビジーインジケータ On
            window.setProgressValue(None)
            
            # ファイルのMD5値を調べる
            import hashlib
            for i, item in enumerate(items):

                if job_item.isCanceled(): break
                if job_item.waitPaused():
                    window.setProgressValue(None)

                digest = hashlib.md5(item[0].open().read(64*1024)).hexdigest()
                print( 'MD5 : %s : %s' % ( item[0].getName(), digest ) )
                items[i][1] = digest
            
            # ファイルサイズとハッシュでソート
            if not job_item.isCanceled():
                items.sort( key = lambda item: ( item[0].size(), item[1] ) )

            for i in range(len(items)):

                if job_item.isCanceled(): break
                if job_item.waitPaused():
                    window.setProgressValue(None)
                
                item1 = items[i]
                if item1[2] : continue
                
                dumplicate_items = []
                dumplicate_filenames = [ item1[0].getFullpath() ]
                
                for k in range( i+1, len(items) ):

                    if job_item.isCanceled(): break
                    if job_item.waitPaused():
                        window.setProgressValue(None)

                    item2 = items[k]
                    if item1[1] != item2[1] : break
                    if item2[2] : continue
                    if item2[0].getFullpath() in dumplicate_filenames :
                        item2[2] = True
                        continue
                        
                    print( '比較 : %5s : %s' % ( leftOrRight(item1[0]), item1[0].getName() ) )
                    print( '     : %5s : %s …' % ( leftOrRight(item2[0]), item2[0].getName() ), )
                    
                    try:
                        result = compareFile( item1[0].getFullpath(), item2[0].getFullpath(), shallow=1, schedule_handler=job_item.isCanceled )
                    except CanceledError:
                        print( '中断' )
                        break

                    if result:
                        print( '一致' )
                        dumplicate_items.append(item2)
                        dumplicate_filenames.append(item2[0].getFullpath())
                        item2[2] = True
                    else:
                        print( '不一致' )

                    print( '' )

                if dumplicate_items:
                    appendResult(item1[0])
                    for item2 in dumplicate_items:
                        appendResult(item2[0])
                    printBoth("")
                
            message[0] += '\n'
            message[0] += '検索結果をファイルリストに反映しますか？(Enter/Esc):\n'

        def jobCheckDuplicateFinished( job_item ):
        
            # ビジーインジケータ Off
            window.clearProgress()

            if job_item.isCanceled():
                print( '中断しました.\n' )
            else:
                print( 'Done.\n' )

            if job_item.isCanceled(): return

            result = popResultWindow( window, "検索完了", message[0] )
            if not result: return

            window.leftJumpLister( lister_Custom( window, "[duplicate] ", left_location, list(result_left_items) ) )
            window.rightJumpLister( lister_Custom( window, "[duplicate] ", right_location, list(result_right_items) ) )

        job_item = ckit.JobItem( jobCheckDuplicate, jobCheckDuplicateFinished )
        window.taskEnqueue( job_item, "CheckDuplicate" )


    # --------------------------------------------------------------------
    # "CheckSimilar" コマンド 
    #   左右のペイン両方のアイテムを通して、名前が似ているファイルを検索します。

    def command_CheckSimilar(info):

        left_location = window.leftFileList().getLocation()
        right_location = window.rightFileList().getLocation()
        left_items = window.leftItems()
        right_items = window.rightItems()
        items = left_items + right_items

        result_left_items = set()
        result_right_items = set()
        message = [""]

        def jobCheckSimilar( job_item ):

            def printBoth(s):
                print( s )
                message[0] += s + "\n"
                
            def appendResult(item):
                if item in left_items:
                    result_left_items.add(item)
                    printBoth( '   Left: %s' % item.getName() )
                else:
                    result_right_items.add(item)
                    printBoth( '  Right: %s' % item.getName() )

            printBoth('名前が似ているファイルを検索 :')

            # ビジーインジケータ On
            window.setProgressValue(None)
            
            def to_charset(item):
                return ( item, set(item.getName().lower()) )
            item_charset_list = map( to_charset, items )
        
            for i in range(len(item_charset_list)-1):

                if job_item.isCanceled(): break
                if job_item.waitPaused():
                    window.setProgressValue(None)

                item_charset1 = item_charset_list[i]
                for k in range( i+1, len(item_charset_list) ):

                    if job_item.isCanceled(): break
                    if job_item.waitPaused():
                        window.setProgressValue(None)

                    item_charset2 = item_charset_list[k]
                    or_set = item_charset1[1].union(item_charset2[1])
                    and_set = item_charset1[1].intersection(item_charset2[1])
                    score = float(len(and_set)) / float(len(or_set))

                    if score>=0.90:
                        appendResult(item_charset1[0])
                        appendResult(item_charset2[0])
                        printBoth('')
                        
            message[0] += '\n'
            message[0] += '検索結果をファイルリストに反映しますか？(Enter/Esc):\n'

        def jobCheckSimilarFinished( job_item ):
        
            # ビジーインジケータ Off
            window.clearProgress()

            if job_item.isCanceled():
                print( '中断しました.\n' )
            else:
                print( 'Done.\n' )

            if job_item.isCanceled(): return

            result = popResultWindow( window, "検索完了", message[0] )
            if not result: return

            window.leftJumpLister( lister_Custom( window, "[similar] ", left_location, list(result_left_items) ) )
            window.rightJumpLister( lister_Custom( window, "[similar] ", right_location, list(result_right_items) ) )

        job_item = ckit.JobItem( jobCheckSimilar, jobCheckSimilarFinished )
        window.taskEnqueue( job_item, "CheckSimilar" )


    # --------------------------------------------------------------------
    # コマンドランチャにコマンドを登録する

    window.launcher.command_list += [
        ( "Help",              command_Help ),
        ( "AFX",               command_LaunchAFX ),
        ( "Google",            command_Google ),
        ( "Eijiro",            command_Eijiro ),
        ( "Subst",             command_Subst ),
        ( "NetDrive",          command_NetDrive ),
        ( "CheckEmpty",        command_CheckEmpty ),
        ( "CheckDuplicate",    command_CheckDuplicate ),
        ( "CheckSimilar",      command_CheckSimilar ),
    ]

    # --------------------------------------------------------------------
    # Subversionでバージョン管理しているファイルだけを表示するフィルタ
    class filter_Subversion:

        svn_exe_path = "c:/Program Files/TortoiseSVN/bin/svn.exe"

        def __init__( self, nonsvn_dir_policy ):

            self.nonsvn_dir_policy = nonsvn_dir_policy
            self.cache = {}
            self.last_used = time.time()

        def _getSvnFiles( self, dirname ):
        
            if dirname.replace("\\","/").find("/.svn/") >= 0:
                return set()
        
            filename_set = set()
            
            cmd = [ filter_Subversion.svn_exe_path, "stat", "-q", "-v", "--xml", "--depth", "immediates" ]
            svn_output = io.StringIO()
            subprocess = SubProcess( cmd, cwd=dirname, env=None, stdout_write=svn_output.write )
            subprocess()
            
            try:
                elm1 = xml.etree.ElementTree.fromstring(svn_output.getvalue())
            except xml.etree.ElementTree.ParseError as e:
                for line in svn_output.getvalue().splitlines():
                    if line.startswith("svn:"):
                        print( line )
                return filename_set
            elm2 = elm1.find("target")
            for elm3 in elm2.findall("entry"):
                elm4 = elm3.find("wc-status")
                if elm4.get("item")=="unversioned": continue
                filename_set.add( elm3.get("path") )

            return filename_set

        def __call__( self, item ):

            now = time.time()
            if now - self.last_used > 3.0:
                self.cache = {}
            self.last_used = now
        
            if not hasattr(item,"getFullpath"): return False

            fullpath = item.getFullpath()
        
            dirname, filename = os.path.split(fullpath)
            
            try:
                filename_set = self.cache[dirname]
            except KeyError:
                filename_set = self._getSvnFiles(dirname)
                self.cache[dirname] = filename_set

            if item.isdir() and not filename_set:
                return self.nonsvn_dir_policy
            return filename in filename_set
    
        def __str__(self):
            return "[svn]"

    window.filter_list += [
        ( "SUBVERSION",    filter_Subversion( nonsvn_dir_policy=True ) ),
    ]

    window.select_filter_list += [
        ( "SUBVERSION",    filter_Subversion( nonsvn_dir_policy=False ) ),
    ]

    # --------------------------------------------------------------------


# テキストビューアの設定処理
def configure_TextViewer(window):

    # --------------------------------------------------------------------
    # F1 キーでヘルプファイルを表示する

    def command_Help():
        print( "Helpを起動 :" )
        help_path = os.path.join( getAppExePath(), 'doc\\index.html' )
        shellExecute( None, help_path, "", "" )
        print( "Done.\n" )

    window.keymap[ "F1" ] = command_Help


# テキスト差分ビューアの設定処理
def configure_DiffViewer(window):

    # --------------------------------------------------------------------
    # F1 キーでヘルプファイルを表示する

    def command_Help():
        print( "Helpを起動 :" )
        help_path = os.path.join( getAppExePath(), 'doc\\index.html' )
        shellExecute( None, help_path, "", "" )
        print( "Done.\n" )

    window.keymap[ "F1" ] = command_Help


# イメージビューアの設定処理
def configure_ImageViewer(window):

    # --------------------------------------------------------------------
    # F1 キーでヘルプファイルを表示する

    def command_Help():
        print( "Helpを起動 :" )
        help_path = os.path.join( getAppExePath(), 'doc\\index.html' )
        shellExecute( None, help_path, "", "" )
        print( "Done.\n" )

    window.keymap[ "F1" ] = command_Help


# リストウインドウの設定処理
def configure_ListWindow(window):

    # --------------------------------------------------------------------
    # F1 キーでヘルプファイルを表示する

    def command_Help():
        print( "Helpを起動 :" )
        help_path = os.path.join( getAppExePath(), 'doc\\index.html' )
        shellExecute( None, help_path, "", "" )
        print( "Done.\n" )

    window.keymap[ "F1" ] = command_Help

