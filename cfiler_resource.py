
cfiler_appname = "CraftCommander"
cfiler_dirname = "CraftCommander"
cfiler_version = "2.43"

_startup_string_fmt = """\
%s version %s:
  http://sites.google.com/site/craftware/
"""

def startupString():
    return _startup_string_fmt % ( cfiler_appname, cfiler_version )
