import os
import inspect

import ckit
from ckit.ckit_const import *

import cfiler_misc
import cfiler_native
import cfiler_error
import cfiler_debug

class commandline_Launcher:

    def __init__( self, main_window ):
        self.main_window = main_window
        self.command_list = []

    def onCandidate( self, update_info ):

        pane = self.main_window.activePane()
        basedir = pane.file_list.getLocation()

        left = update_info.text[ : update_info.selection[0] ]
        left_lower = left.lower()
        pos_arg = left.rfind(";")+1
        arg = left[ pos_arg : ]
        pos_dir = max( arg.rfind("/")+1, arg.rfind("\\")+1 )
        directory = arg[:pos_dir]
        directory_lower = directory.lower()
        name_prefix = arg[pos_dir:].lower()

        dirname_list = []
        filename_list = []
        candidate_list = []
        
        if len(arg)>0:

            try:
                path = ckit.joinPath( basedir, directory )
                unc = os.path.splitunc(path)
                if unc[0]:
                    cfiler_misc.checkNetConnection(path)
                if unc[0] and not unc[1]:
                    servername = unc[0].replace('/','\\')
                    infolist = cfiler_native.enumShare(servername)
                    for info in infolist:
                        if info[1]==0:
                            if info[0].lower().startswith(name_prefix):
                                if ckit.pathSlash():
                                    dirname_list.append( info[0] + "/" )
                                else:
                                    dirname_list.append( info[0] + "\\" )
                else:
                    infolist = cfiler_native.findFile( ckit.joinPath(path,'*'), use_cache=True )
                    for info in infolist:
                        if info[0].lower().startswith(name_prefix):
                            if info[3] & ckit.FILE_ATTRIBUTE_DIRECTORY:
                                if ckit.pathSlash():
                                    dirname_list.append( info[0] + "/" )
                                else:
                                    dirname_list.append( info[0] + "\\" )
                            else:                    
                                filename_list.append( info[0] )
            except Exception:
                cfiler_debug.printErrorInfo()

        for item in self.command_list:
            item_lower = item[0].lower()
            if item_lower.startswith(left_lower) and len(item_lower)!=len(left_lower):
                candidate_list.append( item[0] )

        return dirname_list + filename_list + candidate_list

    def onEnter( self, commandline, text, mod ):
        
        args = text.split(';')
        
        command_name = args[0].lower()
        
        for command in self.command_list:
            if command[0].lower() == command_name:

                # 引数を受け取らない関数やメソッドを許容するためのトリック                
                argspec = inspect.getargspec(command[1])
                if type(command[1])==type(self.onEnter):
                    num_args = len(argspec[0])-1
                else:
                    num_args = len(argspec[0])

                try:
                    if num_args==0:
                        command[1]()
                    elif num_args==1:
                        command[1](args[1:])
                    elif num_args==2:
                        command[1](args[1:],mod)
                    else:
                        raise TypeError("arg spec is not acceptable.")
                except Exception as e:
                    cfiler_debug.printErrorInfo()
                    print( e )
                    return True

                commandline.setText("")
                commandline.selectAll()

                commandline.appendHistory( text )

                commandline.quit()

                return True
        
        return False
    
    def onStatusString( self, text ):
        text_lower = text.lower()
        for command in self.command_list:
            if command[0].lower() == text_lower:
                return "OK"
        return None
    

class commandline_Calculator:

    def __init__(self):
        pass

    def onCandidate( self, update_info ):
        return []
    
    def onEnter( self, commandline, text, mod ):
        
        from math import sin, cos, tan, acos, asin, atan
        from math import e, fabs, log, log10, pi, pow, sqrt

        try:
            result = eval(text)
        except (SyntaxError,TypeError):
            return False
        
        if isinstance(result,int):
            result_string = "%d" % result
        elif isinstance(result,float):
            result_string = "%f" % result
        else:
            return False

        commandline.appendHistory( text )
        
        if result_string!=text:

            print( "%s => %s" % ( text, result_string ) )
            commandline.setText( result_string )
            commandline.selectAll()
        
        return True

    def onStatusString( self, text ):
        return None


class commandline_Int32Hex:

    def __init__(self):
        pass

    def onCandidate( self, update_info ):
        return []
    
    def onEnter( self, commandline, text, mod ):
    
        def base16to10(src):
            if src[:2].lower() != "0x":
                raise ValueError
            i = int( src, 16 )
            if i<0 or i>0xffffffff:
                raise ValueError
            if i>=0x80000000:
                dst = "%d" % ( -0x80000000 + ( i - 0x80000000 ) )
            else:
                dst = "%d" % i
            return dst    

        def base10to16(src):
            i = int( src, 10 )
            if i<-0x80000000 or i>=0x80000000:
                raise ValueError
            if i<0:
                dst = "0x%08x" % ( 0x80000000 + ( i + 0x80000000 ) )
            else:
                dst = "0x%08x" % i
            return dst
        
        text = text.strip()

        try:
            result_string = base10to16(text)
        except ValueError:
            try:
                result_string = base16to10(text)
            except ValueError:
                return False    

        commandline.appendHistory( text )
        
        if result_string!=text:

            print( "%s => %s" % ( text, result_string ) )
            commandline.setText( result_string )
            commandline.selectAll()
        
        return True

    def onStatusString( self, text ):
        return None
