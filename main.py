#!/usr/bin/env python3

# VasDom AudioBot - Main entry point for Render deployment

import sys
import os
from pathlib import Path

# Add the backend directory to Python path
backend_path = Path(__file__).parent / 'backend'
sys.path.insert(0, str(backend_path))

# Import the FastAPI app with fallback
try:
    from server import app
    print("✅ VasDom AudioBot imported successfully from backend/server.py")
except ImportError as e:
    print(f"❌ Import error: {e}")
    # Fallback - create a simple app
    from fastapi import FastAPI
    from fastapi.responses import JSONResponse
    
    app = FastAPI(title="VasDom AudioBot - Fallback")
    
    # Store the error message for use in the route
    import_error = str(e)
    
    @app.get("/")
    async def root():
        return {
            "message": "VasDom AudioBot - Import Error",
            "error": import_error,
            "status": "fallback_mode"
        }

if __name__ == "__main__":
    import uvicorn
    
    port = int(os.environ.get("PORT", 10000))
    uvicorn.run("main:app", host="0.0.0.0", port=port, log_level="info")