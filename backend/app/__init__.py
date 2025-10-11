"""
Backend app package with universal import compatibility
"""
import sys
from pathlib import Path

# Add parent directory to sys.path for both local and Render environments
backend_dir = Path(__file__).parent.parent.resolve()
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

# Create alias: app.* -> backend.app.*
# This allows "from app.config" to work even when "from backend.app.config" is needed
if 'backend' not in sys.modules:
    # We're in Render environment, running as backend.server
    # Need to make 'app' available as alias to 'backend.app'
    pass
else:
    # Make app.* imports work by aliasing to backend.app.*
    backend_app = sys.modules.get('backend.app')
    if backend_app:
        sys.modules['app'] = backend_app