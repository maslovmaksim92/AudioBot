"""
Entry point для VasDom AudioBot на Render
Cloud-native версия без MongoDB, только PostgreSQL
"""
import sys
import os

# Добавляем backend в путь для импортов
backend_path = os.path.join(os.path.dirname(__file__), 'backend')
sys.path.insert(0, backend_path)

try:
    # Используем новое модульное приложение для Render
    from app.main import app
    print("✅ Запуск VasDom AudioBot с самообучением v2.0 на Render")
except ImportError as e:
    print(f"⚠️ Модульное приложение недоступно: {e}")
    print("🔄 Fallback на минимальную версию")
    
    # Fallback на минимальное приложение
    try:
        from server import app
        print("✅ Запуск минимальной версии на Render")
    except ImportError as fallback_error:
        print(f"❌ Критическая ошибка: {fallback_error}")
        # Создаем экстренное приложение
        from fastapi import FastAPI
        app = FastAPI(title="VasDom AudioBot - Emergency Mode")
        
        @app.get("/")
        async def emergency_root():
            return {
                "status": "emergency_mode",
                "message": "Приложение запущено в аварийном режиме на Render",
                "platform": "Render",
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