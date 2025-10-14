"""
Роутер для планёрок с транскрипцией и AI-анализом
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime, date
import logging
import os
from dotenv import load_dotenv

load_dotenv()

router = APIRouter(prefix="/plannerka", tags=["plannerka"])
logger = logging.getLogger(__name__)

# Pydantic модели
class TaskItem(BaseModel):
    title: str
    assignee: Optional[str] = None
    deadline: Optional[str] = None
    priority: Optional[str] = "medium"

class PlannerkaCreate(BaseModel):
    title: str
    transcription: str
    participants: Optional[List[str]] = []

class PlannerkaResponse(BaseModel):
    id: str
    title: str
    date: str
    transcription: str
    summary: Optional[str]
    tasks: List[dict]
    participants: List[str]
    created_at: str

@router.post("/create", response_model=PlannerkaResponse)
async def create_plannerka(data: PlannerkaCreate):
    """
    Создать новую планёрку с транскрипцией
    """
    try:
        from app.config.database import get_db_pool
        import uuid
        
        db_pool = await get_db_pool()
        if not db_pool:
            raise HTTPException(status_code=500, detail="Database connection error")
        
        meeting_id = str(uuid.uuid4())
        now = datetime.now()
        
        async with db_pool.acquire() as conn:
            await conn.execute(
                """
                INSERT INTO plannerka_meetings (
                    id, title, date, start_time, transcription, 
                    participants, created_at, updated_at
                ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
                """,
                meeting_id,
                data.title,
                now.date(),
                now,
                data.transcription,
                data.participants,
                now,
                now
            )
        
        logger.info(f"[plannerka] Created meeting {meeting_id}")
        
        return {
            "id": meeting_id,
            "title": data.title,
            "date": now.date().isoformat(),
            "transcription": data.transcription,
            "summary": None,
            "tasks": [],
            "participants": data.participants,
            "created_at": now.isoformat()
        }
        
    except Exception as e:
        logger.error(f"[plannerka] Error creating meeting: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/analyze/{meeting_id}")
async def analyze_plannerka(meeting_id: str):
    """
    Анализировать планёрку через GPT-5:
    - Генерация саммари
    - Извлечение задач (кто, что, срок)
    """
    try:
        from app.config.database import get_db_pool
        from emergentintegrations.llm.chat import LlmChat, UserMessage
        
        # Получаем транскрипцию из БД
        db_pool = await get_db_pool()
        if not db_pool:
            raise HTTPException(status_code=500, detail="Database connection error")
        
        async with db_pool.acquire() as conn:
            row = await conn.fetchrow(
                "SELECT transcription FROM plannerka_meetings WHERE id = $1",
                meeting_id
            )
            
            if not row:
                raise HTTPException(status_code=404, detail="Meeting not found")
            
            transcription = row['transcription']
        
        if not transcription or len(transcription) < 50:
            raise HTTPException(status_code=400, detail="Transcription is too short for analysis")
        
        # Инициализация OpenAI
        api_key = os.getenv('OPENAI_API_KEY')
        if not api_key:
            raise HTTPException(status_code=500, detail="OPENAI_API_KEY not configured")
        
        from openai import AsyncOpenAI
        
        client = AsyncOpenAI(api_key=api_key)
        
        # Промпт для анализа
        analysis_prompt = f"""
Проанализируй текст планёрки и предоставь:

1. КРАТКОЕ САММАРИ (2-3 абзаца):
   - Основные темы обсуждения
   - Ключевые решения
   - Важные моменты

2. СПИСОК ЗАДАЧ в формате JSON:
   - title: название задачи
   - assignee: кому поручено (если указано)
   - deadline: срок выполнения (если указан)
   - priority: приоритет (high/medium/low)

Текст планёрки:
{transcription}

Ответь СТРОГО в формате JSON:
{{
    "summary": "текст саммари",
    "tasks": [
        {{"title": "задача", "assignee": "кто", "deadline": "срок", "priority": "medium"}}
    ]
}}
"""
        
        logger.info(f"[plannerka] Analyzing meeting {meeting_id} with GPT-4o...")
        
        # Отправка запроса к OpenAI GPT-4o
        completion = await client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "Ты помощник для анализа планёрок. Создаёшь краткие саммари и извлекаешь задачи. Отвечаешь ТОЛЬКО в формате JSON."},
                {"role": "user", "content": analysis_prompt}
            ],
            temperature=0.7,
            response_format={"type": "json_object"}
        )
        
        response = completion.choices[0].message.content
        
        logger.info(f"[plannerka] GPT-5 response received")
        
        # Парсинг ответа
        import json
        
        # Извлекаем JSON из ответа (может быть обёрнут в markdown)
        response_text = response.strip()
        if response_text.startswith("```json"):
            response_text = response_text.split("```json")[1].split("```")[0].strip()
        elif response_text.startswith("```"):
            response_text = response_text.split("```")[1].split("```")[0].strip()
        
        analysis_data = json.loads(response_text)
        
        summary = analysis_data.get('summary', '')
        tasks = analysis_data.get('tasks', [])
        
        # Сохраняем результаты в БД
        async with db_pool.acquire() as conn:
            await conn.execute(
                """
                UPDATE plannerka_meetings 
                SET summary = $1, tasks = $2, updated_at = $3
                WHERE id = $4
                """,
                summary,
                json.dumps(tasks),
                datetime.now(),
                meeting_id
            )
        
        logger.info(f"[plannerka] Analysis saved: {len(tasks)} tasks extracted")
        
        return {
            "success": True,
            "summary": summary,
            "tasks": tasks,
            "tasks_count": len(tasks)
        }
        
    except json.JSONDecodeError as e:
        logger.error(f"[plannerka] Failed to parse GPT-5 response: {e}")
        raise HTTPException(status_code=500, detail="Failed to parse AI response")
    except Exception as e:
        logger.error(f"[plannerka] Error analyzing meeting: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/list")
async def list_plannerkas(limit: int = 20, offset: int = 0):
    """
    Получить список планёрок
    """
    try:
        from app.config.database import get_db_pool
        
        db_pool = await get_db_pool()
        if not db_pool:
            raise HTTPException(status_code=500, detail="Database connection error")
        
        async with db_pool.acquire() as conn:
            rows = await conn.fetch(
                """
                SELECT 
                    id, title, date, start_time, end_time,
                    transcription, summary, tasks, participants,
                    created_at
                FROM plannerka_meetings
                ORDER BY date DESC, start_time DESC
                LIMIT $1 OFFSET $2
                """,
                limit, offset
            )
            
            meetings = []
            for row in rows:
                import json
                meetings.append({
                    "id": str(row['id']),
                    "title": row['title'],
                    "date": row['date'].isoformat() if row['date'] else None,
                    "start_time": row['start_time'].isoformat() if row['start_time'] else None,
                    "end_time": row['end_time'].isoformat() if row['end_time'] else None,
                    "transcription": row['transcription'],
                    "summary": row['summary'],
                    "tasks": json.loads(row['tasks']) if row['tasks'] else [],
                    "participants": row['participants'] or [],
                    "created_at": row['created_at'].isoformat() if row['created_at'] else None
                })
            
            return {"meetings": meetings, "count": len(meetings)}
            
    except Exception as e:
        logger.error(f"[plannerka] Error listing meetings: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{meeting_id}")
async def get_plannerka(meeting_id: str):
    """
    Получить детали планёрки
    """
    try:
        from app.config.database import get_db_pool
        
        db_pool = await get_db_pool()
        if not db_pool:
            raise HTTPException(status_code=500, detail="Database connection error")
        
        async with db_pool.acquire() as conn:
            row = await conn.fetchrow(
                """
                SELECT 
                    id, title, date, start_time, end_time,
                    transcription, summary, tasks, participants,
                    created_at, updated_at
                FROM plannerka_meetings
                WHERE id = $1
                """,
                meeting_id
            )
            
            if not row:
                raise HTTPException(status_code=404, detail="Meeting not found")
            
            import json
            return {
                "id": str(row['id']),
                "title": row['title'],
                "date": row['date'].isoformat() if row['date'] else None,
                "start_time": row['start_time'].isoformat() if row['start_time'] else None,
                "end_time": row['end_time'].isoformat() if row['end_time'] else None,
                "transcription": row['transcription'],
                "summary": row['summary'],
                "tasks": json.loads(row['tasks']) if row['tasks'] else [],
                "participants": row['participants'] or [],
                "created_at": row['created_at'].isoformat() if row['created_at'] else None,
                "updated_at": row['updated_at'].isoformat() if row['updated_at'] else None
            }
            
    except Exception as e:
        logger.error(f"[plannerka] Error getting meeting: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/{meeting_id}")
async def delete_plannerka(meeting_id: str):
    """
    Удалить планёрку
    """
    try:
        from app.config.database import get_db_pool
        
        db_pool = await get_db_pool()
        if not db_pool:
            raise HTTPException(status_code=500, detail="Database connection error")
        
        async with db_pool.acquire() as conn:
            result = await conn.execute(
                "DELETE FROM plannerka_meetings WHERE id = $1",
                meeting_id
            )
            
            if result == "DELETE 0":
                raise HTTPException(status_code=404, detail="Meeting not found")
            
            return {"success": True, "message": "Meeting deleted"}
            
    except Exception as e:
        logger.error(f"[plannerka] Error deleting meeting: {e}")
        raise HTTPException(status_code=500, detail=str(e))
