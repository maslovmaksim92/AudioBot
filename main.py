#!/usr/bin/env python3
"""
Main entry point for AI Assistant deployed on Render
"""

import os
import sys
import logging
from pathlib import Path

# Add backend directory to Python path
backend_dir = Path(__file__).parent / "backend"
sys.path.insert(0, str(backend_dir))

# Configure logging for production
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

def main():
    """Main function to start the application"""
    try:
        # Import and run the FastAPI server
        from backend.server import app
        
        logger.info("🚀 Starting AI Assistant on Render...")
        logger.info(f"Python version: {sys.version}")
        logger.info(f"Working directory: {os.getcwd()}")
        
        return app
        
    except Exception as e:
        logger.error(f"❌ Failed to start application: {e}")
        raise

# Create app instance for ASGI servers
app = main()

if __name__ == "__main__":
    import uvicorn
    
    # Get port from environment (Render provides PORT)
    port = int(os.environ.get("PORT", 8000))
    host = os.environ.get("HOST", "0.0.0.0")
    
    logger.info(f"🎯 Starting server on {host}:{port}")
    
    uvicorn.run(
        app,
        host=host,
        port=port,
        log_level="info",
        access_log=True
    )