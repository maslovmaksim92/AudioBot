#!/usr/bin/env python3

import sys
import os
from pathlib import Path

# Add the backend directory to Python path
backend_path = Path(__file__).parent.parent / 'backend'
sys.path.insert(0, str(backend_path))

# Import the FastAPI app from modular structure
try:
    from app.main import app
    print("✅ App imported successfully from backend/app/main.py")
except ImportError as e:
    print(f"❌ Import error from modular app: {e}")
    # Try old server.py import as fallback
    try:
        from server import app
        print("✅ App imported from backup server.py")
    except ImportError as e2:
        print(f"❌ Backup import also failed: {e2}")
        # Last resort fallback - create a simple app
        from fastapi import FastAPI
        app = FastAPI()
        
        @app.get("/")
        async def root():
            return {"message": "VasDom AudioBot - Import Error Fallback"}

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 10000))
    uvicorn.run(app, host="0.0.0.0", port=port)