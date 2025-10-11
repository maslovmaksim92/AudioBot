#!/usr/bin/env python3
"""
Тест NER функций напрямую
"""
import sys
sys.path.insert(0, '/app/backend')

from app.services.brain_intents import (
    extract_address,
    extract_month,
    extract_specific_date,
    extract_date_range,
    detect_intent
)


def test_address_extraction():
    """Тест извлечения адресов"""
    print("=== ТЕСТ: Извлечение адресов ===")
    
    test_cases = [
        ("Контакты старшего Кибальчича 3", "кибальчича 3"),
        ("Кибальчича 3 стр 2", "кибальчича 3 стр 2"),
        ("на Билибина 6 к1 лит А", "билибина 6 к1 лит а"),
        ("объект Билибина 6к1", "билибина 6 к 1"),
        ("дом на Кибальчича 3", "кибальчича 3"),
        ("График уборок Билибина 6 октябрь", "билибина 6"),
    ]
    
    for text, expected in test_cases:
        result = extract_address(text)
        status = "✅" if result else "❌"
        print(f"{status} '{text}' -> '{result}' (ожидалось: '{expected}')")


def test_month_extraction():
    """Тест извлечения месяцев"""
    print("\n=== ТЕСТ: Извлечение месяцев ===")
    
    test_cases = [
        ("График октябрь", "october"),
        ("в октябре", "october"),
        ("на 10 месяц", "october"),
        ("окт", "october"),
        ("11.2025", "november"),
        ("ноябрь", "november"),
        ("декабря", "december"),
    ]
    
    for text, expected in test_cases:
        result = extract_month(text)
        status = "✅" if result == expected else "❌"
        print(f"{status} '{text}' -> '{result}' (ожидалось: '{expected}')")


def test_date_extraction():
    """Тест извлечения конкретных дат"""
    print("\n=== ТЕСТ: Извлечение конкретных дат ===")
    
    test_cases = [
        "15 октября",
        "2025-10-15",
        "15.10.2025",
        "сегодня",
        "завтра",
    ]
    
    for text in test_cases:
        result = extract_specific_date(text)
        status = "✅" if result else "❌"
        print(f"{status} '{text}' -> '{result}'")


def test_date_range():
    """Тест извлечения диапазонов дат"""
    print("\n=== ТЕСТ: Извлечение диапазонов дат ===")
    
    test_cases = [
        "с 1 по 15 октября",
        "01.10-15.10",
        "за месяц",
        "за квартал",
        "за неделю",
    ]
    
    for text in test_cases:
        result = extract_date_range(text)
        status = "✅" if result else "❌"
        print(f"{status} '{text}' -> {result}")


def test_intent_detection():
    """Тест определения интентов"""
    print("\n=== ТЕСТ: Определение интентов ===")
    
    test_cases = [
        ("Контакты старшего Кибальчича 3", "elder_contact"),
        ("График уборок Билибина 6 октябрь", "cleaning_month"),
        ("Какая бригада на Кибальчича 3?", "brigade"),
        ("Финансы компании", "finance_basic"),
        ("Разбивка по категориям", "finance_breakdown"),
        ("Динамика м/м", "finance_mom"),
        ("Топ категорий расходов", "finance_cat_trends"),
        ("Сколько всего домов?", "structural_totals"),
    ]
    
    for text, expected_type in test_cases:
        result = detect_intent(text)
        detected_type = result.get('type') if result else None
        status = "✅" if detected_type == expected_type else "❌"
        
        entities = []
        if result:
            if result.get('address'):
                entities.append(f"адрес: {result['address']}")
            if result.get('month'):
                entities.append(f"месяц: {result['month']}")
            if result.get('confidence'):
                entities.append(f"confidence: {result['confidence']}")
        
        entities_str = f" ({', '.join(entities)})" if entities else ""
        print(f"{status} '{text}' -> {detected_type}{entities_str} (ожидалось: {expected_type})")


if __name__ == "__main__":
    test_address_extraction()
    test_month_extraction()
    test_date_extraction()
    test_date_range()
    test_intent_detection()
    print("\n=== ТЕСТЫ ЗАВЕРШЕНЫ ===")
