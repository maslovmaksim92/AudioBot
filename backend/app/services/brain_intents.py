"""
Advanced Intent detection and entity extraction for Brain (Phase 2)
Includes sophisticated NER for addresses, months, dates, and date ranges
"""
from __future__ import annotations

from typing import Any, Dict, Optional, List, Tuple
from datetime import datetime, timedelta
import re


# Словарь известных улиц (можно расширить из Bitrix24)
KNOWN_STREETS = {
    'кибальчича', 'кибальчич', 'билибина', 'билибин',
    'ленина', 'пушкина', 'гоголя', 'чехова', 'маяковского',
    'советская', 'московская', 'невский', 'тверская'
}

# Стоп-слова для фильтрации
ADDRESS_STOP_WORDS = {
    "контакт", "контакты", "старшего", "старший", "телефон", "почта", "email",
    "номер", "уборка", "уборки", "график", "когда", "где", "покажи", "нужно",
    "расписание", "даты", "дата", "в", "на", "за"
}


def normalize_address_parts(text: str) -> str:
    """Нормализовать части адреса (к1 -> к 1, стр2 -> стр 2)"""
    # к1, к2 -> к 1, к 2
    text = re.sub(r'\bк(\d+)', r'к \1', text)
    # стр1, стр2 -> стр 1, стр 2
    text = re.sub(r'\bстр(\d+)', r'стр \1', text)
    # корп1 -> корп 1
    text = re.sub(r'\bкорп\.?(\d+)', r'к \1', text)
    # литА, литА -> лит А
    text = re.sub(r'\bлит\.?([а-яa-z])', r'лит \1', text)
    # строение -> стр
    text = re.sub(r'\bстроени[ея]\b', 'стр', text)
    # корпус -> к
    text = re.sub(r'\bкорпус\b', 'к', text)
    return text.strip()


def extract_address(text: str) -> Optional[str]:
    """
    Продвинутое извлечение адреса из текста
    Поддерживает: "Кибальчича 3 стр 2", "Билибина 6 к1 лит А", "на Ленина 5"
    """
    if not text:
        return None
    
    text_lower = text.lower()
    
    # Нормализуем части адреса
    text_normalized = normalize_address_parts(text_lower)
    
    # Паттерн 1: "на <улица> <номер> [доп.части]"
    pattern1 = r'на\s+([а-яё]+(?:ого|ской|ского|ова|ева|ина|ича)?)\s+(\d+(?:\s+(?:стр|к|лит)\s*[а-яёa-z0-9]+)*)'
    match = re.search(pattern1, text_normalized)
    if match:
        street = match.group(1).strip()
        house_parts = match.group(2).strip()
        if street not in ADDRESS_STOP_WORDS:
            return f"{street} {house_parts}"
    
    # Паттерн 2: "по адресу <улица> <номер> [доп.части]"
    pattern2 = r'по\s+адресу\s+([а-яё]+(?:ого|ской|ского|ова|ева|ина|ича)?)\s+(\d+(?:\s+(?:стр|к|лит)\s*[а-яёa-z0-9]+)*)'
    match = re.search(pattern2, text_normalized)
    if match:
        street = match.group(1).strip()
        house_parts = match.group(2).strip()
        if street not in ADDRESS_STOP_WORDS:
            return f"{street} {house_parts}"
    
    # Паттерн 3: Прямое указание "<улица> <номер> [доп.части]" с проверкой известных улиц
    pattern3 = r'\b([а-яё]+(?:ого|ской|ского|ова|ева|ина|ича)?)\s+(\d+(?:\s+(?:стр|к|лит)\s*[а-яёa-z0-9]+)*)\b'
    matches = re.finditer(pattern3, text_normalized)
    for match in matches:
        street = match.group(1).strip()
        house_parts = match.group(2).strip()
        
        # Проверяем, является ли это известной улицей или подходит под паттерн
        street_base = street.rstrip('аоеиуыюя').lower()
        if (street in KNOWN_STREETS or 
            street_base in KNOWN_STREETS or
            any(known in street for known in KNOWN_STREETS)):
            if street not in ADDRESS_STOP_WORDS:
                return f"{street} {house_parts}"
    
    # Паттерн 4: Извлечение с контекстными маркерами
    # "дом на Кибальчича", "объект Билибина 6"
    pattern4 = r'(?:дом|объект|адрес|здание)\s+(?:на\s+)?([а-яё]+(?:ого|ской|ского|ова|ева|ина|ича)?)\s+(\d+(?:\s+(?:стр|к|лит)\s*[а-яёa-z0-9]+)*)'
    match = re.search(pattern4, text_normalized)
    if match:
        street = match.group(1).strip()
        house_parts = match.group(2).strip()
        if street not in ADDRESS_STOP_WORDS:
            return f"{street} {house_parts}"
    
    return None


def extract_month(text: str) -> Optional[str]:
    """
    Продвинутое извлечение месяца из текста
    Поддерживает все падежи, сокращения, числовые форматы
    Возвращает: october/november/december
    """
    if not text:
        return None
    
    text_lower = text.lower()
    
    # Словарь месяцев с различными формами
    month_patterns = {
        'october': [
            'октябр', 'окт', 'октября', 'октябре', 'октябрь', 'октябрём',
            r'\b10\b', r'\b10\.', r'10/2025', r'2025-10'
        ],
        'november': [
            'ноябр', 'ноя', 'ноября', 'ноябре', 'ноябрь', 'ноябрём',
            r'\b11\b', r'\b11\.', r'11/2025', r'2025-11'
        ],
        'december': [
            'декабр', 'дек', 'декабря', 'декабре', 'декабрь', 'декабрём',
            r'\b12\b', r'\b12\.', r'12/2025', r'2025-12'
        ]
    }
    
    # Проверяем каждый месяц
    for month_key, patterns in month_patterns.items():
        for pattern in patterns:
            if re.search(pattern, text_lower):
                return month_key
    
    return None


def extract_specific_date(text: str) -> Optional[str]:
    """
    Извлечь конкретную дату из текста
    Возвращает дату в формате YYYY-MM-DD или None
    """
    if not text:
        return None
    
    text_lower = text.lower()
    
    # Паттерн 1: ISO формат 2025-10-15
    match = re.search(r'(\d{4})-(\d{2})-(\d{2})', text)
    if match:
        return f"{match.group(1)}-{match.group(2)}-{match.group(3)}"
    
    # Паттерн 2: DD.MM.YYYY или DD.MM
    match = re.search(r'(\d{1,2})\.(\d{1,2})(?:\.(\d{4}))?', text)
    if match:
        day = match.group(1).zfill(2)
        month = match.group(2).zfill(2)
        year = match.group(3) if match.group(3) else str(datetime.now().year)
        return f"{year}-{month}-{day}"
    
    # Паттерн 3: "15 октября", "5 ноября"
    day_month_pattern = r'(\d{1,2})\s+(октября|ноября|декабря|окт|ноя|дек)'
    match = re.search(day_month_pattern, text_lower)
    if match:
        day = match.group(1).zfill(2)
        month_str = match.group(2)
        
        month_map = {
            'октября': '10', 'окт': '10',
            'ноября': '11', 'ноя': '11',
            'декабря': '12', 'дек': '12'
        }
        month = month_map.get(month_str, '01')
        year = str(datetime.now().year)
        return f"{year}-{month}-{day}"
    
    # Паттерн 4: Относительные даты
    today = datetime.now().date()
    if 'сегодня' in text_lower or 'сейчас' in text_lower:
        return today.isoformat()
    elif 'завтра' in text_lower:
        return (today + timedelta(days=1)).isoformat()
    elif 'вчера' in text_lower:
        return (today - timedelta(days=1)).isoformat()
    
    return None


def extract_date_range(text: str) -> Optional[Dict[str, Any]]:
    """
    Продвинутое извлечение диапазона дат из текста
    Возвращает: {period: str, days: int, date_from: str, date_to: str}
    """
    if not text:
        return None
    
    text_lower = text.lower()
    today = datetime.now().date()
    
    # Паттерн 1: Явные диапазоны "с 1 по 15 октября", "01.10-15.10"
    # "с DD по DD месяца"
    range_pattern1 = r'с\s+(\d{1,2})\s+по\s+(\d{1,2})\s+(октября|ноября|декабря)'
    match = re.search(range_pattern1, text_lower)
    if match:
        day_from = match.group(1).zfill(2)
        day_to = match.group(2).zfill(2)
        month_str = match.group(3)
        
        month_map = {'октября': '10', 'ноября': '11', 'декабря': '12'}
        month = month_map.get(month_str, '10')
        year = str(datetime.now().year)
        
        return {
            'period': 'custom',
            'date_from': f"{year}-{month}-{day_from}",
            'date_to': f"{year}-{month}-{day_to}",
            'days': int(day_to) - int(day_from) + 1
        }
    
    # Паттерн 2: "DD.MM-DD.MM" или "DD.MM.YYYY-DD.MM.YYYY"
    range_pattern2 = r'(\d{1,2}\.\d{1,2}(?:\.\d{4})?)\s*-\s*(\d{1,2}\.\d{1,2}(?:\.\d{4})?)'
    match = re.search(range_pattern2, text)
    if match:
        from_str = match.group(1)
        to_str = match.group(2)
        
        date_from = extract_specific_date(from_str)
        date_to = extract_specific_date(to_str)
        
        if date_from and date_to:
            df = datetime.fromisoformat(date_from)
            dt = datetime.fromisoformat(date_to)
            days = (dt - df).days + 1
            return {
                'period': 'custom',
                'date_from': date_from,
                'date_to': date_to,
                'days': days
            }
    
    # Паттерн 3: Предопределённые периоды
    if 'за месяц' in text_lower or 'последний месяц' in text_lower or 'этот месяц' in text_lower:
        date_from = (today - timedelta(days=30)).isoformat()
        return {'period': 'month', 'days': 30, 'date_from': date_from, 'date_to': today.isoformat()}
    
    elif 'за квартал' in text_lower or 'последний квартал' in text_lower or 'квартал' in text_lower:
        date_from = (today - timedelta(days=90)).isoformat()
        return {'period': 'quarter', 'days': 90, 'date_from': date_from, 'date_to': today.isoformat()}
    
    elif 'за неделю' in text_lower or 'последняя неделя' in text_lower or 'эта неделя' in text_lower:
        date_from = (today - timedelta(days=7)).isoformat()
        return {'period': 'week', 'days': 7, 'date_from': date_from, 'date_to': today.isoformat()}
    
    elif 'за год' in text_lower or 'последний год' in text_lower or 'г/г' in text_lower or 'год к году' in text_lower:
        date_from = (today - timedelta(days=365)).isoformat()
        return {'period': 'year', 'days': 365, 'date_from': date_from, 'date_to': today.isoformat()}
    
    elif 'сегодня' in text_lower:
        return {'period': 'today', 'days': 1, 'date_from': today.isoformat(), 'date_to': today.isoformat()}
    
    elif 'вчера' in text_lower:
        yesterday = (today - timedelta(days=1)).isoformat()
        return {'period': 'yesterday', 'days': 1, 'date_from': yesterday, 'date_to': yesterday}
    
    return None


def detect_intent(message: str) -> Optional[Dict[str, Any]]:
    """
    Продвинутое определение намерения пользователя с извлечением сущностей
    Использует приоритеты при множественных совпадениях
    """
    if not message:
        return None
    
    tl = message.lower()
    result = {}
    
    # Извлекаем все возможные сущности
    address = extract_address(message)
    month = extract_month(message)
    date_range = extract_date_range(message)
    specific_date = extract_specific_date(message)
    
    # Вычисляем scores для каждого типа запроса
    intent_scores = {}
    
    # 1. Контакты старшего (высокий приоритет при явном упоминании)
    elder_keywords = ["контакт", "телефон", "номер", "почта", "email", "связ"]
    elder_targets = ["старш"]
    elder_score = 0
    for kw in elder_keywords:
        if kw in tl:
            elder_score += 2
    for tg in elder_targets:
        if tg in tl:
            elder_score += 3
    if address:
        elder_score += 1
    if elder_score >= 3:
        intent_scores['elder_contact'] = elder_score
    
    # 2. График уборок (высокий приоритет при месяце + адресе)
    cleaning_keywords = ["уборк", "график", "расписан", "когда", "дат"]
    cleaning_score = 0
    for kw in cleaning_keywords:
        if kw in tl:
            cleaning_score += 2
    if month:
        cleaning_score += 3
    if address:
        cleaning_score += 2
    if cleaning_score >= 2:
        intent_scores['cleaning_month'] = cleaning_score
    
    # 3. Бригада по адресу
    brigade_keywords = ["бригад", "кто убирает", "какая команда"]
    brigade_score = 0
    for kw in brigade_keywords:
        if kw in tl:
            brigade_score += 3
    if address:
        brigade_score += 2
    if brigade_score >= 3:
        intent_scores['brigade'] = brigade_score
    
    # 4. Структурные суммы (квартиры, этажи, подъезды, дома)
    structural_keywords = ["квартир", "этаж", "подъезд", "сколько домов", "всего", "статистика"]
    structural_score = 0
    for kw in structural_keywords:
        if kw in tl:
            structural_score += 2
    if structural_score >= 2:
        intent_scores['structural_totals'] = structural_score
    
    # 5. Финансы - год к году (наивысший приоритет среди финансов)
    if any(k in tl for k in ["yoy", "г/г", "год к году", "годовая динамика"]):
        intent_scores['finance_yoy'] = 10
    
    # 6. Финансы - месяц к месяцу
    if any(k in tl for k in ["м/м", "месяц к месяц", "месячная динамика"]) and not any(k in tl for k in ["г/г", "год"]):
        intent_scores['finance_mom'] = 9
    
    # 7. Финансы - тренды категорий
    trend_keywords = ["топ", "рост", "падени", "лидеры", "просели", "тренд"]
    if any(k in tl for k in trend_keywords):
        intent_scores['finance_cat_trends'] = 8
    
    # 8. Финансы - разбивка по категориям
    breakdown_keywords = ["категори", "разбивк", "по категор", "структура расходов"]
    if any(k in tl for k in breakdown_keywords):
        intent_scores['finance_breakdown'] = 7
    
    # 9. Финансы - базовые (самый низкий приоритет среди финансов)
    finance_basic_keywords = ["финанс", "деньги", "баланс", "прибыль", "доход", "расход"]
    finance_basic_score = 0
    for kw in finance_basic_keywords:
        if kw in tl:
            finance_basic_score += 1
    # Исключаем, если есть более специфичные финансовые запросы
    if finance_basic_score >= 1 and not any(k in ['finance_yoy', 'finance_mom', 'finance_cat_trends', 'finance_breakdown'] for k in intent_scores.keys()):
        intent_scores['finance_basic'] = 5
    
    # 10. Контакты подрядчиков/УК
    contractor_keywords = ["подрядчик", "управляющ", "компани", "ук", "контакты ук"]
    contractor_score = 0
    for kw in contractor_keywords:
        if kw in tl:
            contractor_score += 2
    if contractor_score >= 2:
        intent_scores['contractor_contacts'] = 6
    
    # 11. Задачи/жалобы по адресу
    if any(k in tl for k in ["задач", "жалоб", "заявк", "проблем"]):
        tasks_score = 4
        if address:
            tasks_score += 2
        if any(k in tl for k in ["по адресу", "на доме", "объект"]):
            tasks_score += 1
        if tasks_score >= 4:
            intent_scores['tasks_by_address'] = tasks_score
    
    # 12. Задачи по бригаде
    if any(k in tl for k in ["задач", "жалоб", "заявк"]) and any(k in tl for k in ["бригад", "у бригады"]):
        intent_scores['tasks_by_brigade'] = 7
    
    # Выбираем intent с наивысшим score
    if not intent_scores:
        return None
    
    best_intent = max(intent_scores.items(), key=lambda x: x[1])
    result['type'] = best_intent[0]
    result['confidence'] = best_intent[1]
    
    # Добавляем извлечённые сущности
    if address:
        result['address'] = address
    if month:
        result['month'] = month
    if date_range:
        result['date_range'] = date_range
    if specific_date:
        result['specific_date'] = specific_date
    
    return result