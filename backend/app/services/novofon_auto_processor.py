"""
Автоматический процессор звонков из Novofon
Проверяет новые звонки каждую минуту, транскрибирует и отправляет протокол в Telegram
"""
import os
import logging
import httpx
from typing import Optional, Dict, Any, List
from datetime import datetime, timedelta
import asyncio

from backend.app.services.novofon_service import novofon_service
from backend.app.config.database import async_session_maker

logger = logging.getLogger(__name__)

# Конфигурация
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TG_NEDVIGKA = os.getenv("TG_NEDVIGKA", "-5007549435")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
TARGET_PHONE = os.getenv("NOVOFON_CALLER_ID", "+79843330712")  # Номер для фильтрации


class NovofonAutoProcessor:
    """Автоматический процессор звонков из Novofon"""
    
    def __init__(self):
        self.target_phone = TARGET_PHONE
        self.is_running = False
        logger.info(f"🔧 NovofonAutoProcessor initialized for phone: {self.target_phone}")
    
    async def process_new_calls(self):
        """
        Главная функция: проверяет новые звонки и обрабатывает их
        Вызывается каждую минуту через scheduler
        """
        if self.is_running:
            logger.debug("⏭️ Previous check still running, skipping...")
            return
        
        self.is_running = True
        
        try:
            logger.info("🔍 Checking for new calls from Novofon...")
            
            # Получаем звонки за последние 5 минут
            end_date = datetime.now()
            start_date = end_date - timedelta(minutes=5)
            
            calls = await novofon_service.get_calls(
                start_date=start_date,
                end_date=end_date,
                limit=50,
                is_recorded=True
            )
            
            if not calls:
                logger.debug("📭 No calls found")
                return
            
            logger.info(f"📞 Found {len(calls)} calls, filtering...")
            
            # Фильтруем только звонки с нашим номером
            filtered_calls = self._filter_calls_by_phone(calls)
            
            if not filtered_calls:
                logger.debug(f"📭 No calls with phone {self.target_phone}")
                return
            
            logger.info(f"✅ Found {len(filtered_calls)} calls with {self.target_phone}")
            
            # Обрабатываем каждый звонок
            for call in filtered_calls:
                try:
                    # Проверяем, не обработан ли уже
                    if await self._is_call_processed(call.get("id")):
                        logger.debug(f"⏭️ Call {call.get('id')} already processed")
                        continue
                    
                    # Обрабатываем звонок
                    await self._process_single_call(call)
                    
                except Exception as e:
                    logger.error(f"❌ Error processing call {call.get('id')}: {e}")
                    continue
        
        except Exception as e:
            logger.error(f"❌ Error in process_new_calls: {e}")
            import traceback
            logger.error(traceback.format_exc())
        
        finally:
            self.is_running = False
    
    def _filter_calls_by_phone(self, calls: List[Dict]) -> List[Dict]:
        """Фильтрует звонки по номеру телефона"""
        filtered = []
        
        for call in calls:
            # Проверяем caller (звонящий) и called (кому звонили)
            caller = call.get("caller", "")
            called = call.get("called", "") or call.get("callee", "")
            
            # Нормализуем номера (убираем пробелы, дефисы)
            target_normalized = self.target_phone.replace("+", "").replace("-", "").replace(" ", "")
            caller_normalized = caller.replace("+", "").replace("-", "").replace(" ", "")
            called_normalized = called.replace("+", "").replace("-", "").replace(" ", "")
            
            # Проверяем входящие (звонят НА наш номер) или исходящие (мы звоним)
            if target_normalized in caller_normalized or target_normalized in called_normalized:
                filtered.append(call)
        
        return filtered
    
    async def _is_call_processed(self, call_id: str) -> bool:
        """Проверяет, был ли звонок уже обработан"""
        try:
            async with async_session_maker() as session:
                from sqlalchemy import text
                
                result = await session.execute(
                    text("SELECT COUNT(*) FROM processed_calls WHERE call_id = :call_id"),
                    {"call_id": call_id}
                )
                count = result.scalar()
                return count > 0
                
        except Exception as e:
            # Если таблицы нет, создадим позже
            logger.debug(f"Table check error (expected on first run): {e}")
            return False
    
    async def _process_single_call(self, call: Dict[str, Any]):
        """Обрабатывает один звонок полностью"""
        call_id = call.get("id")
        
        try:
            logger.info(f"🎙️ Processing call {call_id}...")
            
            # 1. Получаем URL записи
            recording_url = await self._get_recording_url(call)
            if not recording_url:
                logger.warning(f"⚠️ No recording URL for call {call_id}")
                await self._mark_as_processed(call_id, success=False)
                return
            
            # 2. Скачиваем аудио
            audio_data = await self._download_audio(recording_url)
            if not audio_data:
                logger.error(f"❌ Failed to download audio for call {call_id}")
                await self._mark_as_processed(call_id, success=False)
                return
            
            # 3. Транскрибируем
            transcription = await self._transcribe_audio(audio_data)
            if not transcription:
                logger.error(f"❌ Failed to transcribe call {call_id}")
                await self._mark_as_processed(call_id, success=False)
                return
            
            logger.info(f"✅ Transcription completed: {len(transcription)} characters")
            
            # 4. Анализируем через AI
            analysis = await self._analyze_call(transcription, call)
            
            # 5. Сохраняем в БД
            await self._save_to_database(call_id, call, transcription, analysis)
            
            # 6. Отправляем в Telegram
            await self._send_to_telegram(call, transcription, analysis)
            
            # 7. Помечаем как обработанный
            await self._mark_as_processed(call_id, success=True)
            
            logger.info(f"✅ Call {call_id} processed successfully!")
            
        except Exception as e:
            logger.error(f"❌ Error processing call {call_id}: {e}")
            import traceback
            logger.error(traceback.format_exc())
            await self._mark_as_processed(call_id, success=False)
    
    async def _get_recording_url(self, call: Dict) -> Optional[str]:
        """Получает URL записи звонка"""
        try:
            # Проверяем, есть ли URL в данных звонка
            if "record_url" in call:
                return call["record_url"]
            
            # Если нет, запрашиваем через API
            call_id = call.get("id")
            recording_url = await novofon_service.get_call_recording_url(call_id)
            return recording_url
            
        except Exception as e:
            logger.error(f"Error getting recording URL: {e}")
            return None
    
    async def _download_audio(self, recording_url: str) -> Optional[bytes]:
        """Скачивает аудиозапись"""
        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.get(recording_url)
                
                if response.status_code == 200:
                    return response.content
                else:
                    logger.error(f"Failed to download: {response.status_code}")
                    return None
                    
        except Exception as e:
            logger.error(f"Error downloading audio: {e}")
            return None
    
    async def _transcribe_audio(self, audio_data: bytes) -> Optional[str]:
        """Транскрибирует аудио через OpenAI Whisper"""
        try:
            from openai import AsyncOpenAI
            
            client = AsyncOpenAI(api_key=OPENAI_API_KEY)
            
            # Сохраняем временно
            temp_file = f"/tmp/novofon_call_{datetime.now().timestamp()}.mp3"
            with open(temp_file, "wb") as f:
                f.write(audio_data)
            
            # Транскрибируем
            with open(temp_file, "rb") as audio_file:
                transcription = await client.audio.transcriptions.create(
                    model="whisper-1",
                    file=audio_file,
                    language="ru"
                )
            
            # Удаляем временный файл
            try:
                os.remove(temp_file)
            except:
                pass
            
            return transcription.text
            
        except Exception as e:
            logger.error(f"Error transcribing audio: {e}")
            return None
    
    async def _analyze_call(self, transcription: str, call: Dict) -> Dict[str, Any]:
        """
        Анализирует звонок через GPT-4o
        Специальный промпт для агентств недвижимости
        """
        try:
            from openai import AsyncOpenAI
            import json
            
            client = AsyncOpenAI(api_key=OPENAI_API_KEY)
            
            # Определяем направление
            direction = self._get_call_direction(call)
            direction_text = "исходящий" if direction == "out" else "входящий"
            
            prompt = f"""Ты - AI-ассистент для анализа телефонных разговоров с агентствами недвижимости.

КОНТЕКСТ: Это {direction_text} звонок. Мы продаём объект недвижимости и общаемся с агентствами/агентами, которые могут привести покупателей.

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
                    {"role": "system", "content": "Ты - эксперт по анализу продаж недвижимости. Создаёшь точные оценки потенциала сделок."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                response_format={"type": "json_object"}
            )
            
            analysis = json.loads(response.choices[0].message.content)
            return analysis
            
        except Exception as e:
            logger.error(f"Error analyzing call: {e}")
            return {
                "agency_name": "Не указано",
                "lead_category": "НЕ ОПРЕДЕЛЕНО",
                "interest_rating": 5,
                "interest_reasons": ["Ошибка анализа"],
                "has_ready_buyers": False,
                "summary": "Не удалось проанализировать звонок"
            }
    
    def _get_call_direction(self, call: Dict) -> str:
        """Определяет направление звонка"""
        direction = call.get("direction", "")
        if direction:
            return direction
        
        # Пробуем определить по номерам
        caller = call.get("caller", "")
        target_normalized = self.target_phone.replace("+", "").replace("-", "").replace(" ", "")
        caller_normalized = caller.replace("+", "").replace("-", "").replace(" ", "")
        
        if target_normalized in caller_normalized:
            return "out"  # Мы звоним
        else:
            return "in"  # Нам звонят
    
    async def _save_to_database(
        self,
        call_id: str,
        call: Dict,
        transcription: str,
        analysis: Dict
    ):
        """Сохраняет результаты в БД"""
        try:
            async with async_session_maker() as session:
                from sqlalchemy import text
                from uuid import uuid4
                
                # Создаём таблицу если не существует
                await session.execute(text("""
                    CREATE TABLE IF NOT EXISTS nedvigka_calls (
                        id VARCHAR PRIMARY KEY,
                        call_id VARCHAR UNIQUE,
                        caller VARCHAR,
                        called VARCHAR,
                        direction VARCHAR,
                        duration INTEGER,
                        transcription TEXT,
                        analysis JSONB,
                        agency_name VARCHAR,
                        lead_category VARCHAR,
                        interest_rating INTEGER,
                        priority VARCHAR,
                        created_at TIMESTAMP DEFAULT NOW()
                    )
                """))
                
                # Вставляем данные
                record_id = str(uuid4())
                await session.execute(
                    text("""
                        INSERT INTO nedvigka_calls (
                            id, call_id, caller, called, direction, duration,
                            transcription, analysis, agency_name, lead_category,
                            interest_rating, priority
                        ) VALUES (
                            :id, :call_id, :caller, :called, :direction, :duration,
                            :transcription, :analysis, :agency_name, :lead_category,
                            :interest_rating, :priority
                        )
                    """),
                    {
                        "id": record_id,
                        "call_id": call_id,
                        "caller": call.get("caller", ""),
                        "called": call.get("called", "") or call.get("callee", ""),
                        "direction": self._get_call_direction(call),
                        "duration": call.get("duration", 0),
                        "transcription": transcription,
                        "analysis": json.dumps(analysis, ensure_ascii=False),
                        "agency_name": analysis.get("agency_name", ""),
                        "lead_category": analysis.get("lead_category", ""),
                        "interest_rating": analysis.get("interest_rating", 0),
                        "priority": analysis.get("priority", "")
                    }
                )
                
                await session.commit()
                logger.info(f"✅ Saved to database: {record_id}")
                
        except Exception as e:
            logger.error(f"Error saving to database: {e}")
            import traceback
            logger.error(traceback.format_exc())
    
    async def _send_to_telegram(self, call: Dict, transcription: str, analysis: Dict):
        """Отправляет красивый протокол в Telegram группу"""
        try:
            # Форматируем данные звонка
            direction = self._get_call_direction(call)
            direction_emoji = "📱" if direction == "out" else "📞"
            direction_text = "Исходящий звонок" if direction == "out" else "Входящий звонок"
            
            # Номер телефона
            if direction == "out":
                phone = call.get("called", "") or call.get("callee", "")
            else:
                phone = call.get("caller", "")
            
            # Длительность
            duration = call.get("duration", 0)
            minutes = duration // 60
            seconds = duration % 60
            
            # Дата/время
            timestamp = call.get("timestamp") or call.get("start_time") or datetime.now().isoformat()
            try:
                dt = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
                date_str = dt.strftime("%d.%m.%Y %H:%M")
            except:
                date_str = datetime.now().strftime("%d.%m.%Y %H:%M")
            
            # Эмодзи для категории лида
            lead_emoji = "🔥" if "ГОРЯЧ" in analysis.get("lead_category", "") else \
                        "🌡️" if "ТЁПЛ" in analysis.get("lead_category", "") else \
                        "❄️" if "ХОЛОДН" in analysis.get("lead_category", "") else "⛔"
            
            # Эмодзи для приоритета
            priority_emoji = "🔴" if analysis.get("priority") == "ВЫСОКИЙ" else \
                            "🟡" if analysis.get("priority") == "СРЕДНИЙ" else "🟢"
            
            # Формируем сообщение
            message = f"""{direction_emoji} <b>{direction_text}</b>
━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📅 <b>Дата:</b> {date_str}
📱 <b>Телефон:</b> <code>{phone}</code>
⏱️ <b>Длительность:</b> {minutes}м {seconds}с
🏢 <b>Агентство:</b> {analysis.get('agency_name', 'Не указано')}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🎯 <b>ОЦЕНКА ЗАИНТЕРЕСОВАННОСТИ</b>
━━━━━━━━━━━━━━━━━━━━━━━━━━━━

{lead_emoji} <b>Уровень:</b> {analysis.get('lead_category', 'Не определено')}
⭐ <b>Рейтинг:</b> {analysis.get('interest_rating', 0)}/10

📊 <b>Обоснование:</b>
{chr(10).join([f"• {reason}" for reason in analysis.get('interest_reasons', [])])}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━
💰 <b>КОММЕРЧЕСКИЙ ПОТЕНЦИАЛ</b>
━━━━━━━━━━━━━━━━━━━━━━━━━━━━

✅ <b>База покупателей:</b> {'ДА' if analysis.get('has_ready_buyers') else 'НЕТ'}{', ' + analysis.get('buyers_count', '') if analysis.get('buyers_count') and analysis.get('buyers_count') != 'Не указано' else ''}
💵 <b>Бюджет клиентов:</b> {analysis.get('buyer_budget', 'Не указан')}
📅 <b>Готовность к сделке:</b> {analysis.get('readiness_timeframe', 'Не указана')}
{f"📈 <b>Комиссия агентства:</b> {analysis.get('commission_mentioned', 'Не указана')}" if analysis.get('commission_mentioned') and analysis.get('commission_mentioned') != 'Не указано' else ''}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🎯 <b>КЛЮЧЕВЫЕ МОМЕНТЫ</b>
━━━━━━━━━━━━━━━━━━━━━━━━━━━━

{chr(10).join([f"✓ {point}" for point in analysis.get('key_interests', [])])}
"""

            # Добавляем возражения если есть
            if analysis.get('concerns') and len(analysis.get('concerns', [])) > 0:
                message += f"""
<b>⚠️ Возражения:</b>
{chr(10).join([f"• {concern}" for concern in analysis.get('concerns', [])])}
"""

            # Добавляем конкурентов если упомянуты
            if analysis.get('competitors_mentioned') and len(analysis.get('competitors_mentioned', [])) > 0:
                message += f"""
<b>🏆 Упомянутые конкуренты:</b>
{chr(10).join([f"• {comp}" for comp in analysis.get('competitors_mentioned', [])])}
"""

            message += f"""
━━━━━━━━━━━━━━━━━━━━━━━━━━━━
✅ <b>РЕКОМЕНДАЦИИ</b>
━━━━━━━━━━━━━━━━━━━━━━━━━━━━

{priority_emoji} <b>Приоритет:</b> {analysis.get('priority', 'СРЕДНИЙ')}

<b>Следующие шаги:</b>
{chr(10).join([f"• {step}" for step in analysis.get('next_steps', [])])}

<b>💡 Рекомендуемые действия:</b>
{chr(10).join([f"• {action}" for action in analysis.get('recommended_actions', [])])}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📝 <b>ТРАНСКРИПЦИЯ РАЗГОВОРА</b>
━━━━━━━━━━━━━━━━━━━━━━━━━━━━

{transcription[:2000]}{"..." if len(transcription) > 2000 else ""}
"""

            # Отправляем в Telegram
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage",
                    json={
                        "chat_id": TG_NEDVIGKA,
                        "text": message,
                        "parse_mode": "HTML"
                    }
                )
                
                if response.status_code == 200:
                    logger.info(f"✅ Sent to Telegram group {TG_NEDVIGKA}")
                else:
                    logger.error(f"Failed to send to Telegram: {response.status_code} {response.text}")
                    
        except Exception as e:
            logger.error(f"Error sending to Telegram: {e}")
            import traceback
            logger.error(traceback.format_exc())
    
    async def _mark_as_processed(self, call_id: str, success: bool = True):
        """Помечает звонок как обработанный"""
        try:
            async with async_session_maker() as session:
                from sqlalchemy import text
                
                # Создаём таблицу если не существует
                await session.execute(text("""
                    CREATE TABLE IF NOT EXISTS processed_calls (
                        call_id VARCHAR PRIMARY KEY,
                        processed_at TIMESTAMP DEFAULT NOW(),
                        success BOOLEAN DEFAULT TRUE
                    )
                """))
                
                # Вставляем запись
                await session.execute(
                    text("""
                        INSERT INTO processed_calls (call_id, success)
                        VALUES (:call_id, :success)
                        ON CONFLICT (call_id) DO NOTHING
                    """),
                    {"call_id": call_id, "success": success}
                )
                
                await session.commit()
                
        except Exception as e:
            logger.error(f"Error marking call as processed: {e}")


# Глобальный экземпляр
novofon_auto_processor = NovofonAutoProcessor()
