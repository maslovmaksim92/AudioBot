#!/usr/bin/env python3
"""
Простая проверка API без оптимизации для отладки
"""

import asyncio
import httpx
import urllib.parse

WEBHOOK_URL = "https://vas-dom.bitrix24.ru/rest/1/4l8hq1gqgodjt7yo/"

async def test_simple_api():
    """Простой тест API без дополнительных вызовов"""
    print("🔍 Простой тест Bitrix24 API...")
    
    # Получаем только основные поля без внешних вызовов
    params = {
        'select[0]': 'ID',
        'select[1]': 'TITLE', 
        'select[2]': 'STAGE_ID',
        'select[3]': 'ASSIGNED_BY_ID',       # ID ответственного (есть)
        'select[4]': 'COMPANY_ID',           # ID компании (нужно проверить)
        'filter[CATEGORY_ID]': '34',
        'start': '0'
    }
    
    query_string = urllib.parse.urlencode(params)
    url = f"{WEBHOOK_URL}crm.deal.list.json?{query_string}"
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(url, timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                deals = data.get('result', [])
                
                if deals:
                    print(f"✅ Получено {len(deals)} сделок")
                    
                    # Анализируем ID компаний и пользователей
                    company_ids = set()
                    user_ids = set() 
                    
                    for deal in deals[:5]:  # Анализируем первые 5
                        print(f"\n🏠 Дом: {deal.get('TITLE')}")
                        print(f"   ID: {deal.get('ID')}")
                        print(f"   ASSIGNED_BY_ID: {deal.get('ASSIGNED_BY_ID')}")
                        print(f"   COMPANY_ID: {deal.get('COMPANY_ID')}")
                        
                        if deal.get('COMPANY_ID'):
                            company_ids.add(deal.get('COMPANY_ID'))
                        if deal.get('ASSIGNED_BY_ID'):
                            user_ids.add(deal.get('ASSIGNED_BY_ID'))
                    
                    print(f"\n📊 Статистика:")
                    print(f"   Уникальных COMPANY_ID: {len(company_ids)}")
                    print(f"   Уникальных ASSIGNED_BY_ID: {len(user_ids)}")
                    print(f"   Company IDs: {list(company_ids)[:5]}...")
                    print(f"   User IDs: {list(user_ids)[:5]}...")
                    
                    # Проверим один компанию и одного пользователя
                    if company_ids:
                        company_id = list(company_ids)[0]
                        print(f"\n🏢 Тестируем компанию ID: {company_id}")
                        await test_company_api(company_id)
                    
                    if user_ids:
                        user_id = list(user_ids)[0]
                        print(f"\n👤 Тестируем пользователя ID: {user_id}")
                        await test_user_api(user_id)
                    
                    return True
                else:
                    print("❌ Нет сделок")
                    return False
            else:
                print(f"❌ HTTP ошибка: {response.status_code}")
                return False
                
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        return False

async def test_company_api(company_id):
    """Тест API компании"""
    try:
        params = {'id': str(company_id)}
        query_string = urllib.parse.urlencode(params)
        url = f"{WEBHOOK_URL}crm.company.get.json?{query_string}"
        
        async with httpx.AsyncClient() as client:
            response = await client.get(url, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                result = data.get('result')
                
                if result:
                    print(f"   ✅ Компания: {result.get('TITLE', 'Без названия')}")
                else:
                    print(f"   ❌ Компания не найдена")
            else:
                print(f"   ❌ HTTP ошибка компании: {response.status_code}")
                
    except Exception as e:
        print(f"   ❌ Ошибка компании: {e}")

async def test_user_api(user_id):
    """Тест API пользователя"""
    try:
        params = {'ID': str(user_id)}
        query_string = urllib.parse.urlencode(params)
        url = f"{WEBHOOK_URL}user.get.json?{query_string}"
        
        async with httpx.AsyncClient() as client:
            response = await client.get(url, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                result = data.get('result')
                
                if result and isinstance(result, list) and len(result) > 0:
                    user = result[0]
                    name = f"{user.get('NAME', '')} {user.get('LAST_NAME', '')}".strip()
                    print(f"   ✅ Пользователь: {name}")
                else:
                    print(f"   ❌ Пользователь не найден")
            else:
                print(f"   ❌ HTTP ошибка пользователя: {response.status_code}")
                
    except Exception as e:
        print(f"   ❌ Ошибка пользователя: {e}")

async def main():
    success = await test_simple_api()
    if success:
        print(f"\n✅ Тест успешен!")
    else:
        print(f"\n❌ Тест не прошел")

if __name__ == "__main__":
    asyncio.run(main())