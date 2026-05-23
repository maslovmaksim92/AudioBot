#!/usr/bin/env python3
"""
Тест отправки фото через Telegram API
"""
import asyncio
import httpx
import os
from dotenv import load_dotenv

load_dotenv('/app/backend/.env')

BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
TEST_CHAT_ID = os.getenv('TELEGRAM_TARGET_CHAT_ID')  # Тестовая группа

API_URL = f"https://api.telegram.org/bot{BOT_TOKEN}"

async def test_send_photo():
    """Тест отправки тестового фото"""
    print(f"🤖 Testing Telegram Bot")
    print(f"Token: {BOT_TOKEN[:20]}...")
    print(f"Chat ID: {TEST_CHAT_ID}")
    
    # Сначала проверим информацию о боте
    try:
        async with httpx.AsyncClient(timeout=30) as client:
            print("\n🔍 Получение информации о боте...")
            response = await client.get(f"{API_URL}/getMe")
            if response.status_code == 200:
                bot_info = response.json()
                print(f"✅ Бот: @{bot_info['result']['username']}")
                print(f"   ID: {bot_info['result']['id']}")
                print(f"   Имя: {bot_info['result']['first_name']}")
            else:
                print(f"❌ Ошибка получения информации о боте")
                
            # Попробуем получить updates чтобы увидеть chat_id
            print("\n🔍 Получение последних обновлений...")
            response2 = await client.get(f"{API_URL}/getUpdates?limit=5")
            if response2.status_code == 200:
                updates = response2.json()
                print(f"Updates: {updates}")
    except Exception as e:
        print(f"❌ Ошибка: {e}")
    
    # Тестовый file_id (нужно получить реальный)
    # Для теста используем URL изображения
    test_photo_url = "https://picsum.photos/800/600"
    
    try:
        async with httpx.AsyncClient(timeout=30) as client:
            # Сначала отправим фото по URL, чтобы получить file_id
            print("\n📤 Отправка тестового фото по URL...")
            payload = {
                "chat_id": TEST_CHAT_ID,
                "photo": test_photo_url,
                "caption": "🧪 Тест отправки фото\n\nЭто тестовое сообщение для проверки бота."
            }
            
            response = await client.post(f"{API_URL}/sendPhoto", json=payload)
            
            if response.status_code == 200:
                result = response.json()
                print(f"✅ Фото отправлено успешно!")
                print(f"Response: {result}")
                
                # Получаем file_id
                photo = result.get('result', {}).get('photo', [])
                if photo:
                    file_id = photo[-1].get('file_id')  # Берем самое большое фото
                    print(f"\n📝 File ID: {file_id}")
                    
                    # Теперь пробуем отправить это же фото обратно через file_id
                    print("\n📤 Переотправка через file_id...")
                    payload2 = {
                        "chat_id": TEST_CHAT_ID,
                        "photo": file_id,
                        "caption": "✅ Это переотправка через file_id"
                    }
                    
                    response2 = await client.post(f"{API_URL}/sendPhoto", json=payload2)
                    
                    if response2.status_code == 200:
                        print("✅ Переотправка успешна!")
                    else:
                        print(f"❌ Ошибка переотправки: {response2.text}")
                        
            else:
                print(f"❌ Ошибка отправки: {response.status_code}")
                print(f"Response: {response.text}")
                
    except Exception as e:
        print(f"❌ Exception: {e}")

if __name__ == "__main__":
    asyncio.run(test_send_photo())
