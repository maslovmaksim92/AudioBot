#!/usr/bin/env python3
"""
Main entry point for AI Assistant deployed on Render
"""

import os
import sys
import logging
from pathlib import Path

# Add current directory to Python path
current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir))
sys.path.insert(0, str(current_dir / "backend"))

# Configure logging for production
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

def create_app():
    """Create and configure the FastAPI application"""
    import_error = None
    
    try:
        # Import the render version of server
        from backend.server_render import app
        
        logger.info("🚀 AI Assistant loaded successfully")
        logger.info(f"Python version: {sys.version}")
        logger.info(f"Working directory: {os.getcwd()}")
        logger.info(f"Python path: {sys.path[:3]}")
        
        return app
        
    except ImportError as e:
        import_error = e
        logger.error(f"❌ Import error: {e}")
        # Fallback to basic FastAPI app
        from fastapi import FastAPI
        
        fallback_app = FastAPI(title="AI Assistant", version="1.0.0")
        
        @fallback_app.get("/")
        async def root():
            return {
                "message": "AI Assistant Fallback Mode",
                "status": "partial",
                "error": str(import_error),
                "note": "Some features may not be available"
            }
        
        @fallback_app.get("/health")
        async def health():
            return {"status": "ok", "mode": "fallback"}
        
        return fallback_app
        
    except Exception as e:
        logger.error(f"❌ Failed to create application: {e}")
        raise

# Create app instance for ASGI servers (Render uses this)
app = create_app()

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