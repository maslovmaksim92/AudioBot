"""
API роутер для dashboard мониторинга агентов
"""
from fastapi import APIRouter, HTTPException
from typing import List
from datetime import datetime, timezone, timedelta
import logging
import json

from backend.app.models.agent_execution_log import AgentExecutionLog, AgentExecutionStats

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/agents/dashboard", tags=["Agent Dashboard"])

@router.get("/execution-logs", response_model=List[AgentExecutionLog])
async def get_execution_logs(
    agent_id: str = None,
    limit: int = 50,
    skip: int = 0
):
    """
    Получить логи выполнения агентов
    """
    try:
        import asyncpg
        import os
        
        db_url = os.environ.get('DATABASE_URL', '').replace('postgresql+asyncpg://', 'postgresql://')
        conn = await asyncpg.connect(db_url)
        
        try:
            query = """
                SELECT * FROM agent_execution_logs
                WHERE 1=1
            """
            params = []
            
            if agent_id:
                query += " AND agent_id = $1"
                params.append(agent_id)
            
            query += " ORDER BY executed_at DESC LIMIT $%d OFFSET $%d" % (len(params) + 1, len(params) + 2)
            params.extend([limit, skip])
            
            rows = await conn.fetch(query, *params)
            
            logs = []
            for row in rows:
                results = row['results']
                if isinstance(results, str):
                    results = json.loads(results)
                
                logs.append(AgentExecutionLog(
                    id=row['id'],
                    agent_id=row['agent_id'],
                    agent_name=row['agent_name'],
                    executed_at=row['executed_at'].isoformat() if row['executed_at'] else None,
                    success=row['success'],
                    skipped=row['skipped'] if row.get('skipped') is not None else False,
                    skip_reason=row.get('skip_reason'),
                    actions_executed=row['actions_executed'],
                    results=results or [],
                    error=row.get('error'),
                    duration_ms=row.get('duration_ms')
                ))
            
            return logs
        finally:
            await conn.close()
    
    except Exception as e:
        logger.error(f"❌ Error fetching execution logs: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/stats", response_model=AgentExecutionStats)
async def get_execution_stats(agent_id: str = None):
    """
    Получить статистику выполнения агентов
    """
    try:
        import asyncpg
        import os
        
        db_url = os.environ.get('DATABASE_URL', '').replace('postgresql+asyncpg://', 'postgresql://')
        conn = await asyncpg.connect(db_url)
        
        try:
            where_clause = ""
            params = []
            
            if agent_id:
                where_clause = "WHERE agent_id = $1"
                params.append(agent_id)
            
            # Общая статистика
            stats_row = await conn.fetchrow(f"""
                SELECT 
                    COUNT(*) as total,
                    SUM(CASE WHEN success = true AND skipped = false THEN 1 ELSE 0 END) as successful,
                    SUM(CASE WHEN success = false THEN 1 ELSE 0 END) as failed,
                    SUM(CASE WHEN skipped = true THEN 1 ELSE 0 END) as skipped,
                    AVG(duration_ms) as avg_duration
                FROM agent_execution_logs
                {where_clause}
            """, *params)
            
            # Выполнения за последние 24 часа
            last_24h_params = params + [datetime.now(timezone.utc) - timedelta(hours=24)]
            last_24h = await conn.fetchval(f"""
                SELECT COUNT(*)
                FROM agent_execution_logs
                {where_clause}
                {"AND" if where_clause else "WHERE"} executed_at >= ${len(params) + 1}
            """, *last_24h_params)
            
            total = stats_row['total'] or 0
            successful = stats_row['successful'] or 0
            failed = stats_row['failed'] or 0
            skipped = stats_row['skipped'] or 0
            
            success_rate = (successful / total * 100) if total > 0 else 0
            
            return AgentExecutionStats(
                total_executions=total,
                successful_executions=successful,
                failed_executions=failed,
                skipped_executions=skipped,
                success_rate=round(success_rate, 2),
                avg_duration_ms=round(stats_row['avg_duration'] or 0, 2),
                last_24h_executions=last_24h or 0
            )
        finally:
            await conn.close()
    
    except Exception as e:
        logger.error(f"❌ Error fetching execution stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/init-logs-table")
async def initialize_logs_table():
    """
    Инициализировать таблицу логов выполнения
    """
    try:
        import asyncpg
        import os
        
        db_url = os.environ.get('DATABASE_URL', '').replace('postgresql+asyncpg://', 'postgresql://')
        conn = await asyncpg.connect(db_url)
        
        try:
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS agent_execution_logs (
                    id VARCHAR(36) PRIMARY KEY,
                    agent_id VARCHAR(36) NOT NULL,
                    agent_name VARCHAR(200),
                    executed_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                    success BOOLEAN DEFAULT false,
                    skipped BOOLEAN DEFAULT false,
                    skip_reason TEXT,
                    actions_executed INTEGER DEFAULT 0,
                    results JSONB DEFAULT '[]'::jsonb,
                    error TEXT,
                    duration_ms INTEGER
                )
            """)
            
            await conn.execute("CREATE INDEX IF NOT EXISTS idx_agent_logs_agent_id ON agent_execution_logs(agent_id)")
            await conn.execute("CREATE INDEX IF NOT EXISTS idx_agent_logs_executed_at ON agent_execution_logs(executed_at)")
            
            logger.info("✅ Agent execution logs table created successfully")
            
            return {"success": True, "message": "Logs table created successfully"}
        finally:
            await conn.close()
    
    except Exception as e:
        logger.error(f"❌ Error creating logs table: {e}")
        raise HTTPException(status_code=500, detail=str(e))
