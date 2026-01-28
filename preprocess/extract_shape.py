# -*- coding: utf-8 -*-
import os
import sys

THIS_DIR = os.path.dirname(os.path.abspath(__file__))
if THIS_DIR not in sys.path:
    sys.path.insert(0, THIS_DIR)

from main import main


if __name__ == "__main__":
    main()
