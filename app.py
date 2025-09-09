#!/usr/bin/env python3
"""
VasDom AudioBot - Render Compatibility Entry Point
Simple entry point that should work on Render deployment.
"""

import sys
import os
from pathlib import Path

print("🚀 VasDom AudioBot initializing on Render...")

# Add the backend directory to Python path  
backend_path = Path(__file__).parent / 'backend'
sys.path.insert(0, str(backend_path))

# Initialize variables for error handling
modular_error = None
legacy_error = None
app = None

try:
    # First try: modular structure
    print("📁 Attempting import from modular structure...")
    from app.main import app
    print("✅ SUCCESS: App imported from backend/app/main.py")
except ImportError as e1:
    modular_error = str(e1)
    print(f"❌ Modular import failed: {modular_error}")
    
    try:
        # Second try: legacy server.py
        print("📁 Attempting import from legacy server.py...")
        from server import app
        print("✅ SUCCESS: App imported from backend/server.py")
    except ImportError as e2:
        legacy_error = str(e2)
        print(f"❌ Legacy import failed: {legacy_error}")
        
        # Last resort: create minimal FastAPI app
        print("📁 Creating minimal fallback app...")
        from fastapi import FastAPI
        from fastapi.responses import JSONResponse
        
        app = FastAPI(
            title="VasDom AudioBot",
            version="3.0.0",
            description="🤖 Emergency fallback mode"
        )
        
        @app.get("/")
        async def emergency_root():
            return JSONResponse({
                "message": "VasDom AudioBot - Emergency Mode",
                "status": "fallback_active",
                "errors": {
                    "modular_error": modular_error,
                    "legacy_error": legacy_error
                },
                "instructions": "Check backend imports and structure"
            })
            
        @app.get("/api/")
        async def emergency_api():
            return JSONResponse({
                "message": "VasDom AudioBot API",
                "version": "3.0.0",
                "status": "emergency_fallback"
            })
            
        print("✅ Fallback app created successfully")

# Ensure app is available for import
if app is None:
    raise RuntimeError("Failed to create any FastAPI app instance")

print(f"🎯 App ready: {type(app).__name__}")