#!/usr/bin/env python3
"""
Прямое тестирование Bitrix24 API
"""
import asyncio
import httpx
import json

async def test_bitrix24_direct():
    """Прямой тест Bitrix24 webhook"""
    webhook_url = "https://vas-dom.bitrix24.ru/rest/1/bi0kv4y9ym8quxpa/"
    
    print("🔗 Тестируем прямое подключение к Bitrix24...")
    
    async with httpx.AsyncClient(timeout=30) as client:
        # 1. Тест user.current
        print("\n1. Тест user.current:")
        try:
            response = await client.post(f"{webhook_url}user.current")
            if response.status_code == 200:
                result = response.json()
                user = result.get("result", {})
                print(f"✅ Пользователь: {user.get('NAME')} {user.get('LAST_NAME')}")
            else:
                print(f"❌ Ошибка: {response.status_code} - {response.text}")
        except Exception as e:
            print(f"❌ Исключение: {e}")
        
        # 2. Тест crm.deal.list
        print("\n2. Тест crm.deal.list:")
        try:
            params = {
                "select": ["ID", "TITLE", "STAGE_ID", "OPPORTUNITY"],
                "filter": {},
                "start": 0
            }
            response = await client.post(
                f"{webhook_url}crm.deal.list",
                json=params
            )
            if response.status_code == 200:
                result = response.json()
                deals = result.get("result", [])
                print(f"✅ Найдено сделок: {len(deals)}")
                if deals:
                    print(f"  Первая сделка: {deals[0].get('TITLE', 'Без названия')}")
            else:
                print(f"❌ Ошибка: {response.status_code} - {response.text}")
        except Exception as e:
            print(f"❌ Исключение: {e}")
            
        # 3. Тест crm.dealcategory.list
        print("\n3. Тест crm.dealcategory.list:")
        try:
            response = await client.post(f"{webhook_url}crm.dealcategory.list")
            if response.status_code == 200:
                result = response.json()
                categories = result.get("result", [])
                print(f"✅ Найдено воронок: {len(categories)}")
                for cat in categories:
                    print(f"  - {cat.get('NAME', 'Без названия')} (ID: {cat.get('ID')})")
            else:
                print(f"❌ Ошибка: {response.status_code} - {response.text}")
        except Exception as e:
            print(f"❌ Исключение: {e}")

if __name__ == "__main__":
    asyncio.run(test_bitrix24_direct())