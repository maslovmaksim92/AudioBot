"""
Скрипт импорта финансовых данных из Excel файлов
"""
import asyncio
import os
import sys
import pandas as pd
import asyncpg
from datetime import datetime
from uuid import uuid4
import logging
import re
import requests

# Добавляем путь к корневой директории для импортов
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# URL файлов
FILE_URLS = [
    "https://customer-assets.emergentagent.com/job_clean-works-hub/artifacts/nfd56oad_01.%D0%A0%D0%B5%D0%B5%D1%81%D1%82%D1%80%20%D1%80%D0%B0%D1%81%D1%85%D0%BE%D0%B4%D0%BE%D0%B2%20%D0%B7%D0%B0%20%D0%AF%D0%BD%D0%B2%D0%B0%D1%80%D1%8C%202025.xlsx",
    "https://customer-assets.emergentagent.com/job_clean-works-hub/artifacts/u3xa9pbv_02.%D0%A0%D0%B5%D0%B5%D1%81%D1%82%D1%80%20%D1%80%D0%B0%D1%81%D1%85%D0%BE%D0%B4%D0%BE%D0%B2%20%D0%B7%D0%B0%20%D0%A4%D0%B5%D0%B2%D1%80%D0%B0%D0%BB%D1%8C%202025.xlsx",
    "https://customer-assets.emergentagent.com/job_clean-works-hub/artifacts/oho2203i_03.%D0%A0%D0%B5%D0%B5%D1%81%D1%82%D1%80%20%D1%80%D0%B0%D1%81%D1%85%D0%BE%D0%B4%D0%BE%D0%B2%20%D0%B7%D0%B0%20%D0%9C%D0%B0%D1%80%D1%82%202025.xlsx",
    "https://customer-assets.emergentagent.com/job_clean-works-hub/artifacts/wmtw5wo4_04.%D0%A0%D0%B5%D0%B5%D1%81%D1%82%D1%80%20%D1%80%D0%B0%D1%81%D1%85%D0%BE%D0%B4%D0%BE%D0%B2%20%D0%B7%D0%B0%20%D0%90%D0%BF%D1%80%D0%B5%D0%BB%D1%8C%202025.xlsx",
    "https://customer-assets.emergentagent.com/job_clean-works-hub/artifacts/mtp9dsv_05.%D0%A0%D0%B5%D0%B5%D1%81%D1%82%D1%80%20%D1%80%D0%B0%D1%81%D1%85%D0%BE%D0%B4%D0%BE%D0%B2%20%D0%B7%D0%B0%20%D0%9C%D0%B0%D0%B9%202025.xlsx"
]

# Маппинг статей расходов на категории
CATEGORY_MAPPING = {
    # Административно-хозяйственные
    "1.001": "Аренда",
    "1.101": "Покупка авто",
    "1.104": "Продукты питания",
    "1.109": "Цифровая техника",
    "1.006": "Мобильная связь",
    "1.007": "Мобильная связь",
    
    # Рекламные
    "3.001": "Реклама и маркетинг",
    "3.004": "Реклама и маркетинг",
    "3.005": "Реклама и маркетинг",
    
    # Аутсорсинг
    "4.001": "Аутсорсинг",
    "4.102": "Канцтовары",
    "4.103": "Юридические услуги",
    
    # Транспортные
    "9.001": "Транспорт",
    "9.007": "Транспорт",
    "9.008": "Транспорт",
    "9.009": "Транспорт",
    "9.012": "Транспорт",
    "9.013": "Реклама и маркетинг",
    
    # Расходные
    "11.002": "Материалы",
    "11.003": "Материалы",
    "11.004": "Материалы",
    "11.005": "Коммунальные услуги",
    
    # Производственные
    "13.002": "Зарплата",
    "16.001": "Зарплата",
    "16.002": "Зарплата",
    "16.003": "Зарплата",
    
    # Долговые
    "17.001": "Лизинг",
    "17.003": "Кредиты",
}

DEFAULT_CATEGORY_MAPPING = {
    "зп": "Зарплата",
    "зарплата": "Зарплата",
    "оплата труда": "Зарплата",
    "аренда": "Аренда",
    "материал": "Материалы",
    "расходник": "Материалы",
    "химия": "Материалы",
    "запчаст": "Транспорт",
    "гсм": "Транспорт",
    "топливо": "Транспорт",
    "коммунальн": "Коммунальные услуги",
    "реклама": "Реклама и маркетинг",
    "налог": "Налоги",
    "страхован": "Страхование",
    "уборщик": "Зарплата",
    "покупка авто": "Оборудование",
}


def normalize_date(date_str):
    """Нормализация различных форматов дат"""
    if pd.isna(date_str):
        return None
    
    if isinstance(date_str, datetime):
        return date_str
    
    date_str = str(date_str).strip()
    
    # Попытки распарсить разные форматы
    formats = [
        "%d.%m.%Y",
        "%d.%m.%y",
        "%Y-%m-%d",
        "%d/%m/%Y",
        "%d/%m/%y"
    ]
    
    # Убираем "г." в конце
    date_str = re.sub(r'г\.$', '', date_str).strip()
    
    for fmt in formats:
        try:
            return datetime.strptime(date_str, fmt)
        except ValueError:
            continue
    
    logger.warning(f"Не удалось распарсить дату: {date_str}")
    return None


def normalize_amount(amount_str):
    """Нормализация суммы"""
    if pd.isna(amount_str):
        return 0.0
    
    if isinstance(amount_str, (int, float)):
        return float(amount_str)
    
    # Убираем пробелы и заменяем запятую на точку
    amount_str = str(amount_str).strip().replace(' ', '').replace(',', '.')
    
    try:
        return float(amount_str)
    except ValueError:
        logger.warning(f"Не удалось распарсить сумму: {amount_str}")
        return 0.0


def determine_category(row):
    """Определить категорию на основе данных строки"""
    # Проверяем номер статьи расходов
    article_num = str(row.get('Номер статьи расходов', '')).strip()
    if article_num in CATEGORY_MAPPING:
        return CATEGORY_MAPPING[article_num]
    
    # Проверяем наименование
    name = str(row.get('Наименование', '')).lower()
    for keyword, category in DEFAULT_CATEGORY_MAPPING.items():
        if keyword in name:
            return category
    
    # Проверяем содержание операции
    content = str(row.get('Содержание операции', '')).lower()
    for keyword, category in DEFAULT_CATEGORY_MAPPING.items():
        if keyword in content:
            return category
    
    return "Прочие расходы"


def download_file(url, filename):
    """Скачать файл по URL"""
    try:
        response = requests.get(url, timeout=30)
        response.raise_for_status()
        
        filepath = f"/tmp/{filename}"
        with open(filepath, 'wb') as f:
            f.write(response.content)
        
        logger.info(f"Файл {filename} успешно скачан")
        return filepath
    except Exception as e:
        logger.error(f"Ошибка при скачивании {filename}: {e}")
        return None


def parse_excel_file(filepath, month_name):
    """Парсинг Excel файла и извлечение транзакций"""
    try:
        # Читаем все листы файла
        xls = pd.ExcelFile(filepath)
        all_transactions = []
        
        for sheet_name in xls.sheet_names:
            logger.info(f"Обработка листа: {sheet_name}")
            df = pd.read_excel(filepath, sheet_name=sheet_name)
            
            # Ищем колонки с данными
            # Пробуем найти основные колонки
            possible_columns = {
                'date': ['Дата', 'дата', 'Date'],
                'counterparty': ['Контрагент', 'контрагент', 'Counterparty'],
                'content': ['Содержание операции', 'содержание', 'Content', 'Описание'],
                'article': ['Номер статьи расходов', 'статья', 'Article'],
                'amount': ['Сумма', 'сумма', 'Amount'],
                'expense': ['Расход', 'расход', 'Expense'],
                'income': ['Поступление', 'поступление', 'Income'],
                'name': ['Наименование', 'наименование', 'Name']
            }
            
            # Создаем маппинг колонок
            column_map = {}
            for key, variants in possible_columns.items():
                for col in df.columns:
                    if any(variant in str(col) for variant in variants):
                        column_map[key] = col
                        break
            
            logger.info(f"Найденные колонки: {column_map}")
            
            # Извлекаем транзакции
            for idx, row in df.iterrows():
                # Пропускаем пустые строки
                if row.isna().all():
                    continue
                
                date_col = column_map.get('date')
                if not date_col or pd.isna(row.get(date_col)):
                    continue
                
                transaction_date = normalize_date(row.get(date_col))
                if not transaction_date:
                    continue
                
                # Определяем сумму и тип
                expense = normalize_amount(row.get(column_map.get('expense', ''), 0))
                income = normalize_amount(row.get(column_map.get('income', ''), 0))
                
                # Если есть только "Сумма", пытаемся определить по знаку
                if expense == 0 and income == 0:
                    amount = normalize_amount(row.get(column_map.get('amount', ''), 0))
                    if amount < 0:
                        expense = abs(amount)
                    elif amount > 0:
                        income = amount
                
                if expense == 0 and income == 0:
                    continue
                
                trans_type = "expense" if expense > 0 else "income"
                trans_amount = expense if expense > 0 else income
                
                transaction = {
                    'date': transaction_date,
                    'amount': trans_amount,
                    'type': trans_type,
                    'counterparty': str(row.get(column_map.get('counterparty', ''), '')).strip(),
                    'description': str(row.get(column_map.get('content', ''), '')).strip(),
                    'article': str(row.get(column_map.get('article', ''), '')).strip(),
                    'name': str(row.get(column_map.get('name', ''), '')).strip(),
                    'category': None,
                    'month': month_name
                }
                
                # Определяем категорию
                transaction['category'] = determine_category(transaction)
                
                all_transactions.append(transaction)
        
        logger.info(f"Извлечено транзакций из файла: {len(all_transactions)}")
        return all_transactions
    
    except Exception as e:
        logger.error(f"Ошибка при парсинге файла {filepath}: {e}")
        return []


async def import_to_database(transactions):
    """Импорт транзакций в базу данных"""
    db_url = os.environ.get('DATABASE_URL', '')
    if not db_url:
        logger.error("DATABASE_URL не установлен")
        return
    
    # Преобразуем URL для asyncpg
    db_url = db_url.replace('postgresql+asyncpg://', 'postgresql://')
    
    try:
        conn = await asyncpg.connect(db_url)
        
        # Очищаем существующие данные (опционально)
        # await conn.execute("TRUNCATE TABLE financial_transactions")
        # logger.info("Таблица очищена")
        
        imported_count = 0
        skipped_count = 0
        
        for trans in transactions:
            try:
                transaction_id = str(uuid4())
                now = datetime.now()
                
                await conn.execute("""
                    INSERT INTO financial_transactions 
                    (id, date, amount, category, type, description, payment_method, 
                     counterparty, project, tags, created_at)
                    VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11)
                """, 
                    transaction_id,
                    trans['date'],
                    trans['amount'],
                    trans['category'],
                    trans['type'],
                    trans['description'],
                    None,  # payment_method
                    trans['counterparty'],
                    trans['month'],  # используем месяц как project
                    [trans['article'], trans['name']],  # tags
                    now
                )
                
                imported_count += 1
                
            except Exception as e:
                logger.error(f"Ошибка при импорте транзакции: {e}")
                skipped_count += 1
        
        await conn.close()
        
        logger.info(f"Импортировано: {imported_count}, пропущено: {skipped_count}")
        
    except Exception as e:
        logger.error(f"Ошибка подключения к базе данных: {e}")


async def main():
    """Основная функция"""
    logger.info("Начало импорта финансовых данных")
    
    months = ["Январь 2025", "Февраль 2025", "Март 2025", "Апрель 2025", "Май 2025"]
    all_transactions = []
    
    for idx, url in enumerate(FILE_URLS):
        month_name = months[idx]
        filename = f"expenses_{idx + 1}.xlsx"
        
        logger.info(f"Обработка файла: {month_name}")
        
        # Скачиваем файл
        filepath = download_file(url, filename)
        if not filepath:
            continue
        
        # Парсим файл
        transactions = parse_excel_file(filepath, month_name)
        all_transactions.extend(transactions)
        
        # Удаляем временный файл
        try:
            os.remove(filepath)
        except:
            pass
    
    logger.info(f"Всего транзакций для импорта: {len(all_transactions)}")
    
    # Импортируем в базу данных
    if all_transactions:
        await import_to_database(all_transactions)
    
    logger.info("Импорт завершен")


if __name__ == "__main__":
    asyncio.run(main())
