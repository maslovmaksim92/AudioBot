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
    from app.main import app
    print("✅ VasDom AudioBot imported successfully from modular backend/app/main.py")
except ImportError as e:
    print(f"❌ Modular import error: {e}")
    # Store first error for later use
    first_error = str(e)
    # Fallback to old server structure if exists
    try:
        from server import app
        print("✅ VasDom AudioBot imported from fallback backend/server.py")
    except ImportError as e2:
        print(f"❌ Fallback import error: {e2}")
        # Store second error for later use
        second_error = str(e2)
        # Create emergency fallback app
        from fastapi import FastAPI
        from fastapi.responses import JSONResponse
        
        app = FastAPI(title="VasDom AudioBot - Emergency Fallback")
        
        @app.get("/")
        async def emergency_root():
            return JSONResponse({
                "message": "VasDom AudioBot - Import Error Fallback",
                "error": f"Import errors: {first_error} | {second_error}",
                "status": "emergency_mode",
                "instructions": "Check backend structure and imports"
            })
        
        @app.get("/api/")
        async def emergency_api():
            return JSONResponse({
                "message": "VasDom AudioBot API - Emergency Mode",
                "error": "Backend import failed",
                "status": "fallback"
            })

if __name__ == "__main__":
    import uvicorn
    
    port = int(os.environ.get("PORT", 10000))
    uvicorn.run("main:app", host="0.0.0.0", port=port, log_level="info")