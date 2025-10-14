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
    # Проверяем номер статьи из tags
    if tags and len(tags) > 0:
        article = str(tags[0]).strip()
        
        # Маппинг статей расходов на категории
        article_mapping = {
            "1.001": "Аренда",
            "1.101": "Покупка авто",
            "1.104": "Продукты питания",
            "1.109": "Цифровая техника",
            "1.006": "Мобильная связь",
            "1.007": "Мобильная связь",
            "3.001": "Реклама и маркетинг",
            "3.004": "Реклама и маркетинг",
            "3.005": "Реклама и маркетинг",
            "4.001": "Аутсорсинг",
            "4.102": "Канцтовары",
            "4.103": "Юридические услуги",
            "9.001": "Транспорт",
            "9.007": "Транспорт",
            "9.008": "Транспорт",
            "9.009": "Транспорт",
            "9.012": "Транспорт",
            "9.013": "Реклама и маркетинг",
            "11.002": "Материалы",
            "11.003": "Материалы",
            "11.004": "Материалы",
            "11.005": "Коммунальные услуги",
            "11.006": "Коммунальные услуги",
            "13.002": "Зарплата",
            "16.001": "Зарплата",
            "16.002": "Зарплата",
            "16.003": "Зарплата",
            "16.004": "Зарплата",
            "16.005": "Зарплата",
            "16.006": "Зарплата",
            "17.001": "Лизинг",
            "17.003": "Кредиты",
        }
        
        if article in article_mapping:
            return article_mapping[article]
    
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
