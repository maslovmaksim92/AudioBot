"""
VasDom AudioBot - Entry Point для Render
Максимально обучаемый AI в production режиме
"""
import sys
import os

# Добавляем backend в путь для импортов
backend_path = os.path.join(os.path.dirname(__file__), 'backend')
sys.path.insert(0, backend_path)

try:
    # Импортируем готовое production приложение
    from server import app
    print("🎯 VasDom AudioBot v3.0 - Максимально обучаемый AI запущен!")
    print("🧠 Режим: Непрерывное самообучение на реальных данных")
    print("🚀 Платформа: Render Cloud")
except ImportError as e:
    print(f"❌ Критическая ошибка импорта: {e}")
    
    # Экстренное приложение
    from fastapi import FastAPI
    app = FastAPI(title="VasDom AudioBot - Emergency")
    
    @app.get("/")
    async def emergency():
        return {
            "status": "emergency",
            "error": str(e),
            "message": "Свяжитесь с администратором"
        }

# Для Render
if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8001))
    print(f"🚀 Запуск на порту {port} для Render")
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=port,
        reload=False,
        log_level="info"
    )