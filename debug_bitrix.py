#!/usr/bin/env python3
"""
Отладочный скрипт для исследования Bitrix24 API
"""

import asyncio
import httpx
import urllib.parse
import json

WEBHOOK_URL = "https://vas-dom.bitrix24.ru/rest/1/4l8hq1gqgodjt7yd/"

async def debug_bitrix_fields():
    """Исследование доступных полей в Bitrix24"""
    print("🔍 Отладка полей Bitrix24 API...")
    
    # Запрашиваем поля, которые должны содержать УК и ответственного
    params = {
        'select[0]': 'ID',
        'select[1]': 'TITLE', 
        'select[2]': 'STAGE_ID',
        'select[3]': 'COMPANY_ID',
        'select[4]': 'COMPANY_TITLE',        # Тестируем название УК
        'select[5]': 'ASSIGNED_BY_ID',       # ID ответственного
        'select[6]': 'ASSIGNED_BY_NAME',     # Имя ответственного
        'select[7]': 'ASSIGNED_BY_LAST_NAME', # Фамилия ответственного
        'select[8]': 'ASSIGNED_BY_SECOND_NAME', # Отчество ответственного
        'filter[CATEGORY_ID]': '34',
        'start': '0'
    }
    
    query_string = urllib.parse.urlencode(params)
    url = f"{WEBHOOK_URL}crm.deal.list.json?{query_string}"
    
    print(f"🔗 URL: {url[:80]}...")
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(url, timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                deals = data.get('result', [])
                
                if deals:
                    first_deal = deals[0]
                    
                    print(f"✅ Получено {len(deals)} сделок")
                    print(f"🔍 Первая сделка: {first_deal.get('TITLE')}")
                    print(f"📋 Всего полей: {len(first_deal)}")
                    
                    # Проверяем поля УК
                    print("\n🏢 ПОЛЯ УПРАВЛЯЮЩЕЙ КОМПАНИИ:")
                    print(f"  COMPANY_ID: {first_deal.get('COMPANY_ID', 'НЕТ')}")
                    print(f"  COMPANY_TITLE: {first_deal.get('COMPANY_TITLE', 'НЕТ')}")
                    
                    # Проверяем поля ответственного
                    print("\n👤 ПОЛЯ ОТВЕТСТВЕННОГО:")
                    print(f"  ASSIGNED_BY_ID: {first_deal.get('ASSIGNED_BY_ID', 'НЕТ')}")
                    print(f"  ASSIGNED_BY_NAME: {first_deal.get('ASSIGNED_BY_NAME', 'НЕТ')}")
                    print(f"  ASSIGNED_BY_LAST_NAME: {first_deal.get('ASSIGNED_BY_LAST_NAME', 'НЕТ')}")
                    print(f"  ASSIGNED_BY_SECOND_NAME: {first_deal.get('ASSIGNED_BY_SECOND_NAME', 'НЕТ')}")
                    
                    # Показываем ВСЕ доступные поля
                    print(f"\n📝 ВСЕ ДОСТУПНЫЕ ПОЛЯ ({len(first_deal)}):")
                    for key, value in first_deal.items():
                        if value:  # Показываем только заполненные поля
                            print(f"  {key}: {str(value)[:50]}...")
                    
                    return first_deal
                else:
                    print("❌ Нет сделок в категории 34")
                    return None
            else:
                print(f"❌ HTTP ошибка: {response.status_code}")
                print(f"Ответ: {response.text[:200]}")
                return None
                
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        return None

async def main():
    result = await debug_bitrix_fields()
    if result:
        print(f"\n✅ Отладка успешна!")
    else:
        print(f"\n❌ Отладка не удалась")

if __name__ == "__main__":
    asyncio.run(main())