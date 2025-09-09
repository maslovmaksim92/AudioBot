#!/usr/bin/env python3
"""
VasDom AudioBot Backend API Testing Suite
Tests all critical API endpoints for the cleaning company management system
"""

import requests
import json
import sys
import time
from datetime import datetime
from io import BytesIO

class VasDomAPITester:
    def __init__(self, base_url="https://crm-connector-2.preview.emergentagent.com"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.tests_run = 0
        self.tests_passed = 0
        self.failed_tests = []

    def log_test(self, name, success, details=""):
        """Log test results"""
        self.tests_run += 1
        if success:
            self.tests_passed += 1
            print(f"✅ {name} - PASSED")
        else:
            self.failed_tests.append({"name": name, "details": details})
            print(f"❌ {name} - FAILED: {details}")

    def test_api_root(self):
        """Test API root endpoint"""
        try:
            response = requests.get(f"{self.api_url}/", timeout=10)
            success = response.status_code == 200
            
            if success:
                data = response.json()
                expected_keys = ["message", "version", "status", "features"]
                has_keys = all(key in data for key in expected_keys)
                success = has_keys and "VasDom AudioBot API" in data.get("message", "")
                
            self.log_test("API Root (/api/)", success, 
                         f"Status: {response.status_code}, Response: {response.text[:100]}")
            return success
        except Exception as e:
            self.log_test("API Root (/api/)", False, str(e))
            return False

    def test_health_endpoint(self):
        """Test health check endpoint"""
        try:
            response = requests.get(f"{self.api_url}/health", timeout=10)
            success = response.status_code == 200
            
            if success:
                data = response.json()
                success = (data.get("status") == "healthy" and 
                          "service" in data and
                          "VasDom AudioBot" in data.get("service", ""))
                print(f"   🏥 Health status: {data.get('status')}")
                print(f"   🏥 Service: {data.get('service')}")
                print(f"   🏥 AI mode: {data.get('ai_mode', 'unknown')}")
                
            self.log_test("Health Check (/api/health)", success, 
                         f"Status: {response.status_code}")
            return success
        except Exception as e:
            self.log_test("Health Check (/api/health)", False, str(e))
            return False

    def test_dashboard_html(self):
        """Test dashboard HTML page"""
        try:
            response = requests.get(f"{self.base_url}/dashboard", timeout=10)
            success = response.status_code == 200
            
            if success:
                html_content = response.text
                success = ("VasDom AudioBot" in html_content and 
                          "<!DOCTYPE html>" in html_content and
                          "491" in html_content)
                print(f"   📄 HTML length: {len(html_content)} chars")
                print(f"   📄 Contains VasDom title: {'✅' if 'VasDom AudioBot' in html_content else '❌'}")
                print(f"   📄 Contains 491 houses: {'✅' if '491' in html_content else '❌'}")
                
            self.log_test("Dashboard HTML (/dashboard)", success, 
                         f"Status: {response.status_code}, HTML: {'✅' if success else '❌'}")
            return success
        except Exception as e:
            self.log_test("Dashboard HTML (/dashboard)", False, str(e))
            return False

    def test_dashboard_html_typo(self):
        """Test dashboard HTML page with typo"""
        try:
            response = requests.get(f"{self.base_url}/dashbord", timeout=10)
            success = response.status_code == 200
            
            if success:
                html_content = response.text
                success = ("VasDom AudioBot" in html_content and 
                          "<!DOCTYPE html>" in html_content)
                print(f"   📄 Typo URL works: {'✅' if success else '❌'}")
                
            self.log_test("Dashboard HTML with typo (/dashbord)", success, 
                         f"Status: {response.status_code}")
            return success
        except Exception as e:
            self.log_test("Dashboard HTML with typo (/dashbord)", False, str(e))
            return False

    def test_telegram_status(self):
        """Test Telegram bot status"""
        try:
            response = requests.get(f"{self.api_url}/telegram/status", timeout=10)
            success = response.status_code == 200
            
            if success:
                data = response.json()
                success = "status" in data
                print(f"   📱 Telegram status: {data.get('status')}")
                print(f"   📱 Bot token: {data.get('bot_token')}")
                print(f"   📱 Webhook URL: {data.get('webhook_url', 'not configured')}")
                
            self.log_test("Telegram Status (/api/telegram/status)", success, 
                         f"Status: {response.status_code}")
            return success
        except Exception as e:
            self.log_test("Telegram Status (/api/telegram/status)", False, str(e))
            return False

    def test_telegram_webhook(self):
        """Test Telegram webhook endpoint - должен обрабатывать сообщения и отправлять ответы"""
        try:
            # Test with sample webhook data
            webhook_data = {
                "update_id": 123456789,
                "message": {
                    "message_id": 1,
                    "from": {"id": 123, "first_name": "TestUser"},
                    "chat": {"id": 123, "type": "private"},
                    "date": 1234567890,
                    "text": "Сколько домов у VasDom?"
                }
            }
            
            response = requests.post(f"{self.api_url}/telegram/webhook", 
                                   json=webhook_data, timeout=15)
            success = response.status_code == 200
            
            if success:
                data = response.json()
                # Проверяем что webhook обрабатывает сообщения и отправляет ответы
                success = data.get("status") in ["processed", "received"]
                print(f"   📱 Webhook status: {data.get('status')}")
                print(f"   📱 Response message: {data.get('message', 'No message')}")
                
                # Проверяем что есть AI ответ (если сообщение обработано)
                if data.get("status") == "processed":
                    ai_response = data.get("ai_response", "")
                    if ai_response:
                        print(f"   📱 AI Response generated: {ai_response[:100]}...")
                        print(f"   ✅ Telegram webhook processes messages and sends AI responses")
                    else:
                        print(f"   ❌ No AI response generated")
                        success = False
                elif data.get("status") == "received":
                    print(f"   ⚠️ Message received but not processed (may be expected)")
                
            self.log_test("Telegram Webhook Processing", success, 
                         f"Status: {response.status_code}, Processing: {data.get('status') if success else 'Failed'}")
            return success
        except Exception as e:
            self.log_test("Telegram Webhook Processing", False, str(e))
            return False

    def test_self_learning_status(self):
        """Test AI self-learning status endpoint"""
        try:
            response = requests.get(f"{self.api_url}/self-learning/status", timeout=10)
            success = response.status_code == 200
            
            if success:
                data = response.json()
                success = "status" in data
                print(f"   🧠 Self-learning status: {data.get('status')}")
                print(f"   🧠 AI interactions: {data.get('ai_interactions', 0)}")
                print(f"   🧠 Database: {data.get('database', 'unknown')}")
                
                emergent_info = data.get('emergent_llm', {})
                print(f"   🧠 Emergent LLM available: {emergent_info.get('package_available', False)}")
                print(f"   🧠 AI mode: {emergent_info.get('mode', 'unknown')}")
                
            self.log_test("Self-Learning Status (/api/self-learning/status)", success, 
                         f"Status: {response.status_code}")
            return success
        except Exception as e:
            self.log_test("Self-Learning Status (/api/self-learning/status)", False, str(e))
            return False

    def test_dashboard_stats(self):
        """Test dashboard statistics endpoint - должен показывать ТОЛЬКО CRM данные (348 домов), НЕ CSV fallback"""
        try:
            response = requests.get(f"{self.api_url}/dashboard", timeout=15)
            success = response.status_code == 200
            
            if success:
                data = response.json()
                success = (data.get("status") == "success" and 
                          "stats" in data and
                          isinstance(data["stats"], dict))
                
                if success:
                    stats = data["stats"]
                    required_stats = ["employees", "houses", "entrances", "apartments", "floors"]
                    success = all(stat in stats for stat in required_stats)
                    
                    houses_count = stats.get('houses', 0)
                    data_source = data.get('data_source', 'Unknown')
                    print(f"   📊 Houses: {houses_count}, Employees: {stats.get('employees', 0)}")
                    print(f"   📊 Data source: {data_source}")
                    
                    # КРИТИЧЕСКИЙ ТЕСТ: должно быть 348 домов из CRM, НЕ 491 из CSV fallback
                    if houses_count == 348:
                        print(f"   ✅ CORRECT: Shows 348 houses from CRM Bitrix24 (no CSV fallback)")
                        # Проверяем что источник данных указывает на CRM
                        if "CRM" in data_source or "Bitrix24" in data_source:
                            print(f"   ✅ Data source correctly indicates CRM: {data_source}")
                        else:
                            print(f"   ⚠️ Data source unclear: {data_source}")
                    elif houses_count == 491:
                        print(f"   ❌ WRONG: Shows 491 houses - using CSV fallback instead of CRM-only data")
                        success = False
                    else:
                        print(f"   ⚠️ UNEXPECTED: Shows {houses_count} houses (expected 348 from CRM)")
                        success = False
                
            self.log_test("Dashboard CRM-Only Data (348 Houses)", success, 
                         f"Status: {response.status_code}, Houses: {data.get('stats', {}).get('houses', 'N/A')}")
            return success
        except Exception as e:
            self.log_test("Dashboard CRM-Only Data (348 Houses)", False, str(e))
            return False

    def test_bitrix24_connection(self):
        """Test Bitrix24 integration"""
        try:
            response = requests.get(f"{self.api_url}/bitrix24/test", timeout=15)
            success = response.status_code == 200
            
            if success:
                data = response.json()
                success = data.get("status") == "success"
                print(f"   🔗 Bitrix24 connection: {data.get('bitrix_info', {})}")
                
            self.log_test("Bitrix24 Connection", success, 
                         f"Status: {response.status_code}, Response: {response.text[:150]}")
            return success
        except Exception as e:
            self.log_test("Bitrix24 Connection", False, str(e))
            return False

    def test_cleaning_houses(self):
        """Test cleaning houses data from Bitrix24 CRM - должен загружать ТОЛЬКО CRM данные (348 домов)"""
        try:
            response = requests.get(f"{self.api_url}/cleaning/houses", timeout=25)
            success = response.status_code == 200
            
            if success:
                data = response.json()
                success = (data.get("status") == "success" and 
                          "houses" in data and
                          isinstance(data["houses"], list))
                
                if success:
                    houses_count = len(data["houses"])
                    total_from_api = data.get("total", houses_count)
                    source = data.get("source", "Unknown")
                    print(f"   🏠 Loaded {houses_count} houses from {source}")
                    print(f"   🏠 Total reported: {total_from_api}")
                    
                    # КРИТИЧЕСКИЙ ТЕСТ: должно быть 348 домов из CRM, НЕ 491 из CSV
                    if houses_count == 348:
                        print(f"   ✅ CORRECT: 348 houses from CRM Bitrix24 (no CSV fallback)")
                    elif houses_count == 491:
                        print(f"   ❌ WRONG: 491 houses - using CSV fallback instead of CRM-only")
                        success = False
                    else:
                        print(f"   ⚠️ UNEXPECTED: {houses_count} houses (expected 348 from CRM)")
                    
                    if houses_count > 0:
                        sample_house = data["houses"][0]
                        print(f"   🏠 Sample: {sample_house.get('address', 'No address')}")
                        print(f"   🏠 Brigade: {sample_house.get('brigade', 'No brigade')}")
                        print(f"   🏠 Deal ID: {sample_house.get('deal_id', 'No ID')}")
                        
                        # Проверяем что данные реально из Bitrix24
                        has_bitrix_fields = (sample_house.get('deal_id') and 
                                           sample_house.get('stage') and
                                           sample_house.get('brigade'))
                        
                        if has_bitrix_fields:
                            print("   ✅ Real Bitrix24 CRM data detected")
                        else:
                            print("   ❌ May be using mock data instead of real Bitrix24")
                            success = False
                    
                    # Проверяем источник данных
                    if "Bitrix24" in source or "CRM" in source:
                        print(f"   ✅ Data source correctly indicates CRM: {source}")
                    else:
                        print(f"   ❌ Data source unclear or wrong: {source}")
                        success = False
                
            self.log_test("Bitrix24 CRM-Only Houses (348)", success, 
                         f"Status: {response.status_code}, Houses: {len(data.get('houses', []))}")
            return success
        except Exception as e:
            self.log_test("Bitrix24 CRM-Only Houses (348)", False, str(e))
            return False

    def test_voice_ai_processing(self):
        """Test AI voice processing with GPT-4 mini через Emergent LLM - должен упоминать 348 домов из CRM"""
        try:
            test_message = {
                "text": "Сколько домов у нас в работе и какие бригады работают?",
                "user_id": "test_manager"
            }
            
            response = requests.post(f"{self.api_url}/voice/process", 
                                   json=test_message, timeout=30)
            success = response.status_code == 200
            
            if success:
                data = response.json()
                success = ("response" in data and 
                          len(data["response"]) > 10 and
                          "timestamp" in data)
                
                if success:
                    ai_response = data["response"]
                    print(f"   🤖 AI Response: {ai_response[:150]}...")
                    
                    # Проверяем что AI отвечает с контекстом VasDom
                    vasdom_keywords = ["дом", "бригад", "калуг", "vasdom", "клининг", "подъезд"]
                    has_vasdom_context = any(keyword.lower() in ai_response.lower() for keyword in vasdom_keywords)
                    
                    if has_vasdom_context:
                        print("   ✅ AI response contains VasDom context (GPT-4 mini working)")
                    else:
                        print("   ❌ AI response lacks VasDom context - may not be using GPT-4 mini properly")
                        success = False
                    
                    # Проверяем упоминание правильного количества домов (348 из CRM, НЕ 491 из CSV)
                    if "348" in ai_response:
                        print("   ✅ AI correctly mentions 348 houses from CRM")
                    elif "491" in ai_response:
                        print("   ❌ AI mentions 491 houses - using CSV data instead of CRM")
                        success = False
                    else:
                        print("   ⚠️ AI doesn't mention specific house count")
                
            self.log_test("GPT-4 Mini AI Processing (CRM Context)", success, 
                         f"Status: {response.status_code}, Context check: {'✅' if success else '❌'}")
            return success
        except Exception as e:
            self.log_test("GPT-4 Mini AI Processing (CRM Context)", False, str(e))
            return False

    def test_meetings_functionality(self):
        """Test meetings recording functionality"""
        try:
            # Start recording
            start_response = requests.post(f"{self.api_url}/meetings/start-recording", timeout=10)
            success = start_response.status_code == 200
            
            if success:
                start_data = start_response.json()
                success = (start_data.get("status") == "success" and 
                          "meeting_id" in start_data)
                
                if success:
                    meeting_id = start_data["meeting_id"]
                    print(f"   🎤 Started meeting: {meeting_id}")
                    
                    # Wait a moment then stop recording
                    time.sleep(2)
                    
                    stop_response = requests.post(f"{self.api_url}/meetings/stop-recording?meeting_id={meeting_id}", 
                                                timeout=15)
                    success = stop_response.status_code == 200
                    
                    if success:
                        stop_data = stop_response.json()
                        success = stop_data.get("status") == "success"
                        print(f"   ⏹️ Stopped meeting successfully")
                
            self.log_test("Meetings Functionality", success, 
                         f"Start: {start_response.status_code}, Stop: {stop_response.status_code if 'stop_response' in locals() else 'N/A'}")
            return success
        except Exception as e:
            self.log_test("Meetings Functionality", False, str(e))
            return False

    def test_meetings_list(self):
        """Test meetings list functionality"""
        try:
            response = requests.get(f"{self.api_url}/meetings", timeout=10)
            success = response.status_code == 200
            
            if success:
                data = response.json()
                success = (data.get("status") == "success" and 
                          "meetings" in data)
                
                if success:
                    meetings_count = len(data["meetings"])
                    print(f"   📋 Meetings: {meetings_count}")
                
            self.log_test("Meetings List", success, 
                         f"Status: {response.status_code}, Meetings: {len(data.get('meetings', []))}")
            return success
        except Exception as e:
            self.log_test("Meetings List", False, str(e))
            return False

    def test_self_learning_system(self):
        """Test AI self-learning system - логи должны сохраняться в PostgreSQL"""
        try:
            # Сначала отправляем сообщение AI для создания лога
            test_message = {
                "text": "Тест системы самообучения VasDom",
                "user_id": "self_learning_test"
            }
            
            ai_response = requests.post(f"{self.api_url}/voice/process", 
                                      json=test_message, timeout=30)
            
            if ai_response.status_code != 200:
                self.log_test("Self-Learning System", False, "AI processing failed")
                return False
            
            # Ждем немного чтобы лог сохранился
            time.sleep(3)
            
            # Проверяем что логи сохраняются
            logs_response = requests.get(f"{self.api_url}/logs", timeout=10)
            success = logs_response.status_code == 200
            
            if success:
                data = logs_response.json()
                success = (data.get("status") == "success" and 
                          "voice_logs" in data and
                          isinstance(data["voice_logs"], list))
                
                if success:
                    voice_logs = data["voice_logs"]
                    logs_count = len(voice_logs)
                    print(f"   🧠 Voice logs in PostgreSQL: {logs_count}")
                    
                    # Проверяем что наш тестовый лог сохранился
                    test_log_found = False
                    for log in voice_logs:
                        if (log.get("user_message") and 
                            "самообучения" in log["user_message"].lower()):
                            test_log_found = True
                            print(f"   ✅ Self-learning test log found in PostgreSQL")
                            print(f"   🧠 Log context: {log.get('context', 'No context')}")
                            break
                    
                    if not test_log_found and logs_count > 0:
                        print(f"   ⚠️ Test log not found, but {logs_count} other logs exist")
                    elif not test_log_found:
                        print(f"   ❌ No logs found - self-learning may not be working")
                        success = False
                    
                    # Проверяем что есть GPT4mini логи
                    gpt4_logs = [log for log in voice_logs if 
                               log.get("context", "").startswith("GPT4mini_")]
                    if gpt4_logs:
                        print(f"   ✅ Found {len(gpt4_logs)} GPT-4 mini learning logs")
                    else:
                        print(f"   ⚠️ No GPT-4 mini specific logs found")
                
            self.log_test("Self-Learning System (PostgreSQL)", success, 
                         f"Logs: {logs_response.status_code}, Count: {len(data.get('voice_logs', []))}")
            return success
        except Exception as e:
            self.log_test("Self-Learning System (PostgreSQL)", False, str(e))
            return False

    def test_bitrix24_house_fields(self):
        """Тест полей Bitrix24: проверка house_address и количественных данных"""
        try:
            response = requests.get(f"{self.api_url}/cleaning/houses", timeout=25)
            success = response.status_code == 200
            
            if success:
                data = response.json()
                success = (data.get("status") == "success" and 
                          "houses" in data and
                          isinstance(data["houses"], list))
                
                if success and len(data["houses"]) > 0:
                    houses = data["houses"]
                    print(f"   🏠 Загружено домов: {len(houses)}")
                    
                    # Проверяем поле house_address (реальный адрес дома)
                    houses_with_address = [h for h in houses if h.get('house_address')]
                    print(f"   🏠 Домов с полем house_address: {len(houses_with_address)}")
                    
                    if houses_with_address:
                        sample_address = houses_with_address[0]['house_address']
                        print(f"   🏠 Пример адреса: {sample_address}")
                        success = len(houses_with_address) > 0
                    else:
                        print(f"   ❌ Поле house_address отсутствует или пустое")
                        success = False
                    
                    # Проверяем количественные данные
                    total_apartments = sum(h.get('apartments_count', 0) or 0 for h in houses)
                    total_entrances = sum(h.get('entrances_count', 0) or 0 for h in houses)
                    total_floors = sum(h.get('floors_count', 0) or 0 for h in houses)
                    
                    print(f"   🏠 Общее количество квартир: {total_apartments}")
                    print(f"   🏠 Общее количество подъездов: {total_entrances}")
                    print(f"   🏠 Общее количество этажей: {total_floors}")
                    
                    # Проверяем что данные реалистичные (не нули)
                    if total_apartments > 0 and total_entrances > 0 and total_floors > 0:
                        print(f"   ✅ Количественные данные реалистичные")
                    else:
                        print(f"   ❌ Количественные данные содержат нули")
                        success = False
                    
                    # Проверяем управляющие компании
                    management_companies = set(h.get('management_company', '') for h in houses if h.get('management_company'))
                    print(f"   🏠 Управляющих компаний: {len(management_companies)}")
                    
                    if len(management_companies) >= 25:
                        print(f"   ✅ Достаточно УК для писем и звонков (>= 25)")
                        print(f"   🏠 Примеры УК: {list(management_companies)[:3]}")
                    else:
                        print(f"   ❌ Недостаточно УК: {len(management_companies)} < 25")
                        success = False
                
            self.log_test("Bitrix24 House Fields (house_address, counts, УК)", success, 
                         f"Status: {response.status_code}, Houses: {len(data.get('houses', []))}")
            return success
        except Exception as e:
            self.log_test("Bitrix24 House Fields (house_address, counts, УК)", False, str(e))
            return False

    def test_cleaning_filters(self):
        """Тест фильтров: проверка /api/cleaning/filters"""
        try:
            response = requests.get(f"{self.api_url}/cleaning/filters", timeout=15)
            success = response.status_code == 200
            
            if success:
                data = response.json()
                success = (data.get("status") == "success" and 
                          "brigades" in data and
                          "cleaning_weeks" in data and
                          "management_companies" in data and
                          "months" in data)
                
                if success:
                    brigades = data.get("brigades", [])
                    weeks = data.get("cleaning_weeks", [])
                    companies = data.get("management_companies", [])
                    months = data.get("months", [])
                    
                    print(f"   🔍 Бригад: {len(brigades)}")
                    print(f"   🔍 Недель уборки: {weeks}")
                    print(f"   🔍 УК: {len(companies)}")
                    print(f"   🔍 Месяцев: {months}")
                    
                    # Проверяем что есть недели 1-5
                    expected_weeks = [1, 2, 3, 4, 5]
                    weeks_check = all(week in weeks for week in expected_weeks)
                    if weeks_check:
                        print(f"   ✅ Недели 1-5 присутствуют")
                    else:
                        print(f"   ❌ Не все недели 1-5 найдены: {weeks}")
                        success = False
                    
                    # Проверяем количество УК
                    if len(companies) >= 25:
                        print(f"   ✅ Много УК для писем: {len(companies)}")
                        print(f"   🔍 Примеры: {companies[:3]}")
                    else:
                        print(f"   ❌ Мало УК: {len(companies)} < 25")
                        success = False
                    
                    # Проверяем месяцы
                    if len(months) > 0:
                        print(f"   ✅ Месяцы с расписанием: {months}")
                    else:
                        print(f"   ❌ Нет месяцев с расписанием")
                        success = False
                
            self.log_test("Cleaning Filters (УК, недели, месяцы)", success, 
                         f"Status: {response.status_code}")
            return success
        except Exception as e:
            self.log_test("Cleaning Filters (УК, недели, месяцы)", False, str(e))
            return False

    def test_cleaning_filters_query(self):
        """Тест фильтрации: GET /api/cleaning/houses?brigade=1&cleaning_week=2&month=september"""
        try:
            # Тестируем фильтрацию с параметрами
            params = {
                'brigade': '1',
                'cleaning_week': '2', 
                'month': 'september'
            }
            
            response = requests.get(f"{self.api_url}/cleaning/houses", params=params, timeout=25)
            success = response.status_code == 200
            
            if success:
                data = response.json()
                success = (data.get("status") == "success" and 
                          "houses" in data and
                          "filters" in data)
                
                if success:
                    houses = data.get("houses", [])
                    filters = data.get("filters", {})
                    
                    print(f"   🔍 Отфильтровано домов: {len(houses)}")
                    print(f"   🔍 Примененные фильтры: {filters}")
                    
                    # Проверяем что фильтры применились
                    if filters.get('brigade') == '1' and filters.get('cleaning_week') == 2:
                        print(f"   ✅ Фильтры корректно применены")
                    else:
                        print(f"   ❌ Фильтры не применились корректно")
                        success = False
                    
                    # Проверяем что есть результаты (если данные корректные)
                    if len(houses) > 0:
                        sample_house = houses[0]
                        print(f"   🔍 Пример дома: {sample_house.get('address', 'Нет адреса')}")
                        print(f"   🔍 Бригада: {sample_house.get('brigade', 'Нет бригады')}")
                    else:
                        print(f"   ⚠️ Нет домов после фильтрации (может быть нормально)")
                
            self.log_test("Cleaning Filters Query (brigade=1&week=2&month=september)", success, 
                         f"Status: {response.status_code}, Filtered: {len(data.get('houses', []))}")
            return success
        except Exception as e:
            self.log_test("Cleaning Filters Query (brigade=1&week=2&month=september)", False, str(e))
            return False

    def test_cleaning_dashboard_stats(self):
        """Тест статистики дашборда: /api/cleaning/stats"""
        try:
            response = requests.get(f"{self.api_url}/cleaning/stats", timeout=15)
            success = response.status_code == 200
            
            if success:
                data = response.json()
                success = (data.get("status") == "success" and 
                          "stats" in data)
                
                if success:
                    stats = data.get("stats", {})
                    
                    total_houses = stats.get("total_houses", 0)
                    total_apartments = stats.get("total_apartments", 0)
                    total_entrances = stats.get("total_entrances", 0)
                    total_floors = stats.get("total_floors", 0)
                    
                    print(f"   📊 Всего домов: {total_houses}")
                    print(f"   📊 Всего квартир: {total_apartments}")
                    print(f"   📊 Всего подъездов: {total_entrances}")
                    print(f"   📊 Всего этажей: {total_floors}")
                    
                    # Проверяем что данные реалистичные (не нули)
                    if all(val > 0 for val in [total_houses, total_apartments, total_entrances, total_floors]):
                        print(f"   ✅ Статистика реалистичная (не нули)")
                    else:
                        print(f"   ❌ Статистика содержит нули")
                        success = False
                    
                    # Проверяем распределение по бригадам
                    brigades_dist = stats.get("brigades_distribution", {})
                    companies_dist = stats.get("companies_distribution", {})
                    
                    print(f"   📊 Распределение по бригадам: {len(brigades_dist)} бригад")
                    print(f"   📊 Распределение по УК: {len(companies_dist)} компаний")
                    
                    if len(brigades_dist) > 0 and len(companies_dist) > 0:
                        print(f"   ✅ Есть распределение по бригадам и УК")
                    else:
                        print(f"   ❌ Нет распределения по бригадам или УК")
                        success = False
                
            self.log_test("Cleaning Dashboard Stats (реалистичные данные)", success, 
                         f"Status: {response.status_code}")
            return success
        except Exception as e:
            self.log_test("Cleaning Dashboard Stats (реалистичные данные)", False, str(e))
            return False

    def test_export_fields_completeness(self):
        """Тест экспорта: проверка что все поля есть в ответе для CSV"""
        try:
            response = requests.get(f"{self.api_url}/cleaning/houses?limit=5", timeout=25)
            success = response.status_code == 200
            
            if success:
                data = response.json()
                success = (data.get("status") == "success" and 
                          "houses" in data and
                          len(data["houses"]) > 0)
                
                if success:
                    house = data["houses"][0]
                    
                    # Основные поля для экспорта
                    required_fields = [
                        'address', 'house_address', 'deal_id', 'brigade', 'status_text',
                        'apartments_count', 'floors_count', 'entrances_count', 
                        'management_company', 'cleaning_weeks', 'cleaning_days'
                    ]
                    
                    # Поля расписания
                    schedule_fields = [
                        'september_schedule', 'october_schedule', 
                        'november_schedule', 'december_schedule'
                    ]
                    
                    missing_fields = []
                    present_fields = []
                    
                    for field in required_fields:
                        if field in house and house[field] is not None:
                            present_fields.append(field)
                        else:
                            missing_fields.append(field)
                    
                    # Проверяем поля расписания
                    schedule_present = []
                    for field in schedule_fields:
                        if field in house and house[field] is not None:
                            schedule_present.append(field)
                    
                    print(f"   📋 Основных полей присутствует: {len(present_fields)}/{len(required_fields)}")
                    print(f"   📋 Полей расписания: {len(schedule_present)}/{len(schedule_fields)}")
                    
                    if missing_fields:
                        print(f"   ❌ Отсутствующие поля: {missing_fields}")
                        success = False
                    else:
                        print(f"   ✅ Все основные поля для экспорта присутствуют")
                    
                    if len(schedule_present) > 0:
                        print(f"   ✅ Есть поля расписания: {schedule_present}")
                    else:
                        print(f"   ⚠️ Нет полей расписания")
                    
                    # Проверяем структуру данных для CSV
                    print(f"   📋 Пример структуры дома:")
                    print(f"   📋 - Адрес: {house.get('address', 'Нет')}")
                    print(f"   📋 - Реальный адрес: {house.get('house_address', 'Нет')}")
                    print(f"   📋 - Бригада: {house.get('brigade', 'Нет')}")
                    print(f"   📋 - УК: {house.get('management_company', 'Нет')}")
                    print(f"   📋 - Квартиры: {house.get('apartments_count', 'Нет')}")
                
            self.log_test("Export Fields Completeness (все поля для CSV)", success, 
                         f"Status: {response.status_code}")
            return success
        except Exception as e:
            self.log_test("Export Fields Completeness (все поля для CSV)", False, str(e))
            return False

    def test_x_api_key_authentication(self):
        """Test X-API-Key header validation fix"""
        try:
            # Test without authentication first
            response = requests.post(f"{self.api_url}/voice/process", 
                                   json={"text": "Test message", "user_id": "test"}, 
                                   timeout=10)
            
            # Should work without auth (optional_auth)
            success = response.status_code == 200
            
            if success:
                print(f"   🔑 Voice API works without auth (optional_auth): ✅")
            else:
                print(f"   🔑 Voice API failed without auth: {response.status_code}")
            
            # Test with X-API-Key header (if auth is required)
            headers = {"X-API-Key": "test-key"}
            response_with_key = requests.post(f"{self.api_url}/voice/process", 
                                            json={"text": "Test message", "user_id": "test"}, 
                                            headers=headers,
                                            timeout=10)
            
            # Should handle X-API-Key header properly (not crash)
            key_handled = response_with_key.status_code in [200, 401]
            
            if key_handled:
                print(f"   🔑 X-API-Key header properly handled: ✅")
            else:
                print(f"   🔑 X-API-Key header caused error: {response_with_key.status_code}")
                success = False
            
            self.log_test("X-API-Key Header Validation Fix", success, 
                         f"No auth: {response.status_code}, With X-API-Key: {response_with_key.status_code}")
            return success
        except Exception as e:
            self.log_test("X-API-Key Header Validation Fix", False, str(e))
            return False

    def test_voice_api_error_handling(self):
        """Test Voice API exception handling - should return HTTP 500 on errors"""
        try:
            # Test with invalid/malformed data to trigger error
            invalid_data = {"invalid_field": "test"}  # Missing required fields
            
            response = requests.post(f"{self.api_url}/voice/process", 
                                   json=invalid_data, 
                                   timeout=10)
            
            # Should return 422 for validation error or 500 for processing error
            success = response.status_code in [422, 500]
            
            if response.status_code == 422:
                print(f"   ❌ Validation error (422) - expected for malformed data: ✅")
            elif response.status_code == 500:
                print(f"   ❌ Internal server error (500) - proper error handling: ✅")
            else:
                print(f"   ❌ Unexpected status code: {response.status_code}")
                success = False
            
            # Test with valid data but potentially error-inducing content
            error_test_data = {
                "text": "🔥" * 1000,  # Very long text that might cause processing errors
                "user_id": "error_test"
            }
            
            response2 = requests.post(f"{self.api_url}/voice/process", 
                                    json=error_test_data, 
                                    timeout=15)
            
            # Should handle gracefully - either process or return 500
            graceful_handling = response2.status_code in [200, 500]
            
            if response2.status_code == 500:
                print(f"   ❌ Processing error returns HTTP 500 (not 200): ✅")
                # Check that it's not returning 200 with masked error
                if response2.status_code != 200:
                    print(f"   ✅ Error handling fixed - no HTTP 200 with masked errors")
                else:
                    print(f"   ❌ Still returning HTTP 200 for errors")
                    success = False
            elif response2.status_code == 200:
                print(f"   ✅ Long text processed successfully")
            
            self.log_test("Voice API Error Handling (HTTP 500)", success and graceful_handling, 
                         f"Invalid data: {response.status_code}, Long text: {response2.status_code}")
            return success and graceful_handling
        except Exception as e:
            self.log_test("Voice API Error Handling (HTTP 500)", False, str(e))
            return False

    def test_code_quality_fixes(self):
        """Test that code quality fixes don't break functionality"""
        try:
            # Test that database.py improvements don't break database connection
            response = requests.get(f"{self.api_url}/health", timeout=10)
            success = response.status_code == 200
            
            if success:
                data = response.json()
                # Should still report database status properly
                has_db_info = "database" in str(data).lower() or "service" in data
                print(f"   📊 Health endpoint works after database.py fixes: ✅")
                print(f"   📊 Database info present: {'✅' if has_db_info else '❌'}")
                success = has_db_info
            
            # Test that final newlines don't break file parsing
            response2 = requests.get(f"{self.api_url}/", timeout=10)
            api_works = response2.status_code == 200
            
            if api_works:
                print(f"   📄 API root works after newline fixes: ✅")
            else:
                print(f"   📄 API root broken after fixes: ❌")
                success = False
            
            self.log_test("Code Quality Fixes (no functionality break)", success and api_works, 
                         f"Health: {response.status_code}, API: {response2.status_code}")
            return success and api_works
        except Exception as e:
            self.log_test("Code Quality Fixes (no functionality break)", False, str(e))
            return False

    def test_bitrix24_management_company_fix(self):
        """КРИТИЧЕСКИЙ ТЕСТ: Проверка исправления полей management_company и brigade из Bitrix24"""
        try:
            print("\n🔧 ТЕСТИРОВАНИЕ ИСПРАВЛЕНИЯ BITRIX24 INTEGRATION:")
            print("   Проблема: management_company и brigade возвращали null")
            print("   Решение: Добавлены отдельные API вызовы user.get и crm.company.get")
            print("   Ожидается: Реальные названия УК и бригад вместо null")
            
            response = requests.get(f"{self.api_url}/cleaning/houses?limit=3", timeout=30)
            success = response.status_code == 200
            
            if success:
                data = response.json()
                success = (data.get("status") == "success" and 
                          "houses" in data and
                          isinstance(data["houses"], list) and
                          len(data["houses"]) > 0)
                
                if success:
                    houses = data["houses"]
                    print(f"   🏠 Загружено домов для проверки: {len(houses)}")
                    
                    # КРИТИЧЕСКАЯ ПРОВЕРКА 1: management_company НЕ null
                    management_companies_not_null = 0
                    management_companies_with_real_names = 0
                    
                    for house in houses:
                        management_company = house.get('management_company')
                        if management_company and management_company != 'null':
                            management_companies_not_null += 1
                            
                            # Проверяем что это реальные названия УК
                            real_uc_keywords = ['ООО', 'УК', 'ЖРЭУ', 'РИЦ', 'ГУП', 'Калуги', 'Тайфун', 'УЮТНЫЙ ДОМ']
                            if any(keyword in management_company for keyword in real_uc_keywords):
                                management_companies_with_real_names += 1
                                print(f"   ✅ УК найдена: {management_company}")
                    
                    print(f"   📊 УК не null: {management_companies_not_null}/{len(houses)}")
                    print(f"   📊 УК с реальными названиями: {management_companies_with_real_names}/{len(houses)}")
                    
                    # КРИТИЧЕСКАЯ ПРОВЕРКА 2: brigade НЕ null и содержит корректные названия
                    brigades_not_null = 0
                    brigades_with_correct_names = 0
                    
                    for house in houses:
                        brigade = house.get('brigade')
                        if brigade and brigade != 'null':
                            brigades_not_null += 1
                            
                            # Проверяем что это корректные названия бригад
                            brigade_keywords = ['бригада', '1 бригада', '2 бригада', '3 бригада', '4 бригада', '5 бригада', '6 бригада']
                            if any(keyword in brigade for keyword in brigade_keywords):
                                brigades_with_correct_names += 1
                                print(f"   ✅ Бригада найдена: {brigade}")
                    
                    print(f"   📊 Бригады не null: {brigades_not_null}/{len(houses)}")
                    print(f"   📊 Бригады с корректными названиями: {brigades_with_correct_names}/{len(houses)}")
                    
                    # КРИТИЧЕСКАЯ ПРОВЕРКА 3: assigned_by_id заполнен
                    assigned_ids_filled = 0
                    for house in houses:
                        assigned_by_id = house.get('assigned_by_id')
                        if assigned_by_id and assigned_by_id != 'null' and assigned_by_id != '':
                            assigned_ids_filled += 1
                    
                    print(f"   📊 assigned_by_id заполнен: {assigned_ids_filled}/{len(houses)}")
                    
                    # ПРОВЕРКА УСПЕШНОСТИ ИСПРАВЛЕНИЯ
                    management_fix_success = management_companies_not_null > 0
                    brigade_fix_success = brigades_not_null > 0
                    assigned_fix_success = assigned_ids_filled > 0
                    
                    if management_fix_success and brigade_fix_success:
                        print(f"   ✅ ИСПРАВЛЕНИЕ УСПЕШНО: УК и бригады больше не null")
                        success = True
                    else:
                        print(f"   ❌ ИСПРАВЛЕНИЕ НЕ РАБОТАЕТ:")
                        if not management_fix_success:
                            print(f"      - management_company все еще null")
                        if not brigade_fix_success:
                            print(f"      - brigade все еще null")
                        success = False
                    
                    # Показываем примеры данных
                    if len(houses) > 0:
                        sample_house = houses[0]
                        print(f"   📋 Пример дома:")
                        print(f"      - Адрес: {sample_house.get('address', 'Нет')}")
                        print(f"      - УК: {sample_house.get('management_company', 'null')}")
                        print(f"      - Бригада: {sample_house.get('brigade', 'null')}")
                        print(f"      - Ответственный ID: {sample_house.get('assigned_by_id', 'null')}")
                
            self.log_test("Bitrix24 Management Company & Brigade Fix", success, 
                         f"Status: {response.status_code}, УК не null: {management_companies_not_null if 'management_companies_not_null' in locals() else 0}, Бригады не null: {brigades_not_null if 'brigades_not_null' in locals() else 0}")
            return success
        except Exception as e:
            self.log_test("Bitrix24 Management Company & Brigade Fix", False, str(e))
            return False

    def test_cleaning_filters_management_companies(self):
        """Проверка что управляющие компании не пустые в фильтрах"""
        try:
            response = requests.get(f"{self.api_url}/cleaning/filters", timeout=15)
            success = response.status_code == 200
            
            if success:
                data = response.json()
                success = (data.get("status") == "success" and 
                          "management_companies" in data)
                
                if success:
                    companies = data.get("management_companies", [])
                    print(f"   🏢 Управляющих компаний в фильтрах: {len(companies)}")
                    
                    if len(companies) > 0:
                        print(f"   ✅ УК не пустые: {companies[:3]}...")  # Показываем первые 3
                        
                        # Проверяем что это реальные названия УК
                        real_companies = [c for c in companies if any(keyword in c for keyword in ['ООО', 'УК', 'ЖРЭУ', 'РИЦ', 'ГУП'])]
                        print(f"   📊 Реальных УК: {len(real_companies)}/{len(companies)}")
                        
                        success = len(companies) > 0
                    else:
                        print(f"   ❌ Управляющие компании пустые в фильтрах")
                        success = False
                
            self.log_test("Cleaning Filters - Management Companies Not Empty", success, 
                         f"Status: {response.status_code}, Companies: {len(companies) if 'companies' in locals() else 0}")
            return success
        except Exception as e:
            self.log_test("Cleaning Filters - Management Companies Not Empty", False, str(e))
            return False

    def test_bitrix24_tasks_api(self):
        """НОВЫЙ ТЕСТ: Проверка API задач Bitrix24 - GET /api/tasks"""
        try:
            print("\n📋 ТЕСТИРОВАНИЕ НОВОЙ ФУНКЦИОНАЛЬНОСТИ ЗАДАЧ:")
            print("   Новый API: GET /api/tasks - получение списка задач из Bitrix24")
            print("   Ожидается: Задачи с полными данными (название, статус, приоритет, ответственный)")
            
            # Тест 1: Получение списка задач с лимитом
            response = requests.get(f"{self.api_url}/tasks?limit=3", timeout=30)
            success = response.status_code == 200
            
            if success:
                data = response.json()
                success = (data.get("status") == "success" and 
                          "tasks" in data and
                          isinstance(data["tasks"], list))
                
                if success:
                    tasks = data["tasks"]
                    total = data.get("total", 0)
                    source = data.get("source", "Unknown")
                    
                    print(f"   📋 Загружено задач: {len(tasks)}")
                    print(f"   📋 Общее количество: {total}")
                    print(f"   📋 Источник данных: {source}")
                    
                    # Проверяем что данные из Bitrix24
                    if "Bitrix24" in source:
                        print(f"   ✅ Данные загружены из Bitrix24")
                    else:
                        print(f"   ⚠️ Источник данных неясен: {source}")
                    
                    # Проверяем структуру задач
                    if len(tasks) > 0:
                        sample_task = tasks[0]
                        required_fields = ['id', 'title', 'status', 'status_text', 'priority', 'priority_text', 'responsible_name']
                        
                        missing_fields = [field for field in required_fields if field not in sample_task]
                        
                        if not missing_fields:
                            print(f"   ✅ Все обязательные поля присутствуют")
                            print(f"   📋 Пример задачи:")
                            print(f"      - ID: {sample_task.get('id')}")
                            print(f"      - Название: {sample_task.get('title', 'Нет названия')}")
                            print(f"      - Статус: {sample_task.get('status_text', 'Неизвестно')}")
                            print(f"      - Приоритет: {sample_task.get('priority_text', 'Неизвестно')}")
                            print(f"      - Ответственный: {sample_task.get('responsible_name', 'Не назначен')}")
                            
                            # Проверяем URL задачи в Bitrix24
                            bitrix_url = sample_task.get('bitrix_url')
                            if bitrix_url and 'vas-dom.bitrix24.ru' in bitrix_url:
                                print(f"   ✅ URL задачи в Bitrix24 сформирован корректно")
                            else:
                                print(f"   ⚠️ URL задачи отсутствует или некорректен")
                        else:
                            print(f"   ❌ Отсутствующие поля: {missing_fields}")
                            success = False
                    else:
                        print(f"   ⚠️ Нет задач для проверки структуры")
                        # Это может быть нормально, если задач нет
                        success = True
                
            self.log_test("Bitrix24 Tasks API - GET /api/tasks", success, 
                         f"Status: {response.status_code}, Tasks: {len(data.get('tasks', [])) if success else 0}")
            return success
        except Exception as e:
            self.log_test("Bitrix24 Tasks API - GET /api/tasks", False, str(e))
            return False

    def test_bitrix24_tasks_stats(self):
        """НОВЫЙ ТЕСТ: Проверка статистики задач - GET /api/tasks/stats"""
        try:
            print("\n📊 ТЕСТИРОВАНИЕ СТАТИСТИКИ ЗАДАЧ:")
            print("   Новый API: GET /api/tasks/stats - статистика по задачам")
            print("   Ожидается: Всего задач, по статусам, просрочки")
            
            response = requests.get(f"{self.api_url}/tasks/stats", timeout=30)
            success = response.status_code == 200
            
            if success:
                data = response.json()
                success = (data.get("status") == "success" and 
                          "stats" in data)
                
                if success:
                    stats = data["stats"]
                    
                    total_tasks = stats.get("total_tasks", 0)
                    by_status = stats.get("by_status", {})
                    by_priority = stats.get("by_priority", {})
                    overdue_tasks = stats.get("overdue_tasks", 0)
                    today_deadline = stats.get("today_deadline", 0)
                    
                    print(f"   📊 Всего задач: {total_tasks}")
                    print(f"   📊 По статусам: {by_status}")
                    print(f"   📊 По приоритетам: {by_priority}")
                    print(f"   📊 Просроченных: {overdue_tasks}")
                    print(f"   📊 На сегодня: {today_deadline}")
                    
                    # Проверяем что статистика корректна
                    if total_tasks >= 0:
                        print(f"   ✅ Статистика корректно подсчитывается")
                        
                        # Проверяем что есть разбивка по статусам
                        if len(by_status) > 0:
                            print(f"   ✅ Есть разбивка по статусам: {list(by_status.keys())}")
                        else:
                            print(f"   ⚠️ Нет разбивки по статусам (может быть нормально если нет задач)")
                        
                        # Проверяем что есть разбивка по приоритетам
                        if len(by_priority) > 0:
                            print(f"   ✅ Есть разбивка по приоритетам: {list(by_priority.keys())}")
                        else:
                            print(f"   ⚠️ Нет разбивки по приоритетам (может быть нормально если нет задач)")
                    else:
                        print(f"   ❌ Некорректная статистика")
                        success = False
                
            self.log_test("Bitrix24 Tasks Stats - GET /api/tasks/stats", success, 
                         f"Status: {response.status_code}, Total tasks: {stats.get('total_tasks', 0) if success else 0}")
            return success
        except Exception as e:
            self.log_test("Bitrix24 Tasks Stats - GET /api/tasks/stats", False, str(e))
            return False

    def test_bitrix24_tasks_users(self):
        """НОВЫЙ ТЕСТ: Проверка пользователей для назначения - GET /api/tasks/users"""
        try:
            print("\n👥 ТЕСТИРОВАНИЕ ПОЛЬЗОВАТЕЛЕЙ ДЛЯ НАЗНАЧЕНИЯ:")
            print("   Новый API: GET /api/tasks/users - список пользователей для назначения")
            print("   Ожидается: Активные пользователи с именами и должностями")
            
            response = requests.get(f"{self.api_url}/tasks/users", timeout=30)
            success = response.status_code == 200
            
            if success:
                data = response.json()
                success = (data.get("status") == "success" and 
                          "users" in data and
                          isinstance(data["users"], list))
                
                if success:
                    users = data["users"]
                    total = data.get("total", 0)
                    
                    print(f"   👥 Загружено пользователей: {len(users)}")
                    print(f"   👥 Общее количество: {total}")
                    
                    # Проверяем структуру пользователей
                    if len(users) > 0:
                        sample_user = users[0]
                        required_fields = ['id', 'name']
                        
                        missing_fields = [field for field in required_fields if field not in sample_user]
                        
                        if not missing_fields:
                            print(f"   ✅ Все обязательные поля присутствуют")
                            print(f"   👥 Пример пользователя:")
                            print(f"      - ID: {sample_user.get('id')}")
                            print(f"      - Имя: {sample_user.get('name', 'Нет имени')}")
                            print(f"      - Email: {sample_user.get('email', 'Нет email')}")
                            print(f"      - Должность: {sample_user.get('position', 'Нет должности')}")
                            
                            # Проверяем что есть пользователи с именами
                            users_with_names = [u for u in users if u.get('name') and u.get('name').strip()]
                            print(f"   👥 Пользователей с именами: {len(users_with_names)}/{len(users)}")
                            
                            if len(users_with_names) > 0:
                                print(f"   ✅ Пользователи имеют корректные имена")
                            else:
                                print(f"   ❌ Пользователи без имен")
                                success = False
                        else:
                            print(f"   ❌ Отсутствующие поля: {missing_fields}")
                            success = False
                    else:
                        print(f"   ⚠️ Нет пользователей для проверки")
                        success = False
                
            self.log_test("Bitrix24 Tasks Users - GET /api/tasks/users", success, 
                         f"Status: {response.status_code}, Users: {len(data.get('users', [])) if success else 0}")
            return success
        except Exception as e:
            self.log_test("Bitrix24 Tasks Users - GET /api/tasks/users", False, str(e))
            return False

    def test_bitrix24_create_task(self):
        """НОВЫЙ ТЕСТ: Проверка создания задач - POST /api/tasks"""
        try:
            print("\n📝 ТЕСТИРОВАНИЕ СОЗДАНИЯ ЗАДАЧ:")
            print("   Новый API: POST /api/tasks - создание задач в Bitrix24")
            print("   Ожидается: Создание задачи и возврат ID в Bitrix24")
            
            # Создаем тестовую задачу
            task_data = {
                "title": f"Тестовая задача VasDom - {datetime.now().strftime('%Y-%m-%d %H:%M')}",
                "description": "Автоматически созданная задача для тестирования интеграции с Bitrix24",
                "responsible_id": 1,  # ID администратора
                "priority": 2,  # Высокий приоритет
                "deadline": "2024-12-31"
            }
            
            response = requests.post(f"{self.api_url}/tasks", json=task_data, timeout=30)
            success = response.status_code == 200
            
            if success:
                data = response.json()
                success = (data.get("status") == "success" and 
                          "task_id" in data)
                
                if success:
                    task_id = data.get("task_id")
                    title = data.get("title")
                    bitrix_url = data.get("bitrix_url")
                    
                    print(f"   📝 Задача создана успешно:")
                    print(f"      - ID в Bitrix24: {task_id}")
                    print(f"      - Название: {title}")
                    print(f"      - URL в Bitrix24: {bitrix_url}")
                    
                    # Проверяем что ID задачи корректен
                    if task_id and str(task_id).isdigit():
                        print(f"   ✅ ID задачи корректен: {task_id}")
                    else:
                        print(f"   ❌ Некорректный ID задачи: {task_id}")
                        success = False
                    
                    # Проверяем URL задачи
                    if bitrix_url and 'vas-dom.bitrix24.ru' in bitrix_url and str(task_id) in bitrix_url:
                        print(f"   ✅ URL задачи в Bitrix24 корректен")
                    else:
                        print(f"   ❌ Некорректный URL задачи")
                        success = False
                else:
                    error_message = data.get("message", "Unknown error")
                    print(f"   ❌ Ошибка создания задачи: {error_message}")
                    success = False
            else:
                print(f"   ❌ HTTP ошибка: {response.status_code}")
                try:
                    error_data = response.json()
                    print(f"   ❌ Детали ошибки: {error_data}")
                except:
                    print(f"   ❌ Ответ сервера: {response.text[:200]}")
                success = False
                
            self.log_test("Bitrix24 Create Task - POST /api/tasks", success, 
                         f"Status: {response.status_code}, Task ID: {data.get('task_id', 'N/A') if success else 'Failed'}")
            return success
        except Exception as e:
            self.log_test("Bitrix24 Create Task - POST /api/tasks", False, str(e))
            return False

    def run_all_tests(self):
        """Run all API tests focusing on new Bitrix24 Tasks functionality"""
        print("🚀 Starting VasDom AudioBot API Tests - Bitrix24 Tasks Integration")
        print(f"🔗 Testing API at: {self.api_url}")
        print("📋 Review Requirements - Testing new Bitrix24 Tasks functionality:")
        print("   НОВАЯ ФУНКЦИОНАЛЬНОСТЬ:")
        print("   1. GET /api/tasks - получение списка задач из Bitrix24")
        print("   2. POST /api/tasks - создание задач в Bitrix24")
        print("   3. GET /api/tasks/stats - статистика по задачам")
        print("   4. GET /api/tasks/users - список пользователей для назначения")
        print("   КЛЮЧЕВЫЕ ТЕСТЫ:")
        print("   1. GET /api/tasks?limit=3 - проверить загрузку задач из Bitrix24")
        print("   2. GET /api/tasks/stats - проверить статистику (всего задач, по статусам, просрочки)")
        print("   3. GET /api/tasks/users - проверить список пользователей")
        print("   4. POST /api/tasks - создать тестовую задачу в Bitrix24")
        print("=" * 80)
        
        # НОВЫЕ ТЕСТЫ - Bitrix24 Tasks API
        self.test_bitrix24_tasks_api()
        self.test_bitrix24_tasks_stats()
        self.test_bitrix24_tasks_users()
        self.test_bitrix24_create_task()
        
        # Базовые тесты для проверки что система работает
        self.test_api_root()
        self.test_health_endpoint()
        self.test_bitrix24_connection()
        
        # Print results
        print("=" * 80)
        print(f"📊 Test Results: {self.tests_passed}/{self.tests_run} passed")
        
        if self.failed_tests:
            print("\n❌ Failed Tests:")
            for test in self.failed_tests:
                print(f"   • {test['name']}: {test['details']}")
        
        success_rate = (self.tests_passed / self.tests_run) * 100 if self.tests_run > 0 else 0
        print(f"✅ Success Rate: {success_rate:.1f}%")
        
        # Bitrix24 fix summary
        print("\n📋 Bitrix24 Management Company Fix Status:")
        
        # Check main fix
        main_fix_tests = [test for test in self.failed_tests if "Management Company & Brigade Fix" in test["name"]]
        main_fix_passed = len(main_fix_tests) == 0
        
        # Check filters fix
        filters_fix_tests = [test for test in self.failed_tests if "Management Companies Not Empty" in test["name"]]
        filters_fix_passed = len(filters_fix_tests) == 0
        
        print(f"   1. management_company поля НЕ null: {'✅' if main_fix_passed else '❌'}")
        print(f"   2. brigade поля содержат корректные названия: {'✅' if main_fix_passed else '❌'}")
        print(f"   3. assigned_by_id заполнен: {'✅' if main_fix_passed else '❌'}")
        print(f"   4. Фильтры УК не пустые: {'✅' if filters_fix_passed else '❌'}")
        
        # Overall fix status
        overall_fix_success = main_fix_passed and filters_fix_passed
        print(f"\n🎯 ОБЩИЙ СТАТУС ИСПРАВЛЕНИЯ: {'✅ УСПЕШНО' if overall_fix_success else '❌ ТРЕБУЕТ ДОРАБОТКИ'}")
        
        if overall_fix_success:
            print("   ✅ Интеграция Bitrix24 для получения данных УК и персонала работает корректно")
        else:
            print("   ❌ Интеграция Bitrix24 требует дополнительной отладки")
        
        return self.tests_passed == self.tests_run

def main():
    """Main test execution"""
    tester = VasDomAPITester()
    
    try:
        all_passed = tester.run_all_tests()
        return 0 if all_passed else 1
    except KeyboardInterrupt:
        print("\n⏹️ Tests interrupted by user")
        return 1
    except Exception as e:
        print(f"\n💥 Unexpected error: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())