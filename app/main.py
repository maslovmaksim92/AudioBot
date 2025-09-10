"""
Redirect для Render auto-detection
Render ищет app.main:app, мы даем ему то что он хочет
"""

# Импортируем наше реальное приложение
import sys
import os

# Добавляем корень в путь
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

error_msg = None

try:
    # Импортируем наше настоящее приложение
    from main import app
    print("🎯 VasDom AudioBot v3.0 через app.main:app redirect - SUCCESS!")
except ImportError as e:
    error_msg = str(e)
    print(f"❌ Ошибка импорта main: {error_msg}")
    
    # Emergency fallback
    from fastapi import FastAPI
    app = FastAPI(title="VasDom AudioBot - Emergency Redirect")
    
    @app.get("/")
    async def emergency():
        return {
            "status": "emergency_redirect", 
            "message": "Main app not found, using emergency mode",
            "error": error_msg
        }

# Render получает то что хочет
__all__ = ['app']