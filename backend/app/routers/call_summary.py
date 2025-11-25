"""
API роутер для саммари звонков из Новофон
Автоматическая транскрипция и создание саммари после завершения звонка
"""
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, Request
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
TELEGRAM_TARGET_CHAT_ID = os.getenv("TG_NEDVIGKA", "-5007549435")  # Группа для недвижимости
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
BITRIX24_WEBHOOK_URL = os.getenv("BITRIX24_WEBHOOK_URL")

# Novofon API credentials для скачивания записей
NOVOFON_API_KEY = os.getenv("NOVOFON_API_KEY", "")
NOVOFON_API_SECRET = os.getenv("NOVOFON_API_SECRET", "")

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
@router.get("/webhook/novofon")
async def novofon_webhook(
    request: Request,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db)
):
    """
    Webhook от Новофон при завершении звонка
    Автоматически создаёт саммари и отправляет в Telegram + Bitrix24
    """
    try:
        # ЛОГИРУЕМ МЕТОД И ЗАГОЛОВКИ
        logger.info(f"📞 Received webhook: method={request.method}, content-type={request.headers.get('content-type')}")
        
        # Получаем сырое тело
        body = await request.body()
        logger.info(f"📞 Raw body: {body[:500]}")  # Первые 500 байт
        
        # Пробуем разные способы получения данных
        webhook_data = {}
        
        # 1. Пробуем JSON
        if body:
            try:
                webhook_data = await request.json()
                logger.info(f"✅ Parsed as JSON: {webhook_data}")
            except:
                pass
        
        # 2. Пробуем form-data
        if not webhook_data:
            try:
                form = await request.form()
                webhook_data = dict(form)
                logger.info(f"✅ Parsed as form-data: {webhook_data}")
            except:
                pass
        
        # 3. Пробуем query params
        if not webhook_data:
            webhook_data = dict(request.query_params)
            logger.info(f"✅ Parsed as query params: {webhook_data}")
        
        # ЛОГИРУЕМ ВСЁ ЧТО ПОЛУЧИЛИ
        logger.info(f"📞 Final webhook data: {webhook_data}")
        
        # Если данных нет - возвращаем OK чтобы Novofon не ретраил
        if not webhook_data:
            logger.warning("⚠️ Empty webhook data received")
            return {"status": "ok", "message": "empty_data_received"}
        
        # Обрабатываем события
        event = webhook_data.get("event", "")
        
        # === ОБРАБОТКА SPEECH_RECOGNITION (ГОТОВАЯ ТРАНСКРИПЦИЯ ОТ NOVOFON) ===
        if event == "SPEECH_RECOGNITION":
            pbx_call_id = webhook_data.get("pbx_call_id", "")
            result_json = webhook_data.get("result", "{}")
            
            logger.info(f"🎤 Received SPEECH_RECOGNITION for call {pbx_call_id}")
            
            # Парсим транскрипцию из JSON
            import json
            try:
                result_data = json.loads(result_json) if isinstance(result_json, str) else result_json
                phrases = result_data.get("phrases", [])
                
                # Собираем текст транскрипции с разделением по каналам
                transcription_lines = []
                for phrase in phrases:
                    channel = phrase.get("channel", 0)
                    text = phrase.get("result", "")
                    # Канал 1 - обычно звонящий, канал 2 - принимающий
                    speaker = "📞 Агент:" if channel == 2 else "👤 Клиент:"
                    transcription_lines.append(f"{speaker} {text}")
                
                transcription = "\n".join(transcription_lines)
                
                if not transcription.strip():
                    logger.warning(f"⚠️ Empty transcription for call {pbx_call_id}")
                    return {"status": "skipped", "reason": "empty_transcription"}
                
                logger.info(f"✅ Got transcription for call {pbx_call_id}: {len(transcription)} chars")
                
                # Формируем данные для обработки
                normalized_data = {
                    "call_id": pbx_call_id,
                    "call_id_with_rec": webhook_data.get("call_id", ""),
                    "caller": "",  # Будет заполнено из кэша или оставлено пустым
                    "called": "",
                    "direction": "out",  # По умолчанию исходящий
                    "duration": 0,
                    "status": "answered",
                    "timestamp": "",
                    "transcription": transcription  # ВАЖНО: передаём готовую транскрипцию
                }
                
                # Добавляем задачу для создания саммари
                background_tasks.add_task(
                    process_transcription,
                    normalized_data,
                    db
                )
                
                logger.info(f"🚀 Started processing transcription for call {pbx_call_id}")
                return {"status": "accepted", "call_id": pbx_call_id, "type": "speech_recognition"}
                
            except json.JSONDecodeError as e:
                logger.error(f"❌ Failed to parse SPEECH_RECOGNITION result: {e}")
                return {"status": "error", "reason": "invalid_json"}
        
        # === ОБРАБОТКА СОБЫТИЙ ЗАВЕРШЕНИЯ ЗВОНКА (для получения метаданных) ===
        # Проверяем что это событие завершения с записью
        if event not in ["NOTIFY_OUT_END", "NOTIFY_END"]:
            logger.info(f"⏭️ Skipping event: {event}")
            return {"status": "skipped", "reason": "not_end_event"}
        
        # Сохраняем метаданные звонка для использования в SPEECH_RECOGNITION
        pbx_call_id = webhook_data.get("pbx_call_id", "")
        call_id_with_rec = webhook_data.get("call_id_with_rec", "")
        
        # Сохраняем в кэш (простой словарь в памяти)
        call_metadata = {
            "call_id": pbx_call_id,
            "call_id_with_rec": call_id_with_rec,
            "caller": webhook_data.get("caller_id", ""),
            "called": webhook_data.get("destination", webhook_data.get("called_did", "")),
            "direction": "out" if event == "NOTIFY_OUT_END" else "in",
            "duration": int(webhook_data.get("duration", 0)),
            "status": webhook_data.get("disposition", "answered"),
            "timestamp": webhook_data.get("call_start", "")
        }
        
        # Сохраняем метаданные в глобальный кэш
        if not hasattr(novofon_webhook, '_call_cache'):
            novofon_webhook._call_cache = {}
        novofon_webhook._call_cache[pbx_call_id] = call_metadata
        
        logger.info(f"📋 Cached metadata for call {pbx_call_id}: caller={call_metadata['caller']}, called={call_metadata['called']}, duration={call_metadata['duration']}s")
        
        # Проверяем наличие записи
        is_recorded = webhook_data.get("is_recorded", "0")
        if is_recorded != "1":
            logger.info(f"⏭️ Skipping: no recording (is_recorded={is_recorded})")
            return {"status": "skipped", "reason": "no_recording"}
        
        logger.info(f"📞 Call {pbx_call_id} has recording, waiting for SPEECH_RECOGNITION event...")
        return {"status": "ok", "call_id": pbx_call_id, "message": "metadata_cached"}
        
    except Exception as e:
        logger.error(f"❌ Error processing webhook: {e}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=str(e))

async def process_transcription(webhook_data: dict, db: AsyncSession):
    """
    Фоновая задача: обработка готовой транскрипции от Novofon
    1. Получить метаданные из кэша (если есть)
    2. Создать саммари через GPT-4o
    3. Сохранить в БД
    4. Отправить в Telegram
    5. Добавить в Bitrix24
    """
    call_id = webhook_data["call_id"]
    transcription = webhook_data.get("transcription", "")
    
    try:
        logger.info(f"🎤 Processing transcription for call: {call_id}")
        
        # Получаем метаданные из кэша
        cached_metadata = getattr(novofon_webhook, '_call_cache', {}).get(call_id, {})
        if cached_metadata:
            webhook_data.update({
                "caller": cached_metadata.get("caller", webhook_data.get("caller", "")),
                "called": cached_metadata.get("called", webhook_data.get("called", "")),
                "direction": cached_metadata.get("direction", webhook_data.get("direction", "out")),
                "duration": cached_metadata.get("duration", webhook_data.get("duration", 0)),
                "timestamp": cached_metadata.get("timestamp", webhook_data.get("timestamp", "")),
            })
            logger.info(f"📋 Using cached metadata: caller={webhook_data['caller']}, called={webhook_data['called']}")
        
        if not transcription:
            logger.error(f"❌ Empty transcription for call {call_id}")
            return
        
        logger.info(f"✅ Transcription ready for {call_id}: {len(transcription)} chars")
        
        # Создать саммари через GPT-4o
        summary_data = await create_call_summary(transcription, webhook_data)
        
        # Добавляем транскрипцию в summary_data для отправки
        summary_data["transcription"] = transcription
        
        # Сохранить в БД
        try:
            call_summary_id = await save_to_database(
                db,
                call_id,
                webhook_data,
                transcription,
                summary_data
            )
        except Exception as db_error:
            logger.warning(f"⚠️ Could not save to database: {db_error}")
        
        # Отправить в Telegram - ГЛАВНАЯ ЦЕЛЬ!
        await send_to_telegram(webhook_data, summary_data)
        
        # Добавить в Bitrix24
        try:
            await add_to_bitrix24(webhook_data, summary_data)
        except Exception as bitrix_error:
            logger.warning(f"⚠️ Could not add to Bitrix24: {bitrix_error}")
        
        logger.info(f"✅ Call {call_id} processed successfully!")
        
    except Exception as e:
        logger.error(f"❌ Error processing transcription for call {call_id}: {e}")
        import traceback
        logger.error(traceback.format_exc())

async def process_call_recording(webhook_data: dict, db: AsyncSession):
    """
    Фоновая задача: обработка записи звонка (FALLBACK если нет SPEECH_RECOGNITION)
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
        
        # 3. Создать саммари через GPT-4o
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
        
        prompt = f"""Ты - AI-ассистент для анализа телефонных разговоров с агентствами недвижимости.

КОНТЕКСТ: Это {direction} звонок. Мы продаём объект недвижимости и общаемся с агентствами/агентами, которые могут привести покупателей.

ТРАНСКРИПЦИЯ РАЗГОВОРА:
{transcription}

ЗАДАЧА: Создай детальный анализ разговора в формате JSON со следующими полями:

{{
  "agency_name": "Название агентства или имя агента (если упомянуто, иначе 'Не указано')",
  "lead_category": "ГОРЯЧИЙ ЛИД / ТЁПЛЫЙ ЛИД / ХОЛОДНЫЙ ЛИД / ОТКАЗ",
  "interest_rating": 8,
  "interest_reasons": [
    "Причина 1 почему такая оценка",
    "Причина 2",
    "Причина 3"
  ],
  "has_ready_buyers": true,
  "buyers_count": "3-5 готовых клиентов",
  "buyer_budget": "15-20 млн руб",
  "readiness_timeframe": "1-2 месяца",
  "commission_mentioned": "3%",
  "key_interests": [
    "Что конкретно интересует агентство",
    "На что обращал внимание",
    "Какие вопросы задавал"
  ],
  "concerns": [
    "Что смущает или вызывает сомнения",
    "Возражения"
  ],
  "competitors_mentioned": [
    "Конкуренты если упомянуты"
  ],
  "next_steps": [
    "Что нужно сделать дальше",
    "Какие материалы отправить",
    "Когда связаться"
  ],
  "priority": "ВЫСОКИЙ / СРЕДНИЙ / НИЗКИЙ",
  "recommended_actions": [
    "Конкретное действие 1",
    "Конкретное действие 2"
  ],
  "summary": "Краткое содержание разговора в 2-3 предложениях"
}}

ВАЖНО:
- Если информация не упоминалась в разговоре, пиши "Не указано" или null
- Будь максимально конкретен в оценках
- interest_rating от 1 до 10, где 10 = точно купят
- Учитывай тон разговора, энтузиазм, конкретику вопросов

Отвечай ТОЛЬКО валидным JSON без дополнительного текста."""

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
    """Отправить саммари в Telegram (для агентств недвижимости)"""
    try:
        direction_emoji = "📞" if webhook_data["direction"] == "in" else "📱"
        direction_text = "Входящий звонок" if webhook_data["direction"] == "in" else "Исходящий звонок"
        
        # Форматируем длительность
        duration = webhook_data["duration"]
        minutes = duration // 60
        seconds = duration % 60
        
        # Дата/время (если есть)
        from datetime import datetime
        timestamp = webhook_data.get("timestamp", datetime.now().isoformat())
        try:
            dt = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
            date_str = dt.strftime("%d.%m.%Y %H:%M")
        except:
            date_str = datetime.now().strftime("%d.%m.%Y %H:%M")
        
        # Номер телефона
        if webhook_data["direction"] == "out":
            phone = webhook_data.get("called", "")
        else:
            phone = webhook_data.get("caller", "")
        
        # Эмодзи для категории лида
        lead_emoji = "🔥" if "ГОРЯЧ" in summary_data.get("lead_category", "") else \
                    "🌡️" if "ТЁПЛ" in summary_data.get("lead_category", "") else \
                    "❄️" if "ХОЛОДН" in summary_data.get("lead_category", "") else "⛔"
        
        # Эмодзи для приоритета
        priority_emoji = "🔴" if summary_data.get("priority") == "ВЫСОКИЙ" else \
                        "🟡" if summary_data.get("priority") == "СРЕДНИЙ" else "🟢"
        
        # Формируем сообщение
        message = f"""{direction_emoji} <b>{direction_text}</b>
━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📅 <b>Дата:</b> {date_str}
📱 <b>Телефон:</b> <code>{phone}</code>
⏱️ <b>Длительность:</b> {minutes}м {seconds}с
🏢 <b>Агентство:</b> {summary_data.get('agency_name', 'Не указано')}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🎯 <b>ОЦЕНКА ЗАИНТЕРЕСОВАННОСТИ</b>
━━━━━━━━━━━━━━━━━━━━━━━━━━━━

{lead_emoji} <b>Уровень:</b> {summary_data.get('lead_category', 'Не определено')}
⭐ <b>Рейтинг:</b> {summary_data.get('interest_rating', 0)}/10

📊 <b>Обоснование:</b>
{chr(10).join([f"• {reason}" for reason in summary_data.get('interest_reasons', [])])}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━
💰 <b>КОММЕРЧЕСКИЙ ПОТЕНЦИАЛ</b>
━━━━━━━━━━━━━━━━━━━━━━━━━━━━

✅ <b>База покупателей:</b> {'ДА' if summary_data.get('has_ready_buyers') else 'НЕТ'}{', ' + summary_data.get('buyers_count', '') if summary_data.get('buyers_count') and summary_data.get('buyers_count') != 'Не указано' else ''}
💵 <b>Бюджет клиентов:</b> {summary_data.get('buyer_budget', 'Не указан')}
📅 <b>Готовность к сделке:</b> {summary_data.get('readiness_timeframe', 'Не указана')}
{f"📈 <b>Комиссия агентства:</b> {summary_data.get('commission_mentioned', 'Не указана')}" if summary_data.get('commission_mentioned') and summary_data.get('commission_mentioned') != 'Не указано' else ''}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🎯 <b>КЛЮЧЕВЫЕ МОМЕНТЫ</b>
━━━━━━━━━━━━━━━━━━━━━━━━━━━━

{chr(10).join([f"✓ {point}" for point in summary_data.get('key_interests', [])])}
"""

        # Добавляем возражения если есть
        if summary_data.get('concerns') and len(summary_data.get('concerns', [])) > 0:
            message += f"""
<b>⚠️ Возражения:</b>
{chr(10).join([f"• {concern}" for concern in summary_data.get('concerns', [])])}
"""

        # Добавляем конкурентов если упомянуты
        if summary_data.get('competitors_mentioned') and len(summary_data.get('competitors_mentioned', [])) > 0:
            message += f"""
<b>🏆 Упомянутые конкуренты:</b>
{chr(10).join([f"• {comp}" for comp in summary_data.get('competitors_mentioned', [])])}
"""

        message += f"""
━━━━━━━━━━━━━━━━━━━━━━━━━━━━
✅ <b>РЕКОМЕНДАЦИИ</b>
━━━━━━━━━━━━━━━━━━━━━━━━━━━━

{priority_emoji} <b>Приоритет:</b> {summary_data.get('priority', 'СРЕДНИЙ')}

<b>Следующие шаги:</b>
{chr(10).join([f"• {step}" for step in summary_data.get('next_steps', [])])}

<b>💡 Рекомендуемые действия:</b>
{chr(10).join([f"• {action}" for action in summary_data.get('recommended_actions', [])])}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📝 <b>КРАТКОЕ САММАРИ</b>
━━━━━━━━━━━━━━━━━━━━━━━━━━━━

{summary_data.get('summary', 'Не удалось создать саммари')}
"""
        
        # Добавляем транскрипцию если есть (обрезаем если очень длинная)
        transcription = summary_data.get('transcription', '')
        if transcription:
            # Telegram ограничивает сообщения 4096 символами
            # Оставляем место для основного сообщения (примерно 3000 символов)
            max_transcription_length = 3500
            if len(transcription) > max_transcription_length:
                transcription = transcription[:max_transcription_length] + "\n\n... [транскрипция обрезана из-за длины]"
            
            message += f"""
━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🎤 <b>ТРАНСКРИПЦИЯ</b>
━━━━━━━━━━━━━━━━━━━━━━━━━━━━

<pre>{transcription}</pre>
"""
        
        # Проверяем длину сообщения для Telegram (макс 4096)
        if len(message) > 4096:
            # Отправляем в двух частях
            first_part = message[:4000] + "\n\n... [продолжение в следующем сообщении]"
            second_part = message[4000:]
            
            async with httpx.AsyncClient() as client:
                # Первая часть
                response1 = await client.post(
                    f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage",
                    json={
                        "chat_id": TELEGRAM_TARGET_CHAT_ID,
                        "text": first_part,
                        "parse_mode": "HTML"
                    }
                )
                
                # Вторая часть
                if len(second_part) > 0:
                    response2 = await client.post(
                        f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage",
                        json={
                            "chat_id": TELEGRAM_TARGET_CHAT_ID,
                            "text": f"<b>Продолжение:</b>\n{second_part[:4000]}",
                            "parse_mode": "HTML"
                        }
                    )
                
                if response1.status_code == 200:
                    logger.info(f"✅ Sent to Telegram chat {TELEGRAM_TARGET_CHAT_ID}")
                else:
                    logger.error(f"Failed to send to Telegram: {response1.text}")
        else:
            # Отправляем одним сообщением
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
