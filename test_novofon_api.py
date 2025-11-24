"""
Тестирование разных методов Novofon API
"""
import asyncio
import httpx
import hashlib
import hmac
import base64
from urllib.parse import urlencode
import os
from dotenv import load_dotenv

load_dotenv('/app/backend/.env')

API_KEY = os.getenv('novofon_appid', '')
API_SECRET = os.getenv('novofon_secret', '')
BASE_URL = "https://api.novofon.com/v1"

def generate_signature(method_path, query_string):
    """Генерирует SHA1 подпись"""
    string_to_sign = method_path + query_string
    signature_hash = hmac.new(
        API_SECRET.encode(),
        string_to_sign.encode(),
        hashlib.sha1
    ).digest()
    return base64.b64encode(signature_hash).decode()

async def test_info_balance():
    """Тест: проверка баланса"""
    print("\n" + "="*60)
    print("🧪 ТЕСТ 1: Проверка баланса /info/balance/")
    print("="*60)
    
    try:
        params = {"id": API_KEY}
        query_string = "?" + urlencode(params)
        method_path = "/info/balance/"
        
        signature = generate_signature(method_path, query_string)
        headers = {
            "Content-Type": "application/x-www-form-urlencoded",
            "X-API-Signature": signature
        }
        
        url = f"{BASE_URL}{method_path}"
        
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(url, params=params, headers=headers)
            
            print(f"URL: {response.url}")
            print(f"Status: {response.status_code}")
            print(f"Response: {response.text}")
            
            return response.status_code == 200
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        return False

async def test_statistics_calls():
    """Тест: статистика звонков"""
    print("\n" + "="*60)
    print("🧪 ТЕСТ 2: Статистика звонков /statistics/calls/")
    print("="*60)
    
    try:
        from datetime import datetime, timedelta
        
        end_date = datetime.now()
        start_date = end_date - timedelta(days=7)
        
        params = {
            "id": API_KEY,
            "start": start_date.strftime("%Y-%m-%d %H:%M:%S"),
            "end": end_date.strftime("%Y-%m-%d %H:%M:%S")
        }
        query_string = "?" + urlencode(params)
        method_path = "/statistics/calls/"
        
        signature = generate_signature(method_path, query_string)
        headers = {
            "Content-Type": "application/x-www-form-urlencoded",
            "X-API-Signature": signature
        }
        
        url = f"{BASE_URL}{method_path}"
        
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(url, params=params, headers=headers)
            
            print(f"URL: {response.url}")
            print(f"Status: {response.status_code}")
            print(f"Response: {response.text[:500]}")
            
            return response.status_code == 200
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        import traceback
        traceback.print_exc()
        return False

async def test_info_account():
    """Тест: информация об аккаунте"""
    print("\n" + "="*60)
    print("🧪 ТЕСТ 3: Информация об аккаунте /info/account/")
    print("="*60)
    
    try:
        params = {"id": API_KEY}
        query_string = "?" + urlencode(params)
        method_path = "/info/account/"
        
        signature = generate_signature(method_path, query_string)
        headers = {
            "Content-Type": "application/x-www-form-urlencoded",
            "X-API-Signature": signature
        }
        
        url = f"{BASE_URL}{method_path}"
        
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(url, params=params, headers=headers)
            
            print(f"URL: {response.url}")
            print(f"Status: {response.status_code}")
            print(f"Response: {response.text}")
            
            return response.status_code == 200
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        return False

async def main():
    print("="*60)
    print("🔍 ТЕСТИРОВАНИЕ NOVOFON API")
    print("="*60)
    print(f"API Key: {API_KEY}")
    print(f"API Secret: {'*' * 20}")
    print(f"Base URL: {BASE_URL}")
    
    results = {}
    
    results['balance'] = await test_info_balance()
    results['calls'] = await test_statistics_calls()
    results['account'] = await test_info_account()
    
    print("\n" + "="*60)
    print("📊 РЕЗУЛЬТАТЫ")
    print("="*60)
    for test_name, success in results.items():
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} - {test_name}")
    
    print("\n💡 Если все тесты падают с 500 ошибкой:")
    print("1. Проверьте что API включен в настройках Novofon")
    print("2. Проверьте правильность API Key и Secret")
    print("3. Возможно нужно использовать webhook вместо API")

if __name__ == "__main__":
    asyncio.run(main())
