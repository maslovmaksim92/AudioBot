#!/usr/bin/env python3
"""
Alternative start file for Render
"""
import os
import uvicorn

if __name__ == "__main__":
    # Try to import app
    try:
        from app import app
        print("✅ Successfully imported app from app.py")
    except ImportError as e:
        print(f"❌ Failed to import app: {e}")
        exit(1)
    
    port = int(os.environ.get("PORT", 8000))
    host = "0.0.0.0"
    
    print(f"🚀 Starting AI Assistant on {host}:{port}")
    print("🏢 ВасДом Cleaning Company")
    print("💰 4+ million rubles revenue")
    print("👥 100 employees in Kaluga & Kemerovo")
    
    uvicorn.run(
        app,
        host=host,
        port=port,
        log_level="info",
        access_log=True
    )