#!/usr/bin/env python3
"""
VasDom AudioBot - Backend API Testing
Тестирование всех meetings API endpoints и voice processing endpoints
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
    """Получить URL backend из frontend/.env"""
    try:
        frontend_env_path = Path(__file__).parent / "frontend" / ".env"
        if frontend_env_path.exists():
            with open(frontend_env_path, 'r') as f:
                for line in f:
                    if line.startswith('REACT_APP_BACKEND_URL='):
                        url = line.split('=', 1)[1].strip()
                        return f"{url}/api"
        
        # Fallback
        return "https://crmunified.preview.emergentagent.com/api"
    except Exception as e:
        print(f"❌ Error reading backend URL: {e}")
        return "https://crmunified.preview.emergentagent.com/api"

BACKEND_URL = get_backend_url()
print(f"🔗 Testing backend at: {BACKEND_URL}")

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
                else:
                    print(f"❌ FAILED: HTTP {response.status_code}")
                    print(f"Response: {response.text}")
                    return False
                    
        except Exception as e:
            print(f"❌ ERROR: {e}")
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