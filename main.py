"""
Entry point для VasDom AudioBot с модулем самообучения
Совместимость с Render.com и supervisor управлением
"""
import sys
import os

# Добавляем backend в путь для импортов
backend_path = os.path.join(os.path.dirname(__file__), 'backend')
sys.path.insert(0, backend_path)

try:
    # Пытаемся использовать новое модульное приложение
    import sys
    import os
    backend_path = os.path.join(os.path.dirname(__file__), 'backend')
    if backend_path not in sys.path:
        sys.path.insert(0, backend_path)
    
    from app.main import app
    print("✅ Запуск модульного приложения с самообучением v2.0")
except ImportError as e:
    print(f"⚠️ Ошибка импорта модульного приложения: {e}")
    print("🔄 Fallback на старый server.py")
    
    # Fallback на старое приложение
    try:
        from server import app
        print("✅ Запуск совместимого приложения")
    except ImportError as fallback_error:
        print(f"❌ Критическая ошибка: {fallback_error}")
        # Создаем минимальное приложение
        from fastapi import FastAPI
        app = FastAPI(title="VasDom AudioBot - Emergency Mode")
        
        @app.get("/")
        async def emergency_root():
            return {
                "status": "emergency_mode",
                "message": "Приложение запущено в аварийном режиме",
                "error": str(fallback_error)
            }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=int(os.getenv("PORT", 8001)),
        reload=False,  # В production отключаем reload
        log_level="info"
    )