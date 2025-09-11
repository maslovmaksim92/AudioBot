#!/bin/bash
# Build script для установки emergentintegrations на Render

echo "🔧 Installing emergentintegrations on Render..."

# Upgrade pip first
pip install --upgrade pip

# Try to install emergentintegrations with custom index
pip install emergentintegrations --extra-index-url https://d33sy5i8bnduwe.cloudfront.net/simple/ || {
    echo "⚠️ Failed to install emergentintegrations, continuing with fallback mode"
    exit 0
}

echo "✅ emergentintegrations installed successfully"