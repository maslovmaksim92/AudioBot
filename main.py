#!/usr/bin/env python3
"""
VasDom AudioBot - Entry point for Render deployment
"""

import sys
import os
from pathlib import Path

# Add backend to Python path
backend_path = Path(__file__).parent / "backend"
sys.path.insert(0, str(backend_path))

# Import and run the FastAPI app
if __name__ == "__main__":
    import uvicorn
    from server import app
    
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)