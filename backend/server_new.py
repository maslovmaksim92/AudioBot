# New modular server entry point
from app.main import app

# Export app for backward compatibility
__all__ = ["app"]

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)