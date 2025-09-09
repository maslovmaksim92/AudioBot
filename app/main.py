#!/usr/bin/env python3
"""
VasDom AudioBot - App Directory Entry Point
This redirects to the real app in parent directory
"""

import sys
from pathlib import Path

# Add parent directory to path
parent_path = Path(__file__).parent.parent
sys.path.insert(0, str(parent_path))

print("🔄 app/main.py: Redirecting to main app...")

# Import from parent directory
from app import app

print("✅ app/main.py: Successfully imported app")

# Export for uvicorn
__all__ = ["app"]