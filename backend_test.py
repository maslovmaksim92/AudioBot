#!/usr/bin/env python3
"""
VasDom AudioBot - Backend API Testing
Тестирование API домов и анализ проблем с УК и графиками уборки
"""

import asyncio
import httpx
import json
import os
import sys
from datetime import datetime
from pathlib import Path

# Получаем URL backend из frontend/.env
def get_backend_url():
    """Получить URL backend - сначала локальный, потом из frontend/.env"""
    # Проверяем локальный backend
    try:
        import httpx
        import asyncio
        
        async def check_local():
            try:
                async with httpx.AsyncClient(timeout=5.0) as client:
                    response = await client.get("http://localhost:8001/api/")
                    if response.status_code == 200:
                        return "http://localhost:8001/api"
            except:
                pass
            return None
        
        local_url = asyncio.run(check_local())
        if local_url:
            print("🏠 Using local backend")
            return local_url
    except:
        pass
    
    # Fallback к URL из frontend/.env
    try:
        frontend_env_path = Path(__file__).parent / "frontend" / ".env"
        if frontend_env_path.exists():
            with open(frontend_env_path, 'r') as f:
                for line in f:
                    if line.startswith('REACT_APP_BACKEND_URL='):
                        url = line.split('=', 1)[1].strip()
                        print("🌐 Using external backend from .env")
                        return f"{url}/api"
        
        # Final fallback
        print("⚠️ Using fallback URL")
        return "https://crmunified.preview.emergentagent.com/api"
    except Exception as e:
        print(f"❌ Error reading backend URL: {e}")
        return "https://crmunified.preview.emergentagent.com/api"

BACKEND_URL = get_backend_url()
print(f"🔗 Testing backend at: {BACKEND_URL}")

class HousesAPITester:
    """Тестер для Houses API endpoints - анализ проблем с УК и графиками уборки"""
    
    def __init__(self, base_url: str):
        self.base_url = base_url
        self.houses_data = None
        
    async def test_get_houses(self):
        """Тест GET /api/cleaning/houses - получить список домов с УК и графиками"""
        print("\n🏠 Testing GET /api/cleaning/houses...")
        
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(f"{self.base_url}/cleaning/houses")
                
                print(f"Status: {response.status_code}")
                
                if response.status_code == 200:
                    data = response.json()
                    print(f"✅ SUCCESS: API responded")
                    
                    # Анализируем структуру ответа
                    if "houses" in data:
                        houses = data.get("houses", [])
                        total = len(houses)
                        print(f"📊 Total houses loaded: {total}")
                        
                        # Сохраняем данные для дальнейшего анализа
                        self.houses_data = houses
                        
                        # Анализ проблем с УК
                        uk_analysis = self._analyze_management_companies(houses)
                        print(f"🏢 Management Companies Analysis:")
                        print(f"   - Houses with УК: {uk_analysis['filled']}/{total}")
                        print(f"   - Houses with null УК: {uk_analysis['null']}/{total}")
                        print(f"   - Unique УК found: {len(uk_analysis['unique_companies'])}")
                        
                        # Анализ графиков уборки
                        schedule_analysis = self._analyze_cleaning_schedules(houses)
                        print(f"📅 Cleaning Schedules Analysis:")
                        print(f"   - Houses with september_schedule: {schedule_analysis['with_september']}/{total}")
                        print(f"   - Houses with cleaning dates: {schedule_analysis['with_dates']}/{total}")
                        print(f"   - Schedule fields found: {schedule_analysis['schedule_fields']}")
                        
                        # Анализ источника данных
                        source = data.get("source", "Unknown")
                        print(f"🔗 Data source: {source}")
                        
                        return True
                    else:
                        print("❌ Invalid response structure - no 'houses' field")
                        return False
                else:
                    print(f"❌ FAILED: HTTP {response.status_code}")
                    print(f"Response: {response.text}")
                    return False
                    
        except Exception as e:
            print(f"❌ ERROR: {e}")
            return False
    
    async def test_get_houses_490(self):
        """Тест GET /api/cleaning/houses-490 - получить 490 домов"""
        print("\n🏠 Testing GET /api/cleaning/houses-490...")
        
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(f"{self.base_url}/cleaning/houses-490")
                
                print(f"Status: {response.status_code}")
                
                if response.status_code == 200:
                    data = response.json()
                    print(f"✅ SUCCESS: API responded")
                    
                    houses = data.get("houses", [])
                    total = len(houses)
                    print(f"📊 Houses loaded: {total} (expected: 490)")
                    
                    if total >= 490:
                        print("✅ SUCCESS: 490+ houses loaded")
                    else:
                        print(f"⚠️ WARNING: Only {total} houses loaded, expected 490")
                    
                    # Проверяем категорию
                    category_used = data.get("category_used", "unknown")
                    print(f"🏷️ Category used: {category_used}")
                    
                    # Анализ первых 5 домов
                    if houses:
                        sample_house = houses[0]
                        print(f"📋 Sample house fields: {list(sample_house.keys())}")
                        print(f"   - Address: {sample_house.get('address', 'N/A')}")
                        print(f"   - УК: {sample_house.get('management_company', 'N/A')}")
                        print(f"   - Brigade: {sample_house.get('brigade', 'N/A')}")
                        print(f"   - September schedule: {bool(sample_house.get('september_schedule'))}")
                    
                    return True
                else:
                    print(f"❌ FAILED: HTTP {response.status_code}")
                    print(f"Response: {response.text}")
                    return False
                    
        except Exception as e:
            print(f"❌ ERROR: {e}")
            return False
    
    async def test_dashboard_stats(self):
        """Тест GET /api/dashboard - статистика домов"""
        print("\n📊 Testing GET /api/dashboard...")
        
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(f"{self.base_url}/dashboard")
                
                print(f"Status: {response.status_code}")
                
                if response.status_code == 200:
                    data = response.json()
                    print(f"✅ SUCCESS: Dashboard API responded")
                    
                    # Анализируем статистику домов
                    stats = data.get("stats", {})
                    houses_count = stats.get("houses", 0)
                    employees_count = stats.get("employees", 0)
                    
                    print(f"🏠 Houses in dashboard: {houses_count}")
                    print(f"👥 Employees: {employees_count}")
                    print(f"🏢 Apartments: {stats.get('apartments', 0)}")
                    print(f"🚪 Entrances: {stats.get('entrances', 0)}")
                    print(f"📊 Floors: {stats.get('floors', 0)}")
                    
                    # Проверяем источник данных
                    data_source = data.get("data_source", "Unknown")
                    print(f"🔗 Data source: {data_source}")
                    
                    return True
                else:
                    print(f"❌ FAILED: HTTP {response.status_code}")
                    print(f"Response: {response.text}")
                    return False
                    
        except Exception as e:
            print(f"❌ ERROR: {e}")
            return False
    
    async def test_brigades_info(self):
        """Тест GET /api/cleaning/brigades - информация о бригадах"""
        print("\n👥 Testing GET /api/cleaning/brigades...")
        
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(f"{self.base_url}/cleaning/brigades")
                
                print(f"Status: {response.status_code}")
                
                if response.status_code == 200:
                    data = response.json()
                    print(f"✅ SUCCESS: Brigades API responded")
                    
                    brigades = data.get("brigades", [])
                    total_employees = data.get("total_employees", 0)
                    total_brigades = data.get("total_brigades", 0)
                    
                    print(f"👥 Total brigades: {total_brigades}")
                    print(f"👷 Total employees: {total_employees}")
                    
                    # Показываем информацию о бригадах
                    for brigade in brigades:
                        name = brigade.get("name", "Unknown")
                        employees = brigade.get("employees", 0)
                        areas = brigade.get("areas", [])
                        print(f"   - {name}: {employees} employees, areas: {areas}")
                    
                    return True
                else:
                    print(f"❌ FAILED: HTTP {response.status_code}")
                    print(f"Response: {response.text}")
                    return False
                    
        except Exception as e:
            print(f"❌ ERROR: {e}")
            return False
    
    async def test_production_debug_endpoints(self):
        """Тест новых production debug endpoints"""
        print("\n🔍 Testing Production Debug Endpoints...")
        
        debug_endpoints = [
            "/cleaning/production-debug",
            "/cleaning/fix-management-companies", 
            "/cleaning/houses-fixed"
        ]
        
        results = {}
        
        for endpoint in debug_endpoints:
            print(f"\n🔧 Testing {endpoint}...")
            try:
                async with httpx.AsyncClient(timeout=30.0) as client:
                    response = await client.get(f"{self.base_url}{endpoint}")
                    
                    print(f"Status: {response.status_code}")
                    
                    if response.status_code == 200:
                        data = response.json()
                        print(f"✅ SUCCESS: {endpoint}")
                        results[endpoint] = True
                        
                        # Специальный анализ для каждого endpoint
                        if "production-debug" in endpoint:
                            has_optimized = data.get("code_version_check", {}).get("has_optimized_loading", False)
                            has_enrichment = data.get("code_version_check", {}).get("has_enrichment_method", False)
                            print(f"   - Has optimized loading: {has_optimized}")
                            print(f"   - Has enrichment method: {has_enrichment}")
                        
                        elif "fix-management-companies" in endpoint:
                            fixed_houses = data.get("fixed_houses", [])
                            print(f"   - Fixed houses: {len(fixed_houses)}")
                            if fixed_houses:
                                sample = fixed_houses[0]
                                print(f"   - Sample УК: {sample.get('fixed_management_company', 'N/A')}")
                        
                        elif "houses-fixed" in endpoint:
                            houses = data.get("houses", [])
                            print(f"   - Houses with forced enrichment: {len(houses)}")
                            
                    elif response.status_code == 404:
                        print(f"❌ NOT FOUND: {endpoint} - endpoint not deployed")
                        results[endpoint] = False
                    else:
                        print(f"❌ FAILED: HTTP {response.status_code}")
                        results[endpoint] = False
                        
            except Exception as e:
                print(f"❌ ERROR: {e}")
                results[endpoint] = False
        
        return results
    
    async def test_bitrix24_integration(self):
        """Тест интеграции с Bitrix24"""
        print("\n🔗 Testing Bitrix24 Integration...")
        
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(f"{self.base_url}/bitrix24/test")
                
                print(f"Status: {response.status_code}")
                
                if response.status_code == 200:
                    data = response.json()
                    print(f"✅ SUCCESS: Bitrix24 integration working")
                    
                    connection = data.get("connection", "Unknown")
                    sample_deals = data.get("sample_deals", 0)
                    
                    print(f"🔗 Connection status: {connection}")
                    print(f"📊 Sample deals loaded: {sample_deals}")
                    
                    return True
                else:
                    print(f"❌ FAILED: HTTP {response.status_code}")
                    print(f"Response: {response.text}")
                    return False
                    
        except Exception as e:
            print(f"❌ ERROR: {e}")
            return False
    
    def _analyze_management_companies(self, houses):
        """Анализ проблем с управляющими компаниями"""
        filled_count = 0
        null_count = 0
        unique_companies = set()
        
        for house in houses:
            uk = house.get("management_company")
            if uk and uk != "null" and uk.strip():
                filled_count += 1
                unique_companies.add(uk)
            else:
                null_count += 1
        
        return {
            "filled": filled_count,
            "null": null_count,
            "unique_companies": list(unique_companies)
        }
    
    def _analyze_cleaning_schedules(self, houses):
        """Анализ проблем с графиками уборки"""
        with_september = 0
        with_dates = 0
        schedule_fields = set()
        
        for house in houses:
            # Проверяем september_schedule
            september_schedule = house.get("september_schedule")
            if september_schedule:
                with_september += 1
                
                # Анализируем структуру графика
                if isinstance(september_schedule, dict):
                    if september_schedule.get("cleaning_date_1"):
                        with_dates += 1
                    
                    # Собираем все поля графика
                    for key in september_schedule.keys():
                        schedule_fields.add(key)
            
            # Проверяем другие поля с датами уборки
            for key, value in house.items():
                if "cleaning" in key.lower() or "schedule" in key.lower():
                    if value:
                        schedule_fields.add(key)
                
                # Проверяем UF_CRM поля
                if key.startswith("UF_CRM_") and "174159" in key:
                    if value:
                        schedule_fields.add(key)
        
        return {
            "with_september": with_september,
            "with_dates": with_dates,
            "schedule_fields": list(schedule_fields)
        }

class MeetingsAPITester:
    """Тестер для Meetings API endpoints"""
    
    def __init__(self, base_url: str):
        self.base_url = base_url
        self.meeting_id = None
        
    async def test_get_meetings(self):
        """Тест GET /api/meetings - получить список всех планерок"""
        print("\n📋 Testing GET /api/meetings...")
        
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(f"{self.base_url}/meetings")
                
                print(f"Status: {response.status_code}")
                
                if response.status_code == 200:
                    data = response.json()
                    print(f"✅ SUCCESS: {data}")
                    
                    # Проверяем структуру ответа
                    if "status" in data and "meetings" in data:
                        meetings_count = len(data.get("meetings", []))
                        print(f"📊 Found {meetings_count} meetings")
                        return True
                    else:
                        print("❌ Invalid response structure")
                        return False
                else:
                    print(f"❌ FAILED: HTTP {response.status_code}")
                    print(f"Response: {response.text}")
                    return False
                    
        except Exception as e:
            print(f"❌ ERROR: {e}")
            return False
    
    async def test_start_recording(self):
        """Тест POST /api/meetings/start-recording - начать запись планерки"""
        print("\n🎤 Testing POST /api/meetings/start-recording...")
        
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(f"{self.base_url}/meetings/start-recording")
                
                print(f"Status: {response.status_code}")
                
                if response.status_code == 200:
                    data = response.json()
                    print(f"✅ SUCCESS: {data}")
                    
                    # Сохраняем meeting_id для следующего теста
                    if "meeting_id" in data:
                        self.meeting_id = data["meeting_id"]
                        print(f"📝 Meeting ID saved: {self.meeting_id}")
                        return True
                    else:
                        print("❌ No meeting_id in response")
                        return False
                else:
                    print(f"❌ FAILED: HTTP {response.status_code}")
                    print(f"Response: {response.text}")
                    return False
                    
        except Exception as e:
            print(f"❌ ERROR: {e}")
            return False
    
    async def test_stop_recording(self):
        """Тест POST /api/meetings/stop-recording - остановить запись планерки"""
        print("\n⏹️ Testing POST /api/meetings/stop-recording...")
        
        if not self.meeting_id:
            print("❌ No meeting_id available, skipping test")
            return False
        
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                # Отправляем meeting_id как query parameter
                response = await client.post(
                    f"{self.base_url}/meetings/stop-recording",
                    params={"meeting_id": self.meeting_id}
                )
                
                print(f"Status: {response.status_code}")
                
                if response.status_code == 200:
                    data = response.json()
                    print(f"✅ SUCCESS: {data}")
                    return True
                else:
                    print(f"❌ FAILED: HTTP {response.status_code}")
                    print(f"Response: {response.text}")
                    return False
                    
        except Exception as e:
            print(f"❌ ERROR: {e}")
            return False

class VoiceAPITester:
    """Тестер для Voice API endpoints"""
    
    def __init__(self, base_url: str):
        self.base_url = base_url
    
    async def test_voice_process_post(self):
        """Тест POST /api/voice/process - обработка голосовых сообщений"""
        print("\n🎙️ Testing POST /api/voice/process...")
        
        test_message = {
            "text": "Привет! Сколько у нас домов в управлении?",
            "user_id": "test_user_meetings"
        }
        
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    f"{self.base_url}/voice/process",
                    json=test_message
                )
                
                print(f"Status: {response.status_code}")
                print(f"Response text: {response.text}")
                
                if response.status_code == 200:
                    data = response.json()
                    print(f"✅ SUCCESS: {data}")
                    
                    # Проверяем структуру ответа
                    if "response" in data:
                        ai_response = data["response"]
                        print(f"🤖 AI Response: {ai_response[:100]}...")
                        return True
                    else:
                        print("❌ Invalid response structure")
                        return False
                elif response.status_code == 422:
                    print("❌ Validation error - checking request format")
                    return False
                else:
                    print(f"❌ FAILED: HTTP {response.status_code}")
                    print(f"Response: {response.text}")
                    return False
                    
        except Exception as e:
            print(f"❌ ERROR: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    async def test_self_learning_status(self):
        """Тест GET /api/self-learning/status - статус системы самообучения"""
        print("\n🧠 Testing GET /api/self-learning/status...")
        
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(f"{self.base_url}/self-learning/status")
                
                print(f"Status: {response.status_code}")
                
                if response.status_code == 200:
                    data = response.json()
                    print(f"✅ SUCCESS: {data}")
                    
                    # Проверяем ключевые поля
                    status = data.get("status", "unknown")
                    emergent_llm = data.get("emergent_llm", {})
                    
                    print(f"📊 Self-learning status: {status}")
                    print(f"🤖 Emergent LLM mode: {emergent_llm.get('mode', 'unknown')}")
                    
                    return True
                else:
                    print(f"❌ FAILED: HTTP {response.status_code}")
                    print(f"Response: {response.text}")
                    return False
                    
        except Exception as e:
            print(f"❌ ERROR: {e}")
            return False

async def run_comprehensive_tests():
    """Запуск всех тестов meetings и voice API"""
    print("🚀 VasDom AudioBot - Meetings & Voice API Testing")
    print("=" * 60)
    
    # Инициализация тестеров
    meetings_tester = MeetingsAPITester(BACKEND_URL)
    voice_tester = VoiceAPITester(BACKEND_URL)
    
    # Результаты тестов
    results = {}
    
    # Тестирование Meetings API
    print("\n🎤 MEETINGS API TESTING")
    print("-" * 30)
    
    results["get_meetings"] = await meetings_tester.test_get_meetings()
    results["start_recording"] = await meetings_tester.test_start_recording()
    results["stop_recording"] = await meetings_tester.test_stop_recording()
    
    # Тестирование Voice API
    print("\n🎙️ VOICE API TESTING")
    print("-" * 30)
    
    results["voice_process"] = await voice_tester.test_voice_process_post()
    results["self_learning_status"] = await voice_tester.test_self_learning_status()
    
    # Итоговый отчет
    print("\n📊 TEST RESULTS SUMMARY")
    print("=" * 60)
    
    passed_tests = []
    failed_tests = []
    
    for test_name, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{test_name:25} {status}")
        
        if result:
            passed_tests.append(test_name)
        else:
            failed_tests.append(test_name)
    
    print(f"\n📈 TOTAL: {len(passed_tests)}/{len(results)} tests passed")
    
    if failed_tests:
        print(f"\n❌ FAILED TESTS:")
        for test in failed_tests:
            print(f"  - {test}")
    
    if passed_tests:
        print(f"\n✅ PASSED TESTS:")
        for test in passed_tests:
            print(f"  - {test}")
    
    # Проверка критических функций
    critical_tests = ["voice_process", "get_meetings"]
    critical_passed = all(results.get(test, False) for test in critical_tests)
    
    if critical_passed:
        print("\n🎉 CRITICAL FUNCTIONALITY: All core meetings and voice endpoints working!")
    else:
        print("\n⚠️ CRITICAL ISSUES: Some core endpoints are not working properly")
    
    return results

if __name__ == "__main__":
    print(f"🔗 Backend URL: {BACKEND_URL}")
    results = asyncio.run(run_comprehensive_tests())
    
    # Exit code для CI/CD
    failed_count = sum(1 for result in results.values() if not result)
    sys.exit(failed_count)