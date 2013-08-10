import os
import sys
import getopt
import shutil
import threading
import locale

os.environ["PATH"] = os.path.join( os.path.split(sys.argv[0])[0], 'lib' ) + ";" + os.environ["PATH"]

sys.path[0:0] = [
    os.path.join( os.path.split(sys.argv[0])[0], '..' ),
    os.path.join( os.path.split(sys.argv[0])[0], 'extension' ),
    os.path.join( os.path.split(sys.argv[0])[0], 'lib' ),
    ]

import ckit

ckit.setLocale( locale.getdefaultlocale()[0] )

import cfiler_mainwindow
import cfiler_misc
import cfiler_debug
import cfiler_resource

debug = False
profile = False
left_location = None
right_location = None

option_list, args = getopt.getopt( ckit.getArgv()[1:], "dpL:R:" )
for option in option_list:
    if option[0]=="-d":
        debug = True
    elif option[0]=="-p":
        profile = True
    elif option[0]=="-L":
        left_location = option[1]
    elif option[0]=="-R":
        right_location = option[1]

if __name__ == "__main__":

    ckit.registerWindowClass( "Cfiler" )

    sys.path[0:0] = [
        os.path.join( ckit.getAppExePath(), 'extension' ),
        ]
        
    # exeと同じ位置にある設定ファイルを優先する
    if os.path.exists( os.path.join( ckit.getAppExePath(), 'config.py' ) ):
        ckit.setDataPath( ckit.getAppExePath() )
    else:    
        ckit.setDataPath( os.path.join( ckit.getAppDataPath(), cfiler_resource.cfiler_dirname ) )
        if not os.path.exists(ckit.dataPath()):
            os.mkdir(ckit.dataPath())

    default_config_filename = os.path.join( ckit.getAppExePath(), '_config.py' )
    config_filename = os.path.join( ckit.dataPath(), 'config.py' )
    ini_filename = os.path.join( ckit.dataPath(), 'cfiler.ini' )

    # config.py がどこにもない場合は作成する
    if not os.path.exists(config_filename) and os.path.exists(default_config_filename):
        shutil.copy( default_config_filename, config_filename )

    _main_window = cfiler_mainwindow.MainWindow(
        config_filename = config_filename,
        ini_filename = ini_filename,
        debug = debug, 
        profile = profile )

    _main_window.registerStdio()

    ckit.initTemp("cfiler_")

    _main_window.configure()

    _main_window.startup( left_location, right_location )

    _main_window.topLevelMessageLoop()
    
    _main_window.saveState()

    cfiler_debug.enableExitTimeout()

    _main_window.unregisterStdio()

    ckit.JobQueue.cancelAll()
    ckit.JobQueue.joinAll()

    ckit.destroyTemp()

    _main_window.destroy()

    cfiler_debug.disableExitTimeout()

    # スレッドが残っていても強制終了
    if 0:
        if not debug:
            os._exit(0)
    else:
        os._exit(0)

