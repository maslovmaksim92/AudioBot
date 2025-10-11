#!/bin/bash
# Pre-start script for Render deployment
# Fixes import statements to work with backend.app.* structure

echo "🔧 Fixing imports for Render deployment..."
python /opt/render/project/src/backend/fix_imports.py

echo "✅ Pre-start complete"
