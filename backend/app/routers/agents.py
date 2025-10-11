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
import json

from backend.app.config.database import get_db
from backend.app.models.agent import Agent, AgentCreate, AgentUpdate, AgentResponse, AgentStats

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/agents", tags=["Agents"])

# ============= CRUD Operations =============

@router.post("/", response_model=AgentResponse)
async def create_agent(
    agent_data: AgentCreate,
):
    """
    Создать нового агента
    """
    try:
        import asyncpg
        import os
        import json
        
        db_url = os.environ.get('DATABASE_URL', '').replace('postgresql+asyncpg://', 'postgresql://')
        conn = await asyncpg.connect(db_url)
        
        try:
            agent_id = str(uuid4())
            now = datetime.now(timezone.utc)
            
            await conn.execute("""
                INSERT INTO agents (id, name, description, type, status, triggers, actions, config, 
                                    executions_total, executions_success, executions_failed, created_at, updated_at)
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13)
            """, agent_id, agent_data.name, agent_data.description, agent_data.type, agent_data.status,
                json.dumps([t.dict() for t in agent_data.triggers]),
                json.dumps([a.dict() for a in agent_data.actions]),
                json.dumps(agent_data.config),
                0, 0, 0, now, now)
            
            row = await conn.fetchrow("SELECT * FROM agents WHERE id = $1", agent_id)
            
            logger.info(f"✅ Agent created: {agent_data.name} (ID: {agent_id})")
            
            # Десериализуем JSON поля если они строки
            triggers = row['triggers']
            if isinstance(triggers, str):
                triggers = json.loads(triggers)
            
            actions = row['actions']
            if isinstance(actions, str):
                actions = json.loads(actions)
            
            config = row['config']
            if isinstance(config, str):
                config = json.loads(config)
            
            return AgentResponse(
                id=row['id'],
                name=row['name'],
                description=row['description'],
                type=row['type'],
                status=row['status'],
                triggers=triggers or [],
                actions=actions or [],
                config=config or {},
                executions_total=row['executions_total'] or 0,
                executions_success=row['executions_success'] or 0,
                executions_failed=row['executions_failed'] or 0,
                last_execution=row['last_execution'].isoformat() if row['last_execution'] else None,
                created_at=row['created_at'].isoformat(),
                updated_at=row['updated_at'].isoformat(),
                created_by=row['created_by']
            )
        finally:
            await conn.close()
    
    except Exception as e:
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
                # Десериализуем JSON поля если они строки
                triggers = row['triggers']
                if isinstance(triggers, str):
                    triggers = json.loads(triggers)
                
                actions = row['actions']
                if isinstance(actions, str):
                    actions = json.loads(actions)
                
                config = row['config']
                if isinstance(config, str):
                    config = json.loads(config)
                
                agents.append(AgentResponse(
                    id=row['id'],
                    name=row['name'],
                    description=row['description'],
                    type=row['type'],
                    status=row['status'],
                    triggers=triggers or [],
                    actions=actions or [],
                    config=config or {},
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
):
    """
    Удалить агента
    """
    try:
        import asyncpg
        import os
        
        db_url = os.environ.get('DATABASE_URL', '').replace('postgresql+asyncpg://', 'postgresql://')
        conn = await asyncpg.connect(db_url)
        
        try:
            result = await conn.fetchrow("SELECT name FROM agents WHERE id = $1", agent_id)
            
            if not result:
                raise HTTPException(status_code=404, detail="Agent not found")
            
            await conn.execute("DELETE FROM agents WHERE id = $1", agent_id)
            
            logger.info(f"✅ Agent deleted: {result['name']} (ID: {agent_id})")
            
            return {"success": True, "message": "Agent deleted successfully"}
        finally:
            await conn.close()
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error deleting agent {agent_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to delete agent: {str(e)}")


# ============= Statistics =============

@router.get("/stats/summary", response_model=AgentStats)
async def get_agent_stats():
    """
    Получить статистику по агентам
    """
    try:
        import asyncpg
        import os
        
        db_url = os.environ.get('DATABASE_URL', '').replace('postgresql+asyncpg://', 'postgresql://')
        conn = await asyncpg.connect(db_url)
        
        try:
            # Общее количество агентов
            total_agents = await conn.fetchval("SELECT COUNT(*) FROM agents")
            
            # Активные агенты
            active_agents = await conn.fetchval("SELECT COUNT(*) FROM agents WHERE status = 'active'")
            
            # Неактивные агенты
            inactive_agents = total_agents - active_agents
            
            # Сумма всех выполнений
            total_exec = await conn.fetchval("SELECT COALESCE(SUM(executions_total), 0) FROM agents") or 0
            success_exec = await conn.fetchval("SELECT COALESCE(SUM(executions_success), 0) FROM agents") or 0
            
            success_rate = (success_exec / total_exec * 100) if total_exec > 0 else 0
            
            # Выполнения за сегодня (приблизительно)
            today_start = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
            executions_today = await conn.fetchval(
                "SELECT COALESCE(SUM(executions_total), 0) FROM agents WHERE last_execution >= $1",
                today_start
            ) or 0
            
            # Количество пользователей
            total_users = await conn.fetchval("SELECT COUNT(DISTINCT created_by) FROM agents WHERE created_by IS NOT NULL") or 0
            
            return AgentStats(
                total_agents=total_agents or 0,
                active_agents=active_agents or 0,
                inactive_agents=inactive_agents or 0,
                executions_today=int(executions_today),
                executions_success_rate=round(success_rate, 2),
                total_users=total_users
            )
        finally:
            await conn.close()
    
    except Exception as e:
        logger.error(f"❌ Error fetching agent stats: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch stats: {str(e)}")


@router.post("/{agent_id}/execute")
async def execute_agent(agent_id: str):
    """
    Ручное выполнение агента
    """
    try:
        import asyncpg
        import os
        from backend.app.services.agent_executor import agent_executor
        
        db_url = os.environ.get('DATABASE_URL', '').replace('postgresql+asyncpg://', 'postgresql://')
        conn = await asyncpg.connect(db_url)
        
        try:
            # Получаем агента
            row = await conn.fetchrow("SELECT * FROM agents WHERE id = $1", agent_id)
            
            if not row:
                raise HTTPException(status_code=404, detail="Agent not found")
            
            if row['status'] != 'active':
                raise HTTPException(status_code=400, detail="Agent is not active")
            
            # Преобразуем в dict для executor
            agent = {
                'id': row['id'],
                'name': row['name'],
                'description': row['description'],
                'type': row['type'],
                'status': row['status'],
                'triggers': row['triggers'] if isinstance(row['triggers'], list) else json.loads(row['triggers']) if row['triggers'] else [],
                'actions': row['actions'] if isinstance(row['actions'], list) else json.loads(row['actions']) if row['actions'] else [],
                'config': row['config'] if isinstance(row['config'], dict) else json.loads(row['config']) if row['config'] else {}
            }
            
            # Выполняем агента
            result = await agent_executor.execute_agent(agent)
            
            # Обновляем статистику
            now = datetime.now(timezone.utc)
            if result['success']:
                await conn.execute("""
                    UPDATE agents 
                    SET executions_total = executions_total + 1,
                        executions_success = executions_success + 1,
                        last_execution = $1,
                        updated_at = $1
                    WHERE id = $2
                """, now, agent_id)
            else:
                await conn.execute("""
                    UPDATE agents 
                    SET executions_total = executions_total + 1,
                        executions_failed = executions_failed + 1,
                        last_execution = $1,
                        updated_at = $1
                    WHERE id = $2
                """, now, agent_id)
            
            logger.info(f"✅ Agent executed: {agent['name']} (ID: {agent_id})")
            
            return {
                "success": result['success'],
                "message": "Agent executed successfully" if result['success'] else "Agent execution failed",
                "agent_id": agent_id,
                "execution_time": now.isoformat(),
                "details": result
            }
        finally:
            await conn.close()
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error executing agent {agent_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to execute agent: {str(e)}")


# ============= Database Initialization =============

@router.post("/reload-scheduler")
async def reload_agents_in_scheduler():
    """
    Перезагрузить всех агентов в планировщик
    """
    try:
        import asyncpg
        import os
        from backend.app.services.agent_scheduler import agent_scheduler
        from backend.app.services.agent_executor import agent_executor
        
        if not agent_scheduler:
            raise HTTPException(status_code=500, detail="Agent scheduler not initialized")
        
        db_url = os.environ.get('DATABASE_URL', '').replace('postgresql+asyncpg://', 'postgresql://')
        conn = await asyncpg.connect(db_url)
        
        try:
            # Получаем всех активных агентов
            rows = await conn.fetch("SELECT * FROM agents WHERE status = 'active'")
            
            agents = []
            for row in rows:
                # Десериализуем JSON поля
                triggers = row['triggers']
                if isinstance(triggers, str):
                    triggers = json.loads(triggers)
                
                actions = row['actions']
                if isinstance(actions, str):
                    actions = json.loads(actions)
                
                config = row['config']
                if isinstance(config, str):
                    config = json.loads(config)
                
                agents.append({
                    'id': row['id'],
                    'name': row['name'],
                    'description': row['description'],
                    'type': row['type'],
                    'status': row['status'],
                    'triggers': triggers or [],
                    'actions': actions or [],
                    'config': config or {}
                })
            
            # Функция-обёртка для выполнения агента с обновлением статистики
            async def execute_and_update(agent):
                result = await agent_executor.execute_agent(agent)
                
                # Обновляем статистику в БД
                now = datetime.now(timezone.utc)
                if result['success']:
                    await conn.execute("""
                        UPDATE agents 
                        SET executions_total = executions_total + 1,
                            executions_success = executions_success + 1,
                            last_execution = $1,
                            updated_at = $1
                        WHERE id = $2
                    """, now, agent['id'])
                else:
                    await conn.execute("""
                        UPDATE agents 
                        SET executions_total = executions_total + 1,
                            executions_failed = executions_failed + 1,
                            last_execution = $1,
                            updated_at = $1
                        WHERE id = $2
                    """, now, agent['id'])
            
            # Перезагружаем агентов
            await agent_scheduler.reload_all_agents(agents, execute_and_update)
            
            registered = agent_scheduler.get_registered_agents()
            
            return {
                "success": True,
                "message": f"Loaded {len(registered)} agents into scheduler",
                "registered_agents": registered
            }
        finally:
            await conn.close()
    
    except Exception as e:
        logger.error(f"❌ Error reloading scheduler: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to reload scheduler: {str(e)}")


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
