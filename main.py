#!/usr/bin/env python3
"""
VasDom AudioBot - Main Entry Point for Render
This imports from app.py to ensure compatibility
"""

import os

# Simple import from vasdom_app.py
from vasdom_app import app

print("✅ main.py: App imported successfully")

# Export for uvicorn
__all__ = ["app"]

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 10000))
    uvicorn.run(app, host="0.0.0.0", port=port)