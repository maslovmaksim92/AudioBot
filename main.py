#!/usr/bin/env python3
"""
AudioBot Launcher for Render deployment
Простой запуск existing backend
"""

import sys
import os
from pathlib import Path

# Add backend to path
backend_dir = Path(__file__).parent / "backend"
sys.path.insert(0, str(backend_dir))

if __name__ == "__main__":
    import uvicorn
    from server import app
    
    # Get port from environment (Render sets this)
    port = int(os.environ.get("PORT", 8000))
    
    print(f"🚀 Starting AudioBot on port {port}")
    uvicorn.run(app, host="0.0.0.0", port=port, log_level="info")