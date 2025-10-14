"""
Скрипт для обновления категорий транзакций
"""
import asyncio
import os
import asyncpg
from dotenv import load_dotenv
import logging

load_dotenv('/app/backend/.env')

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Маппинг ключевых слов на категории
CATEGORY_KEYWORDS = {
    "Зарплата": ["зп", "зарплат", "оплата труд", "самозанят", "работник", "уборщик"],
    "Материалы": ["материал", "расходник", "химия", "канцтовар", "хозяйственн"],
    "Транспорт": ["запчаст", "гсм", "топливо", "бензин", "масло", "шиномонтаж", "автомойка"],
    "Аренда": ["аренда"],
    "Коммунальные услуги": ["коммунальн", "жкх", "электричеств", "вода", "отопление", "газ"],
    "Реклама и маркетинг": ["реклам", "маркетинг", "продвижени"],
    "Налоги": ["налог", "ндфл", "страхов"],
    "Оборудование": ["оборудован", "инвентар", "инструмент", "техник"],
    "Покупка авто": ["покупка авто", "автомобил", "машин"],
    "Юридические услуги": ["юридическ", "правов"],
    "Аутсорсинг": ["аутсорс"],
    "Лизинг": ["лизинг"],
    "Кредиты": ["кредит", "займ"],
    "Мобильная связь": ["связь", "интернет", "телефон"],
    "Продукты питания": ["продукт", "питание", "еда"],
}


def categorize_transaction(description, counterparty, tags):
    """Определить категорию на основе данных транзакции"""
    # Объединяем все текстовые поля
    text = f"{description} {counterparty} {' '.join(tags if tags else [])}".lower()
    
    # Проверяем ключевые слова
    for category, keywords in CATEGORY_KEYWORDS.items():
        for keyword in keywords:
            if keyword in text:
                return category
    
    return "Прочие расходы"


async def main():
    """Основная функция"""
    db_url = os.environ.get('DATABASE_URL', '')
    if not db_url:
        logger.error("DATABASE_URL не установлен")
        return
    
    try:
        conn = await asyncpg.connect(db_url)
        logger.info("Подключение к базе данных установлено")
        
        # Получаем все транзакции
        rows = await conn.fetch("""
            SELECT id, description, counterparty, tags, category
            FROM financial_transactions
        """)
        
        logger.info(f"Найдено транзакций: {len(rows)}")
        
        updated_count = 0
        
        for row in rows:
            new_category = categorize_transaction(
                row['description'] or '',
                row['counterparty'] or '',
                row['tags'] or []
            )
            
            if new_category != row['category']:
                await conn.execute("""
                    UPDATE financial_transactions
                    SET category = $1
                    WHERE id = $2
                """, new_category, row['id'])
                updated_count += 1
            
            if updated_count % 100 == 0 and updated_count > 0:
                logger.info(f"Обновлено: {updated_count} транзакций")
        
        await conn.close()
        
        logger.info(f"Обновление завершено! Обновлено: {updated_count} транзакций")
        
    except Exception as e:
        logger.error(f"Ошибка: {e}")


if __name__ == "__main__":
    asyncio.run(main())
