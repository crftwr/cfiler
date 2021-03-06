import os
import sys
import getopt
import shutil
import zipfile
import hashlib
import subprocess
import py_compile

sys.path[0:0] = [
    os.path.join( os.path.split(sys.argv[0])[0], '..' ),
    ]

import cfiler_resource

#-------------------------------------------

action = "all"

debug = False

option_list, args = getopt.getopt( sys.argv[1:], "d" )
for option in option_list:
    if option[0]=="-d":
        debug = True

if len(args)>0:
    action = args[0]

#-------------------------------------------

PYTHON_DIR = "c:/Python38-64"

PYTHON = PYTHON_DIR + "/python.exe"

DOXYGEN_DIR = "c:/Program Files/doxygen"

NSIS_DIR = "c:/Program Files (x86)/NSIS"

DIST_DIR = "dist/cfiler"
VERSION = cfiler_resource.cfiler_version.replace(".","")
ARCHIVE_NAME = "cfiler_%s.zip" % VERSION
INSTALLER_NAME = "cfiler_%s.exe" % VERSION

DIST_FILES = {
    "cfiler.exe" :          "cfiler/cfiler.exe",
    "lib" :                 "cfiler/lib",
    "python38.dll" :        "cfiler/python38.dll",
    "_config.py" :          "cfiler/_config.py",
    "readme.txt" :          "cfiler/readme.txt",
    "theme/black" :         "cfiler/theme/black",
    "theme/white" :         "cfiler/theme/white",
    "license" :             "cfiler/license",
    "doc/html" :            "cfiler/doc",
    "library.zip" :         "cfiler/library.zip",
    "dict/.keepme" :        "cfiler/dict/.keepme",
    "extension/.keepme" :   "cfiler/extension/.keepme",
    }

#-------------------------------------------

def unlink(filename):
    try:
        os.unlink(filename)
    except OSError:
        pass

def makedirs(dirname):
    try:
        os.makedirs(dirname)
    except OSError:
        pass

def rmtree(dirname):
    try:
        shutil.rmtree(dirname)
    except OSError:
        pass

def compilePythonRecursively( src, dst, file_black_list=[], directory_black_list=[] ):

    for root, dirs, files in os.walk( src ):

        for directory_to_remove in directory_black_list:
            if directory_to_remove in dirs:
                dirs.remove(directory_to_remove)

        for file_to_remove in file_black_list:
            if file_to_remove in files:
                files.remove(file_to_remove)

        for filename in files:
            if filename.endswith(".py"):
                src_filename = os.path.join(root,filename)
                dst_filename = os.path.join(dst+root[len(src):],filename+"c")
                print("compile", src_filename, dst_filename )
                py_compile.compile( src_filename, dst_filename, optimize=2 )


def createZip( zip_filename, items ):
    z = zipfile.ZipFile( zip_filename, "w", zipfile.ZIP_DEFLATED, True )
    for item in items:
        if os.path.isdir(item):
            for root, dirs, files in os.walk(item):
                for f in files:
                    f = os.path.normpath(os.path.join(root,f))
                    print( f )
                    z.write(f)
        else:
            print( item )
            z.write(item)
    z.close()


def printMd5( filename ):

    fd = open(filename,"rb")
    m = hashlib.md5()
    while 1:
        data = fd.read( 1024 * 1024 )
        if not data: break
        m.update(data)
    fd.close()
    print( "" )
    print( filename, ":", m.hexdigest() )


#-------------------------------------------

def target_all():

    target_compile()
    target_copy()
    target_document()
    target_dist()
    target_archive()
    target_installer()


def target_compile():

    # compile python source files
    compilePythonRecursively( f"{PYTHON_DIR}/Lib", "build/Lib", 
        directory_black_list = [
            "site-packages",
            "test",
            "tests",
            "idlelib",
            ]
        )
    compilePythonRecursively( f"{PYTHON_DIR}/Lib/site-packages/PIL", "build/Lib/PIL" )
    compilePythonRecursively( "../ckit", "build/Lib/ckit" )
    compilePythonRecursively( "../pyauto", "build/Lib/pyauto" )
    compilePythonRecursively( ".", "build/Lib", 
        file_black_list = [
            "makefile.py",
            "_config.py",
            "config.py",
            ]
        )

    # archive python compiled files
    os.chdir("build/Lib")
    createZip( "../../library.zip", "." )
    os.chdir("../..")


def target_copy():

    rmtree("lib")

    shutil.copy( f"{PYTHON_DIR}/python38.dll", "python38.dll" )

    shutil.copytree( f"{PYTHON_DIR}/DLLs", "lib", 
        ignore=shutil.ignore_patterns(
            "tcl*.*",
            "tk*.*",
            "_tk*.*",
            "*.pdb",
            "*_d.pyd",
            "*_d.dll",
            "*_test.pyd",
            "_test*.pyd",
            "*.ico",
            "*.lib"
            )
        )

    shutil.copy( f"{PYTHON_DIR}/Lib/site-packages/PIL/_imaging.cp38-win_amd64.pyd", "lib/_imaging.pyd" )

    shutil.copy( "../ckit/ckitcore.pyd", "lib/ckitcore.pyd" )
    shutil.copy( "../pyauto/pyautocore.pyd", "lib/pyautocore.pyd" )
    shutil.copy( "cfiler_native.pyd", "lib/cfiler_native.pyd" )
    shutil.copy( "migemo.dll", "lib/migemo.dll" )
    shutil.copy( "7-zip64.dll", "lib/7-zip64.dll" )
    shutil.copy( "tar64.dll", "lib/tar64.dll" )


def target_document():
    rmtree( "doc/html" )
    makedirs( "doc/obj" )
    makedirs( "doc/html" )

    subprocess.call( [ PYTHON, "tool/rst2html_pygments.py", "--stylesheet=tool/rst2html_pygments.css", "doc/index.txt", "doc/obj/index.html" ] )
    subprocess.call( [ PYTHON, "tool/rst2html_pygments.py", "--stylesheet=tool/rst2html_pygments.css", "--template=tool/rst2html_template.txt", "doc/index.txt", "doc/obj/index.htm_" ] )

    subprocess.call( [ PYTHON, "tool/rst2html_pygments.py", "--stylesheet=tool/rst2html_pygments.css", "doc/changes.txt", "doc/obj/changes.html" ] )
    subprocess.call( [ PYTHON, "tool/rst2html_pygments.py", "--stylesheet=tool/rst2html_pygments.css", "--template=tool/rst2html_template.txt", "doc/changes.txt", "doc/obj/changes.htm_" ] )

    subprocess.call( [ DOXYGEN_DIR + "/bin/doxygen.exe", "doc/doxyfile" ] )
    shutil.copytree( "doc/image", "doc/html/image", ignore=shutil.ignore_patterns("*.pdn",) )


def target_dist():
    
    rmtree("dist/cfiler")

    src_root = "."
    dst_root = "./dist"
    
    for src, dst in DIST_FILES.items():

        src = os.path.join(src_root,src)
        dst = os.path.join(dst_root,dst)

        print( "copy : %s -> %s" % (src,dst) )
            
        if os.path.isdir(src):
            shutil.copytree( src, dst )
        else:
            makedirs( os.path.dirname(dst) )
            shutil.copy( src, dst )


def target_archive():

    makedirs("dist")

    os.chdir("dist")
    createZip( ARCHIVE_NAME, DIST_FILES.values() )
    os.chdir("..")
    
    fd = open( "dist/%s" % ARCHIVE_NAME, "rb" )
    m = hashlib.md5()
    while 1:
        data = fd.read( 1024 * 1024 )
        if not data: break
        m.update(data)
    fd.close()
    print( "" )
    print( m.hexdigest() )


def target_installer():

    topdir = DIST_DIR

    if 1:
        fd_instfiles = open("instfiles.nsh", "w")

        for location, dirs, files in os.walk(topdir):
        
            assert( location.startswith(topdir) )
            location2 = location[ len(topdir) + 1 : ]
        
            fd_instfiles.write( "  SetOutPath $INSTDIR\\%s\n" % location2 )
            fd_instfiles.write( "\n" )
        
            for f in files:
                fd_instfiles.write( "    File %s\n" % os.path.join(location,f) )

            fd_instfiles.write( "\n\n" )

        fd_instfiles.close()

    if 1:
        fd_uninstfiles = open("uninstfiles.nsh", "w")

        for location, dirs, files in os.walk(topdir,topdown=False):
        
            assert( location.startswith(topdir) )
            location2 = location[ len(topdir) + 1 : ]
        
            for f in files:
                fd_uninstfiles.write( "  Delete $INSTDIR\\%s\n" % os.path.join(location2,f) )

            fd_uninstfiles.write( "  RMDir $INSTDIR\\%s\n" % location2 )
            fd_uninstfiles.write( "\n" )

        fd_uninstfiles.close()

    subprocess.call( [ NSIS_DIR + "/makensis.exe", "installer.nsi" ] )

    unlink( "dist/%s" % INSTALLER_NAME )
    os.rename( "dist/cfiler_000.exe", "dist/%s" % INSTALLER_NAME )

    printMd5( "dist/%s" % INSTALLER_NAME )


def target_clean():
    rmtree("dist")
    rmtree("build")
    rmtree("doc/html_en")
    rmtree("doc/html_ja")
    unlink( "tags" )


#-------------------------------------------

eval( "target_" + action +"()" )
