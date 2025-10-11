"""
Seed data для AI агентов
"""
import asyncio
from uuid import uuid4
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from backend.app.config.database import AsyncSessionLocal
from backend.app.models.ai_agent_config import AIAgentConfig


DEFAULT_SECTION_IMPROVER_PROMPT = """Ты - AI агент для улучшения разделов веб-приложения VasDom.

Твоя задача:
1. Проанализировать запрос пользователя на улучшение раздела
2. Понять текущую структуру кода (frontend React + backend FastAPI)
3. Внести необходимые изменения в код
4. Создать коммит в GitHub репозитории
5. Запустить деплой на Render

ВАЖНО:
- Используй TypeScript/JavaScript для frontend (React, Tailwind CSS)
- Используй Python для backend (FastAPI, SQLAlchemy)
- Следуй best practices и код стандартам проекта
- Тестируй изменения перед деплоем
- Пиши чистый, читаемый код с комментариями

ДОСТУП:
- GitHub API для коммитов: используй переданный token
- Render API для деплоя: используй переданный API key

ОТВЕТ:
Опиши что ты сделал, какие файлы изменил, ссылку на коммит и статус деплоя.
"""


async def seed_ai_agents():
    """Создает базовые конфигурации AI агентов"""
    async with AsyncSessionLocal() as db:
        try:
            # Проверяем есть ли уже агент section_improver
            result = await db.execute(
                select(AIAgentConfig)
                .where(AIAgentConfig.agent_name == "section_improver")
            )
            existing = result.scalar_one_or_none()
            
            if not existing:
                # Создаем нового
                agent = AIAgentConfig(
                    id=str(uuid4()),
                    agent_name="section_improver",
                    display_name="Улучшение разделов",
                    description="AI агент для автоматического улучшения разделов приложения. Анализирует запросы, вносит изменения в код, коммитит в GitHub и деплоит на Render.",
                    prompt=DEFAULT_SECTION_IMPROVER_PROMPT,
                    model="gpt-4",
                    temperature=0.7,
                    enabled=False  # По умолчанию выключен, пользователь должен настроить
                )
                db.add(agent)
                await db.commit()
                print(f"✅ Created AI agent: section_improver")
            else:
                print(f"ℹ️  AI agent already exists: section_improver")
                
        except Exception as e:
            print(f"❌ Error seeding AI agents: {e}")
            await db.rollback()


if __name__ == "__main__":
    print("🌱 Seeding AI agents...")
    asyncio.run(seed_ai_agents())
    print("✅ Done!")
