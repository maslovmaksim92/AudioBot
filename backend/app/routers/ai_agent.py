"""
AI Agent router для улучшений разделов
"""
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Optional
import os
import logging
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import uuid4

from backend.app.config.database import get_db
from backend.app.models.ai_agent_config import AIAgentConfig
from sqlalchemy import select

router = APIRouter(prefix="/ai-agent", tags=["AI Agent"])
logger = logging.getLogger(__name__)


class ImprovementRequest(BaseModel):
    section: str
    improvement_request: str


class AgentConfigUpdate(BaseModel):
    agent_name: str
    prompt: Optional[str] = None
    model: Optional[str] = None
    temperature: Optional[float] = None
    enabled: Optional[bool] = None


@router.post("/improve-section")
async def improve_section(request: ImprovementRequest, db: AsyncSession = Depends(get_db)):
    """
    Endpoint для запроса улучшения раздела через AI агента
    
    Этот endpoint будет вызывать настроенного AI агента из platform.openai
    который анализирует запрос, вносит изменения в код, коммитит в GitHub
    и деплоит на Render.
    """
    try:
        # Получаем конфигурацию агента
        result = await db.execute(
            select(AIAgentConfig)
            .where(AIAgentConfig.agent_name == "section_improver")
            .where(AIAgentConfig.enabled == True)
        )
        agent_config = result.scalar_one_or_none()
        
        if not agent_config:
            return {
                "success": False,
                "error": "AI агент не настроен. Перейдите в раздел 'Агенты' для настройки."
            }
        
        # TODO: Здесь будет интеграция с platform.openai
        # Пока возвращаем информацию о том что нужно сделать
        
        return {
            "success": True,
            "message": f"""AI агент получил запрос на улучшение раздела "{request.section}".

Запрос: {request.improvement_request}

Агент проанализирует код, внесет необходимые изменения и задеплоит обновление.

[PLACEHOLDER - Здесь будет реальный вызов OpenAI Assistant API]

Для активации:
1. Перейдите в раздел "Агенты"
2. Настройте параметры агента "Улучшение разделов"
3. Вставьте промпт и API ключ
4. Активируйте агента

Текущая конфигурация агента:
- Модель: {agent_config.model}
- Temperature: {agent_config.temperature}
- Промпт: {agent_config.prompt[:100]}...
"""
        }
        
    except Exception as e:
        logger.error(f"Error in improve_section: {e}")
        return {
            "success": False,
            "error": f"Ошибка обработки запроса: {str(e)}"
        }


@router.get("/configs")
async def get_agent_configs(db: AsyncSession = Depends(get_db)):
    """Получить все конфигурации AI агентов"""
    try:
        result = await db.execute(select(AIAgentConfig))
        configs = result.scalars().all()
        
        return {
            "agents": [
                {
                    "id": str(config.id),
                    "agent_name": config.agent_name,
                    "display_name": config.display_name,
                    "description": config.description,
                    "prompt": config.prompt,
                    "model": config.model,
                    "temperature": config.temperature,
                    "enabled": config.enabled,
                    "created_at": config.created_at.isoformat() if config.created_at else None
                }
                for config in configs
            ]
        }
    except Exception as e:
        logger.error(f"Error getting agent configs: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/configs")
async def create_or_update_agent_config(
    config: AgentConfigUpdate, 
    db: AsyncSession = Depends(get_db)
):
    """Создать или обновить конфигурацию AI агента"""
    try:
        # Проверяем существует ли агент
        result = await db.execute(
            select(AIAgentConfig)
            .where(AIAgentConfig.agent_name == config.agent_name)
        )
        existing = result.scalar_one_or_none()
        
        if existing:
            # Обновляем существующего
            if config.prompt is not None:
                existing.prompt = config.prompt
            if config.model is not None:
                existing.model = config.model
            if config.temperature is not None:
                existing.temperature = config.temperature
            if config.enabled is not None:
                existing.enabled = config.enabled
        else:
            # Создаем нового
            new_config = AIAgentConfig(
                id=str(uuid4()),
                agent_name=config.agent_name,
                display_name=config.agent_name.replace('_', ' ').title(),
                description="Custom AI agent",
                prompt=config.prompt or "",
                model=config.model or "gpt-4",
                temperature=config.temperature or 0.7,
                enabled=config.enabled if config.enabled is not None else True
            )
            db.add(new_config)
        
        await db.commit()
        
        return {
            "success": True,
            "message": "Конфигурация агента сохранена"
        }
        
    except Exception as e:
        await db.rollback()
        logger.error(f"Error saving agent config: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/configs/{agent_name}")
async def get_agent_config(agent_name: str, db: AsyncSession = Depends(get_db)):
    """Получить конфигурацию конкретного агента"""
    try:
        result = await db.execute(
            select(AIAgentConfig)
            .where(AIAgentConfig.agent_name == agent_name)
        )
        config = result.scalar_one_or_none()
        
        if not config:
            raise HTTPException(status_code=404, detail="Agent not found")
        
        return {
            "id": str(config.id),
            "agent_name": config.agent_name,
            "display_name": config.display_name,
            "description": config.description,
            "prompt": config.prompt,
            "model": config.model,
            "temperature": config.temperature,
            "enabled": config.enabled,
            "created_at": config.created_at.isoformat() if config.created_at else None
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting agent config: {e}")
        raise HTTPException(status_code=500, detail=str(e))
