"""
Проверка доступности webhook endpoint
"""
import asyncio
import httpx

BACKEND_URL = "https://audiobot-qci2.onrender.com"
WEBHOOK_URL = f"{BACKEND_URL}/api/call-summary/webhook/novofon"

async def test_webhook_endpoint():
    """Проверяет что webhook endpoint доступен"""
    print("="*60)
    print("🧪 ТЕСТ: Проверка webhook endpoint")
    print("="*60)
    print(f"URL: {WEBHOOK_URL}")
    print()
    
    try:
        # Пробуем отправить тестовые данные
        test_data = {
            "call_id": "test_12345",
            "caller": "+79001234567",
            "called": "+79843330712",
            "direction": "in",
            "duration": 120,
            "status": "answered",
            "record_url": "https://example.com/test.mp3",
            "timestamp": "2025-11-24T10:00:00Z"
        }
        
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(WEBHOOK_URL, json=test_data)
            
            print(f"✅ Статус: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                print(f"✅ Ответ: {data}")
                print("\n✅ Webhook endpoint работает!")
                return True
            else:
                print(f"⚠️ Неожиданный статус: {response.status_code}")
                print(f"Response: {response.text}")
                return False
                
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        return False

async def test_health():
    """Проверяет что backend запущен"""
    print("\n" + "="*60)
    print("🧪 ТЕСТ: Проверка что backend запущен")
    print("="*60)
    
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(f"{BACKEND_URL}/api/health")
            
            if response.status_code == 200:
                print(f"✅ Backend запущен: {response.json()}")
                return True
            else:
                print(f"❌ Backend не отвечает: {response.status_code}")
                return False
                
    except Exception as e:
        print(f"❌ Ошибка подключения: {e}")
        return False

async def main():
    print("\n" + "="*60)
    print("🚀 ПРОВЕРКА WEBHOOK ENDPOINT")
    print("="*60)
    
    # Проверяем что backend запущен
    backend_ok = await test_health()
    
    if not backend_ok:
        print("\n❌ Backend не запущен! Webhook не будет работать.")
        print("Проверьте https://dashboard.render.com")
        return
    
    # Проверяем webhook endpoint
    webhook_ok = await test_webhook_endpoint()
    
    print("\n" + "="*60)
    print("📊 ИТОГИ")
    print("="*60)
    print(f"Backend: {'✅ OK' if backend_ok else '❌ FAIL'}")
    print(f"Webhook: {'✅ OK' if webhook_ok else '❌ FAIL'}")
    
    if backend_ok and webhook_ok:
        print("\n✅ ВСЁ ГОТОВО!")
        print("\n📝 СЛЕДУЮЩИЙ ШАГ:")
        print("1. Сделайте тестовый звонок на/с +79843330712")
        print("2. Подождите 1-2 минуты")
        print("3. Проверьте Telegram группу -5007549435")
        print("\n🎉 Там должна появиться карточка звонка!")
    else:
        print("\n⚠️ Есть проблемы - webhook может не работать")

if __name__ == "__main__":
    asyncio.run(main())
