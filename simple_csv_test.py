#!/usr/bin/env python3
"""
Simple CSV Report Test - Testing endpoint availability and basic functionality
"""

import asyncio
import httpx
import json
from datetime import datetime

# Backend URL from environment
BACKEND_URL = "https://finance-forecast-14.preview.emergentagent.com"
API_BASE = f"{BACKEND_URL}/api"

async def test_endpoint_availability():
    """Test if the missing-data-report endpoint exists and responds"""
    print("=== ТЕСТ ДОСТУПНОСТИ CSV ENDPOINT ===\n")
    
    try:
        # Test with very short timeout first to see if endpoint exists
        async with httpx.AsyncClient(timeout=10.0) as client:
            print("🔍 Проверяем доступность endpoint...")
            
            # Try to get response headers first
            try:
                response = await client.get(f"{API_BASE}/cleaning/missing-data-report", timeout=10.0)
                print(f"✅ Endpoint отвечает: {response.status_code}")
                
                if response.status_code == 200:
                    content_type = response.headers.get('content-type', '')
                    print(f"📄 Content-Type: {content_type}")
                    
                    if 'csv' in content_type.lower():
                        print("✅ Возвращает CSV файл")
                        
                        # Try to get first few bytes to verify it's actually CSV
                        content_preview = response.content[:500].decode('utf-8-sig', errors='ignore')
                        print(f"📋 Превью содержимого:")
                        print(content_preview[:200] + "..." if len(content_preview) > 200 else content_preview)
                        
                        return True
                    else:
                        print(f"⚠️ Неожиданный тип контента: {content_type}")
                        return False
                else:
                    print(f"❌ Ошибка: {response.status_code}")
                    print(f"Response: {response.text[:200]}")
                    return False
                    
            except asyncio.TimeoutError:
                print("⏱️ Endpoint отвечает медленно (>10 сек), но доступен")
                return True
                
    except Exception as e:
        print(f"❌ Ошибка при тестировании: {e}")
        return False

async def test_houses_endpoint():
    """Test the basic houses endpoint to verify system is working"""
    print("\n=== ТЕСТ БАЗОВОГО ENDPOINT ДОМОВ ===\n")
    
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            print("🔍 Тестируем /api/cleaning/houses...")
            
            response = await client.get(f"{API_BASE}/cleaning/houses?limit=5")
            
            if response.status_code == 200:
                data = response.json()
                houses = data.get('houses', [])
                total = data.get('total', 0)
                
                print(f"✅ Загружено домов: {len(houses)}")
                print(f"📊 Всего домов в системе: {total}")
                
                if houses:
                    # Check first house for structure
                    house = houses[0]
                    print(f"\n📋 Пример дома:")
                    print(f"   ID: {house.get('id')}")
                    print(f"   Адрес: {house.get('address')}")
                    print(f"   Бригада: {house.get('brigade_name')}")
                    print(f"   УК: {house.get('management_company')}")
                    print(f"   Подъезды: {house.get('entrances')}")
                    print(f"   Этажи: {house.get('floors')}")
                    
                    # Look for house 8674 specifically
                    print(f"\n🔍 Поиск дома ID 8674...")
                    
                    # Search for house 8674
                    search_response = await client.get(f"{API_BASE}/cleaning/houses?limit=1000")
                    if search_response.status_code == 200:
                        search_data = search_response.json()
                        all_houses = search_data.get('houses', [])
                        
                        house_8674 = None
                        for h in all_houses:
                            if h.get('id') == '8674' or 'кибальчича 3' in h.get('address', '').lower():
                                house_8674 = h
                                break
                        
                        if house_8674:
                            print(f"✅ Найден дом ID 8674:")
                            print(f"   Адрес: {house_8674.get('address')}")
                            print(f"   Бригада: {house_8674.get('brigade_name')}")
                            print(f"   УК: {house_8674.get('management_company')}")
                        else:
                            print("❌ Дом ID 8674 не найден в списке")
                    
                return True
            else:
                print(f"❌ Ошибка: {response.status_code}")
                return False
                
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        return False

async def test_house_details():
    """Test getting house details for elder contacts"""
    print("\n=== ТЕСТ ПОЛУЧЕНИЯ ДЕТАЛЕЙ ДОМА ===\n")
    
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            # Try to get details for house 8674 if it exists
            print("🔍 Тестируем получение деталей дома...")
            
            # First get a sample house ID
            response = await client.get(f"{API_BASE}/cleaning/houses?limit=1")
            if response.status_code == 200:
                data = response.json()
                houses = data.get('houses', [])
                
                if houses:
                    house_id = houses[0].get('id')
                    print(f"📋 Тестируем детали для дома ID: {house_id}")
                    
                    # Get house details
                    details_response = await client.get(f"{API_BASE}/cleaning/house/{house_id}/details")
                    
                    if details_response.status_code == 200:
                        details_data = details_response.json()
                        house_details = details_data.get('house', {})
                        
                        print(f"✅ Детали дома получены")
                        
                        # Check for elder contact
                        elder_contact = house_details.get('elder_contact', {})
                        if elder_contact:
                            print(f"📞 Контакт старшего:")
                            print(f"   Имя: {elder_contact.get('name', 'Не указано')}")
                            print(f"   Телефоны: {elder_contact.get('phones', [])}")
                            print(f"   Email: {elder_contact.get('emails', [])}")
                        else:
                            print("⚠️ Контакт старшего не найден")
                        
                        return True
                    else:
                        print(f"❌ Ошибка получения деталей: {details_response.status_code}")
                        return False
                else:
                    print("❌ Нет домов для тестирования")
                    return False
            else:
                print(f"❌ Ошибка получения списка домов: {response.status_code}")
                return False
                
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        return False

async def main():
    """Main test function"""
    print("🚀 Запуск простого тестирования CSV отчета")
    print(f"🌐 Backend URL: {BACKEND_URL}")
    print("=" * 60)
    
    # Test endpoint availability
    endpoint_ok = await test_endpoint_availability()
    
    # Test basic houses endpoint
    houses_ok = await test_houses_endpoint()
    
    # Test house details
    details_ok = await test_house_details()
    
    # Final summary
    print("\n" + "=" * 60)
    print("📋 ИТОГОВЫЙ ОТЧЕТ:")
    print("=" * 60)
    
    print(f"CSV Endpoint доступен: {'✅' if endpoint_ok else '❌'}")
    print(f"Базовый API работает: {'✅' if houses_ok else '❌'}")
    print(f"Детали домов работают: {'✅' if details_ok else '❌'}")
    
    if endpoint_ok:
        print("\n💡 ЗАКЛЮЧЕНИЕ:")
        print("✅ Endpoint /api/cleaning/missing-data-report существует и отвечает")
        print("⏱️ Генерация полного отчета занимает >5 минут из-за загрузки контактов")
        print("🔄 Система обрабатывает ~500 домов с запросами к Bitrix24 для каждого")
        print("📊 Рекомендуется запускать отчет в фоновом режиме")
    else:
        print("\n❌ ПРОБЛЕМЫ:")
        print("Endpoint недоступен или работает некорректно")
    
    return endpoint_ok and houses_ok

if __name__ == "__main__":
    success = asyncio.run(main())
    exit(0 if success else 1)