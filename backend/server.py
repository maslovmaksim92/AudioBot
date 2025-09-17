# Minimal shim to keep uvicorn import path stable regardless of package context
import os, sys
CURRENT_DIR = os.path.dirname(__file__)
if CURRENT_DIR not in sys.path:
    sys.path.insert(0, CURRENT_DIR)
from app_main import app  # noqa: F401