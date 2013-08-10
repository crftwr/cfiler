
# Grepの実験中。LREdit由来のGrep。

import os
import re
import fnmatch

import ckit


def grep( job_item, enum_files, pattern, word=False, case=False, regex=False, found_handler=None ):

    if regex:
        if word:
            re_pattern = r"\b" + pattern + r"\b"
        else:
            re_pattern = pattern
    else:
        re_pattern = ""
        for c in pattern:
            if c in "\\[]":
                c = "\\" + c;
            re_pattern += "[" + c + "]"

        if word:
            re_pattern = r"\b" + re_pattern + r"\b"

    re_option = re.UNICODE
    if not case:
        re_option |= re.IGNORECASE

    re_object = re.compile( re_pattern, re_option )

    for fullpath in enum_files():

        if job_item.isCanceled(): break

        try:
            fd = open( fullpath )
            
            data = fd.read()
            
            encoding = ckit.detectTextEncoding( data, ascii_as="utf-8" )
            if encoding.bom:
                data = data[ len(encoding.bom) : ]

            if encoding.encoding:
                data = data.decode( encoding=encoding.encoding, errors='replace' )
            else:
                # FIXME : バイナリでも検索する
                continue
    
            lines = data.splitlines(True)

            lineno = 1
            for line in lines:
                if re_object.search(line):
                    found_handler( fullpath, lineno-1, line )
                lineno += 1
                    
        except IOError as e:
            print( "  %s" % str(e) )

    if job_item.isCanceled():
        print( '中断しました.\n' )
    else:
        print( 'Done.\n' )







## GREPを行う
def command_Grep2(self):

    pane = self.activePane()

    location = pane.file_list.getLocation()
    if not os.path.isdir(location) : return

    item_filter = pane.file_list.getFilter()

    pos = self.centerOfWindowInPixel()
    grep_window = cfiler_grepwindow.GrepWindow( pos[0], pos[1], self, self.ini )
    self.enable(False)
    grep_window.messageLoop()
    result = grep_window.getResult()
    self.enable(True)
    self.activate()
    grep_window.destroy()

    if result==None : return
    pattern, recursive, regexp, ignorecase = result[0], result[1], result[2], result[3]
    word = False # FIXME

    def enumFiles():

        filename_pattern = "*" # FIXME
        file_filter_list = filename_pattern.split(" ")

        def checkFilter(filename):
            """
            result = False
            for pattern in file_filter_list:
                if pattern.startswith("!"):
                    pattern = pattern[1:]
                    if fnmatch.fnmatch( filename, pattern ):
                        return False
                else:
                    if fnmatch.fnmatch( filename, pattern ):
                        result = True
            return result
            """
            return True

        print( 'Grep : %s : %s' % ( location, pattern ) )

        """
        dir_ignore_list = dirname_exclude_pattern.split(" ")
        """

        for root, dirs, files in os.walk( location ):

            if not recursive : del dirs[:]

            """
            # 無視するディレクトリを除外
            for item in dirs:
                for pattern in dir_ignore_list:
                    if fnmatch.fnmatch( item, pattern ):
                        dirs.remove(item)
                        break
            """

            for filename in files:
                if checkFilter(filename):
                    fullpath = os.path.join( root, filename )
                    yield fullpath

    items = []

    def jobGrep( job_item ):

        print( 'Grep : %s' % pattern )
        
        filename_list = []

        def onFound( filename, lineno, line ):
            
            path_from_here = ckit.normPath(filename[len(os.path.join(location,"")):])
            #print( "%s:%d: %s" % ( path_from_here, lineno, line.strip() ) )
            print( "%s:%d" % ( path_from_here, lineno ) )
            
            """
            jump_list_root.items.append(
                GrepJumpItem(
                    self,
                    filename,
                    lineno
                )
            )
            """

        self.setProgressValue(None)
        try:
            cfiler_grep.grep( job_item, enumFiles, pattern, word, not ignorecase, regexp, found_handler=onFound )
        finally:
            self.clearProgress()

        def packListItem( filename ):

            item = cfiler_filelist.item_Default(
                location,
                filename
                )

            return item

        items[:] = map( packListItem, filename_list )

        # ビジーインジケータ Off
        self.clearProgress()

    def jobGrepFinished( job_item ):

        if self.isQuitting() : return

        result = [ True ]

        def onKeyDown( vk, mod ):
            if vk==VK_RETURN and mod==0:
                result[0] = True
                console_window.quit()
                return True
            elif vk==VK_ESCAPE and mod==0:
                result[0] = False
                console_window.quit()
                return True

        pos = self.centerOfWindowInPixel()
        console_window = cfiler_consolewindow.ConsoleWindow( pos[0], pos[1], 60, 24, self, self.ini, "Grep完了", onKeyDown )
        self.enable(False)

        console_window.write( 'Grep : %s\n' % pattern )
        for item in items:
            console_window.write( '  %s\n' % item.getName(), False )
        console_window.write( '\n' )
        console_window.write( 'Grepの結果をファイルリストに反映しますか？(Enter/Esc):\n' )

        console_window.messageLoop()
        self.enable(True)
        self.activate()
        console_window.destroy()

        if not result[0] : return

        new_lister = cfiler_filelist.lister_Custom( self, "[grep] ", location, items )
        pane.file_list.setLister( new_lister )
        pane.file_list.applyItems()
        pane.scroll_info = ckit.ScrollInfo()
        pane.cursor = 0
        pane.scroll_info.makeVisible( pane.cursor, self.fileListItemPaneHeight(), 1 )
        self.paint( PAINT_LEFT | PAINT_RIGHT )

    self.appendHistory( pane, True )

    job_item = ckit.JobItem( jobGrep, jobGrepFinished )
    self.taskEnqueue( job_item, "Grep" )

