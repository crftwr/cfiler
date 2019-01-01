import sys
import os
import shutil
import datetime
import ctypes

import pyauto

import ckit
from ckit.ckit_const import *

import cfiler_native
import cfiler_resource
import cfiler_debug

## @addtogroup misc
## @{

#--------------------------------------------------------------------

ignore_1second = True

#--------------------------------------------------------------------

class candidate_Filename():

    def __init__( self, basedir, fixed_items=[] ):
        self.basedir = basedir
        self.fixed_items = fixed_items

    def __call__( self, update_info ):
        left = update_info.text[ : update_info.selection[0] ]
        pos_dir = max(left.rfind("/")+1,left.rfind("\\")+1)
        directory = left[:pos_dir]
        directory_lower = directory.lower()
        name_prefix = left[pos_dir:].lower()

        dirname_list = []
        filename_list = []

        for item in self.fixed_items:
            item_lower = item.lower()
            if item_lower.startswith(directory_lower):
                item_lower = item_lower[ len(directory_lower) : ]
                if item_lower.startswith(name_prefix) and len(item_lower)!=len(name_prefix):
                    filename_list.append( item[ len(directory_lower) : ] )

        path = ckit.joinPath( self.basedir, directory )
        
        drive, tail = os.path.splitdrive(path)
        unc = ( drive.startswith("\\\\") or drive.startswith("//") )
        
        if unc:
            checkNetConnection(path)
        if unc and not tail:
            servername = drive.replace('/','\\')
            try:
                infolist = cfiler_native.enumShare(servername)
            except WindowsError:
                infolist = []    
            for info in infolist:
                if info[1]==0:
                    if info[0].lower().startswith(name_prefix):
                        if ckit.pathSlash():
                            dirname_list.append( info[0] + "/" )
                        else:
                            dirname_list.append( info[0] + "\\" )
        else:
            try:
                infolist = cfiler_native.findFile( ckit.joinPath(path,'*'), use_cache=True )
            except WindowsError:
                infolist = []
            for info in infolist:
                if info[0].lower().startswith(name_prefix):
                    if info[3] & ckit.FILE_ATTRIBUTE_DIRECTORY:
                        if ckit.pathSlash():
                            dirname_list.append( info[0] + "/" )
                        else:
                            dirname_list.append( info[0] + "\\" )
                    else:                    
                        filename_list.append( info[0] )
        
        return dirname_list + filename_list, len(directory)

#--------------------------------------------------------------------

def getFileSizeString(size):
    
    if size < 1000:
        return "%dB" % ( size, )
    
    if size < 1000*1024:
        s = "%.1fK" % ( size / float(1024), )
        if len(s)<=6 : return s

    if size < 1000*1024*1024:
        s = "%.1fM" % ( size / float(1024*1024), )
        if len(s)<=6 : return s

    if size < 1000*1024*1024*1024:
        s = "%.1fG" % ( size / float(1024*1024*1024), )
        if len(s)<=6 : return s
    
    return "%.1fT" % ( size / float(1024*1024*1024*1024), )

#--------------------------------------------------------------------

_net_connection_handler = None

def registerNetConnectionHandler(handler):
    global _net_connection_handler
    _net_connection_handler = handler

def checkNetConnection(path):
    
    drive, tail = os.path.splitdrive(path)
    unc = ( drive.startswith("\\\\") or drive.startswith("//") )
    
    if unc:
        remote_resource_name = drive.replace('/','\\').rstrip('\\')
        try:
            _net_connection_handler(remote_resource_name)
        except Exception as e:
            cfiler_debug.printErrorInfo()
            print( e )

#--------------------------------------------------------------------

def compareTime( t1, t2 ):

    if type(t1)!=type(t2):
        raise TypeError("two arguments are not compatible.")

    if ignore_1second:
        delta = abs( datetime.datetime(*t1) - datetime.datetime(*t2) )
        if delta.days==0 and delta.seconds<=1 : return 0

    if t1<t2: return -1
    elif t1>t2: return 1
    else: return 0

#--------------------------------------------------------------------

## @} misc

