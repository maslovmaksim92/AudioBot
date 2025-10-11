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
    """Извлечь месяц из текста (october/november/december)"""
    if not text:
        return None
    
    text_lower = text.lower()
    
    if any(k in text_lower for k in ['октябр', 'окт']):
        return 'october'
    elif any(k in text_lower for k in ['ноябр', 'ноя']):
        return 'november'
    elif any(k in text_lower for k in ['декабр', 'дек']):
        return 'december'
    
    return None


def extract_date_range(text: str) -> Optional[Dict[str, str]]:
    """Извлечь диапазон дат из текста"""
    if not text:
        return None
    
    # Паттерны: "за месяц", "за квартал", "за неделю"
    text_lower = text.lower()
    
    if 'за месяц' in text_lower or 'месяц' in text_lower:
        return {'period': 'month', 'days': 30}
    elif 'за квартал' in text_lower or 'квартал' in text_lower:
        return {'period': 'quarter', 'days': 90}
    elif 'за неделю' in text_lower or 'неделю' in text_lower:
        return {'period': 'week', 'days': 7}
    elif 'за год' in text_lower or 'год' in text_lower or 'г/г' in text_lower:
        return {'period': 'year', 'days': 365}
    
    return None


def detect_intent(message: str) -> Optional[Dict[str, Any]]:
    """Определить намерение пользователя и извлечь сущности"""
    if not message:
        return None
    
    tl = message.lower()
    result = {}
    
    # Извлекаем сущности
    address = extract_address(message)
    month = extract_month(message)
    date_range = extract_date_range(message)
    
    # Определяем тип запроса
    
    # 1. Контакты старшего
    if any(k in tl for k in ["контакт", "телефон", "номер", "почта", "email"]) and any(k in tl for k in ["старш"]):
        result['type'] = 'elder_contact'
        if address:
            result['address'] = address
        return result
    
    # 2. График уборок
    if any(k in tl for k in ["уборк", "график", "расписан", "когда", "дат"]):
        result['type'] = 'cleaning_month'
        if address:
            result['address'] = address
        if month:
            result['month'] = month
        return result
    
    # 3. Бригада по адресу
    if any(k in tl for k in ["бригад", "какая бригада", "кто убирает"]):
        result['type'] = 'brigade'
        if address:
            result['address'] = address
        return result
    
    # 4. Структурные суммы (квартиры, этажи, подъезды)
    if any(k in tl for k in ["квартир", "этаж", "подъезд", "сколько домов", "всего"]):
        result['type'] = 'structural_totals'
        if address:
            result['address'] = address
        return result
    
    # 5. Финансы - базовые
    if any(k in tl for k in ["финанс", "деньги", "баланс", "прибыль"]) and not any(k in tl for k in ["категори", "разбивк", "м/м", "г/г"]):
        result['type'] = 'finance_basic'
        if date_range:
            result['date_range'] = date_range
        return result
    
    # 6. Финансы - разбивка по категориям
    if any(k in tl for k in ["категори", "разбивк", "по категор"]):
        result['type'] = 'finance_breakdown'
        if date_range:
            result['date_range'] = date_range
        return result
    
    # 7. Финансы - месяц к месяцу
    if any(k in tl for k in ["м/м", "месяц к месяц", "динамик"]) and not any(k in tl for k in ["г/г", "год"]):
        result['type'] = 'finance_mom'
        return result
    
    # 8. Финансы - год к году
    if any(k in tl for k in ["yoy", "г/г", "год к году"]):
        result['type'] = 'finance_yoy'
        return result
    
    # 9. Финансы - тренды категорий
    if any(k in tl for k in ["топ", "рост", "падени", "лидеры", "просели", "тренд"]):
        result['type'] = 'finance_cat_trends'
        return result
    
    return None