#!/usr/bin/env python3
"""
Quick Houses API Test - Проверка API домов после Frontend исправлений
Цель: убедиться что backend возвращает корректные данные для отладки Frontend проблемы
"""

import asyncio
import httpx
import json
from pathlib import Path

def get_backend_url():
    """Получить URL backend из frontend/.env"""
    try:
        frontend_env_path = Path(__file__).parent / "frontend" / ".env"
        if frontend_env_path.exists():
            with open(frontend_env_path, 'r') as f:
                for line in f:
                    if line.startswith('REACT_APP_BACKEND_URL='):
                        url = line.split('=', 1)[1].strip()
                        return f"{url}/api"
        return "https://crmunified.preview.emergentagent.com/api"
    except Exception as e:
        print(f"❌ Error reading backend URL: {e}")
        return "https://crmunified.preview.emergentagent.com/api"

BACKEND_URL = get_backend_url()
print(f"🔗 Testing backend at: {BACKEND_URL}")

async def test_houses_490_api():
    """
    Быстрая проверка API домов:
    1. GET /api/cleaning/houses-490 - проверка что API возвращает 490 домов
    2. Проверить structure данных - есть ли все нужные поля
    3. Проверить несколько примеров домов
    """
    print("\n🏠 QUICK HOUSES API TEST - GET /api/cleaning/houses-490")
    print("=" * 60)
    
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(f"{BACKEND_URL}/cleaning/houses-490")
            
            print(f"Status: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                houses = data.get("houses", [])
                total = len(houses)
                
                print(f"✅ SUCCESS: API responded")
                print(f"📊 Houses loaded: {total}")
                
                # 1. Проверка количества домов
                if total >= 490:
                    print(f"✅ КОЛИЧЕСТВО ДОМОВ: {total} (ожидалось 490) - OK")
                else:
                    print(f"⚠️ КОЛИЧЕСТВО ДОМОВ: {total} (ожидалось 490) - МЕНЬШЕ ОЖИДАЕМОГО")
                
                # 2. Проверка структуры данных - обязательные поля
                required_fields = ['address', 'deal_id', 'management_company', 'september_schedule']
                
                if houses:
                    sample_house = houses[0]
                    print(f"\n📋 СТРУКТУРА ДАННЫХ - Проверка обязательных полей:")
                    
                    missing_fields = []
                    present_fields = []
                    
                    for field in required_fields:
                        if field in sample_house:
                            present_fields.append(field)
                            print(f"   ✅ {field}: присутствует")
                        else:
                            missing_fields.append(field)
                            print(f"   ❌ {field}: ОТСУТСТВУЕТ")
                    
                    if missing_fields:
                        print(f"⚠️ ОТСУТСТВУЮЩИЕ ПОЛЯ: {missing_fields}")
                    else:
                        print(f"✅ ВСЕ ОБЯЗАТЕЛЬНЫЕ ПОЛЯ ПРИСУТСТВУЮТ")
                    
                    # 3. Проверка примеров домов - первые 3 дома
                    print(f"\n🏠 ПРИМЕРЫ ДОМОВ - Проверка данных:")
                    
                    for i, house in enumerate(houses[:3]):
                        print(f"\n   Дом #{i+1}:")
                        print(f"   - Address: {house.get('address', 'N/A')}")
                        print(f"   - Deal ID: {house.get('deal_id', 'N/A')}")
                        print(f"   - УК: {house.get('management_company', 'N/A')}")
                        
                        # Проверка september_schedule
                        september_schedule = house.get('september_schedule')
                        if september_schedule:
                            if isinstance(september_schedule, dict):
                                schedule_keys = list(september_schedule.keys())
                                print(f"   - September Schedule: {len(schedule_keys)} полей ({schedule_keys[:3]}...)")
                            else:
                                print(f"   - September Schedule: {type(september_schedule)} - {str(september_schedule)[:50]}...")
                        else:
                            print(f"   - September Schedule: ОТСУТСТВУЕТ")
                    
                    # 4. Анализ качества данных
                    print(f"\n📊 АНАЛИЗ КАЧЕСТВА ДАННЫХ:")
                    
                    # Проверка УК
                    filled_uk = sum(1 for h in houses if h.get('management_company') and h.get('management_company') != 'null')
                    uk_percentage = (filled_uk / total * 100) if total > 0 else 0
                    print(f"   - УК заполнены: {filled_uk}/{total} ({uk_percentage:.1f}%)")
                    
                    # Проверка september_schedule
                    filled_schedule = sum(1 for h in houses if h.get('september_schedule'))
                    schedule_percentage = (filled_schedule / total * 100) if total > 0 else 0
                    print(f"   - September Schedule: {filled_schedule}/{total} ({schedule_percentage:.1f}%)")
                    
                    # Проверка адресов
                    filled_addresses = sum(1 for h in houses if h.get('address'))
                    address_percentage = (filled_addresses / total * 100) if total > 0 else 0
                    print(f"   - Адреса заполнены: {filled_addresses}/{total} ({address_percentage:.1f}%)")
                    
                    # Источник данных
                    source = data.get("source", "Unknown")
                    print(f"   - Источник данных: {source}")
                    
                    # 5. Итоговая оценка
                    print(f"\n🎯 ИТОГОВАЯ ОЦЕНКА:")
                    
                    issues = []
                    if total < 490:
                        issues.append(f"Количество домов меньше ожидаемого ({total} < 490)")
                    if missing_fields:
                        issues.append(f"Отсутствуют обязательные поля: {missing_fields}")
                    if uk_percentage < 50:
                        issues.append(f"Низкий процент заполненных УК ({uk_percentage:.1f}%)")
                    if schedule_percentage < 50:
                        issues.append(f"Низкий процент заполненных графиков ({schedule_percentage:.1f}%)")
                    
                    if issues:
                        print(f"   ❌ НАЙДЕНЫ ПРОБЛЕМЫ:")
                        for issue in issues:
                            print(f"      - {issue}")
                        print(f"   🔍 ВЫВОД: Проблема может быть в backend данных")
                    else:
                        print(f"   ✅ ВСЕ ПРОВЕРКИ ПРОЙДЕНЫ")
                        print(f"   🔍 ВЫВОД: Backend данные корректны, проблема в Frontend")
                    
                    return True
                else:
                    print("❌ Нет данных домов в ответе")
                    return False
                    
            else:
                print(f"❌ FAILED: HTTP {response.status_code}")
                print(f"Response: {response.text}")
                return False
                
    except Exception as e:
        print(f"❌ ERROR: {e}")
        return False

async def main():
    """Главная функция тестирования"""
    print("🚀 VasDom AudioBot - Quick Houses API Test")
    print("🎯 Цель: Проверка API домов после Frontend исправлений")
    print("🔍 Убедиться что backend возвращает корректные данные")
    
    success = await test_houses_490_api()
    
    print(f"\n{'='*60}")
    if success:
        print("✅ ТЕСТИРОВАНИЕ ЗАВЕРШЕНО УСПЕШНО")
    else:
        print("❌ ТЕСТИРОВАНИЕ ЗАВЕРШЕНО С ОШИБКАМИ")
    print(f"{'='*60}")
    
    return success

if __name__ == "__main__":
    result = asyncio.run(main())