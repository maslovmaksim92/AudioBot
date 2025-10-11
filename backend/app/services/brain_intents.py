"""
Intent detection and entity extraction for Brain
"""
from __future__ import annotations

from typing import Any, Dict, Optional, List
import re


def extract_address(text: str) -> Optional[str]:
    """Извлечь адрес из текста"""
    if not text:
        return None
    
    text_lower = text.lower()
    
    # Стоп-слова для фильтрации
    stop_words = {
        "контакт", "контакты", "старшего", "старший", "телефон", "почта", "email",
        "номер", "уборка", "уборки", "график", "когда", "где", "покажи", "нужно"
    }
    
    # Паттерн 1: "на <адрес>"
    match = re.search(r'на\s+([а-яё]+\s+\d+[а-яёa-z\s]*?)(?:\s+в\s+|\s+за\s+|\?|!|\.|\s+октяб|\s+нояб|\s+декаб|$)', text_lower)
    if match:
        addr = match.group(1).strip()
        # Очистка от стоп-слов
        tokens = addr.split()
        filtered = [t for t in tokens if t not in stop_words]
        if len(filtered) >= 2:  # хотя бы улица + номер
            return ' '.join(filtered)
    
    # Паттерн 2: "по адресу <адрес>"
    match = re.search(r'по\s+адресу\s+([а-яё]+\s+\d+[а-яёa-z\s]*?)(?:\s+в\s+|\s+за\s+|\?|!|\.|\s+октяб|\s+нояб|\s+декаб|$)', text_lower)
    if match:
        addr = match.group(1).strip()
        tokens = addr.split()
        filtered = [t for t in tokens if t not in stop_words]
        if len(filtered) >= 2:
            return ' '.join(filtered)
    
    # Паттерн 3: Поиск улица + номер дома (без предлогов)
    # Формат: "<улица> <число>[буквы] [стр|к|корп|лит <число/буква>]"
    match = re.search(r'([а-яё]+(?:ча|ча|на|на|ова|ева|ина|ской|ского|кого|ной|ого)?)\s+(\d+[а-яёa-z]*(?:\s+(?:стр|к|корп|корпус|строение|лит|литера)\.?\s*[а-яёa-z0-9]+)?)', text_lower)
    if match:
        street = match.group(1)
        house_num = match.group(2)
        if street not in stop_words:
            return f"{street} {house_num}".strip()
    
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