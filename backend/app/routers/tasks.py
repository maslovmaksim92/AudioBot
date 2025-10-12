"""
API роутер для задач - полный CRUD с интеграцией Bitrix24 и AI
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_
from typing import List, Optional
from datetime import datetime, timezone
import logging
from uuid import uuid4

from backend.app.config.database import get_db
from backend.app.models.task import Task, TaskStatus, TaskPriority
from backend.app.schemas.task import TaskCreate, TaskUpdate, TaskResponse
from backend.app.utils.auth_deps import get_current_user
from backend.app.models.user import User

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/tasks", tags=["Tasks"])

# ============= CRUD Operations =============

@router.post("/", response_model=TaskResponse)
async def create_task(
    task: TaskCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Создать новую задачу
    """
    try:
        new_task = Task(
            id=str(uuid4()),
            title=task.title,
            description=task.description,
            status=task.status,
            priority=task.priority,
            assigned_to_id=task.assigned_to_id,
            created_by_id=current_user.id,
            house_id=task.house_id,
            due_date=task.due_date,
            checklist=task.checklist,
            mindmap=task.mindmap,
            ai_proposed=task.ai_proposed,
            ai_reasoning=task.ai_reasoning
        )
        
        db.add(new_task)
        await db.commit()
        await db.refresh(new_task)
        
        logger.info(f"Task created: {new_task.id} by user {current_user.id}")
        return new_task
        
    except Exception as e:
        await db.rollback()
        logger.error(f"Error creating task: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to create task: {str(e)}")

@router.get("/", response_model=List[TaskResponse])
async def get_tasks(
    status: Optional[TaskStatus] = None,
    priority: Optional[TaskPriority] = None,
    assigned_to_id: Optional[str] = None,
    house_id: Optional[str] = None,
    ai_proposed: Optional[bool] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    db: AsyncSession = Depends(get_db)
):
    """
    Получить список задач с фильтрами
    """
    try:
        query = select(Task)
        
        # Применяем фильтры
        filters = []
        if status:
            filters.append(Task.status == status)
        if priority:
            filters.append(Task.priority == priority)
        if assigned_to_id:
            filters.append(Task.assigned_to_id == assigned_to_id)
        if house_id:
            filters.append(Task.house_id == house_id)
        if ai_proposed is not None:
            filters.append(Task.ai_proposed == ai_proposed)
        
        if filters:
            query = query.where(and_(*filters))
        
        query = query.offset(skip).limit(limit).order_by(Task.created_at.desc())
        
        result = await db.execute(query)
        tasks = result.scalars().all()
        
        return tasks
        
    except Exception as e:
        logger.error(f"Error fetching tasks: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch tasks: {str(e)}")

@router.get("/{task_id}", response_model=TaskResponse)
async def get_task(
    task_id: str,
    db: AsyncSession = Depends(get_db)
):
    """
    Получить задачу по ID
    """
    try:
        result = await db.execute(select(Task).where(Task.id == task_id))
        task = result.scalar_one_or_none()
        
        if not task:
            raise HTTPException(status_code=404, detail="Task not found")
        
        return task
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching task {task_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch task: {str(e)}")

@router.put("/{task_id}", response_model=TaskResponse)
async def update_task(
    task_id: str,
    task_update: TaskUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Обновить задачу
    """
    try:
        result = await db.execute(select(Task).where(Task.id == task_id))
        task = result.scalar_one_or_none()
        
        if not task:
            raise HTTPException(status_code=404, detail="Task not found")
        
        # Обновляем поля
        update_data = task_update.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(task, field, value)
        
        # Если статус меняется на DONE, устанавливаем completed_at
        if task_update.status == TaskStatus.DONE and not task.completed_at:
            task.completed_at = datetime.now(timezone.utc)
        
        task.updated_at = datetime.now(timezone.utc)
        
        await db.commit()
        await db.refresh(task)
        
        logger.info(f"Task updated: {task_id} by user {current_user.id}")
        return task
        
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        logger.error(f"Error updating task {task_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to update task: {str(e)}")

@router.delete("/{task_id}")
async def delete_task(
    task_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Удалить задачу
    """
    try:
        result = await db.execute(select(Task).where(Task.id == task_id))
        task = result.scalar_one_or_none()
        
        if not task:
            raise HTTPException(status_code=404, detail="Task not found")
        
        await db.delete(task)
        await db.commit()
        
        logger.info(f"Task deleted: {task_id} by user {current_user.id}")
        return {"success": True, "message": "Task deleted successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        logger.error(f"Error deleting task {task_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to delete task: {str(e)}")

# ============= Bitrix24 Integration =============

# ============= Checklist Operations =============

@router.put("/{task_id}/checklist")
async def update_checklist(
    task_id: str,
    checklist: List[dict],
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Обновить чеклист задачи
    Формат: [{"id": "1", "text": "...", "done": false}, ...]
    """
    try:
        result = await db.execute(select(Task).where(Task.id == task_id))
        task = result.scalar_one_or_none()
        
        if not task:
            raise HTTPException(status_code=404, detail="Task not found")
        
        task.checklist = checklist
        task.updated_at = datetime.now(timezone.utc)
        
        await db.commit()
        await db.refresh(task)
        
        logger.info(f"Checklist updated for task {task_id} by user {current_user.id}")
        return {"success": True, "checklist": task.checklist}
        
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        logger.error(f"Error updating checklist for task {task_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to update checklist: {str(e)}")

# ============= Mind-Map Operations =============

@router.put("/{task_id}/mindmap")
async def update_mindmap(
    task_id: str,
    mindmap: dict,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Обновить mind-map задачи
    Формат: {"nodes": [...], "edges": [...]}
    """
    try:
        result = await db.execute(select(Task).where(Task.id == task_id))
        task = result.scalar_one_or_none()
        
        if not task:
            raise HTTPException(status_code=404, detail="Task not found")
        
        task.mindmap = mindmap
        task.updated_at = datetime.now(timezone.utc)
        
        await db.commit()
        await db.refresh(task)
        
        logger.info(f"Mind-map updated for task {task_id} by user {current_user.id}")
        return {"success": True, "mindmap": task.mindmap}
        
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        logger.error(f"Error updating mindmap for task {task_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to update mindmap: {str(e)}")

# ============= AI Task Generation =============

@router.post("/ai/generate")
async def generate_ai_tasks(
    context: dict,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Генерация задач с помощью AI на основе контекста
    context: {"house_id": "...", "description": "...", "count": 3}
    """
    try:
        from openai import AsyncOpenAI
        import os
        
        openai_key = os.getenv('OPENAI_API_KEY')
        if not openai_key:
            raise HTTPException(status_code=500, detail="OpenAI API key not configured")
        
        client = AsyncOpenAI(api_key=openai_key)
        
        # Формируем промпт для AI
        prompt = f"""Ты - помощник по управлению клининговой компанией VasDom.
На основе следующего контекста создай {context.get('count', 3)} конкретных задачи:

Контекст:
{context.get('description', 'Общие задачи по управлению')}

Для каждой задачи предоставь:
1. Название (краткое, до 50 символов)
2. Описание (детальное, что нужно сделать)
3. Приоритет (low/medium/high/urgent)
4. Обоснование (почему эта задача важна)

Формат ответа - JSON массив:
[
  {{
    "title": "...",
    "description": "...",
    "priority": "medium",
    "reasoning": "..."
  }}
]

Задачи должны быть практичными и выполнимыми."""

        response = await client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "Ты - эксперт по управлению клининговой компанией. Генерируешь только JSON."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            response_format={"type": "json_object"}
        )
        
        import json
        ai_response = json.loads(response.choices[0].message.content)
        
        # Создаём задачи в БД
        created_tasks = []
        for task_data in ai_response.get('tasks', []):
            new_task = Task(
                id=str(uuid4()),
                title=task_data['title'],
                description=task_data['description'],
                status=TaskStatus.TODO,
                priority=TaskPriority[task_data['priority'].upper()],
                created_by_id=current_user.id,
                house_id=context.get('house_id'),
                ai_proposed=True,
                ai_reasoning=task_data.get('reasoning')
            )
            db.add(new_task)
            created_tasks.append(new_task)
        
        await db.commit()
        
        for task in created_tasks:
            await db.refresh(task)
        
        logger.info(f"AI generated {len(created_tasks)} tasks for user {current_user.id}")
        return {
            "success": True,
            "tasks": created_tasks,
            "count": len(created_tasks)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        logger.error(f"Error generating AI tasks: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to generate AI tasks: {str(e)}")



@router.get("/bitrix/list")
async def get_bitrix_tasks():
    """
    Получение списка задач из Bitrix24
    Mock данные для dev среды
    """
    try:
        # Mock данные задач
        mock_tasks = [
            {
                "id": "1",
                "title": "Подписать акт Кубяка 5",
                "description": "Связаться со старшим дома для подписания акта",
                "status": "pending",
                "priority": "high",
                "assignee": "Алексей",
                "deadline": "2025-01-07",
                "created_at": "2025-01-06T10:00:00"
            },
            {
                "id": "2",
                "title": "Подготовить КП для УК Комфорт",
                "description": "3 новых дома на обслуживание",
                "status": "in_progress",
                "priority": "medium",
                "assignee": "Наталья",
                "deadline": "2025-01-08",
                "created_at": "2025-01-06T11:30:00"
            },
            {
                "id": "3",
                "title": "Уборка Билибина 6 - подъезд №2",
                "description": "Особое внимание на подъезд №2 по рекламации",
                "status": "completed",
                "priority": "high",
                "assignee": "Бригада 3",
                "deadline": "2025-01-06",
                "created_at": "2025-01-05T08:25:00"
            }
        ]
        
        return {
            "success": True,
            "tasks": mock_tasks,
            "total": len(mock_tasks)
        }
    except Exception as e:
        logger.error(f"Error getting Bitrix tasks: {e}")
        return {
            "success": False,
            "tasks": [],
            "total": 0,
            "error": str(e)
        }