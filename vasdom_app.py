# VasDom AudioBot - Modular Architecture Entry Point
# All functionality has been moved to modular structure: backend/app/
# This file now serves as compatibility layer and imports the main app

import_error = None

try:
    from app.main import app
    print("✅ VasDom AudioBot loaded from modular structure (backend/app/)")
except ImportError as e:
    import_error = e
    print(f"❌ Failed to import modular app: {e}")
    # Fallback to legacy monolithic structure
    from fastapi import FastAPI
    from fastapi.middleware.cors import CORSMiddleware
    from fastapi.responses import RedirectResponse, HTMLResponse
    from pydantic import BaseModel, Field
    from typing import List, Optional, Dict, Any
    from datetime import datetime, timedelta
    import os
    import uuid
    import logging
    import asyncio
    import json
    import httpx
    from pathlib import Path
    from dotenv import load_dotenv
    from sqlalchemy import create_engine, Column, String, DateTime, Text, Integer, Boolean
    from sqlalchemy.ext.declarative import declarative_base
    from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
    from sqlalchemy.orm import sessionmaker
    from databases import Database

    # Load environment variables
    ROOT_DIR = Path(__file__).parent
    load_dotenv(ROOT_DIR / '.env')

    # Setup cloud-friendly logging
    log_handlers = [logging.StreamHandler()]

    # Добавляем файловое логирование только если возможно
    try:
        log_file_path = os.environ.get('LOG_FILE', '/tmp/vasdom_audiobot.log')
        log_handlers.append(logging.FileHandler(log_file_path, encoding='utf-8'))
    except Exception as log_error:
        # На Render может не быть прав на запись в /var/log, используем только stdout
        pass

    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=log_handlers
    )
    logger = logging.getLogger(__name__)

    # Создаем fallback приложение
    app = FastAPI(
        title="VasDom AudioBot API (Fallback)",
        version="3.0.0",
        description="🤖 Fallback mode - модульная структура недоступна"
    )

    @app.get("/")
    async def fallback_root():
        return {
            "message": "VasDom AudioBot - Fallback Mode",
            "status": "Модульная структура недоступна",
            "error": str(import_error) if import_error else "Unknown error"
        }

# Export app for entry point
__all__ = ["app"]

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)