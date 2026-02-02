#src/file_opener.py\
from __future__ import annotations
import os
import sys
import subprocess

def open_file(path: str) -> None:
    if sys.platform.startswith("win"):
        os.startfile(path) 
    elif sys.platform == "darwin":
        subprocess.run(["open", path], check=False)
    else:
        subprocess.run(["xdg-open", path], check=False)
