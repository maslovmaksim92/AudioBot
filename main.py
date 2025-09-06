#!/usr/bin/env python3
"""
Main entry point that imports from app.py
This ensures compatibility with Render's app.main:app command
"""

# Import the app from app.py
from app import app

# This allows uvicorn app.main:app to work
__all__ = ["app"]

if __name__ == "__main__":
    import uvicorn
    import os
    
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)