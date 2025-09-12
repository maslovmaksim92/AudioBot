import logging
from datetime import datetime
from typing import List, Optional
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from ..services.bitrix_service import BitrixService
from ..config.settings import BITRIX24_WEBHOOK_URL

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api", tags=["tasks"])

class CreateTaskRequest(BaseModel):
    title: str = Field(..., min_length=1, max_length=200, description="Название задачи")
    description: str = Field(default="", max_length=2000, description="Описание задачи")
    responsible_id: int = Field(default=1, description="ID ответственного")
    priority: int = Field(default=1, ge=0, le=2, description="Приоритет: 0-низкий, 1-обычный, 2-высокий")
    deadline: Optional[str] = Field(default=None, description="Дедлайн в формате YYYY-MM-DD")
    group_id: Optional[int] = Field(default=None, description="ID группы/проекта")

class TaskResponse(BaseModel):
    id: str
    title: str
    description: str
    status: str
    status_text: str
    priority: str
    priority_text: str
    deadline: Optional[str]
    created_date: str
    creator_name: str
    responsible_name: str
    bitrix_url: Optional[str] = None

@router.get("/tasks", response_model=dict)
async def get_tasks(
    limit: Optional[int] = None,
    status: Optional[str] = None,
    priority: Optional[str] = None,
    responsible_id: Optional[str] = None
):
    """Получить список задач из Bitrix24 с фильтрами"""
    try:
        logger.info(f"📋 Loading tasks with filters: status={status}, priority={priority}, responsible={responsible_id}")
        
        bitrix = BitrixService(BITRIX24_WEBHOOK_URL)
        tasks = await bitrix.get_tasks(limit=limit or 50)
        
        filtered_tasks = []
        for task in tasks:
            # Применяем фильтры
            if status and str(task.get('status', '')) != status:
                continue
            if priority and str(task.get('priority', '')) != priority:
                continue  
            if responsible_id and str(task.get('responsibleId', '')) != responsible_id:
                continue
            
            # Формируем URL задачи в Bitrix24
            task_id = task.get('id')
            bitrix_url = f"https://vas-dom.bitrix24.ru/workgroups/group/0/tasks/task/view/{task_id}/" if task_id else None
            
            task_data = {
                'id': task.get('id', ''),
                'title': task.get('title', ''),
                'description': task.get('description', ''),
                'status': task.get('status', '1'),
                'status_text': task.get('status_text', 'Новая'),
                'priority': task.get('priority', '1'),
                'priority_text': task.get('priority_text', 'Обычный'),
                'deadline': task.get('deadline'),
                'created_date': task.get('createdDate', ''),
                'creator_name': task.get('creator_name', 'Неизвестен'),
                'responsible_name': task.get('responsible_name', 'Не назначен'),
                'bitrix_url': bitrix_url
            }
            
            filtered_tasks.append(task_data)
        
        logger.info(f"✅ Tasks loaded: {len(filtered_tasks)} tasks")
        
        return {
            "status": "success",
            "tasks": filtered_tasks,
            "total": len(filtered_tasks),
            "filters": {
                "status": status,
                "priority": priority,
                "responsible_id": responsible_id,
                "limit": limit
            },
            "source": "🔥 Bitrix24 Tasks API",
            "sync_timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"❌ Tasks error: {e}")
        return {"status": "error", "message": str(e)}

@router.post("/tasks", response_model=dict)
async def create_task(task_data: CreateTaskRequest):
    """Создать новую задачу в Bitrix24"""
    try:
        logger.info(f"📝 Creating new task: {task_data.title}")
        
        if not BITRIX24_WEBHOOK_URL:
            raise HTTPException(
                status_code=500,
                detail="Bitrix24 webhook URL не настроен"
            )
        
        bitrix = BitrixService(BITRIX24_WEBHOOK_URL)
        
        # Создаем задачу в Bitrix24
        result = await bitrix.create_task_enhanced(
            title=task_data.title,
            description=task_data.description,
            responsible_id=task_data.responsible_id,
            priority=task_data.priority,
            deadline=task_data.deadline,
            group_id=task_data.group_id
        )
        
        if result.get('status') == 'success':
            logger.info(f"✅ Task created successfully: {result['task_id']}")
            return {
                "status": "success",
                "message": "Задача успешно создана в Bitrix24",
                "task_id": result['task_id'],
                "title": result['title'],
                "bitrix_url": result.get('bitrix_url'),
                "created_at": datetime.utcnow().isoformat()
            }
        else:
            logger.error(f"❌ Failed to create task: {result.get('message')}")
            raise HTTPException(
                status_code=400,
                detail=f"Ошибка создания задачи: {result.get('message')}"
            )
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Create task endpoint error: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Внутренняя ошибка сервера: {str(e)}"
        )

@router.get("/tasks/users")
async def get_available_users():
    """Получить список пользователей для назначения задач"""
    try:
        bitrix = BitrixService(BITRIX24_WEBHOOK_URL)
        users = await bitrix.get_users()
        
        # Форматируем пользователей для селекта
        formatted_users = []
        for user in users:
            if user.get('ACTIVE') is True:  # Только активные (boolean True, не строка 'Y')
                formatted_users.append({
                    'id': user.get('ID'),
                    'name': f"{user.get('NAME', '')} {user.get('LAST_NAME', '')}".strip(),
                    'email': user.get('EMAIL', ''),
                    'position': user.get('WORK_POSITION', '')
                })
        
        return {
            "status": "success", 
            "users": formatted_users,
            "total": len(formatted_users)
        }
        
    except Exception as e:
        logger.error(f"❌ Get users error: {e}")
        return {"status": "error", "message": str(e)}

@router.get("/tasks/stats")
async def get_tasks_statistics():
    """Получить статистику по задачам"""
    try:
        bitrix = BitrixService(BITRIX24_WEBHOOK_URL)
        tasks = await bitrix.get_tasks()
        
        # Подсчитываем статистику
        stats = {
            "total_tasks": len(tasks),
            "by_status": {},
            "by_priority": {},
            "overdue_tasks": 0,
            "today_deadline": 0
        }
        
        from datetime import date
        today = date.today().isoformat()
        
        for task in tasks:
            # Статистика по статусам
            status = task.get('status_text', 'Неизвестно')
            stats["by_status"][status] = stats["by_status"].get(status, 0) + 1
            
            # Статистика по приоритетам
            priority = task.get('priority_text', 'Обычный')
            stats["by_priority"][priority] = stats["by_priority"].get(priority, 0) + 1
            
            # Проверяем дедлайны
            deadline = task.get('deadline')
            if deadline:
                if deadline < today:
                    stats["overdue_tasks"] += 1
                elif deadline == today:
                    stats["today_deadline"] += 1
        
        return {
            "status": "success",
            "stats": stats,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"❌ Tasks stats error: {e}")
        return {"status": "error", "message": str(e)}