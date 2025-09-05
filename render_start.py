#!/usr/bin/env python3
"""
Alternative startup file for Render
"""
import os
import uvicorn
from app import app

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    host = "0.0.0.0"
    
    print(f"🚀 Starting AI Assistant on {host}:{port}")
    print("📍 Deployed on Render.com")
    print("🏢 ВасДом Cleaning Company")
    
    uvicorn.run(
        app,
        host=host,
        port=port,
        log_level="info"
    )