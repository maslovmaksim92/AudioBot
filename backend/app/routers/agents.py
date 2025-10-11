"""
API роутер для агентов - CRUD операции и статистика
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, text
from typing import List
from datetime import datetime, timezone, timedelta
import logging
from uuid import uuid4

from backend.app.config.database import get_db
from backend.app.models.agent import Agent, AgentCreate, AgentUpdate, AgentResponse, AgentStats

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/agents", tags=["Agents"])

# ============= CRUD Operations =============

@router.post("/", response_model=AgentResponse)
async def create_agent(
    agent_data: AgentCreate,
    db: AsyncSession = Depends(get_db)
):
    """
    Создать нового агента
    """
    try:
        new_agent = Agent(
            id=str(uuid4()),
            name=agent_data.name,
            description=agent_data.description,
            type=agent_data.type,
            status=agent_data.status,
            triggers=[t.dict() for t in agent_data.triggers],
            actions=[a.dict() for a in agent_data.actions],
            config=agent_data.config,
            executions_total=0,
            executions_success=0,
            executions_failed=0
        )
        
        db.add(new_agent)
        await db.commit()
        await db.refresh(new_agent)
        
        logger.info(f"✅ Agent created: {new_agent.name} (ID: {new_agent.id})")
        
        return AgentResponse(**new_agent.to_dict())
    
    except Exception as e:
        await db.rollback()
        logger.error(f"❌ Error creating agent: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to create agent: {str(e)}")


@router.get("/", response_model=List[AgentResponse])
async def get_agents(
    status: str = None,
    type: str = None,
):
    """
    Получить список всех агентов
    """
    try:
        import asyncpg
        import os
        
        db_url = os.environ.get('DATABASE_URL', '').replace('postgresql+asyncpg://', 'postgresql://')
        conn = await asyncpg.connect(db_url)
        
        try:
            query = "SELECT * FROM agents WHERE 1=1"
            params = []
            
            if status:
                query += f" AND status = ${len(params) + 1}"
                params.append(status)
            if type:
                query += f" AND type = ${len(params) + 1}"
                params.append(type)
            
            query += " ORDER BY created_at DESC"
            
            rows = await conn.fetch(query, *params)
            
            agents = []
            for row in rows:
                agents.append(AgentResponse(
                    id=row['id'],
                    name=row['name'],
                    description=row['description'],
                    type=row['type'],
                    status=row['status'],
                    triggers=row['triggers'] or [],
                    actions=row['actions'] or [],
                    config=row['config'] or {},
                    executions_total=row['executions_total'] or 0,
                    executions_success=row['executions_success'] or 0,
                    executions_failed=row['executions_failed'] or 0,
                    last_execution=row['last_execution'].isoformat() if row['last_execution'] else None,
                    created_at=row['created_at'].isoformat(),
                    updated_at=row['updated_at'].isoformat(),
                    created_by=row['created_by']
                ))
            
            return agents
        finally:
            await conn.close()
    
    except Exception as e:
        logger.error(f"❌ Error fetching agents: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch agents: {str(e)}")


@router.get("/{agent_id}", response_model=AgentResponse)
async def get_agent(
    agent_id: str,
    db: AsyncSession = Depends(get_db)
):
    """
    Получить информацию об агенте
    """
    try:
        result = await db.execute(select(Agent).where(Agent.id == agent_id))
        agent = result.scalar_one_or_none()
        
        if not agent:
            raise HTTPException(status_code=404, detail="Agent not found")
        
        return AgentResponse(**agent.to_dict())
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error fetching agent {agent_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch agent: {str(e)}")


@router.put("/{agent_id}", response_model=AgentResponse)
async def update_agent(
    agent_id: str,
    agent_data: AgentUpdate,
    db: AsyncSession = Depends(get_db)
):
    """
    Обновить агента
    """
    try:
        result = await db.execute(select(Agent).where(Agent.id == agent_id))
        agent = result.scalar_one_or_none()
        
        if not agent:
            raise HTTPException(status_code=404, detail="Agent not found")
        
        # Обновление полей
        if agent_data.name is not None:
            agent.name = agent_data.name
        if agent_data.description is not None:
            agent.description = agent_data.description
        if agent_data.type is not None:
            agent.type = agent_data.type
        if agent_data.status is not None:
            agent.status = agent_data.status
        if agent_data.triggers is not None:
            agent.triggers = [t.dict() for t in agent_data.triggers]
        if agent_data.actions is not None:
            agent.actions = [a.dict() for a in agent_data.actions]
        if agent_data.config is not None:
            agent.config = agent_data.config
        
        agent.updated_at = datetime.now(timezone.utc)
        
        await db.commit()
        await db.refresh(agent)
        
        logger.info(f"✅ Agent updated: {agent.name} (ID: {agent.id})")
        
        return AgentResponse(**agent.to_dict())
    
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        logger.error(f"❌ Error updating agent {agent_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to update agent: {str(e)}")


@router.delete("/{agent_id}")
async def delete_agent(
    agent_id: str,
    db: AsyncSession = Depends(get_db)
):
    """
    Удалить агента
    """
    try:
        result = await db.execute(select(Agent).where(Agent.id == agent_id))
        agent = result.scalar_one_or_none()
        
        if not agent:
            raise HTTPException(status_code=404, detail="Agent not found")
        
        await db.delete(agent)
        await db.commit()
        
        logger.info(f"✅ Agent deleted: {agent.name} (ID: {agent.id})")
        
        return {"success": True, "message": "Agent deleted successfully"}
    
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        logger.error(f"❌ Error deleting agent {agent_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to delete agent: {str(e)}")


# ============= Statistics =============

@router.get("/stats/summary", response_model=AgentStats)
async def get_agent_stats(
    db: AsyncSession = Depends(get_db)
):
    """
    Получить статистику по агентам
    """
    try:
        # Общее количество агентов
        total_result = await db.execute(select(func.count(Agent.id)))
        total_agents = total_result.scalar() or 0
        
        # Активные агенты
        active_result = await db.execute(
            select(func.count(Agent.id)).where(Agent.status == 'active')
        )
        active_agents = active_result.scalar() or 0
        
        # Неактивные агенты
        inactive_agents = total_agents - active_agents
        
        # Выполнения за сегодня
        today_start = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
        executions_today_result = await db.execute(
            select(func.sum(Agent.executions_total)).where(
                Agent.last_execution >= today_start
            )
        )
        executions_today = executions_today_result.scalar() or 0
        
        # Процент успешности
        total_exec_result = await db.execute(select(func.sum(Agent.executions_total)))
        total_exec = total_exec_result.scalar() or 0
        
        success_exec_result = await db.execute(select(func.sum(Agent.executions_success)))
        success_exec = success_exec_result.scalar() or 0
        
        success_rate = (success_exec / total_exec * 100) if total_exec > 0 else 0
        
        # Количество пользователей (уникальных created_by)
        users_result = await db.execute(
            select(func.count(func.distinct(Agent.created_by)))
        )
        total_users = users_result.scalar() or 0
        
        return AgentStats(
            total_agents=total_agents,
            active_agents=active_agents,
            inactive_agents=inactive_agents,
            executions_today=int(executions_today),
            executions_success_rate=round(success_rate, 2),
            total_users=total_users
        )
    
    except Exception as e:
        logger.error(f"❌ Error fetching agent stats: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch stats: {str(e)}")


@router.post("/{agent_id}/execute")
async def execute_agent(
    agent_id: str,
    db: AsyncSession = Depends(get_db)
):
    """
    Ручное выполнение агента (для тестирования)
    """
    try:
        result = await db.execute(select(Agent).where(Agent.id == agent_id))
        agent = result.scalar_one_or_none()
        
        if not agent:
            raise HTTPException(status_code=404, detail="Agent not found")
        
        if agent.status != 'active':
            raise HTTPException(status_code=400, detail="Agent is not active")
        
        # Здесь будет логика выполнения агента
        # Пока просто обновляем статистику
        agent.executions_total += 1
        agent.executions_success += 1
        agent.last_execution = datetime.now(timezone.utc)
        
        await db.commit()
        
        logger.info(f"✅ Agent executed: {agent.name} (ID: {agent.id})")
        
        return {
            "success": True,
            "message": "Agent executed successfully",
            "agent_id": agent.id,
            "execution_time": agent.last_execution.isoformat()
        }
    
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        logger.error(f"❌ Error executing agent {agent_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to execute agent: {str(e)}")


# ============= Database Initialization =============

@router.post("/init-db")
async def initialize_agents_table(db: AsyncSession = Depends(get_db)):
    """
    Инициализировать таблицу агентов
    """
    try:
        # Создаём таблицу
        await db.execute(text("""
            CREATE TABLE IF NOT EXISTS agents (
                id VARCHAR(36) PRIMARY KEY,
                name VARCHAR(200) NOT NULL,
                description TEXT,
                type VARCHAR(50) NOT NULL,
                status VARCHAR(20) DEFAULT 'active',
                triggers JSONB DEFAULT '[]'::jsonb,
                actions JSONB DEFAULT '[]'::jsonb,
                config JSONB DEFAULT '{}'::jsonb,
                executions_total INTEGER DEFAULT 0,
                executions_success INTEGER DEFAULT 0,
                executions_failed INTEGER DEFAULT 0,
                last_execution TIMESTAMP WITH TIME ZONE,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                created_by VARCHAR(36)
            )
        """))
        
        # Создаём индексы
        await db.execute(text("CREATE INDEX IF NOT EXISTS idx_agents_status ON agents(status)"))
        await db.execute(text("CREATE INDEX IF NOT EXISTS idx_agents_type ON agents(type)"))
        await db.execute(text("CREATE INDEX IF NOT EXISTS idx_agents_created_at ON agents(created_at)"))
        
        await db.commit()
        
        logger.info("✅ Agents table created successfully")
        
        return {"success": True, "message": "Agents table created successfully"}
    
    except Exception as e:
        await db.rollback()
        logger.error(f"❌ Error creating agents table: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to create table: {str(e)}")
