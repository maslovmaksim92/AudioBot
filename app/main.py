#!/usr/bin/env python3
"""
app/main.py - Render compatibility layer
Импортирует FastAPI app из backend/server.py
"""

import sys
import os
from pathlib import Path

# Add backend to Python path
backend_dir = Path(__file__).parent.parent / "backend"
sys.path.insert(0, str(backend_dir))

# Import the FastAPI app from backend
from server import app

# Export for uvicorn
__all__ = ["app"]