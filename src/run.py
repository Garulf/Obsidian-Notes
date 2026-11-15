# run.py: generic shim, identical across all plugins
import runpy
import sys
import os

PLUGIN_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "plugin")

sys.path.insert(0, os.path.join(PLUGIN_DIR, "site-packages"))
runpy.run_path(PLUGIN_DIR, run_name="__main__")
