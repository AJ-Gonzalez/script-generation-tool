#!/usr/bin/env python3
"""
Demo script to launch the Marketing Tools GUI application.
"""

import sys
import os

sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

from marketing_ui import main

if __name__ == "__main__":
    print("🚀 Starting Marketing Tools GUI...")
    print("This will open a desktop application with a two-column layout.")
    main()