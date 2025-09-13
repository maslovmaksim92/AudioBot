#!/usr/bin/env python3
"""
Houses API Comparison Test - Сравнение обычного и houses-490 endpoints
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

async def test_houses_endpoints():
    """Сравнение обычного и houses-490 endpoints"""
    print("🔍 СРАВНЕНИЕ HOUSES ENDPOINTS")
    print("=" * 50)
    
    endpoints = [
        ("/cleaning/houses", "Обычный houses endpoint"),
        ("/cleaning/houses-490", "Houses-490 endpoint")
    ]
    
    results = {}
    
    for endpoint, description in endpoints:
        print(f"\n📡 Тестирование {description}: {endpoint}")
        
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(f"{BACKEND_URL}{endpoint}")
                
                if response.status_code == 200:
                    data = response.json()
                    houses = data.get("houses", [])
                    total = len(houses)
                    source = data.get("source", "Unknown")
                    
                    print(f"   ✅ Status: {response.status_code}")
                    print(f"   📊 Houses: {total}")
                    print(f"   🔗 Source: {source}")
                    
                    # Анализ качества данных
                    if houses:
                        sample = houses[0]
                        uk_filled = sum(1 for h in houses if h.get('management_company') and h.get('management_company') != 'null')
                        schedule_filled = sum(1 for h in houses if h.get('september_schedule'))
                        
                        print(f"   🏢 УК заполнены: {uk_filled}/{total} ({uk_filled/total*100:.1f}%)")
                        print(f"   📅 Графики: {schedule_filled}/{total} ({schedule_filled/total*100:.1f}%)")
                        print(f"   📋 Поля в примере: {len(sample.keys())}")
                    
                    results[endpoint] = {
                        "success": True,
                        "total": total,
                        "source": source,
                        "uk_filled": uk_filled if houses else 0,
                        "schedule_filled": schedule_filled if houses else 0
                    }
                else:
                    print(f"   ❌ Status: {response.status_code}")
                    print(f"   📝 Response: {response.text[:100]}...")
                    results[endpoint] = {"success": False, "status": response.status_code}
                    
        except Exception as e:
            print(f"   ❌ Error: {e}")
            results[endpoint] = {"success": False, "error": str(e)}
    
    # Сравнение результатов
    print(f"\n📊 СРАВНЕНИЕ РЕЗУЛЬТАТОВ")
    print("=" * 50)
    
    houses_result = results.get("/cleaning/houses", {})
    houses_490_result = results.get("/cleaning/houses-490", {})
    
    if houses_result.get("success") and houses_490_result.get("success"):
        print(f"✅ Оба endpoint работают")
        print(f"📊 Обычный houses: {houses_result['total']} домов")
        print(f"📊 Houses-490: {houses_490_result['total']} домов")
        print(f"🔗 Источник обычный: {houses_result['source']}")
        print(f"🔗 Источник houses-490: {houses_490_result['source']}")
        
        if houses_result['total'] != houses_490_result['total']:
            print(f"⚠️ РАЗНИЦА В КОЛИЧЕСТВЕ: {abs(houses_result['total'] - houses_490_result['total'])} домов")
        else:
            print(f"✅ Количество домов одинаковое")
            
    else:
        print(f"❌ Один или оба endpoint не работают")
        if not houses_result.get("success"):
            print(f"   - Обычный houses: ОШИБКА")
        if not houses_490_result.get("success"):
            print(f"   - Houses-490: ОШИБКА")
    
    return results

async def main():
    """Главная функция"""
    print("🚀 Houses API Comparison Test")
    
    results = await test_houses_endpoints()
    
    print(f"\n{'='*50}")
    print("✅ ТЕСТИРОВАНИЕ ЗАВЕРШЕНО")
    print(f"{'='*50}")
    
    return results

if __name__ == "__main__":
    result = asyncio.run(main())