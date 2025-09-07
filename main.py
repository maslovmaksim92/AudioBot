#!/usr/bin/env python3
"""
VasDom AI Business Management System - Main Entry Point
Главный файл запуска приложения для деплоя на Render
"""

import sys
import os
from pathlib import Path
import uvicorn
import logging

# Добавляем путь к backend в PYTHONPATH
backend_path = Path(__file__).parent / "backend"
sys.path.insert(0, str(backend_path))

# Настраиваем логирование
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

if __name__ == "__main__":
    try:
        # Импортируем FastAPI приложение из backend
        from server import app
        
        # Получаем порт из переменных окружения (для Render)
        port = int(os.environ.get("PORT", 8001))
        
        logger.info(f"🚀 Starting VasDom AI Business Management System on port {port}")
        
        # Запускаем сервер
        uvicorn.run(
            app, 
            host="0.0.0.0", 
            port=port,
            log_level="info",
            access_log=True
        )
        
    except Exception as e:
        logger.error(f"❌ Failed to start server: {str(e)}")
        sys.exit(1)