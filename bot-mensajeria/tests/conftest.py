import os
import sys

TESTS_DIR = os.path.dirname(os.path.abspath(__file__))
BOT_DIR = os.path.dirname(TESTS_DIR)
PROJECT_DIR = os.path.dirname(BOT_DIR)

if BOT_DIR not in sys.path:
    sys.path.insert(0, BOT_DIR)
