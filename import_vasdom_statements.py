#!/usr/bin/env python3
"""
Импорт выписок ООО ВАШ ДОМ
"""
import pandas as pd
import asyncpg
import os
import asyncio
from datetime import datetime
from uuid import uuid4
import re

# Маппинг месяцев
MONTH_MAP = {
    1: 'Январь 2025',
    2: 'Февраль 2025',
    3: 'Март 2025',
    4: 'Апрель 2025',
    5: 'Май 2025',
    6: 'Июнь 2025',
    7: 'Июль 2025',
    8: 'Август 2025',
    9: 'Сентябрь 2025'
}

FILES = [
    '/tmp/vyp1.xlsx',
    '/tmp/vyp2.xlsx',
    '/tmp/vyp3.xlsx',
    '/tmp/vyp4.xlsx'
]

def is_internal_transfer(text):
    """Проверяет, является ли операция переводом между своими счетами"""
    if not text or pd.isna(text):
        return False
    text_lower = str(text).lower()
    return ('ваш дом' in text_lower or 
            'ооо "ваш дом"' in text_lower or 
            'ооо ваш дом' in text_lower or
            'перевод средств между счетами' in text_lower or
            'перевод между счетами' in text_lower)

def extract_counterparty(text):
    """Извлекает название контрагента из назначения платежа"""
    if not text or pd.isna(text):
        return None
    
    text = str(text).upper()
    
    # Ищем паттерны с названиями организаций
    patterns = [
        # "ЗА ООО "ЖРЭУ 21""
        r'ЗА\s+(ООО|АО|ПАО|ИП|ЗАО)\s*["\']?([^"\']+?)["\']?\s*(?:ПО|ОТ|$)',
        # "ООО "УК "Ваш Уют""
        r'(ООО|АО|ПАО|ИП|ЗАО)\s*["\']([^"\']+)["\']',
        # "ООО УК Ваш Уют"
        r'(ООО|АО|ПАО|ИП|ЗАО)\s+([А-ЯЁ][А-ЯЁа-яё\s]+?)(?:\s+ПО\s+|\s+ОТ\s+|\s+ЗА\s+|$)',
    ]
    
    for pattern in patterns:
        match = re.search(pattern, text)
        if match:
            if len(match.groups()) == 2:
                org_type = match.group(1)
                org_name = match.group(2).strip()
                counterparty = f'{org_type} "{org_name}"'
            else:
                counterparty = match.group(0).strip()
            
            # Очищаем от лишних символов
            counterparty = re.sub(r'\s+', ' ', counterparty)
            counterparty = counterparty.strip('"\'')
            
            # Приводим к нормальному регистру (первая буква заглавная)
            words = counterparty.split()
            counterparty = ' '.join([w.capitalize() if w not in ['ООО', 'АО', 'ПАО', 'ИП', 'ЗАО'] else w for w in words])
            
            if len(counterparty) > 5 and len(counterparty) < 255:
                return counterparty
    
    return None

async def import_statements():
    db_url = os.environ.get('DATABASE_URL')
    conn = await asyncpg.connect(db_url)
    
    try:
        # Удаляем старые доходы ООО ВАШ ДОМ
        await conn.execute("""
            DELETE FROM financial_transactions
            WHERE company = 'ООО ВАШ ДОМ' AND type = 'income'
        """)
        print("🗑️  Удалены старые доходы ООО ВАШ ДОМ")
        
        imported = 0
        skipped = 0
        
        for file_path in FILES:
            print(f"\n{'='*60}")
            print(f"Обработка файла: {file_path}")
            print('='*60)
            
            try:
                # Читаем файл со строки 10 (заголовки в строке 9, данные с 10)
                df = pd.read_excel(file_path, header=9)
                
                print(f"Загружено строк: {len(df)}")
                print(f"Колонки: {df.columns.tolist()[:10]}")
                
                # Ищем колонки с данными
                date_col = None
                amount_col = None
                purpose_col = None
                counterparty_col = None
                
                # Определяем тип файла (Сбербанк или Альфа)
                is_sber = 'сбербизнес' in file_path.lower() or '40702810' in file_path
                is_alpha = 'альфа' in file_path.lower() or 'выписка_40702810401710001223' in file_path
                
                for col in df.columns:
                    col_str = str(col).lower()
                    if 'дата' in col_str and not date_col:
                        date_col = col
                    if 'кредит' in col_str and 'сумма' in col_str:
                        amount_col = col
                    if 'назначение' in col_str or 'название' in col_str:
                        purpose_col = col
                    if 'контрагент' in col_str or 'название платежа' in col_str:
                        counterparty_col = col
                
                # Для Сбербанка контрагент в колонке 4 (E) - используем индекс
                sber_counterparty_idx = 4 if is_sber else None
                
                print(f"Найденные колонки:")
                print(f"  Дата: {date_col}")
                print(f"  Сумма: {amount_col}")
                print(f"  Назначение: {purpose_col}")
                print(f"  Контрагент: {counterparty_col}")
                
                if not all([date_col, amount_col]):
                    print("⚠️  Не найдены обязательные колонки, пропускаем файл")
                    continue
                
                # Обрабатываем строки
                for index, row in df.iterrows():
                    try:
                        date = row[date_col]
                        amount = row[amount_col]
                        
                        if pd.isna(date) or pd.isna(amount):
                            continue
                        
                        # Преобразуем дату
                        if isinstance(date, str):
                            date = pd.to_datetime(date, dayfirst=True)
                        if not isinstance(date, pd.Timestamp):
                            date = pd.Timestamp(date)
                        
                        python_date = date.to_pydatetime()
                        month_ru = MONTH_MAP.get(python_date.month)
                        
                        if not month_ru:
                            continue
                        
                        # Преобразуем сумму
                        amount_float = float(amount)
                        if amount_float <= 0:
                            continue
                        
                        # Получаем назначение и контрагента
                        purpose = str(row[purpose_col]) if purpose_col and pd.notna(row[purpose_col]) else ""
                        
                        # Пропускаем операции между своими счетами
                        if is_internal_transfer(purpose):
                            skipped += 1
                            continue
                        
                        # Получаем контрагента
                        if is_alpha:
                            # Для Альфа-банка фиксированный контрагент
                            counterparty = 'ООО УК "Ваш Уют"'
                        else:
                            # Для Сбербанка - из колонки
                            counterparty_raw = str(row[counterparty_col]) if counterparty_col and pd.notna(row[counterparty_col]) else ""
                            
                            if is_internal_transfer(counterparty_raw):
                                skipped += 1
                                continue
                            
                            # Извлекаем название ООО из многострочного значения
                            if counterparty_raw and len(counterparty_raw) > 5:
                                # Ищем строку с ООО/АО и т.д.
                                lines = counterparty_raw.split('\n')
                                counterparty = None
                                for line in lines:
                                    line = line.strip()
                                    if any(org_type in line.upper() for org_type in ['ООО', 'АО', 'ПАО', 'ИП', 'ЗАО']):
                                        counterparty = line
                                        break
                                
                                if not counterparty:
                                    # Берем последнюю строку если не нашли ООО
                                    counterparty = lines[-1].strip() if lines else counterparty_raw[:255]
                            else:
                                counterparty = "Контрагент не указан"
                        
                        # Определяем категорию из назначения платежа
                        purpose_lower = purpose.lower()
                        if 'уборк' in purpose_lower or 'моп' in purpose_lower:
                            category = 'Уборка'
                        elif 'шв' in purpose_lower or 'пошив' in purpose_lower:
                            category = 'Швеи'
                        elif 'аутсорс' in purpose_lower:
                            category = 'Аутсорсинг'
                        else:
                            category = 'Прочие доходы'
                        
                        # Вставляем в базу
                        transaction_id = str(uuid4())
                        query = """
                            INSERT INTO financial_transactions 
                            (id, date, amount, category, type, description, counterparty, project, company, created_at, updated_at)
                            VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
                        """
                        await conn.execute(
                            query,
                            transaction_id,
                            python_date,
                            amount_float,
                            category,
                            'income',
                            purpose[:500] if purpose else '',
                            counterparty[:255] if counterparty else '',
                            month_ru,
                            'ООО ВАШ ДОМ'
                        )
                        imported += 1
                        
                    except Exception as e:
                        print(f"Ошибка в строке {index}: {e}")
                        continue
                
            except Exception as e:
                print(f"Ошибка при чтении файла: {e}")
                continue
        
        print(f"\n{'='*60}")
        print(f"=== ИТОГО ===")
        print(f"✅ Импортировано доходов: {imported}")
        print(f"⏭️  Пропущено (внутренние переводы): {skipped}")
        print('='*60)
        
    finally:
        await conn.close()

if __name__ == '__main__':
    asyncio.run(import_statements())
