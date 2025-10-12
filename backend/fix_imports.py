#!/usr/bin/env python3
"""
Fix imports for Render deployment
Converts 'from app.*' to 'from backend.app.*' in all Python files
"""
import os
import re
from pathlib import Path

def fix_imports_in_file(file_path):
    """Fix imports in a single file"""
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    original_content = content
    
    # Replace 'from app.' with 'from backend.app.'
    # But only at the start of a line
    content = re.sub(r'^from app\.', 'from backend.app.', content, flags=re.MULTILINE)
    
    # Replace 'import app.' with 'import backend.app.'
    content = re.sub(r'^import app\.', 'import backend.app.', content, flags=re.MULTILINE)
    
    if content != original_content:
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        return True
    return False

def main():
    """Fix all Python files in app directory"""
    backend_dir = Path(__file__).parent
    app_dir = backend_dir / 'app'
    
    fixed_count = 0
    
    for py_file in app_dir.rglob('*.py'):
        if fix_imports_in_file(py_file):
            print(f"✓ Fixed: {py_file.relative_to(backend_dir)}")
            fixed_count += 1
    
    if fixed_count > 0:
        print(f"\n✅ Fixed {fixed_count} files")
    else:
        print("✅ All imports are correct")

if __name__ == '__main__':
    main()
