#!/bin/bash
export QT_QPA_PLATFORM=xcb
source venv/bin/activate
export PYTHONPATH=src
python3 -m aphelion
