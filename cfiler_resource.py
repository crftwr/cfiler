
cfiler_appname = "内骨格"
cfiler_dirname = "CraftFiler"
cfiler_version = "2.62"

_startup_string_fmt = """\
%s version %s:
  http://sites.google.com/site/craftware/
"""

def startupString():
    return _startup_string_fmt % ( cfiler_appname, cfiler_version )
