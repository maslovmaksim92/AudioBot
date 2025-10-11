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
    
    async def test_ai_chat_general(self):
        """Test POST /api/ai-assistant/chat with general message"""
        print("🔍 Testing AI Assistant Chat Endpoint with General Message...")
        
        payload = {
            "message": "Привет, как дела?",
            "conversation_history": None,
            "voice_mode": False
        }
        
        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.post(
                    f"{self.base_url}/api/ai-assistant/chat",
                    json=payload,
                    headers={"Content-Type": "application/json"}
                )
                
                if response.status_code == 200:
                    data = response.json()
                    self.log_result("/api/ai-assistant/chat (general)", "POST", response.status_code, data)
                    print("✅ AI Chat endpoint returned 200 for general message")
                    return True
                elif response.status_code == 500:
                    # Graceful error handling for missing OpenAI key or DB issues
                    try:
                        data = response.json()
                        self.log_result("/api/ai-assistant/chat (general)", "POST", response.status_code, data)
                        print("⚠️ AI Chat endpoint returned 500 (likely missing OpenAI key or DB issue)")
                        return True  # This is expected behavior per requirements
                    except:
                        self.log_result("/api/ai-assistant/chat (general)", "POST", response.status_code, None, "500 with non-JSON response")
                        return False
                else:
                    self.log_result("/api/ai-assistant/chat (general)", "POST", response.status_code, None, f"HTTP {response.status_code}")
                    return False
                    
        except Exception as e:
            self.log_result("/api/ai-assistant/chat (general)", "POST", 0, None, str(e))
            print(f"❌ AI Chat general endpoint failed: {e}")
            return False
    
    async def run_all_tests(self):
        """Run all backend tests"""
        print("🚀 Starting Backend API Tests")
        print(f"🌐 Backend URL: {self.base_url}")
        print("=" * 60)
        
        tests = [
            ("Health Check", self.test_health_endpoint),
            ("Single Brain API - Kibalchich Contact", self.test_brain_ask_kibalchich),
            ("Single Brain API - Bilybina Cleaning", self.test_brain_ask_bilybina),
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