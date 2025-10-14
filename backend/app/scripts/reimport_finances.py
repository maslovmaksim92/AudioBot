"""
Скрипт правильного импорта финансовых данных из Excel файлов
"""
import asyncio
import os
import sys
import pandas as pd
import asyncpg
from datetime import datetime
from uuid import uuid4
import logging
import requests
from dotenv import load_dotenv

# Добавляем путь к корневой директории для импортов
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

# Загружаем переменные окружения
load_dotenv('/app/backend/.env')

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# URL файлов
FILE_URLS = [
    ("https://customer-assets.emergentagent.com/job_clean-works-hub/artifacts/nfd56oad_01.%D0%A0%D0%B5%D0%B5%D1%81%D1%82%D1%80%20%D1%80%D0%B0%D1%81%D1%85%D0%BE%D0%B4%D0%BE%D0%B2%20%D0%B7%D0%B0%20%D0%AF%D0%BD%D0%B2%D0%B0%D1%80%D1%8C%202025.xlsx", "Январь 2025", "Январь"),
    ("https://customer-assets.emergentagent.com/job_clean-works-hub/artifacts/u3xa9pbv_02.%D0%A0%D0%B5%D0%B5%D1%81%D1%82%D1%80%20%D1%80%D0%B0%D1%81%D1%85%D0%BE%D0%B4%D0%BE%D0%B2%20%D0%B7%D0%B0%20%D0%A4%D0%B5%D0%B2%D1%80%D0%B0%D0%BB%D1%8C%202025.xlsx", "Февраль 2025", "Февраль"),
    ("https://customer-assets.emergentagent.com/job_clean-works-hub/artifacts/oho2203i_03.%D0%A0%D0%B5%D0%B5%D1%81%D1%82%D1%80%20%D1%80%D0%B0%D1%81%D1%85%D0%BE%D0%B4%D0%BE%D0%B2%20%D0%B7%D0%B0%20%D0%9C%D0%B0%D1%80%D1%82%202025.xlsx", "Март 2025", "Март"),
    ("https://customer-assets.emergentagent.com/job_clean-works-hub/artifacts/wmtw5wo4_04.%D0%A0%D0%B5%D0%B5%D1%81%D1%82%D1%80%20%D1%80%D0%B0%D1%81%D1%85%D0%BE%D0%B4%D0%BE%D0%B2%20%D0%B7%D0%B0%20%D0%90%D0%BF%D1%80%D0%B5%D0%BB%D1%8C%202025.xlsx", "Апрель 2025", "Апрель"),
    ("https://customer-assets.emergentagent.com/job_clean-works-hub/artifacts/mtp9dsv6_05.%D0%A0%D0%B5%D0%B5%D1%81%D1%82%D1%80%20%D1%80%D0%B0%D1%81%D1%85%D0%BE%D0%B4%D0%BE%D0%B2%20%D0%B7%D0%B0%20%D0%9C%D0%B0%D0%B9%202025.xlsx", "Май 2025", "Май"),
    ("https://customer-assets.emergentagent.com/job_clean-works-hub/artifacts/pus96mnn_06.%D0%A0%D0%B5%D0%B5%D1%81%D1%82%D1%80%20%D1%80%D0%B0%D1%81%D1%85%D0%BE%D0%B4%D0%BE%D0%B2%20%D0%B7%D0%B0%20%D0%98%D1%8E%D0%BD%D1%8C%202025.xlsx", "Июнь 2025", "Июнь"),
    ("https://customer-assets.emergentagent.com/job_clean-works-hub/artifacts/v0hc2cgx_07.%D0%A0%D0%B5%D0%B5%D1%81%D1%82%D1%80%20%D1%80%D0%B0%D1%81%D1%85%D0%BE%D0%B4%D0%BE%D0%B2%20%D0%B7%D0%B0%20%D0%98%D1%8E%D0%BB%D1%8C%202025.xlsx", "Июль 2025", "Июль"),
    ("https://customer-assets.emergentagent.com/job_clean-works-hub/artifacts/p6m2dcec_08.%D0%A0%D0%B5%D0%B5%D1%81%D1%82%D1%80%20%D1%80%D0%B0%D1%81%D1%85%D0%BE%D0%B4%D0%BE%D0%B2%20%D0%B7%D0%B0%20%D0%90%D0%B2%D0%B3%D1%83%D1%81%D1%82%202025.xlsx", "Август 2025", "Август"),
    ("https://customer-assets.emergentagent.com/job_clean-works-hub/artifacts/293oqddr_09.%D0%A0%D0%B5%D0%B5%D1%81%D1%82%D1%80%20%D1%80%D0%B0%D1%81%D1%85%D0%BE%D0%B4%D0%BE%D0%B2%20%D0%B7%D0%B0%20%D0%A1%D0%B5%D0%BD%D1%82%D1%8F%D0%B1%D1%80%D1%8C%202025.xlsx", "Сентябрь 2025", "Сентябрь"),
]

# Маппинг статей расходов на категории
ARTICLE_MAPPING = {
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
    "17.001": "Лизинг",
    "17.003": "Кредиты",
}


def download_file(url, filename):
    """Скачать файл по URL"""
    try:
        response = requests.get(url, timeout=60)
        response.raise_for_status()
        
        filepath = f"/tmp/{filename}"
        with open(filepath, 'wb') as f:
            f.write(response.content)
        
        logger.info(f"Файл {filename} успешно скачан")
        return filepath
    except Exception as e:
        logger.error(f"Ошибка при скачивании {filename}: {e}")
        return None


def parse_excel_file(filepath, sheet_name, month_name):
    """Парсинг Excel файла и извлечение транзакций"""
    try:
        df = pd.read_excel(filepath, sheet_name=sheet_name)
        
        logger.info(f"Обработка листа: {sheet_name}")
        logger.info(f"Колонки: {df.columns.tolist()}")
        
        all_transactions = []
        
        # Находим колонки с расходами (они заканчиваются на .1)
        expense_columns = [col for col in df.columns if '.1' in str(col)]
        
        # Находим колонки с поступлениями (они заканчиваются на .0 или без суффикса, кроме .1 и .2)
        income_columns = [col for col in df.columns if 
                         ('Расчетный счет' in str(col) or 'Касса' in str(col) or 'РН Карт' in str(col))
                         and '.1' not in str(col) and '.2' not in str(col)]
        
        logger.info(f"Колонки расходов: {expense_columns}")
        logger.info(f"Колонки поступлений: {income_columns}")
        
        # Обрабатываем каждую строку
        for idx, row in df.iterrows():
            # Проверяем наличие даты и статьи
            if pd.isna(row.get('Дата')) or pd.isna(row.get('Номер статьи расходов')):
                continue
            
            trans_date = row['Дата']
            if not isinstance(trans_date, datetime):
                continue
            
            article = str(row.get('Номер статьи расходов', '')).strip()
            description = str(row.get('Движение денежных средств\n' + month_name.split()[0], '')).strip()
            
            # Определяем категорию
            category = ARTICLE_MAPPING.get(article, "Прочие расходы")
            
            # Собираем расходы из всех колонок
            total_expense = 0
            for col in expense_columns:
                value = row.get(col, 0)
                if pd.notna(value) and value != 0:
                    try:
                        total_expense += float(value)
                    except:
                        pass
            
            # Собираем поступления из всех колонок
            total_income = 0
            for col in income_columns:
                value = row.get(col, 0)
                if pd.notna(value) and value != 0:
                    try:
                        total_income += float(value)
                    except:
                        pass
            
            # Создаем транзакции
            if total_expense > 0:
                # Проверяем валидность статьи (исключаем разделители и пустые)
                if article and article != '----------' and article.strip():
                    # Проверяем что статья в диапазоне 1.001 - 18.006
                    try:
                        parts = article.split('.')
                        if len(parts) == 2:
                            major = int(parts[0])
                            if 1 <= major <= 18:
                                all_transactions.append({
                                    'date': trans_date,
                                    'amount': total_expense,
                                    'type': 'expense',
                                    'description': description,
                                    'article': article,
                                    'category': category,
                                    'month': month_name
                                })
                    except:
                        # Пропускаем невалидные статьи
                        pass
            
            if total_income > 0:
                # Проверяем валидность статьи для поступлений
                if article and article != '----------' and article.strip():
                    try:
                        parts = article.split('.')
                        if len(parts) == 2:
                            major = int(parts[0])
                            if 1 <= major <= 18:
                                all_transactions.append({
                                    'date': trans_date,
                                    'amount': total_income,
                                    'type': 'income',
                                    'description': description,
                                    'article': article,
                                    'category': "Поступление от покупателей",
                                    'month': month_name
                                })
                    except:
                        pass
        
        logger.info(f"Извлечено транзакций: {len(all_transactions)}")
        return all_transactions
    
    except Exception as e:
        logger.error(f"Ошибка при парсинге файла {filepath}: {e}")
        import traceback
        traceback.print_exc()
        return []


async def import_to_database(transactions):
    """Импорт транзакций в базу данных"""
    db_url = os.environ.get('DATABASE_URL', '')
    if not db_url:
        logger.error("DATABASE_URL не установлен")
        return
    
    try:
        conn = await asyncpg.connect(db_url)
        
        logger.info("Подключение к базе данных установлено")
        
        # Очищаем существующие данные за 2025 год
        deleted = await conn.execute("DELETE FROM financial_transactions WHERE project LIKE '%2025'")
        logger.info(f"Удалено старых записей: {deleted}")
        
        imported_count = 0
        
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
                    None,
                    "",
                    trans['month'],
                    [trans['article']],
                    now
                )
                
                imported_count += 1
                
                if imported_count % 100 == 0:
                    logger.info(f"Импортировано: {imported_count} транзакций")
                
            except Exception as e:
                logger.error(f"Ошибка при импорте транзакции: {e}")
        
        await conn.close()
        
        logger.info(f"Импорт завершен! Импортировано: {imported_count} транзакций")
        
    except Exception as e:
        logger.error(f"Ошибка подключения к базе данных: {e}")
        import traceback
        traceback.print_exc()


async def main():
    """Основная функция"""
    logger.info("Начало переимпорта финансовых данных")
    
    all_transactions = []
    
    for url, sheet_name, month_name in FILE_URLS:
        filename = f"expenses_{month_name}.xlsx"
        
        logger.info(f"Обработка файла: {month_name}")
        
        # Скачиваем файл
        filepath = download_file(url, filename)
        if not filepath:
            continue
        
        # Парсим файл
        transactions = parse_excel_file(filepath, sheet_name, month_name)
        all_transactions.extend(transactions)
        
        # Удаляем временный файл
        try:
            os.remove(filepath)
        except:
            pass
    
    logger.info(f"Всего транзакций для импорта: {len(all_transactions)}")
    
    # Проверяем суммы по месяцам
    from collections import defaultdict
    by_month = defaultdict(lambda: {'income': 0, 'expense': 0})
    
    for trans in all_transactions:
        by_month[trans['month']][trans['type']] += trans['amount']
    
    logger.info("\n=== Суммы по месяцам ===")
    for month, totals in by_month.items():
        logger.info(f"{month}: Доход = {totals['income']:.2f}, Расход = {totals['expense']:.2f}")
    
    # Импортируем в базу данных
    if all_transactions:
        await import_to_database(all_transactions)
    
    logger.info("Переимпорт завершен")


if __name__ == "__main__":
    asyncio.run(main())
