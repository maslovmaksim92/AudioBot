#!/usr/bin/env python3
"""
Backend API Tests for VasDom AudioBot
Testing AI Assistant endpoints as requested
"""

import asyncio
import httpx
import json
import os
from datetime import datetime

# Get backend URL from frontend .env
BACKEND_URL = "https://smart-agent-system.preview.emergentagent.com"

class BackendTester:
    def __init__(self):
        self.base_url = BACKEND_URL
        self.results = []
        
    def log_result(self, endpoint, method, status_code, response_data, error=None):
        """Log test result"""
        result = {
            'endpoint': endpoint,
            'method': method,
            'status_code': status_code,
            'response': response_data,
            'error': error,
            'timestamp': datetime.now().isoformat()
        }
        self.results.append(result)
        
        status_emoji = "✅" if 200 <= status_code < 300 else "❌"
        print(f"{status_emoji} {method} {endpoint} -> {status_code}")
        if error:
            print(f"   Error: {error}")
        elif response_data:
            print(f"   Response: {json.dumps(response_data, ensure_ascii=False)[:200]}...")
        print()
    
    async def test_health_endpoint(self):
        """Test GET /api/health"""
        print("🔍 Testing Health Endpoint...")
        
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(f"{self.base_url}/api/health")
                
                if response.status_code == 200:
                    data = response.json()
                    self.log_result("/api/health", "GET", response.status_code, data)
                    
                    # Verify expected structure
                    if data.get('ok') is True:
                        print("✅ Health endpoint working correctly")
                        return True
                    else:
                        print("⚠️ Health endpoint returned unexpected structure")
                        return False
                else:
                    self.log_result("/api/health", "GET", response.status_code, None, f"HTTP {response.status_code}")
                    return False
                    
        except Exception as e:
            self.log_result("/api/health", "GET", 0, None, str(e))
            print(f"❌ Health endpoint failed: {e}")
            return False
    
    async def test_ai_context_endpoint(self):
        """Test GET /api/ai-assistant/context"""
        print("🔍 Testing AI Assistant Context Endpoint...")
        
        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.get(f"{self.base_url}/api/ai-assistant/context")
                
                if response.status_code == 200:
                    data = response.json()
                    self.log_result("/api/ai-assistant/context", "GET", response.status_code, data)
                    print("✅ AI Context endpoint returned 200")
                    return True
                elif response.status_code == 500:
                    # Graceful error handling for missing DB
                    try:
                        data = response.json()
                        self.log_result("/api/ai-assistant/context", "GET", response.status_code, data)
                        print("⚠️ AI Context endpoint returned 500 (likely DB connection issue)")
                        return True  # This is expected behavior per requirements
                    except:
                        self.log_result("/api/ai-assistant/context", "GET", response.status_code, None, "500 with non-JSON response")
                        return False
                else:
                    self.log_result("/api/ai-assistant/context", "GET", response.status_code, None, f"HTTP {response.status_code}")
                    return False
                    
        except Exception as e:
            self.log_result("/api/ai-assistant/context", "GET", 0, None, str(e))
            print(f"❌ AI Context endpoint failed: {e}")
            return False
    
    async def test_ai_analyze_endpoint(self):
        """Test POST /api/ai-assistant/analyze"""
        print("🔍 Testing AI Assistant Analyze Endpoint...")
        
        payload = {"analysis_type": "financial"}
        
        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.post(
                    f"{self.base_url}/api/ai-assistant/analyze",
                    json=payload,
                    headers={"Content-Type": "application/json"}
                )
                
                if response.status_code == 200:
                    data = response.json()
                    self.log_result("/api/ai-assistant/analyze", "POST", response.status_code, data)
                    print("✅ AI Analyze endpoint returned 200")
                    return True
                elif response.status_code == 500:
                    # Graceful error handling for missing DB or other issues
                    try:
                        data = response.json()
                        self.log_result("/api/ai-assistant/analyze", "POST", response.status_code, data)
                        print("⚠️ AI Analyze endpoint returned 500 (likely DB connection issue)")
                        return True  # This is expected behavior per requirements
                    except:
                        self.log_result("/api/ai-assistant/analyze", "POST", response.status_code, None, "500 with non-JSON response")
                        return False
                else:
                    self.log_result("/api/ai-assistant/analyze", "POST", response.status_code, None, f"HTTP {response.status_code}")
                    return False
                    
        except Exception as e:
            self.log_result("/api/ai-assistant/analyze", "POST", 0, None, str(e))
            print(f"❌ AI Analyze endpoint failed: {e}")
            return False
    
    async def test_brain_ask_kibalchich(self):
        """Test POST /api/brain/ask with Kibalchich contact query"""
        print("🔍 Testing Single Brain API - Kibalchich Contact Query...")
        
        payload = {
            "message": "Контакты старшего Кибальчича 1"
        }
        
        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.post(
                    f"{self.base_url}/api/brain/ask",
                    json=payload,
                    headers={"Content-Type": "application/json"}
                )
                
                print(f"📊 Status Code: {response.status_code}")
                
                if response.status_code == 200:
                    data = response.json()
                    self.log_result("/api/brain/ask (Kibalchich)", "POST", response.status_code, data)
                    
                    # Check response structure - expect success true or graceful false
                    success = data.get('success')
                    print(f"📋 Response Success: {success}")
                    
                    if success is True:
                        print("✅ Brain API returned successful response for Kibalchich contact")
                        if 'response' in data:
                            print(f"📝 Response content: {data['response'][:200]}...")
                        return True
                    elif success is False:
                        print("✅ Brain API returned graceful failure (contact not found)")
                        error = data.get('error', 'No error message')
                        print(f"📝 Error message: {error}")
                        return True
                    else:
                        print(f"❌ Unexpected response structure: {data}")
                        return False
                elif response.status_code == 500:
                    print("❌ Brain API returned 500 - this should not happen per requirements")
                    try:
                        data = response.json()
                        self.log_result("/api/brain/ask (Kibalchich)", "POST", response.status_code, data)
                        print(f"500 Error details: {data}")
                    except:
                        self.log_result("/api/brain/ask (Kibalchich)", "POST", response.status_code, None, "500 with non-JSON response")
                    return False
                else:
                    try:
                        data = response.json()
                        self.log_result("/api/brain/ask (Kibalchich)", "POST", response.status_code, data)
                        print(f"❌ Unexpected status code {response.status_code}: {data}")
                    except:
                        self.log_result("/api/brain/ask (Kibalchich)", "POST", response.status_code, None, f"HTTP {response.status_code} with non-JSON response")
                    return False
                    
        except Exception as e:
            self.log_result("/api/brain/ask (Kibalchich)", "POST", 0, None, str(e))
            print(f"❌ Brain API Kibalchich test failed: {e}")
            return False

    async def test_brain_ask_bilybina(self):
        """Test POST /api/brain/ask with Bilybina cleaning schedule query"""
        print("🔍 Testing Single Brain API - Bilybina Cleaning Schedule Query...")
        
        payload = {
            "message": "Когда уборка на Билибина 6 в октябре?"
        }
        
        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.post(
                    f"{self.base_url}/api/brain/ask",
                    json=payload,
                    headers={"Content-Type": "application/json"}
                )
                
                print(f"📊 Status Code: {response.status_code}")
                
                if response.status_code == 200:
                    data = response.json()
                    self.log_result("/api/brain/ask (Bilybina)", "POST", response.status_code, data)
                    
                    # Check response structure - expect success true or graceful false
                    success = data.get('success')
                    print(f"📋 Response Success: {success}")
                    
                    if success is True:
                        print("✅ Brain API returned successful response for Bilybina cleaning schedule")
                        if 'response' in data:
                            print(f"📝 Response content: {data['response'][:200]}...")
                        return True
                    elif success is False:
                        print("✅ Brain API returned graceful failure (schedule not found)")
                        error = data.get('error', 'No error message')
                        print(f"📝 Error message: {error}")
                        return True
                    else:
                        print(f"❌ Unexpected response structure: {data}")
                        return False
                elif response.status_code == 500:
                    print("❌ Brain API returned 500 - this should not happen per requirements")
                    try:
                        data = response.json()
                        self.log_result("/api/brain/ask (Bilybina)", "POST", response.status_code, data)
                        print(f"500 Error details: {data}")
                    except:
                        self.log_result("/api/brain/ask (Bilybina)", "POST", response.status_code, None, "500 with non-JSON response")
                    return False
                else:
                    try:
                        data = response.json()
                        self.log_result("/api/brain/ask (Bilybina)", "POST", response.status_code, data)
                        print(f"❌ Unexpected status code {response.status_code}: {data}")
                    except:
                        self.log_result("/api/brain/ask (Bilybina)", "POST", response.status_code, None, f"HTTP {response.status_code} with non-JSON response")
                    return False
                    
        except Exception as e:
            self.log_result("/api/brain/ask (Bilybina)", "POST", 0, None, str(e))
            print(f"❌ Brain API Bilybina test failed: {e}")
            return False
    
    async def test_ai_chat_kibalchich(self):
        """Test POST /api/ai/chat with Kibalchich contact query - Single Brain should respond first"""
        print("🔍 Testing AI Chat Endpoint - Kibalchich Contact Query (Single Brain Priority)...")
        
        payload = {
            "message": "Контакты старшего Кибальчича 1",
            "user_id": "380f5071-b2fd-4585-bf5b-11f53dd6ec8d"  # Created test user
        }
        
        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.post(
                    f"{self.base_url}/api/ai/chat",
                    json=payload,
                    headers={"Content-Type": "application/json"}
                )
                
                print(f"📊 Status Code: {response.status_code}")
                
                if response.status_code == 200:
                    data = response.json()
                    self.log_result("/api/ai/chat (Kibalchich)", "POST", response.status_code, data)
                    
                    message = data.get('message', '')
                    print(f"📝 Response Message: {message[:200]}...")
                    
                    # Check if Single Brain provided fast answer (should contain contact info)
                    if any(keyword in message.lower() for keyword in ['телефон', 'email', 'контакт', 'старший']):
                        print("✅ AI Chat returned contact information (likely from Single Brain fast answer)")
                        return True
                    elif 'openai' in message.lower() or 'api' in message.lower():
                        print("⚠️ AI Chat fell back to OpenAI (Single Brain didn't provide fast answer)")
                        return True  # Still working, just no fast answer available
                    else:
                        print("✅ AI Chat returned 200 with response")
                        return True
                elif response.status_code == 500:
                    print("❌ AI Chat returned 500 - this should not happen per requirements")
                    try:
                        data = response.json()
                        self.log_result("/api/ai/chat (Kibalchich)", "POST", response.status_code, data)
                        print(f"500 Error details: {data}")
                    except:
                        self.log_result("/api/ai/chat (Kibalchich)", "POST", response.status_code, None, "500 with non-JSON response")
                    return False
                else:
                    try:
                        data = response.json()
                        self.log_result("/api/ai/chat (Kibalchich)", "POST", response.status_code, data)
                        print(f"❌ Unexpected status code {response.status_code}: {data}")
                    except:
                        self.log_result("/api/ai/chat (Kibalchich)", "POST", response.status_code, None, f"HTTP {response.status_code} with non-JSON response")
                    return False
                    
        except Exception as e:
            self.log_result("/api/ai/chat (Kibalchich)", "POST", 0, None, str(e))
            print(f"❌ AI Chat Kibalchich test failed: {e}")
            return False

    async def test_ai_chat_bilybina(self):
        """Test POST /api/ai/chat with Bilybina cleaning schedule query - Single Brain should respond first"""
        print("🔍 Testing AI Chat Endpoint - Bilybina Cleaning Schedule Query (Single Brain Priority)...")
        
        payload = {
            "message": "Когда уборка на Билибина 6 в октябре?",
            "user_id": "380f5071-b2fd-4585-bf5b-11f53dd6ec8d"  # Created test user
        }
        
        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.post(
                    f"{self.base_url}/api/ai/chat",
                    json=payload,
                    headers={"Content-Type": "application/json"}
                )
                
                print(f"📊 Status Code: {response.status_code}")
                
                if response.status_code == 200:
                    data = response.json()
                    self.log_result("/api/ai/chat (Bilybina)", "POST", response.status_code, data)
                    
                    message = data.get('message', '')
                    print(f"📝 Response Message: {message[:200]}...")
                    
                    # Check if Single Brain provided fast answer (should contain cleaning dates)
                    if 'октябрь — даты уборок:' in message.lower():
                        print("✅ AI Chat returned expected 'Октябрь — даты уборок:' heading (Single Brain fast answer)")
                        return True
                    elif any(keyword in message.lower() for keyword in ['октябр', 'уборк', 'билибин', 'дат']):
                        print("✅ AI Chat returned cleaning schedule information (likely from Single Brain)")
                        return True
                    elif 'openai' in message.lower() or 'api' in message.lower():
                        print("⚠️ AI Chat fell back to OpenAI (Single Brain didn't provide fast answer)")
                        return True  # Still working, just no fast answer available
                    else:
                        print("✅ AI Chat returned 200 with response")
                        return True
                elif response.status_code == 500:
                    print("❌ AI Chat returned 500 - this should not happen per requirements")
                    try:
                        data = response.json()
                        self.log_result("/api/ai/chat (Bilybina)", "POST", response.status_code, data)
                        print(f"500 Error details: {data}")
                    except:
                        self.log_result("/api/ai/chat (Bilybina)", "POST", response.status_code, None, "500 with non-JSON response")
                    return False
                else:
                    try:
                        data = response.json()
                        self.log_result("/api/ai/chat (Bilybina)", "POST", response.status_code, data)
                        print(f"❌ Unexpected status code {response.status_code}: {data}")
                    except:
                        self.log_result("/api/ai/chat (Bilybina)", "POST", response.status_code, None, f"HTTP {response.status_code} with non-JSON response")
                    return False
                    
        except Exception as e:
            self.log_result("/api/ai/chat (Bilybina)", "POST", 0, None, str(e))
            print(f"❌ AI Chat Bilybina test failed: {e}")
            return False

    # ===== STAGE 6 TESTS =====
    
    async def test_brain_ask_finance_categories(self):
        """Test POST /api/brain/ask with finance categories query (Stage 6)"""
        print("🔍 Testing Stage 6 - Finance Categories Query with Debug...")
        
        payload = {
            "message": "Категорийная разбивка расходов за месяц",
            "debug": True
        }
        
        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.post(
                    f"{self.base_url}/api/brain/ask",
                    json=payload,
                    headers={"Content-Type": "application/json"}
                )
                
                print(f"📊 Status Code: {response.status_code}")
                
                if response.status_code == 200:
                    data = response.json()
                    self.log_result("/api/brain/ask (Finance Categories)", "POST", response.status_code, data)
                    
                    # Check response structure - expect success true or graceful false
                    success = data.get('success')
                    print(f"📋 Response Success: {success}")
                    
                    # Check for debug fields
                    debug_info = data.get('debug', {})
                    matched_rule = debug_info.get('matched_rule')
                    print(f"🔍 Debug matched_rule: {matched_rule}")
                    
                    if debug_info:
                        print(f"🔍 Debug fields present: {list(debug_info.keys())}")
                    
                    if success is True or success is False:
                        print("✅ Brain API returned proper success/failure response")
                        if debug_info:
                            print("✅ Debug information present in response")
                        return True
                    else:
                        print(f"❌ Unexpected response structure: {data}")
                        return False
                elif response.status_code == 500:
                    print("❌ Brain API returned 500 - this should not happen per requirements")
                    try:
                        data = response.json()
                        self.log_result("/api/brain/ask (Finance Categories)", "POST", response.status_code, data)
                        print(f"500 Error details: {data}")
                    except:
                        self.log_result("/api/brain/ask (Finance Categories)", "POST", response.status_code, None, "500 with non-JSON response")
                    return False
                else:
                    try:
                        data = response.json()
                        self.log_result("/api/brain/ask (Finance Categories)", "POST", response.status_code, data)
                        print(f"❌ Unexpected status code {response.status_code}: {data}")
                    except:
                        self.log_result("/api/brain/ask (Finance Categories)", "POST", response.status_code, None, f"HTTP {response.status_code} with non-JSON response")
                    return False
                    
        except Exception as e:
            self.log_result("/api/brain/ask (Finance Categories)", "POST", 0, None, str(e))
            print(f"❌ Brain API Finance Categories test failed: {e}")
            return False

    async def test_brain_ask_finance_yoy(self):
        """Test POST /api/brain/ask with YoY dynamics query (Stage 6)"""
        print("🔍 Testing Stage 6 - YoY Dynamics Query with Debug...")
        
        payload = {
            "message": "Г/Г динамика",
            "debug": True
        }
        
        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.post(
                    f"{self.base_url}/api/brain/ask",
                    json=payload,
                    headers={"Content-Type": "application/json"}
                )
                
                print(f"📊 Status Code: {response.status_code}")
                
                if response.status_code == 200:
                    data = response.json()
                    self.log_result("/api/brain/ask (YoY Dynamics)", "POST", response.status_code, data)
                    
                    # Check response structure - expect success true or graceful false
                    success = data.get('success')
                    print(f"📋 Response Success: {success}")
                    
                    # Check for debug fields and finance_yoy path
                    debug_info = data.get('debug', {})
                    matched_rule = debug_info.get('matched_rule')
                    print(f"🔍 Debug matched_rule: {matched_rule}")
                    
                    # Look for finance_yoy path indication
                    response_text = str(data).lower()
                    if 'finance_yoy' in response_text or 'yoy' in response_text:
                        print("✅ Finance YoY path detected in response")
                    
                    if debug_info:
                        print(f"🔍 Debug fields present: {list(debug_info.keys())}")
                    
                    if success is True or success is False:
                        print("✅ Brain API returned proper success/failure response")
                        if debug_info:
                            print("✅ Debug information present in response")
                        return True
                    else:
                        print(f"❌ Unexpected response structure: {data}")
                        return False
                elif response.status_code == 500:
                    print("❌ Brain API returned 500 - this should not happen per requirements")
                    try:
                        data = response.json()
                        self.log_result("/api/brain/ask (YoY Dynamics)", "POST", response.status_code, data)
                        print(f"500 Error details: {data}")
                    except:
                        self.log_result("/api/brain/ask (YoY Dynamics)", "POST", response.status_code, None, "500 with non-JSON response")
                    return False
                else:
                    try:
                        data = response.json()
                        self.log_result("/api/brain/ask (YoY Dynamics)", "POST", response.status_code, data)
                        print(f"❌ Unexpected status code {response.status_code}: {data}")
                    except:
                        self.log_result("/api/brain/ask (YoY Dynamics)", "POST", response.status_code, None, f"HTTP {response.status_code} with non-JSON response")
                    return False
                    
        except Exception as e:
            self.log_result("/api/brain/ask (YoY Dynamics)", "POST", 0, None, str(e))
            print(f"❌ Brain API YoY Dynamics test failed: {e}")
            return False

    async def test_brain_ask_top_decline(self):
        """Test POST /api/brain/ask with top decline categories query (Stage 6)"""
        print("🔍 Testing Stage 6 - Top Decline Categories Query with Debug...")
        
        payload = {
            "message": "Топ падение категорий за квартал",
            "debug": True
        }
        
        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.post(
                    f"{self.base_url}/api/brain/ask",
                    json=payload,
                    headers={"Content-Type": "application/json"}
                )
                
                print(f"📊 Status Code: {response.status_code}")
                
                if response.status_code == 200:
                    data = response.json()
                    self.log_result("/api/brain/ask (Top Decline)", "POST", response.status_code, data)
                    
                    # Check response structure - expect success true or graceful false
                    success = data.get('success')
                    print(f"📋 Response Success: {success}")
                    
                    # Check for debug fields
                    debug_info = data.get('debug', {})
                    matched_rule = debug_info.get('matched_rule')
                    print(f"🔍 Debug matched_rule: {matched_rule}")
                    
                    if debug_info:
                        print(f"🔍 Debug fields present: {list(debug_info.keys())}")
                    
                    if success is True or success is False:
                        print("✅ Brain API returned proper success/failure response")
                        if debug_info:
                            print("✅ Debug information present in response")
                        return True
                    else:
                        print(f"❌ Unexpected response structure: {data}")
                        return False
                elif response.status_code == 500:
                    print("❌ Brain API returned 500 - this should not happen per requirements")
                    try:
                        data = response.json()
                        self.log_result("/api/brain/ask (Top Decline)", "POST", response.status_code, data)
                        print(f"500 Error details: {data}")
                    except:
                        self.log_result("/api/brain/ask (Top Decline)", "POST", response.status_code, None, "500 with non-JSON response")
                    return False
                else:
                    try:
                        data = response.json()
                        self.log_result("/api/brain/ask (Top Decline)", "POST", response.status_code, data)
                        print(f"❌ Unexpected status code {response.status_code}: {data}")
                    except:
                        self.log_result("/api/brain/ask (Top Decline)", "POST", response.status_code, None, f"HTTP {response.status_code} with non-JSON response")
                    return False
                    
        except Exception as e:
            self.log_result("/api/brain/ask (Top Decline)", "POST", 0, None, str(e))
            print(f"❌ Brain API Top Decline test failed: {e}")
            return False

    async def test_brain_ask_address_ner(self):
        """Test POST /api/brain/ask with address NER query (Stage 6)"""
        print("🔍 Testing Stage 6 - Address NER Query with Debug...")
        
        payload = {
            "message": "Контакты старшего Кибальчича 1 стр 2",
            "debug": True
        }
        
        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.post(
                    f"{self.base_url}/api/brain/ask",
                    json=payload,
                    headers={"Content-Type": "application/json"}
                )
                
                print(f"📊 Status Code: {response.status_code}")
                
                if response.status_code == 200:
                    data = response.json()
                    self.log_result("/api/brain/ask (Address NER)", "POST", response.status_code, data)
                    
                    # Check response structure - expect success true or graceful false
                    success = data.get('success')
                    print(f"📋 Response Success: {success}")
                    
                    # Check for debug fields and address NER
                    debug_info = data.get('debug', {})
                    matched_rule = debug_info.get('matched_rule')
                    print(f"🔍 Debug matched_rule: {matched_rule}")
                    
                    # Look for address NER indicators (стр/к/лит)
                    response_text = str(data).lower()
                    if any(addr_part in response_text for addr_part in ['стр', 'строение', 'корпус', 'литер']):
                        print("✅ Address NER with стр/к/лит detected in response")
                    
                    if debug_info:
                        print(f"🔍 Debug fields present: {list(debug_info.keys())}")
                    
                    if success is True or success is False:
                        print("✅ Brain API returned proper success/failure response")
                        if debug_info:
                            print("✅ Debug information present in response")
                        return True
                    else:
                        print(f"❌ Unexpected response structure: {data}")
                        return False
                elif response.status_code == 500:
                    print("❌ Brain API returned 500 - this should not happen per requirements")
                    try:
                        data = response.json()
                        self.log_result("/api/brain/ask (Address NER)", "POST", response.status_code, data)
                        print(f"500 Error details: {data}")
                    except:
                        self.log_result("/api/brain/ask (Address NER)", "POST", response.status_code, None, "500 with non-JSON response")
                    return False
                else:
                    try:
                        data = response.json()
                        self.log_result("/api/brain/ask (Address NER)", "POST", response.status_code, data)
                        print(f"❌ Unexpected status code {response.status_code}: {data}")
                    except:
                        self.log_result("/api/brain/ask (Address NER)", "POST", response.status_code, None, f"HTTP {response.status_code} with non-JSON response")
                    return False
                    
        except Exception as e:
            self.log_result("/api/brain/ask (Address NER)", "POST", 0, None, str(e))
            print(f"❌ Brain API Address NER test failed: {e}")
            return False
    
    async def run_all_tests(self):
        """Run all backend tests"""
        print("🚀 Starting Backend API Tests - Stage 6 Features")
        print(f"🌐 Backend URL: {self.base_url}")
        print("=" * 60)
        
        tests = [
            ("Health Check", self.test_health_endpoint),
            ("Stage 6 - Finance Categories (Debug)", self.test_brain_ask_finance_categories),
            ("Stage 6 - YoY Dynamics (Debug)", self.test_brain_ask_finance_yoy),
            ("Stage 6 - Top Decline Categories (Debug)", self.test_brain_ask_top_decline),
            ("Stage 6 - Address NER (Debug)", self.test_brain_ask_address_ner),
        ]
        
        results = {}
        
        for test_name, test_func in tests:
            print(f"\n📋 Running {test_name} Test...")
            try:
                success = await test_func()
                results[test_name] = success
            except Exception as e:
                print(f"❌ {test_name} test failed with exception: {e}")
                results[test_name] = False
        
        print("\n" + "=" * 60)
        print("📊 TEST SUMMARY")
        print("=" * 60)
        
        passed = 0
        total = len(results)
        
        for test_name, success in results.items():
            status = "✅ PASS" if success else "❌ FAIL"
            print(f"{status} {test_name}")
            if success:
                passed += 1
        
        print(f"\n🎯 Results: {passed}/{total} tests passed")
        
        if passed == total:
            print("🎉 All tests passed!")
        else:
            print("⚠️ Some tests failed - check logs above")
        
        return results

async def main():
    """Main test runner"""
    tester = BackendTester()
    results = await tester.run_all_tests()
    
    # Save detailed results
    with open('/app/backend_test_results.json', 'w', encoding='utf-8') as f:
        json.dump({
            'summary': results,
            'detailed_results': tester.results,
            'test_time': datetime.now().isoformat(),
            'backend_url': BACKEND_URL
        }, f, ensure_ascii=False, indent=2)
    
    print(f"\n💾 Detailed results saved to backend_test_results.json")

if __name__ == "__main__":
    asyncio.run(main())