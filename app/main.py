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

# Import directly from the root app.py file (not app module)
import importlib.util
app_path = parent_path / "app.py"
spec = importlib.util.spec_from_file_location("vasdom_app", app_path)
vasdom_app = importlib.util.module_from_spec(spec)
spec.loader.exec_module(vasdom_app)

app = vasdom_app.app

print("✅ app/main.py: Successfully imported app")

# Export for uvicorn
__all__ = ["app"]