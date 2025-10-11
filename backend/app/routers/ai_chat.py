"""
API роутер для AI чата
Обработка сообщений, история, AI задачи
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, func
from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime
import json
import uuid
import logging

from backend.app.config.database import get_db
from backend.app.models.chat_history import ChatHistory
from backend.app.models.ai_task import AITask, AITaskStatus, AITaskType
from backend.app.models.house import House
from backend.app.services.openai_service import VasDomAIAgent
from backend.app.services.bitrix24_service import Bitrix24Service

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/ai", tags=["AI Chat"])

# Инициализация сервисов
ai_agent = VasDomAIAgent()
bitrix_service = Bitrix24Service()

# Pydantic модели

class ChatMessage(BaseModel):
    """Сообщение в чате"""
    role: str  # 'user' или 'assistant'
    content: str

class ChatRequest(BaseModel):
    """Запрос на отправку сообщения"""
    message: str
    user_id: str
    debug: bool = False

class ChatResponse(BaseModel):
    """Ответ от AI"""
    message: str
    function_calls: List[dict] = []
    created_at: str
    debug: Optional[dict] = None
    sources: Optional[dict] = None
    rule: Optional[str] = None

class ChatHistoryResponse(BaseModel):
    """История сообщений"""
    messages: List[dict]
    total: int

class AITaskResponse(BaseModel):
    """AI задача"""
    id: str
    task_type: str
    status: str
    title: str
    description: Optional[str]
    scheduled_at: Optional[str]
    completed_at: Optional[str]
    created_at: str

# Утилиты адреса
import re

def _extract_address_candidate(text: str) -> Optional[str]:
    try:
        s = (text or '').lower()
        s = s.replace('\n', ' ').strip()
        # шаблоны: "на <адрес> в ", "на <адрес>?", "по адресу <адрес>"
        m = re.search(r"на\s+(.+?)(?:\s+в\s|\s+за\s|\?|!|\.|$)", s)
        if not m:
            m = re.search(r"по\s+адресу\s+(.+?)(?:\s+в\s|\s+за\s|\?|!|\.|$)", s)
        if m:
            cand = m.group(1).strip(' ,.!?')
            # Ограничим до 6 слов чтобы не захватить весь вопрос
            parts = [p for p in cand.split() if p]
            if len(parts) > 6:
                parts = parts[:6]
            return ' '.join(parts)
        # fallback: если содержит цифру (номер дома), возьмём окно из 3 слов вокруг
        tokens = [t for t in re.split(r"[^\wа-яё]+", s) if t]
        for i, t in enumerate(tokens):
            if re.match(r"^\d+[а-яa-z]*$", t):
                left = tokens[max(0, i-2):i]
                right = tokens[i+1:i+2]
                cand = ' '.join(left + [t] + right)
                if len(cand) >= 3:
                    return cand
        return None
        # Улучшение извлечения: если нашли номер дома, соберём адрес как <улица> <номер> без служебных слов
        stop = {"контакт","контакты","старшего","старший","телефон","почта","email","номер","по","адресу","на"}
        for i, t in enumerate(tokens):
            if re.match(r"^\d+[а-яa-z]*$", t):
                # ищем слева ближайшее слово, не являющееся стоп-словом
                street = None
                for j in range(i-1, max(-1, i-4), -1):
                    if j >= 0 and tokens[j] not in stop and tokens[j].strip():
                        street = tokens[j]
                        break
                if street:
                    return f"{street} {t}".strip()
                # если улицу не нашли — fallback прежний
                left = tokens[max(0, i-2):i]
                left = [w for w in left if w not in stop]
                right = [tokens[i+1]] if i+1 < len(tokens) else []
                cand = ' '.join(left + [t] + right)
                if len(cand) >= 3:
                    return cand

    except Exception:
        return None

# Обработчики функций для AI

async def handle_get_houses_for_date(date: str, brigade_number: Optional[str] = None, user_id: str = None, db: AsyncSession = None) -> dict:
    """Получить дома на определенную дату"""
    try:
        # Парсим дату
        target_date = datetime.strptime(date, "%Y-%m-%d").date()
        date_str = target_date.strftime("%Y-%m-%d")
        
        # Базовый запрос (все дома)
        query = select(House)
        
        if brigade_number:
            query = query.where(House.brigade_number == brigade_number)
        
        result = await db.execute(query)
        houses = result.scalars().all()
        
        # Фильтруем дома, у которых есть уборка на эту дату
        houses_for_date = []
        for house in houses:
            if house.cleaning_schedule:
                cleaning_schedule_dict = house.cleaning_schedule if isinstance(house.cleaning_schedule, dict) else {}
                
                # Извлекаем месяц для поиска (например, "november_2025")
                month_key = target_date.strftime("%B_%Y").lower()  # "november_2025"
                
                # Проверяем есть ли график на этот месяц
                if month_key in cleaning_schedule_dict:
                    month_schedule = cleaning_schedule_dict[month_key]
                    if isinstance(month_schedule, list):
                        # Ищем дату в массиве
                        for item in month_schedule:
                            if isinstance(item, dict) and item.get('date') == date_str:
                                houses_for_date.append({
                                    "id": house.bitrix_id,
                                    "address": house.address,
                                    "brigade_number": house.brigade_number,
                                    "brigade_name": house.assigned_by_name or f"Бригада {house.brigade_number}",
                                    "entrances": house.entrances_count or 0,
                                    "floors": house.floors_count or 0,
                                    "cleaning_type": item.get('type', 'standard')
                                })
                                break
        
        return {
            "date": date_str,
            "total_houses": len(houses_for_date),
            "houses": houses_for_date[:50]  # Ограничиваем до 50 для читаемости
        }
        
    except Exception as e:
        logger.error(f"Ошибка get_houses_for_date: {e}")
        return {"error": str(e)}

async def handle_get_brigade_workload(brigade_number: str, date: Optional[str] = None, user_id: str = None, db: AsyncSession = None) -> dict:
    """Получить загрузку бригады"""
    try:
        target_date = datetime.strptime(date, "%Y-%m-%d").date() if date else datetime.now().date()
        date_str = target_date.strftime("%Y-%m-%d")
        
        # Получаем все дома бригады
        result = await db.execute(
            select(House).where(House.brigade_number == brigade_number)
        )
        houses = result.scalars().all()
        
        # Подсчитываем загрузку
        total_houses = len(houses)
        houses_today = 0
        total_entrances = 0
        total_floors = 0
        
        month_key = target_date.strftime("%B_%Y").lower()  # "november_2025"
        
        for house in houses:
            if house.cleaning_schedule:
                cleaning_schedule_dict = house.cleaning_schedule if isinstance(house.cleaning_schedule, dict) else {}
                
                # Проверяем график на указанный месяц
                if month_key in cleaning_schedule_dict:
                    month_schedule = cleaning_schedule_dict[month_key]
                    if isinstance(month_schedule, list):
                        for item in month_schedule:
                            if isinstance(item, dict) and item.get('date') == date_str:
                                houses_today += 1
                                total_entrances += house.entrances_count or 0
                                total_floors += house.floors_count or 0
                                break
        
        return {
            "brigade_number": brigade_number,
            "date": date_str,
            "total_houses_assigned": total_houses,
            "houses_today": houses_today,
            "total_entrances_today": total_entrances,
            "total_floors_today": total_floors,
            "status": "Высокая загрузка" if houses_today > 10 else "Нормальная загрузка" if houses_today > 5 else "Низкая загрузка"
        }
        
    except Exception as e:
        logger.error(f"Ошибка get_brigade_workload: {e}")
        return {"error": str(e)}

async def handle_get_house_details(house_id: str, user_id: str = None, db: AsyncSession = None) -> dict:
    """Получить детали дома"""
    try:
        # Сначала ищем в локальной БД
        result = await db.execute(
            select(House).where(House.bitrix_id == house_id)
        )
        house = result.scalar_one_or_none()
        
        if house:
            return {
                "id": house.bitrix_id,
                "address": house.address,
                "company_title": house.company_title,
                "brigade_number": house.brigade_number,
                "brigade_name": house.brigade_name,
                "apartments": house.apartments_count,
                "entrances": house.entrances_count,
                "floors": house.floors_count,
                "cleaning_dates": house.cleaning_dates
            }
        else:
            # Если не найден локально, пытаемся получить из Bitrix24
            details = await bitrix_service.get_deal_details(house_id)
            return details if details else {"error": "Дом не найден"}
            
    except Exception as e:
        logger.error(f"Ошибка get_house_details: {e}")
        return {"error": str(e)}

async def handle_create_ai_task(
    task_type: str,
    title: str,
    description: Optional[str] = None,
    scheduled_at: Optional[str] = None,
    user_id: str = None,
    db: AsyncSession = None
) -> dict:
    """Создать AI задачу"""
    try:
        # Парсим дату если указана
        scheduled_datetime = None
        if scheduled_at:
            try:
                scheduled_datetime = datetime.fromisoformat(scheduled_at.replace('Z', '+00:00'))
            except Exception:
                scheduled_datetime = None
        
        # Создаем задачу
        new_task = AITask(
            id=str(uuid.uuid4()),
            created_by=user_id,
            task_type=AITaskType(task_type),
            status=AITaskStatus.PENDING,
            title=title,
            description=description,
            scheduled_at=scheduled_datetime
        )
        
        db.add(new_task)
        await db.commit()
        await db.refresh(new_task)
        
        logger.info(f"AI создал задачу: {title} для пользователя {user_id}")
        
        return {
            "success": True,
            "task_id": new_task.id,
            "message": f"Задача '{title}' успешно создана"
        }
        
    except Exception as e:
        logger.error(f"Ошибка create_ai_task: {e}")
        return {"error": str(e)}

async def handle_send_schedule_email(
    email: str,
    date_from: str,
    date_to: str,
    company_title: Optional[str] = None,
    user_id: str = None,
    db: AsyncSession = None
) -> dict:
    """Отправить график на email (заглушка - реализация позже)"""
    try:
        # TODO: Реализовать отправку email с графиком
        # Пока просто создаем задачу на отправку
        
        task_title = f"Отправить график {company_title or 'управляющей компании'} на {email}"
        task_description = f"Период: {date_from} - {date_to}"
        
        new_task = AITask(
            id=str(uuid.uuid4()),
            created_by=user_id,
            task_type=AITaskType.SEND_SCHEDULE,
            status=AITaskStatus.PENDING,
            title=task_title,
            description=task_description,
            related_data=json.dumps({
                "email": email,
                "date_from": date_from,
                "date_to": date_to,
                "company_title": company_title
            })
        )
        
        db.add(new_task)
        await db.commit()
        
        return {
            "success": True,
            "message": f"Задача на отправку графика создана. Email: {email}"
        }
        
    except Exception as e:
        logger.error(f"Ошибка send_schedule_email: {e}")
        return {"error": str(e)}

# API Endpoints

@router.post("/chat", response_model=ChatResponse)
async def send_message(
    request: ChatRequest,
    db: AsyncSession = Depends(get_db)
):
    """Отправить сообщение AI агенту"""
    try:
        # Try unified Single Brain fast answers first
        try:
            from backend.app.services.brain_router import try_fast_answer
            ans = await try_fast_answer(request.message, db=db, return_debug=bool(request.debug))
            if ans and ans.get('success'):
                reply = ans.get('answer') or ans.get('response') or ''
                
                # Сохраняем сообщение
                assistant_message = ChatHistory(
                    id=str(uuid.uuid4()),
                    user_id=request.user_id,
                    role="assistant",
                    content=reply,
                )
                db.add(assistant_message)
                await db.commit()
                
                # Возвращаем ответ с debug информацией (если запрошена)
                response_data = {
                    "message": reply,
                    "function_calls": [],
                    "created_at": datetime.utcnow().isoformat()
                }
                
                if request.debug and isinstance(ans, dict):
                    response_data["debug"] = ans.get('debug')
                    response_data["sources"] = ans.get('sources')
                    response_data["rule"] = ans.get('rule')
                
                return response_data
            
            # Обработка no_match с подсказками
            elif ans and not ans.get('success'):
                error_type = ans.get('error', 'unknown')
                hints_map = {
                    'no_address': 'Пожалуйста, укажите адрес в запросе. Например: "Контакты старшего Кибальчича 3"',
                    'no_month': 'Укажите месяц (октябрь, ноябрь или декабрь). Например: "График уборки Кибальчича 3 октябрь"',
                    'elder_not_found': 'Контакты старшего не найдены для этого адреса. Проверьте правильность адреса.',
                    'house_not_found': 'Дом по указанному адресу не найден в базе. Попробуйте уточнить адрес.',
                    'cleaning_not_found': 'График уборок не найден для этого дома.',
                    'no_tasks': 'Задачи не найдены. Попробуйте указать другие критерии поиска.',
                    'no_transactions': 'Финансовые транзакции не найдены за указанный период.',
                    'address_required': 'Для этого запроса необходимо указать адрес.',
                    'brigade_not_specified': 'Укажите номер или название бригады.'
                }
                
                error_message = hints_map.get(error_type, 'Не удалось обработать запрос.')
                
                if ans.get('hints'):
                    error_message += '\n\nПодсказки:\n' + '\n'.join(f"• {h}" for h in ans['hints'])
                
                # Сохраняем сообщение об ошибке
                assistant_message = ChatHistory(
                    id=str(uuid.uuid4()),
                    user_id=request.user_id,
                    role="assistant",
                    content=error_message,
                )
                db.add(assistant_message)
                await db.commit()
                
                response_data = {
                    "message": error_message,
                    "function_calls": [],
                    "created_at": datetime.utcnow().isoformat()
                }
                
                if request.debug:
                    response_data["debug"] = ans.get('debug')
                
                return response_data
        except Exception as e:
            logger.warning(f"Brain router failed in ai_chat: {e}")
            # Rollback on error
            await db.rollback()

        # Получаем историю последних 10 сообщений для контекста
        result = await db.execute(
            select(ChatHistory)
            .where(ChatHistory.user_id == request.user_id)
            .order_by(ChatHistory.created_at.desc())
            .limit(10)
        )

        # Ветка: запрос контактов старшего по адресу
        try:
            want_contacts = False
            text_l = (request.message or '').lower()
            if ('контакт' in text_l or 'телефон' in text_l or 'почта' in text_l or 'email' in text_l) and ('старш' in text_l):
                want_contacts = True
            addr = _extract_address_candidate(request.message)
            if want_contacts and addr:
                data = await bitrix_service.list_houses(address=addr, limit=3)
                houses = (data or {}).get('houses') or []
                if houses:
                    h = houses[0]
                    deal_id = h.get('id')
                    details = await bitrix_service.get_deal_details(deal_id)
                    contact = (details or {}).get('elder_contact') or {}
                    phones = contact.get('phones') or []
                    emails = contact.get('emails') or []
                    name = contact.get('name') or 'Старший не указан'
                    fallback_company = (details or {}).get('company') or {}
                    if not phones and fallback_company.get('phones'):
                        phones = fallback_company.get('phones')
                    if not emails and fallback_company.get('emails'):
                        emails = fallback_company.get('emails')
                    if phones or emails or name != 'Старший не указан':
                        lines = [f"🏠 Адрес: {h.get('title') or h.get('address')}", f"Старший: {name}"]
                        if phones:
                            lines.append(f"Телефон(ы): {', '.join(phones)}")
                        if emails:
                            lines.append(f"Email: {', '.join(emails)}")
                        lines.append(f"Ссылка в Bitrix: {h.get('bitrix_url') or '-'}")
                        reply = "\n".join(lines)
                        assistant_message = ChatHistory(
                            id=str(uuid.uuid4()),
                            user_id=request.user_id,
                            role="assistant",
                            content=reply,
                        )
                        db.add(assistant_message)
                        await db.commit()
                        return ChatResponse(message=reply, function_calls=[], created_at=datetime.utcnow().isoformat())
        except Exception as e:
            logger.warning(f"Fast elder contact branch failed: {e}")

        # Быстрая ветка: если это вопрос про адрес — попробуем Bitrix напрямую (октябрьские даты)
        try:
            addr = _extract_address_candidate(request.message)
            if addr:
                data = await bitrix_service.list_houses(address=addr, limit=3)
                houses = (data or {}).get('houses') or []
                if houses:
                    h = houses[0]
                    cd = h.get('cleaning_dates') or {}
                    def _fmt_month(key: str) -> Optional[str]:
                        v = cd.get(key) or {}
                        ds = v.get('dates') or []
                        t = v.get('type') or ''
                        if not ds:
                            return None
                        dates_txt = ', '.join(ds)
                        return f"{key}: {dates_txt} — {t}" if t else f"{key}: {dates_txt}"
                    parts = []
                    m1 = _fmt_month('october_1')
                    m2 = _fmt_month('october_2')
                    if m1:
                        parts.append(m1)
                    if m2:
                        parts.append(m2)
                    if parts:
                        detailed = "\n".join(parts)
                        reply = (
                            f"🏠 Адрес: {h.get('title') or h.get('address')}.\n"
                            f"Периодичность: {h.get('periodicity') or 'не указана'}.\n"
                            f"Октябрь — даты уборок:\n{detailed}\n\n"
                            f"Ссылка в Bitrix: {h.get('bitrix_url') or '-'}"
                        )
                        assistant_message = ChatHistory(
                            id=str(uuid.uuid4()),
                            user_id=request.user_id,
                            role="assistant",
                            content=reply,
                        )
                        db.add(assistant_message)
                        await db.commit()
                        return ChatResponse(message=reply, function_calls=[], created_at=datetime.utcnow().isoformat())
        except Exception as e:
            logger.warning(f"Fast address branch failed: {e}")
            # Продолжаем обычный сценарий без прерывания

        history = result.scalars().all()
        
        # Формируем список сообщений (в обратном порядке)
        messages = [
            {"role": msg.role, "content": msg.content}
            for msg in reversed(history)
        ]
        
        # Добавляем новое сообщение пользователя
        messages.append({"role": "user", "content": request.message})
        
        # Сохраняем сообщение пользователя в БД
        user_message = ChatHistory(
            id=str(uuid.uuid4()),
            user_id=request.user_id,
            role="user",
            content=request.message
        )
        db.add(user_message)
        await db.commit()
        
        # Обработчики функций
        function_handlers = {
            "get_houses_for_date": lambda **kwargs: handle_get_houses_for_date(**kwargs, db=db),
            "get_brigade_workload": lambda **kwargs: handle_get_brigade_workload(**kwargs, db=db),
            "get_house_details": lambda **kwargs: handle_get_house_details(**kwargs, db=db),
            "create_ai_task": lambda **kwargs: handle_create_ai_task(**kwargs, db=db),
            "send_schedule_email": lambda **kwargs: handle_send_schedule_email(**kwargs, db=db)
        }
        
        # Получаем ответ от AI
        ai_response = await ai_agent.chat(
            messages=messages,
            user_id=request.user_id,
            function_handlers=function_handlers
        )
        
        # Сохраняем ответ AI в БД
        assistant_message = ChatHistory(
            id=str(uuid.uuid4()),
            user_id=request.user_id,
            role="assistant",
            content=ai_response["content"],
            message_metadata=json.dumps({
                "function_calls": ai_response.get("function_calls", []),
                "usage": ai_response.get("usage", {})
            })
        )
        db.add(assistant_message)
        await db.commit()
        
        return ChatResponse(
            message=ai_response["content"],
            function_calls=ai_response.get("function_calls", []),
            created_at=datetime.utcnow().isoformat()
        )
        
    except Exception as e:
        logger.error(f"Ошибка в /ai/chat: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ошибка при обработке сообщения: {str(e)}"
        )

@router.get("/history", response_model=ChatHistoryResponse)
async def get_chat_history(
    user_id: str,
    limit: int = 50,
    db: AsyncSession = Depends(get_db)
):
    """Получить историю чата пользователя"""
    try:
        # Получаем историю
        result = await db.execute(
            select(ChatHistory)
            .where(ChatHistory.user_id == user_id)
            .order_by(ChatHistory.created_at.desc())
            .limit(limit)
        )
        messages = result.scalars().all()
        
        # Подсчитываем общее количество
        count_result = await db.execute(
            select(func.count(ChatHistory.id))
            .where(ChatHistory.user_id == user_id)
        )
        total = count_result.scalar()
        
        return ChatHistoryResponse(
            messages=[
                {
                    "id": msg.id,
                    "role": msg.role,
                    "content": msg.content,
                    "created_at": msg.created_at.isoformat() if msg.created_at else None,
                    "synced_to_telegram": msg.synced_to_telegram
                }
                for msg in reversed(messages)
            ],
            total=total or 0
        )
        
    except Exception as e:
        logger.error(f"Ошибка в /ai/history: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ошибка при получении истории: {str(e)}"
        )

@router.delete("/history/{user_id}")
async def clear_chat_history(
    user_id: str,
    db: AsyncSession = Depends(get_db)
):
    """Очистить историю чата пользователя"""
    try:
        await db.execute(
            select(ChatHistory).where(ChatHistory.user_id == user_id)
        )
        
        # Удаляем все сообщения пользователя
        result = await db.execute(
            select(ChatHistory).where(ChatHistory.user_id == user_id)
        )
        messages = result.scalars().all()
        
        for msg in messages:
            await db.delete(msg)
        
        await db.commit()
        
        return {"success": True, "message": "История чата очищена"}
        
    except Exception as e:
        logger.error(f"Ошибка в DELETE /ai/history: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ошибка при очистке истории: {str(e)}"
        )

@router.get("/tasks", response_model=List[AITaskResponse])
async def get_ai_tasks(
    user_id: str,
    status: Optional[str] = None,
    limit: int = 50,
    db: AsyncSession = Depends(get_db)
):
    """Получить AI задачи пользователя"""
    try:
        query = select(AITask).where(
            (AITask.created_by == user_id) | (AITask.assigned_to == user_id)
        )
        
        if status:
            query = query.where(AITask.status == AITaskStatus(status))
        
        query = query.order_by(AITask.created_at.desc()).limit(limit)
        
        result = await db.execute(query)
        tasks = result.scalars().all()
        
        return [
            AITaskResponse(
                id=task.id,
                task_type=task.task_type.value,
                status=task.status.value,
                title=task.title,
                description=task.description,
                scheduled_at=task.scheduled_at.isoformat() if task.scheduled_at else None,
                completed_at=task.completed_at.isoformat() if task.completed_at else None,
                created_at=task.created_at.isoformat() if task.created_at else None
            )
            for task in tasks
        ]
        
    except Exception as e:
        logger.error(f"Ошибка в /ai/tasks: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ошибка при получении задач: {str(e)}"
        )