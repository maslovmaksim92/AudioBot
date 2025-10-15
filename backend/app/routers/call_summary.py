"""
API роутер для саммари звонков из Новофон
Автоматическая транскрипция и создание саммари после завершения звонка
"""
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, insert
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
import logging
import httpx
import os

from backend.app.config.database import get_db

router = APIRouter(prefix="/call-summary", tags=["Call Summary"])
logger = logging.getLogger(__name__)

# Конфигурация
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_TARGET_CHAT_ID = os.getenv("TELEGRAM_TARGET_CHAT_ID", "-1002384210149")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
BITRIX24_WEBHOOK_URL = os.getenv("BITRIX24_WEBHOOK_URL")

class NovofonWebhook(BaseModel):
    """Webhook от Новофон о завершённом звонке"""
    call_id: str
    caller: str  # Номер звонящего
    called: str  # Номер куда звонили
    direction: str  # "in" или "out"
    duration: int  # Длительность в секундах
    status: str  # "answered", "busy", "noanswer"
    record_url: Optional[str] = None  # Ссылка на запись
    timestamp: Optional[str] = None

class CallSummaryResponse(BaseModel):
    call_id: str
    transcription: str
    summary: str
    key_points: List[str]
    action_items: List[str]
    sentiment: str
    created_at: datetime

@router.post("/webhook/novofon")
async def novofon_webhook(
    webhook: NovofonWebhook,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db)
):
    """
    Webhook от Новофон при завершении звонка
    Автоматически создаёт саммари и отправляет в Telegram + Bitrix24
    """
    try:
        logger.info(f"📞 Received call webhook: {webhook.call_id}, status: {webhook.status}")
        
        # Проверяем, что звонок был отвечен и есть запись
        if webhook.status != "answered" or not webhook.record_url:
            logger.info(f"⏭️ Skipping call {webhook.call_id}: status={webhook.status}, has_record={bool(webhook.record_url)}")
            return {"status": "skipped", "reason": "no_recording_or_not_answered"}
        
        # Добавляем задачу в фон для обработки
        background_tasks.add_task(
            process_call_recording,
            webhook.dict(),
            db
        )
        
        return {"status": "accepted", "call_id": webhook.call_id}
        
    except Exception as e:
        logger.error(f"❌ Error processing webhook: {e}")
        raise HTTPException(status_code=500, detail=str(e))

async def process_call_recording(webhook_data: dict, db: AsyncSession):
    """
    Фоновая задача: обработка записи звонка
    1. Скачать аудио
    2. Транскрибировать через Whisper
    3. Создать саммари через GPT
    4. Сохранить в БД
    5. Отправить в Telegram
    6. Добавить в Bitrix24
    """
    call_id = webhook_data["call_id"]
    
    try:
        logger.info(f"🎙️ Processing call recording: {call_id}")
        
        # 1. Скачать аудио запись
        audio_data = await download_call_recording(webhook_data["record_url"])
        if not audio_data:
            logger.error(f"❌ Failed to download recording for {call_id}")
            return
        
        # 2. Транскрибировать через OpenAI Whisper
        transcription = await transcribe_audio(audio_data)
        if not transcription:
            logger.error(f"❌ Failed to transcribe call {call_id}")
            return
        
        logger.info(f"✅ Transcription completed for {call_id}: {len(transcription)} chars")
        
        # 3. Создать саммари через GPT-5
        summary_data = await create_call_summary(transcription, webhook_data)
        
        # 4. Сохранить в БД
        call_summary_id = await save_to_database(
            db,
            call_id,
            webhook_data,
            transcription,
            summary_data
        )
        
        # 5. Отправить в Telegram
        await send_to_telegram(webhook_data, summary_data)
        
        # 6. Добавить в Bitrix24
        await add_to_bitrix24(webhook_data, summary_data)
        
        logger.info(f"✅ Call {call_id} processed successfully!")
        
    except Exception as e:
        logger.error(f"❌ Error processing call {call_id}: {e}")
        import traceback
        logger.error(traceback.format_exc())

async def download_call_recording(record_url: str) -> Optional[bytes]:
    """Скачать аудиозапись звонка"""
    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.get(record_url)
            
            if response.status_code == 200:
                return response.content
            else:
                logger.error(f"Failed to download recording: {response.status_code}")
                return None
                
    except Exception as e:
        logger.error(f"Error downloading recording: {e}")
        return None

async def transcribe_audio(audio_data: bytes) -> Optional[str]:
    """Транскрибировать аудио через OpenAI Whisper"""
    try:
        from openai import AsyncOpenAI
        
        client = AsyncOpenAI(api_key=OPENAI_API_KEY)
        
        # Сохраняем временно
        temp_file = "/tmp/call_recording.mp3"
        with open(temp_file, "wb") as f:
            f.write(audio_data)
        
        # Транскрибируем
        with open(temp_file, "rb") as audio_file:
            transcription = await client.audio.transcriptions.create(
                model="whisper-1",
                file=audio_file,
                language="ru"
            )
        
        return transcription.text
        
    except Exception as e:
        logger.error(f"Error transcribing audio: {e}")
        return None

async def create_call_summary(transcription: str, webhook_data: dict) -> dict:
    """Создать саммари разговора через GPT-5"""
    try:
        from openai import AsyncOpenAI
        
        client = AsyncOpenAI(api_key=OPENAI_API_KEY)
        
        direction = "входящий" if webhook_data["direction"] == "in" else "исходящий"
        
        prompt = f"""Проанализируй {direction} телефонный разговор и создай структурированное саммари.

Транскрипция разговора:
{transcription}

Создай JSON с полями:
{{
  "summary": "Краткое содержание разговора (2-3 предложения)",
  "key_points": ["Ключевой пункт 1", "Ключевой пункт 2", ...],
  "action_items": ["Задача 1", "Задача 2", ...],
  "sentiment": "positive/neutral/negative",
  "client_request": "Основной запрос клиента",
  "next_steps": "Следующие шаги"
}}

Отвечай ТОЛЬКО валидным JSON, без дополнительного текста."""

        response = await client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "Ты - помощник менеджера, создаёшь саммари звонков."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.3,
            response_format={"type": "json_object"}
        )
        
        import json
        summary_data = json.loads(response.choices[0].message.content)
        
        return summary_data
        
    except Exception as e:
        logger.error(f"Error creating summary: {e}")
        return {
            "summary": "Ошибка создания саммари",
            "key_points": [],
            "action_items": [],
            "sentiment": "neutral",
            "client_request": "",
            "next_steps": ""
        }

async def save_to_database(
    db: AsyncSession,
    call_id: str,
    webhook_data: dict,
    transcription: str,
    summary_data: dict
) -> str:
    """Сохранить саммари в БД"""
    try:
        from uuid import uuid4
        
        call_summary_id = str(uuid4())
        
        # Создаём таблицу если не существует
        await db.execute("""
            CREATE TABLE IF NOT EXISTS call_summaries (
                id VARCHAR PRIMARY KEY,
                call_id VARCHAR UNIQUE,
                caller VARCHAR,
                called VARCHAR,
                direction VARCHAR,
                duration INTEGER,
                transcription TEXT,
                summary TEXT,
                key_points JSONB,
                action_items JSONB,
                sentiment VARCHAR,
                client_request TEXT,
                next_steps TEXT,
                created_at TIMESTAMP DEFAULT NOW()
            )
        """)
        
        # Вставляем данные
        await db.execute(
            """
            INSERT INTO call_summaries (
                id, call_id, caller, called, direction, duration,
                transcription, summary, key_points, action_items,
                sentiment, client_request, next_steps
            ) VALUES (
                :id, :call_id, :caller, :called, :direction, :duration,
                :transcription, :summary, :key_points, :action_items,
                :sentiment, :client_request, :next_steps
            )
            """,
            {
                "id": call_summary_id,
                "call_id": call_id,
                "caller": webhook_data["caller"],
                "called": webhook_data["called"],
                "direction": webhook_data["direction"],
                "duration": webhook_data["duration"],
                "transcription": transcription,
                "summary": summary_data.get("summary", ""),
                "key_points": summary_data.get("key_points", []),
                "action_items": summary_data.get("action_items", []),
                "sentiment": summary_data.get("sentiment", "neutral"),
                "client_request": summary_data.get("client_request", ""),
                "next_steps": summary_data.get("next_steps", "")
            }
        )
        
        await db.commit()
        logger.info(f"✅ Saved to database: {call_summary_id}")
        
        return call_summary_id
        
    except Exception as e:
        logger.error(f"Error saving to database: {e}")
        return ""

async def send_to_telegram(webhook_data: dict, summary_data: dict):
    """Отправить саммари в Telegram"""
    try:
        direction_emoji = "📞" if webhook_data["direction"] == "in" else "📱"
        direction_text = "Входящий" if webhook_data["direction"] == "in" else "Исходящий"
        
        # Форматируем длительность
        duration = webhook_data["duration"]
        minutes = duration // 60
        seconds = duration % 60
        
        # Формируем сообщение
        message = f"""
{direction_emoji} <b>{direction_text} звонок</b>

📋 <b>Информация:</b>
• От: {webhook_data['caller']}
• Кому: {webhook_data['called']}
• Длительность: {minutes}м {seconds}с

📝 <b>Саммари:</b>
{summary_data.get('summary', 'Не удалось создать саммари')}

🎯 <b>Ключевые пункты:</b>
{chr(10).join([f"• {point}" for point in summary_data.get('key_points', [])])}

✅ <b>Задачи:</b>
{chr(10).join([f"• {task}" for task in summary_data.get('action_items', [])])}

💬 <b>Запрос клиента:</b>
{summary_data.get('client_request', 'Не указан')}

➡️ <b>Следующие шаги:</b>
{summary_data.get('next_steps', 'Не указаны')}

📊 <b>Тон разговора:</b> {summary_data.get('sentiment', 'neutral')}
"""
        
        # Отправляем в Telegram
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage",
                json={
                    "chat_id": TELEGRAM_TARGET_CHAT_ID,
                    "text": message,
                    "parse_mode": "HTML"
                }
            )
            
            if response.status_code == 200:
                logger.info(f"✅ Sent to Telegram chat {TELEGRAM_TARGET_CHAT_ID}")
            else:
                logger.error(f"Failed to send to Telegram: {response.text}")
                
    except Exception as e:
        logger.error(f"Error sending to Telegram: {e}")

async def add_to_bitrix24(webhook_data: dict, summary_data: dict):
    """Добавить саммари в Bitrix24 (комментарий к сделке/контакту)"""
    try:
        if not BITRIX24_WEBHOOK_URL:
            logger.warning("Bitrix24 webhook URL not configured")
            return
        
        # Ищем контакт по телефону
        phone = webhook_data["caller"] if webhook_data["direction"] == "in" else webhook_data["called"]
        
        async with httpx.AsyncClient() as client:
            # Поиск контакта
            search_response = await client.post(
                f"{BITRIX24_WEBHOOK_URL}crm.contact.list",
                json={
                    "filter": {"PHONE": phone}
                }
            )
            
            if search_response.status_code == 200:
                contacts = search_response.json().get("result", [])
                
                if contacts:
                    contact_id = contacts[0]["ID"]
                    
                    # Добавляем комментарий
                    comment_text = f"""Саммари звонка:
{summary_data.get('summary', '')}

Ключевые пункты:
{chr(10).join([f"• {point}" for point in summary_data.get('key_points', [])])}

Задачи:
{chr(10).join([f"• {task}" for task in summary_data.get('action_items', [])])}
"""
                    
                    await client.post(
                        f"{BITRIX24_WEBHOOK_URL}crm.timeline.comment.add",
                        json={
                            "fields": {
                                "ENTITY_ID": contact_id,
                                "ENTITY_TYPE": "contact",
                                "COMMENT": comment_text
                            }
                        }
                    )
                    
                    logger.info(f"✅ Added to Bitrix24 contact {contact_id}")
                else:
                    logger.warning(f"No Bitrix24 contact found for phone {phone}")
                    
    except Exception as e:
        logger.error(f"Error adding to Bitrix24: {e}")

@router.get("/history")
async def get_call_history(
    limit: int = 50,
    db: AsyncSession = Depends(get_db)
):
    """Получить историю саммари звонков"""
    try:
        from sqlalchemy import text
        
        result = await db.execute(
            text("""
                SELECT * FROM call_summaries
                ORDER BY created_at DESC
                LIMIT :limit
            """),
            {"limit": limit}
        )
        
        calls = result.fetchall()
        
        # Преобразуем в список словарей
        calls_list = []
        for row in calls:
            call_dict = dict(row._mapping)
            # Преобразуем datetime в строку
            if 'created_at' in call_dict and call_dict['created_at']:
                call_dict['created_at'] = call_dict['created_at'].isoformat()
            if 'updated_at' in call_dict and call_dict['updated_at']:
                call_dict['updated_at'] = call_dict['updated_at'].isoformat()
            calls_list.append(call_dict)
        
        return {
            "total": len(calls_list),
            "calls": calls_list
        }
        
    except Exception as e:
        logger.error(f"Error fetching call history: {e}")
        import traceback
        logger.error(traceback.format_exc())
        # Возвращаем пустой список вместо ошибки
        return {
            "total": 0,
            "calls": []
        }

@router.post("/manual/{call_id}")
async def create_manual_summary(
    call_id: str,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db)
):
    """Ручное создание саммари для звонка"""
    # TODO: Реализовать ручное создание саммари
    return {"status": "not_implemented"}
