#!/usr/bin/env python3
"""
VasDom AudioBot - Production Entry Point for Render
This file serves as the main entry point for deployment on Render.
"""

import sys
import os
from pathlib import Path

# Add the backend directory to Python path  
backend_path = Path(__file__).parent / 'backend'
sys.path.insert(0, str(backend_path))

print("🚀 VasDom AudioBot starting on Render...")

# Import the FastAPI app from modular structure
try:
    # Import from backend/app/main.py (modular structure)
    from app.main import app
    print("✅ VasDom AudioBot app imported from modular structure (backend/app/main.py)")
except ImportError as e:
    print(f"❌ Import error from modular app: {e}")
    # Try old server.py import as fallback  
    try:
        from server import app
        print("✅ App imported from backup server.py")
    except ImportError as e2:
        print(f"❌ Backup import also failed: {e2}")
        # Create a simple working app
        from fastapi import FastAPI
        from fastapi.responses import JSONResponse
        
        app = FastAPI(title="VasDom AudioBot", version="3.0.0")
        
        @app.get("/")
        async def root():
            return {"message": "VasDom AudioBot", "status": "Import Error Fallback"}
            
        @app.get("/api/")
        async def api_root():
            return {"message": "VasDom AudioBot API", "status": "Import Error Fallback"}

# Export app for uvicorn
__all__ = ["app"]

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 10000))
    uvicorn.run(app, host="0.0.0.0", port=port)