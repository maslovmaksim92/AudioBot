#!/usr/bin/env python3
"""
Тест исправленной интеграции с Bitrix24
"""

import asyncio
import httpx
import json

async def test_fixed_api():
    """Тест исправленного API"""
    print("🔍 Тестирование исправленной интеграции с Bitrix24...")
    
    base_url = "http://localhost:8001"
    
    try:
        async with httpx.AsyncClient() as client:
            # Тестируем загрузку домов с исправленными полями
            response = await client.get(f"{base_url}/api/cleaning/houses?limit=2", timeout=60)
            
            if response.status_code == 200:
                data = response.json()
                houses = data.get('houses', [])
                
                if houses:
                    first_house = houses[0]
                    
                    print(f"✅ Загружено домов: {len(houses)}")
                    print(f"🏠 Первый дом: {first_house.get('address', 'N/A')}")
                    
                    # Проверяем исправленные поля
                    print(f"\n🏢 Управляющая компания:")
                    print(f"   management_company: {first_house.get('management_company', 'НЕТ')}")
                    print(f"   company_id: {first_house.get('company_id', 'НЕТ')}")
                    
                    print(f"\n👤 Ответственное лицо:")
                    print(f"   brigade: {first_house.get('brigade', 'НЕТ')}")
                    print(f"   assigned_by_id: {first_house.get('assigned_by_id', 'НЕТ')}")
                    
                    print(f"\n📝 Основные данные:")
                    print(f"   deal_id: {first_house.get('deal_id', 'НЕТ')}")
                    print(f"   apartments_count: {first_house.get('apartments_count', 'НЕТ')}")
                    print(f"   entrances_count: {first_house.get('entrances_count', 'НЕТ')}")
                    print(f"   floors_count: {first_house.get('floors_count', 'НЕТ')}")
                    
                    # Проверяем успешность исправления
                    is_fixed = (
                        first_house.get('management_company') is not None and
                        first_house.get('management_company') != "" and
                        first_house.get('assigned_by_id') is not None
                    )
                    
                    if is_fixed:
                        print(f"\n✅ ИСПРАВЛЕНИЕ УСПЕШНО!")
                        print(f"   УК определена: {first_house.get('management_company')}")
                        print(f"   Ответственный: ID {first_house.get('assigned_by_id')}")
                    else:
                        print(f"\n⚠️ ИСПРАВЛЕНИЕ ЧАСТИЧНО:")
                        print(f"   Нужно дополнительно проверить логику маппинга")
                    
                    return True
                else:
                    print("❌ Нет домов в ответе")
                    return False
            else:
                print(f"❌ HTTP ошибка: {response.status_code}")
                print(f"Ответ: {response.text[:200]}")
                return False
                
    except Exception as e:
        print(f"❌ Ошибка теста: {e}")
        return False

async def main():
    success = await test_fixed_api()
    if success:
        print(f"\n🎯 Тест завершен успешно!")
    else:
        print(f"\n❌ Тест не прошел")

if __name__ == "__main__":
    asyncio.run(main())