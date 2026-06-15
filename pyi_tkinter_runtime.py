import os
import sys

base = getattr(sys, "_MEIPASS", os.path.dirname(sys.executable))
if base not in sys.path:
    sys.path.insert(0, base)

os.environ.setdefault("TCL_LIBRARY", os.path.join(base, "tcl", "tcl8.6"))
os.environ.setdefault("TK_LIBRARY", os.path.join(base, "tcl", "tk8.6"))
