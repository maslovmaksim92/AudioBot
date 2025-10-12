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

# Используем Emergent LLM key или OpenAI key
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY', os.getenv('EMERGENT_LLM_KEY'))
client = AsyncOpenAI(api_key=OPENAI_API_KEY) if OPENAI_API_KEY else None


async def generate_caption(address: str, photo_count: int = 1, cleaning_type: str = None) -> str:
    """
    Генерирует вдохновляющую AI подпись к фото уборки
    
    Args:
        address: Адрес дома
        photo_count: Количество фото
        cleaning_type: Тип уборки (влажная, подметание, и т.д.)
    
    Returns:
        Строка с AI-сгенерированной подписью
    """
    if not client:
        logger.warning("[photo_caption] OpenAI client not available, using fallback")
        return _generate_fallback_caption(address, photo_count, cleaning_type)
    
    try:
        # Форматируем текущую дату по-русски
        months_ru = {
            1: 'января', 2: 'февраля', 3: 'марта', 4: 'апреля',
            5: 'мая', 6: 'июня', 7: 'июля', 8: 'августа',
            9: 'сентября', 10: 'октября', 11: 'ноября', 12: 'декабря'
        }
        now = datetime.now()
        russian_date = f"{now.day} {months_ru[now.month]} {now.year}"
        
        # Готовим промпт для GPT
        cleaning_info = f"Тип уборки: {cleaning_type}" if cleaning_type else "Стандартная уборка"
        photo_info = f"Фотоотчёт: {photo_count} фото" if photo_count > 1 else "Фотоотчёт"
        
        prompt = f"""
Вы — бот компании ВасДом по уборке подъездов. Напишите короткий вдохновляющий текст к фотоотчёту об уборке.

Адрес: {address}
{cleaning_info}
{photo_info}
Дата: {russian_date}

Требования:
- Упомяните чистоту, порядок и заботу о доме
- Добавьте благодарность бригаде
- Намекните на социальную ответственность и комфорт жильцов
- Используйте 2-3 подходящих эмодзи
- Максимум 3-4 предложения
- Тон: дружелюбный и профессиональный
"""

        logger.info(f"[photo_caption] Generating caption for address: {address}")
        
        response = await client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "Ты вдохновляющий помощник клининговой компании ВасДом. Пишешь короткие профессиональные тексты к фото уборок."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.8,
            max_tokens=200
        )
        
        text = response.choices[0].message.content.strip()
        logger.info(f"[photo_caption] AI caption generated successfully: {text[:50]}...")
        return text
        
    except Exception as e:
        logger.warning(f"[photo_caption] Error generating AI caption: {e}, using fallback")
        return _generate_fallback_caption(address, photo_count, cleaning_type)


def _generate_fallback_caption(address: str, photo_count: int, cleaning_type: str = None) -> str:
    """
    Fallback подпись если AI не сработал
    """
    months_ru = {
        1: 'января', 2: 'февраля', 3: 'марта', 4: 'апреля',
        5: 'мая', 6: 'июня', 7: 'июля', 8: 'августа',
        9: 'сентября', 10: 'октября', 11: 'ноября', 12: 'декабря'
    }
    now = datetime.now()
    russian_date = f"{now.day} {months_ru[now.month]} {now.year}"
    
    type_text = f"\n🧹 {cleaning_type}" if cleaning_type else ""
    photos_text = f" ({photo_count} фото)" if photo_count > 1 else ""
    
    return (
        f"✨ Уборка завершена успешно!{photos_text}\n"
        f"🏠 Адрес: {address}\n"
        f"📅 Дата: {russian_date}{type_text}\n\n"
        f"Спасибо нашей бригаде за чистоту и заботу о вашем доме! 💙"
    )


async def format_cleaning_completion_message(
    address: str,
    photo_count: int,
    cleaning_type: str = None,
    brigade_name: str = None,
    use_ai: bool = True
) -> str:
    """
    Форматирует полное сообщение о завершении уборки
    
    Args:
        address: Адрес дома
        photo_count: Количество фото
        cleaning_type: Тип уборки
        brigade_name: Название бригады
        use_ai: Использовать ли AI для генерации текста
    
    Returns:
        Полностью отформатированное сообщение
    """
    # Генерируем AI текст или используем fallback
    if use_ai:
        ai_text = await generate_caption(address, photo_count, cleaning_type)
    else:
        ai_text = _generate_fallback_caption(address, photo_count, cleaning_type)
    
    # Добавляем информацию о бригаде если есть
    if brigade_name:
        ai_text += f"\n\n👷 Бригада: {brigade_name}"
    
    return ai_text


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
