# Minimal shim to keep supervisor/uvicorn import path stable
# Redirects to the real FastAPI app defined in app_main.py
from backend.app_main import app  # noqa: F401