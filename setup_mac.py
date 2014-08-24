"""
This is a setup.py script generated by py2applet

Usage:
    python setup_mac.py py2app
"""

import sys
import os

sys.path[0:0] = [
    os.path.join( os.path.split(sys.argv[0])[0], ".." ),
    ]

from setuptools import setup

APP = ['cfiler_main.py']
DATA_FILES = []
OPTIONS = {
	'argv_emulation': True,
	'iconfile': 'app.icns'
}

setup(
    app=APP,
    data_files=DATA_FILES,
    options={'py2app': OPTIONS},
    setup_requires=['py2app'],
)
