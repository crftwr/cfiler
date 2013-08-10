import os
import sys
import subprocess
import shutil
import zipfile
import hashlib

sys.path[0:0] = [
    os.path.join( os.path.split(sys.argv[0])[0], '..' ),
    ]

import cfiler_resource

DIST_DIR = "dist/cfiler"
DIST_SRC_DIR = "dist/src"
VERSION = cfiler_resource.cfiler_version.replace(".","").replace(" ","")
INSTALLER_NAME = "cfiler_%s.exe" % VERSION

PYTHON_DIR = "c:/python33"
PYTHON = PYTHON_DIR + "/python.exe"
SVN_DIR = "c:/Program Files/TortoiseSVN/bin"
DOXYGEN_DIR = "c:/Program Files/doxygen"
NSIS_DIR = "c:/Program Files (x86)/NSIS"

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

def createZip( zip_filename, items ):
    z = zipfile.ZipFile( zip_filename, "w", zipfile.ZIP_DEFLATED, True )
    for item in items:
        if os.path.isdir(item):
            for root, dirs, files in os.walk(item):
                for f in files:
                    f = os.path.join(root,f)
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


DIST_FILES = [
    "cfiler/cfiler.exe",
    "cfiler/lib",
    "cfiler/python33.dll",
    "cfiler/_config.py",
    "cfiler/readme.txt",
    "cfiler/theme/black",
    "cfiler/theme/white",
    "cfiler/license",
    "cfiler/doc",
    "cfiler/src.zip",
    "cfiler/dict/.keepme",
    "cfiler/extension/.keepme",
    ]

def all():
    doc()
    exe()
    installer()
    printMd5("dist/%s" % INSTALLER_NAME)

def exe():
    subprocess.call( [ PYTHON, "setup.py", "build" ] )
    rmtree( DIST_SRC_DIR )
    makedirs( DIST_SRC_DIR )
    os.chdir(DIST_SRC_DIR)
    subprocess.call( [ SVN_DIR + "/svn.exe", "export", "--force", "../../../ckit" ] )
    subprocess.call( [ SVN_DIR + "/svn.exe", "export", "--force", "../../../pyauto" ] )
    subprocess.call( [ SVN_DIR + "/svn.exe", "export", "--force", "../../../cfiler" ] )
    os.chdir("..")
    createZip( "cfiler/src.zip", [ "src" ] )
    os.chdir("..")

def clean():
    rmtree("dist")
    rmtree("build")
    rmtree("doc/html")
    unlink( "tags" )

def doc():
    rmtree( "doc/html" )
    makedirs( "doc/html" )
    subprocess.call( [ DOXYGEN_DIR + "/bin/doxygen.exe", "doc/doxyfile" ] )
    subprocess.call( [ PYTHON, "tool/rst2html_pygments.py", "--stylesheet=tool/rst2html_pygments.css", "doc/index.txt", "doc/html/index.html" ] )
    subprocess.call( [ PYTHON, "tool/rst2html_pygments.py", "--stylesheet=tool/rst2html_pygments.css", "doc/changes.txt", "doc/html/changes.html" ] )
    shutil.copytree( "doc/image", "doc/html/image", ignore=shutil.ignore_patterns(".svn","*.pdn") )

def archive():
    os.chdir("dist")
    createZip( "cfiler_000.zip", DIST_FILES )
    os.chdir("..")

def installer():

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


def run():
    subprocess.call( [ PYTHON, "cfiler_main.py" ] )

def debug():
    subprocess.call( [ PYTHON, "cfiler_main.py", "-d" ] )

def profile():
    subprocess.call( [ PYTHON, "cfiler_main.py", "-d", "-p" ] )

if len(sys.argv)<=1:
    target = "all"
else:
    target = sys.argv[1]

eval( target + "()" )

