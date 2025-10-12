"""
Telegram бот для бригад - загрузка фото уборок
Функционал:
1. /start - показать список домов на сегодня для бригады
2. Выбор дома через inline buttons
3. Загрузка фото
4. /done - завершить уборку и отправить фото с AI подписью
"""
import os
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime, date
import httpx

logger = logging.getLogger(__name__)

# Telegram credentials
BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
API_URL = f"https://api.telegram.org/bot{BOT_TOKEN}"

# Хранилище состояния пользователей (в production использовать Redis)
user_sessions = {}


class CleaningSession:
    """Сессия уборки для пользователя"""
    def __init__(self, user_id: int, brigade_id: str = None):
        self.user_id = user_id
        self.brigade_id = brigade_id
        self.selected_house_id = None
        self.selected_house_address = None
        self.photos = []  # List of file_ids
        self.started_at = datetime.now()
    
    def add_photo(self, file_id: str):
        """Добавить фото в сессию"""
        self.photos.append(file_id)
    
    def clear(self):
        """Очистить сессию"""
        self.selected_house_id = None
        self.selected_house_address = None
        self.photos = []


def get_or_create_session(user_id: int) -> CleaningSession:
    """Получить или создать сессию для пользователя"""
    if user_id not in user_sessions:
        user_sessions[user_id] = CleaningSession(user_id)
    return user_sessions[user_id]


async def send_message(
    chat_id: int,
    text: str,
    reply_markup: Optional[Dict] = None,
    parse_mode: str = "HTML"
) -> bool:
    """Отправить текстовое сообщение"""
    try:
        async with httpx.AsyncClient(timeout=30) as client:
            payload = {
                "chat_id": chat_id,
                "text": text,
                "parse_mode": parse_mode
            }
            if reply_markup:
                payload["reply_markup"] = reply_markup
            
            response = await client.post(f"{API_URL}/sendMessage", json=payload)
            
            if response.status_code == 200:
                logger.info(f"[telegram_cleaning_bot] Message sent to {chat_id}")
                return True
            else:
                logger.error(f"[telegram_cleaning_bot] Failed to send message: {response.text}")
                return False
    
    except Exception as e:
        logger.error(f"[telegram_cleaning_bot] Error sending message: {e}")
        return False


async def send_photo(
    chat_id: int,
    photo_file_id: str,
    caption: str = None
) -> bool:
    """Отправить фото"""
    try:
        async with httpx.AsyncClient(timeout=30) as client:
            payload = {
                "chat_id": chat_id,
                "photo": photo_file_id
            }
            if caption:
                payload["caption"] = caption
                payload["parse_mode"] = "HTML"
            
            response = await client.post(f"{API_URL}/sendPhoto", json=payload)
            
            if response.status_code == 200:
                logger.info(f"[telegram_cleaning_bot] Photo sent to {chat_id}")
                return True
            else:
                logger.error(f"[telegram_cleaning_bot] Failed to send photo: {response.text}")
                return False
    
    except Exception as e:
        logger.error(f"[telegram_cleaning_bot] Error sending photo: {e}")
        return False


async def send_media_group(
    chat_id: int,
    photos: List[str],
    caption: str = None
) -> bool:
    """Отправить группу фото с подписью"""
    try:
        if not photos:
            logger.warning("[telegram_cleaning_bot] No photos to send")
            return False
        
        # Формируем media array
        media = []
        for idx, photo_file_id in enumerate(photos):
            media_item = {
                "type": "photo",
                "media": photo_file_id
            }
            # Подпись только к первому фото
            if idx == 0 and caption:
                media_item["caption"] = caption
                media_item["parse_mode"] = "HTML"
            
            media.append(media_item)
        
        async with httpx.AsyncClient(timeout=30) as client:
            payload = {
                "chat_id": chat_id,
                "media": media
            }
            
            response = await client.post(f"{API_URL}/sendMediaGroup", json=payload)
            
            if response.status_code == 200:
                logger.info(f"[telegram_cleaning_bot] Media group sent to {chat_id}: {len(photos)} photos")
                return True
            else:
                logger.error(f"[telegram_cleaning_bot] Failed to send media group: {response.text}")
                return False
    
    except Exception as e:
        logger.error(f"[telegram_cleaning_bot] Error sending media group: {e}")
        return False


async def handle_start_command(chat_id: int, user_id: int, db_session):
    """
    Обработка команды /start
    Показать список домов на сегодня для бригады пользователя
    """
    logger.info(f"[telegram_cleaning_bot] /start command from user {user_id}")
    
    try:
        # Получаем или создаём сессию
        session = get_or_create_session(user_id)
        
        # TODO: Получить бригаду пользователя из БД по telegram_id
        # brigade = await get_brigade_by_telegram_id(user_id, db_session)
        # if not brigade:
        #     await send_message(chat_id, "❌ Вы не зарегистрированы в системе. Обратитесь к администратору.")
        #     return
        
        # TODO: Получить дома на сегодня для этой бригады
        # today = date.today()
        # houses = await get_houses_for_brigade_by_date(brigade.id, today, db_session)
        
        # Определяем бригаду пользователя
        # TODO: В продакшене получать из БД по telegram_user_id
        session.brigade_id = "brigade_1"  # Бригада 1
        
        # Получаем дома на завтра (13.10.2025)
        # TODO: В продакшене получать из БД/Bitrix24 по графику бригады
        from datetime import datetime, timedelta
        tomorrow = datetime.now().date() + timedelta(days=1)  # 13.10.2025
        
        # Моковые данные для Бригады 1 на 13.10.2025
        houses = [
            {"id": "house_1", "address": "ул. Ленина, д. 10, подъезд 1"},
            {"id": "house_2", "address": "ул. Пушкина, д. 25, подъезды 1-3"},
            {"id": "house_3", "address": "пр. Мира, д. 5, подъезды 1-4"}
        ]
        
        if not houses:
            await send_message(
                chat_id,
                "📋 На сегодня у вас нет запланированных уборок.\n\n"
                "Если это ошибка, обратитесь к диспетчеру."
            )
            return
        
        # Создаём inline keyboard с адресами
        keyboard = []
        for house in houses:
            button = {
                "text": house["address"],
                "callback_data": f"house_{house['id']}"
            }
            keyboard.append([button])
        
        reply_markup = {
            "inline_keyboard": keyboard
        }
        
        await send_message(
            chat_id,
            f"🏠 <b>Выберите дом для загрузки фото:</b>\n\n"
            f"📅 Сегодня: {datetime.now().strftime('%d.%m.%Y')}\n"
            f"📍 Домов на сегодня: {len(houses)}",
            reply_markup=reply_markup
        )
        
    except Exception as e:
        logger.error(f"[telegram_cleaning_bot] Error in handle_start_command: {e}")
        await send_message(chat_id, "❌ Произошла ошибка. Попробуйте позже.")


async def handle_house_selection(
    chat_id: int,
    user_id: int,
    house_id: str,
    callback_query_id: str,
    db_session
):
    """
    Обработка выбора дома
    """
    logger.info(f"[telegram_cleaning_bot] House selected: {house_id} by user {user_id}")
    
    try:
        session = get_or_create_session(user_id)
        
        # TODO: Получить информацию о доме из БД
        # house = await get_house_by_id(house_id, db_session)
        
        # Временные моковые данные
        houses_mock = {
            "house_1": {"id": "house_1", "address": "ул. Ленина, д. 10, подъезд 1", "entrances": 1, "floors": 5},
            "house_2": {"id": "house_2", "address": "ул. Пушкина, д. 25, подъезды 1-3", "entrances": 3, "floors": 9},
            "house_3": {"id": "house_3", "address": "пр. Мира, д. 5, подъезды 1-4", "entrances": 4, "floors": 5}
        }
        house = houses_mock.get(house_id)
        
        if not house:
            await send_message(chat_id, "❌ Дом не найден")
            return
        
        # Сохраняем выбранный дом в сессию
        session.selected_house_id = house["id"]
        session.selected_house_address = house["address"]
        session.photos = []  # Очищаем предыдущие фото
        
        # Подтверждаем выбор
        await send_message(
            chat_id,
            f"✅ <b>Выбран дом:</b>\n"
            f"🏠 {house['address']}\n"
            f"🚪 Подъездов: {house.get('entrances', '—')}\n"
            f"📊 Этажей: {house.get('floors', '—')}\n\n"
            f"📸 <b>Отправьте фото уборки</b>\n"
            f"Когда закончите, нажмите /done"
        )
        
        # Отвечаем на callback query
        async with httpx.AsyncClient(timeout=10) as client:
            await client.post(
                f"{API_URL}/answerCallbackQuery",
                json={"callback_query_id": callback_query_id, "text": "Дом выбран ✅"}
            )
        
    except Exception as e:
        logger.error(f"[telegram_cleaning_bot] Error in handle_house_selection: {e}")
        await send_message(chat_id, "❌ Произошла ошибка при выборе дома")


async def handle_photo(chat_id: int, user_id: int, photo_file_id: str):
    """
    Обработка загруженного фото
    """
    logger.info(f"[telegram_cleaning_bot] Photo received from user {user_id}")
    
    try:
        session = get_or_create_session(user_id)
        
        if not session.selected_house_id:
            await send_message(
                chat_id,
                "⚠️ Сначала выберите дом командой /start"
            )
            return
        
        # Добавляем фото в сессию
        session.add_photo(photo_file_id)
        
        await send_message(
            chat_id,
            f"✅ Фото {len(session.photos)} сохранено\n"
            f"🏠 Дом: {session.selected_house_address}\n\n"
            f"📸 Отправьте ещё фото или нажмите /done для завершения"
        )
        
    except Exception as e:
        logger.error(f"[telegram_cleaning_bot] Error in handle_photo: {e}")
        await send_message(chat_id, "❌ Ошибка при сохранении фото")


async def handle_done_command(chat_id: int, user_id: int, db_session):
    """
    Обработка команды /done - завершение уборки
    Отправляет фото обратным сообщением с AI подписью (тестовый режим)
    """
    logger.info(f"[telegram_cleaning_bot] /done command from user {user_id}")
    
    try:
        session = get_or_create_session(user_id)
        
        if not session.selected_house_id or not session.photos:
            await send_message(
                chat_id,
                "⚠️ Нет данных для отправки.\n"
                "Используйте /start чтобы выбрать дом и загрузить фото."
            )
            return
        
        await send_message(chat_id, "⏳ Обрабатываю фото и генерирую подпись...")
        
        # Импорт внутри функции чтобы избежать циклической зависимости
        from app.services.photo_caption_service import format_cleaning_completion_message
        
        # Генерируем AI подпись с номером бригады
        brigade_number = session.brigade_id.replace("brigade_", "") if session.brigade_id else "1"
        
        caption = await format_cleaning_completion_message(
            address=session.selected_house_address,
            photo_count=len(session.photos),
            cleaning_type="Влажная уборка",  # TODO: получить из БД
            brigade_number=brigade_number,  # Тестовый режим: "1"
            use_ai=True
        )
        
        logger.info(f"[telegram_cleaning_bot] Generated caption for {session.selected_house_address}")
        
        # ПРОДАКШЕН РЕЖИМ: Отправляем в Telegram группу
        target_chat_id = os.getenv('TELEGRAM_TARGET_CHAT_ID')
        
        if target_chat_id:
            # Отправляем в группу
            logger.info(f"[telegram_cleaning_bot] Sending to group: {target_chat_id}")
            if len(session.photos) == 1:
                await send_photo(target_chat_id, session.photos[0], caption)
            else:
                await send_media_group(target_chat_id, session.photos, caption)
            
            sent_to_group = True
        else:
            # Fallback: отправляем обратно пользователю (тестовый режим)
            logger.warning("[telegram_cleaning_bot] TELEGRAM_TARGET_CHAT_ID not set, sending to user")
            if len(session.photos) == 1:
                await send_photo(chat_id, session.photos[0], caption)
            else:
                await send_media_group(chat_id, session.photos, caption)
            
            sent_to_group = False
        
        # Сохраняем в БД
        try:
            from datetime import datetime
            from app.config.database import get_db_pool
            
            db_pool = await get_db_pool()
            if db_pool:
                async with db_pool.acquire() as conn:
                    await conn.execute(
                        """
                        INSERT INTO cleaning_photos (
                            house_id, house_address, brigade_id, telegram_user_id,
                            cleaning_date, photo_file_ids, photo_count, ai_caption,
                            status, sent_to_group_at
                        ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10)
                        ON CONFLICT (house_id, cleaning_date, brigade_id) 
                        DO UPDATE SET
                            photo_file_ids = EXCLUDED.photo_file_ids,
                            photo_count = EXCLUDED.photo_count,
                            ai_caption = EXCLUDED.ai_caption,
                            status = EXCLUDED.status,
                            sent_to_group_at = EXCLUDED.sent_to_group_at,
                            updated_at = NOW()
                        """,
                        session.selected_house_id,
                        session.selected_house_address,
                        session.brigade_id,
                        user_id,
                        datetime.now().date(),
                        session.photos,
                        len(session.photos),
                        caption,
                        'sent_to_group' if sent_to_group else 'uploaded',
                        datetime.now() if sent_to_group else None
                    )
                    logger.info(f"[telegram_cleaning_bot] ✅ Saved to DB: {session.selected_house_id}")
        except Exception as db_error:
            logger.error(f"[telegram_cleaning_bot] ❌ Failed to save to DB: {db_error}")
        
        # TODO: Отправить вебхук в Bitrix24
        # await send_bitrix24_webhook(
        #     house_id=session.selected_house_id,
        #     cleaning_date=datetime.now().date(),
        #     photo_count=len(session.photos)
        # )
        
        # Уведомляем об успехе
        success_msg = "✅ <b>Уборка завершена!</b>\n"
        success_msg += f"🏠 {session.selected_house_address}\n"
        success_msg += f"📸 Отправлено фото: {len(session.photos)}\n"
        if sent_to_group:
            success_msg += "📨 Отправлено в группу\n"
        success_msg += "\nСпасибо за работу! 💙"
        
        await send_message(chat_id, success_msg)
        
        # Очищаем сессию
        session.clear()
        
    except Exception as e:
        logger.error(f"[telegram_cleaning_bot] Error in handle_done_command: {e}")
        await send_message(chat_id, "❌ Ошибка при завершении уборки")
