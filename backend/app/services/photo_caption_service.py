"""
Сервис для генерации AI подписей к фото уборок
Адаптирован из PostingFotoTG
"""
import os
import logging
from datetime import datetime
from typing import Optional
from openai import AsyncOpenAI

logger = logging.getLogger(__name__)

# Используем ТОЛЬКО OpenAI API ключ
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
client = AsyncOpenAI(api_key=OPENAI_API_KEY) if OPENAI_API_KEY else None


async def generate_motivational_text(address: str) -> str:
    """
    Генерирует ТОЛЬКО мотивирующий текст от GPT-4o (БЕЗ анализа фото)
    
    Args:
        address: Адрес дома
    
    Returns:
        Мотивирующий текст (3-5 предложений)
    """
    if not client:
        logger.warning("[photo_caption] OpenAI client not available, using fallback")
        return "🌟 Великолепная работа! Благодарим нашу команду за труд и внимание к деталям. Чистота в подъезде — это забота о каждом жильце. Давайте вместе делать мир чище и светлее! 💪🌿"
    
    try:
        prompt = f"""
Напиши короткий вдохновляющий текст для поста об уборке подъезда по адресу: {address}

Требования:
- Поблагодари бригаду уборщиков за работу
- Упомяни важность чистоты и заботы о доме
- Добавь мотивацию и социальную ответственность
- Используй 3-4 эмодзи (🌟, 🧹, 💪, 🌿, ✨, 🏠, 💫)
- 3-5 предложений максимум
- Тон: вдохновляющий, благодарный, мотивирующий

Примеры стиля:
"Великолепная работа! Светлый подъезд теперь сияет чистотой благодаря вашим усилиям. Спасибо за заботу о нашем общем пространстве!"
"Сегодня мы сделали мир немного чище! Благодарим уборщиков за труд и внимание. Давайте вместе делать наш город лучше!"
"""

        logger.info(f"[photo_caption] Generating motivational text with GPT-5")
        
        response = await client.chat.completions.create(
            model="gpt-5",  # Новейшая модель GPT-5
            messages=[
                {"role": "system", "content": "Ты вдохновляющий копирайтер клининговой компании ВасДом. Пишешь короткие мотивирующие тексты про уборку подъездов."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.9,  # Больше креативности
            max_tokens=200
        )
        
        text = response.choices[0].message.content.strip()
        logger.info(f"[photo_caption] Motivational text generated: {text[:60]}...")
        return text
        
    except Exception as e:
        logger.error(f"[photo_caption] Error generating motivational text: {e}", exc_info=True)
        return "🌟 Великолепная работа! Благодарим нашу команду за труд и внимание к деталям. Чистота в подъезде — это забота о каждом жильце. Давайте вместе делать мир чище и светлее! 💪🌿"


async def generate_caption(
    address: str, 
    photo_count: int = 1, 
    cleaning_type: str = None,
    brigade_number: str = None
) -> str:
    """
    Генерирует полную подпись к фото уборки в формате PostingFotoTG
    БЕЗ анализа фото, только красивый текст
    
    Args:
        address: Адрес дома
        photo_count: Количество фото
        cleaning_type: Тип уборки (влажная, подметание, и т.д.)
        brigade_number: Номер бригады
    
    Returns:
        Полная отформатированная подпись
    """
    # Форматируем текущую дату по-русски
    months_ru = {
        1: 'января', 2: 'февраля', 3: 'марта', 4: 'апреля',
        5: 'мая', 6: 'июня', 7: 'июля', 8: 'августа',
        9: 'сентября', 10: 'октября', 11: 'ноября', 12: 'декабря'
    }
    now = datetime.now()
    russian_date = f"{now.day} {months_ru[now.month]} {now.year}"
    
    # Генерируем мотивирующий текст через GPT
    motivational_text = await generate_motivational_text(address)
    
    # Формируем хештеги из адреса
    city = "Калуга"  # TODO: извлекать из адреса
    address_clean = address.replace(" ", "_").replace(",", "")
    hashtags = f"#Чистота #Благодарность #СоциальнаяОтветственность #{city}"
    
    # Собираем полную подпись
    caption_parts = [
        "🧹 Уборка завершена",
        f"🏠 Адрес: {address}",
        f"📅 Дата: {russian_date}"
    ]
    
    if brigade_number:
        caption_parts.append(f"👷 Бригада: #{brigade_number}")
    
    caption_parts.append("")  # Пустая строка
    caption_parts.append(motivational_text)
    caption_parts.append(hashtags)
    
    full_caption = "\n".join(caption_parts)
    
    logger.info(f"[photo_caption] Full caption generated for {address}")
    return full_caption


def _generate_fallback_caption(address: str, brigade_number: str = None) -> str:
    """
    Fallback подпись если AI не сработал (в стиле PostingFotoTG)
    """
    months_ru = {
        1: 'января', 2: 'февраля', 3: 'марта', 4: 'апреля',
        5: 'мая', 6: 'июня', 7: 'июля', 8: 'августа',
        9: 'сентября', 10: 'октября', 11: 'ноября', 12: 'декабря'
    }
    now = datetime.now()
    russian_date = f"{now.day} {months_ru[now.month]} {now.year}"
    
    brigade_text = f"\n👷 Бригада: #{brigade_number}" if brigade_number else ""
    
    return (
        f"🧹 Уборка завершена\n"
        f"🏠 Адрес: {address}\n"
        f"📅 Дата: {russian_date}{brigade_text}\n\n"
        f"🌟 Великолепная работа! Благодарим нашу команду за труд и внимание к деталям. "
        f"Чистота в подъезде — это забота о каждом жильце и уважение к себе. "
        f"Давайте вместе делать мир чище и светлее! 💪🌿\n"
        f"#Чистота #Благодарность #СоциальнаяОтветственность"
    )


async def format_cleaning_completion_message(
    address: str,
    photo_count: int = 1,
    cleaning_type: str = None,
    brigade_number: str = None,
    use_ai: bool = True
) -> str:
    """
    Форматирует полное сообщение о завершении уборки в стиле PostingFotoTG
    
    Args:
        address: Адрес дома
        photo_count: Количество фото
        cleaning_type: Тип уборки
        brigade_number: Номер бригады (например "1")
        use_ai: Использовать ли GPT-4o для генерации мотивирующего текста
    
    Returns:
        Полностью отформатированное сообщение
    """
    if use_ai:
        caption = await generate_caption(address, photo_count, cleaning_type, brigade_number)
    else:
        caption = _generate_fallback_caption(address, brigade_number)
    
    return caption


# Для тестирования
if __name__ == "__main__":
    import asyncio
    
    async def test():
        caption = await generate_caption(
            address="ул. Ленина, д. 10",
            photo_count=3,
            cleaning_type="Влажная уборка всех этажей"
        )
        print("Generated caption:")
        print(caption)
    
    asyncio.run(test())
