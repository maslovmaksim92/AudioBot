#!/usr/bin/env python3

# This is the main entry point for Render deployment
# It imports and runs the FastAPI app from the backend

import sys
import os
from pathlib import Path

# Add the backend directory to Python path
backend_path = Path(__file__).parent / 'backend'
sys.path.insert(0, str(backend_path))

# Import the FastAPI app
from server import app

if __name__ == "__main__":
    import uvicorn
    
    port = int(os.environ.get("PORT", 10000))
    uvicorn.run("main:app", host="0.0.0.0", port=port, log_level="info")