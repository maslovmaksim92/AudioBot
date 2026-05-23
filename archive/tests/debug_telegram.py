"""
Детальная проверка Telegram бота
"""
import asyncio
import httpx
import os
from dotenv import load_dotenv

load_dotenv('/app/backend/.env')

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TG_NEDVIGKA = os.getenv("TG_NEDVIGKA", "-5007549435")

async def check_bot():
    """Проверяет бота"""
    print("\n🔍 ШАГ 1: Проверка бота")
    print("="*60)
    
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(
                f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/getMe"
            )
            
            if response.status_code == 200:
                data = response.json()
                if data.get("ok"):
                    bot = data["result"]
                    print(f"✅ Бот найден:")
                    print(f"   ID: {bot['id']}")
                    print(f"   Username: @{bot['username']}")
                    print(f"   Name: {bot['first_name']}")
                    return True
                else:
                    print(f"❌ Ошибка API: {data}")
                    return False
            else:
                print(f"❌ HTTP Error: {response.status_code}")
                print(f"Response: {response.text}")
                return False
                
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        return False

async def get_updates():
    """Получает обновления бота"""
    print("\n🔍 ШАГ 2: Проверка групп где есть бот")
    print("="*60)
    
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(
                f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/getUpdates"
            )
            
            if response.status_code == 200:
                data = response.json()
                if data.get("ok"):
                    updates = data["result"]
                    print(f"✅ Найдено обновлений: {len(updates)}")
                    
                    # Ищем уникальные chat_id
                    chat_ids = set()
                    for update in updates[-10:]:  # Последние 10
                        if "message" in update:
                            chat = update["message"]["chat"]
                            chat_ids.add(chat["id"])
                            print(f"\n   Chat ID: {chat['id']}")
                            print(f"   Type: {chat['type']}")
                            print(f"   Title: {chat.get('title', 'N/A')}")
                    
                    return chat_ids
                else:
                    print(f"❌ Ошибка API: {data}")
                    return set()
            else:
                print(f"❌ HTTP Error: {response.status_code}")
                return set()
                
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        return set()

async def send_test_message(chat_id):
    """Отправляет простое тестовое сообщение"""
    print(f"\n🔍 ШАГ 3: Отправка простого сообщения в {chat_id}")
    print("="*60)
    
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(
                f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage",
                json={
                    "chat_id": chat_id,
                    "text": "🧪 Тестовое сообщение от AudioBot\n\nЭто проверка отправки сообщений."
                }
            )
            
            print(f"Status: {response.status_code}")
            data = response.json()
            print(f"Response: {data}")
            
            if response.status_code == 200 and data.get("ok"):
                print(f"✅ Сообщение отправлено успешно!")
                return True
            else:
                print(f"❌ Ошибка отправки:")
                if "description" in data:
                    print(f"   {data['description']}")
                return False
                
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        import traceback
        traceback.print_exc()
        return False

async def main():
    print("="*60)
    print("🔍 ДИАГНОСТИКА TELEGRAM БОТА")
    print("="*60)
    print(f"Bot Token: {TELEGRAM_BOT_TOKEN[:20]}..." if TELEGRAM_BOT_TOKEN else "⚠️ Нет токена")
    print(f"Target Chat ID: {TG_NEDVIGKA}")
    
    # Проверяем бота
    bot_ok = await check_bot()
    if not bot_ok:
        print("\n❌ Бот не работает! Проверьте токен.")
        return
    
    # Получаем обновления
    chat_ids = await get_updates()
    
    # Пробуем отправить в целевую группу
    await send_test_message(TG_NEDVIGKA)
    
    # Если есть другие группы, предлагаем попробовать
    if chat_ids:
        print(f"\n💡 Найдены другие чаты где есть бот:")
        for chat_id in chat_ids:
            if str(chat_id) != str(TG_NEDVIGKA):
                print(f"   {chat_id}")
    
    print("\n" + "="*60)
    print("📝 ЧТО ПРОВЕРИТЬ:")
    print("="*60)
    print("1. Бот добавлен в группу -5007549435?")
    print("2. У бота есть права отправлять сообщения?")
    print("3. Группа не архивирована?")
    print("4. Правильный ли ID группы?")
    print("\n💡 Как проверить ID группы:")
    print("   1. Добавьте @userinfobot в группу")
    print("   2. Он покажет правильный ID группы")
    print("   3. ID группы должен начинаться с минуса: -100...")

if __name__ == "__main__":
    asyncio.run(main())
