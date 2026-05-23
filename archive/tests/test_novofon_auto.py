"""
Тестовый скрипт для проверки автоматической обработки звонков Novofon
"""
import asyncio
import httpx
import json
from datetime import datetime

BACKEND_URL = "http://localhost:8001"

async def test_scheduler_status():
    """Проверка статуса scheduler"""
    print("\n" + "="*60)
    print("🔍 ТЕСТ 1: Проверка статуса scheduler")
    print("="*60)
    
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(f"{BACKEND_URL}/api/novofon-status/scheduler")
            
            if response.status_code == 200:
                data = response.json()
                print(f"✅ Scheduler запущен: {data['scheduler']['running']}")
                
                if data['scheduler']['jobs']:
                    for job in data['scheduler']['jobs']:
                        print(f"\n📋 Задача: {job['name']}")
                        print(f"   ID: {job['id']}")
                        print(f"   Следующий запуск: {job['next_run']}")
                        print(f"   Интервал: {job['trigger']}")
                else:
                    print("⚠️ Нет активных задач")
            else:
                print(f"❌ Ошибка: {response.status_code}")
                print(response.text)
                
    except Exception as e:
        print(f"❌ Ошибка проверки scheduler: {e}")

async def test_stats():
    """Проверка статистики обработанных звонков"""
    print("\n" + "="*60)
    print("🔍 ТЕСТ 2: Проверка статистики обработанных звонков")
    print("="*60)
    
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(f"{BACKEND_URL}/api/novofon-status/stats")
            
            if response.status_code == 200:
                data = response.json()
                
                if data['success']:
                    stats = data['stats']
                    print(f"✅ Всего звонков: {stats['total_calls']}")
                    print(f"   Успешных: {stats['successful']}")
                    print(f"   Ошибок: {stats['failed']}")
                    
                    if data['recent_calls']:
                        print(f"\n📞 Последние обработанные звонки:")
                        for call in data['recent_calls'][:5]:
                            status = "✅" if call['success'] else "❌"
                            print(f"   {status} {call['call_id']} - {call['processed_at']}")
                    else:
                        print("\n📭 Нет обработанных звонков")
                else:
                    print(f"⚠️ {data.get('error', 'Unknown error')}")
                    
            else:
                print(f"❌ Ошибка: {response.status_code}")
                
    except Exception as e:
        print(f"❌ Ошибка проверки статистики: {e}")

async def test_nedvigka_calls():
    """Проверка истории звонков по недвижимости"""
    print("\n" + "="*60)
    print("🔍 ТЕСТ 3: Проверка истории звонков по недвижимости")
    print("="*60)
    
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(f"{BACKEND_URL}/api/novofon-status/nedvigka-calls?limit=10")
            
            if response.status_code == 200:
                data = response.json()
                
                if data['success']:
                    print(f"✅ Найдено звонков: {data['total']}")
                    
                    if data['calls']:
                        print(f"\n📋 Последние звонки:")
                        for call in data['calls'][:5]:
                            direction = "📞 Входящий" if call['direction'] == 'in' else "📱 Исходящий"
                            print(f"\n   {direction} - {call['created_at']}")
                            print(f"   Телефон: {call['caller']} -> {call['called']}")
                            print(f"   Длительность: {call['duration']}с")
                            print(f"   Агентство: {call.get('agency_name', 'Не указано')}")
                            print(f"   Категория: {call.get('lead_category', 'Не определено')}")
                            print(f"   Рейтинг: {call.get('interest_rating', 0)}/10")
                            print(f"   Приоритет: {call.get('priority', 'Не указан')}")
                    else:
                        print("\n📭 Нет звонков в базе")
                else:
                    print(f"⚠️ {data.get('error', 'Unknown error')}")
                    
            else:
                print(f"❌ Ошибка: {response.status_code}")
                
    except Exception as e:
        print(f"❌ Ошибка проверки истории: {e}")

async def test_novofon_service():
    """Проверка подключения к Novofon API"""
    print("\n" + "="*60)
    print("🔍 ТЕСТ 4: Проверка подключения к Novofon API")
    print("="*60)
    
    try:
        # Импортируем сервис
        import sys
        sys.path.insert(0, '/app/backend')
        from backend.app.services.novofon_service import novofon_service
        
        print(f"✅ Novofon service инициализирован")
        print(f"   API Key: {novofon_service.api_key[:10]}..." if novofon_service.api_key else "   ⚠️ API Key не найден")
        print(f"   API Secret: {'*' * 20}" if novofon_service.api_secret else "   ⚠️ API Secret не найден")
        
        # Пробуем получить звонки
        if novofon_service.api_key and novofon_service.api_secret:
            print(f"\n🔄 Запрос к Novofon API...")
            from datetime import datetime, timedelta
            
            calls = await novofon_service.get_calls(
                start_date=datetime.now() - timedelta(days=1),
                end_date=datetime.now(),
                limit=5
            )
            
            if calls:
                print(f"✅ Получено звонков: {len(calls)}")
                for call in calls[:3]:
                    print(f"\n   📞 Call ID: {call.get('id', 'N/A')}")
                    print(f"      Caller: {call.get('caller', 'N/A')}")
                    print(f"      Called: {call.get('called', 'N/A')}")
                    print(f"      Duration: {call.get('duration', 0)}s")
            else:
                print(f"📭 Нет звонков за последние 24 часа")
        else:
            print(f"⚠️ Пропускаем тест API - нет credentials")
            
    except Exception as e:
        print(f"❌ Ошибка проверки Novofon: {e}")
        import traceback
        print(traceback.format_exc())

async def main():
    """Запуск всех тестов"""
    print("\n" + "="*60)
    print("🚀 ТЕСТИРОВАНИЕ АВТОМАТИЧЕСКОЙ ОБРАБОТКИ ЗВОНКОВ NOVOFON")
    print("="*60)
    print(f"Время: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Backend: {BACKEND_URL}")
    
    await test_scheduler_status()
    await test_stats()
    await test_nedvigka_calls()
    await test_novofon_service()
    
    print("\n" + "="*60)
    print("✅ ТЕСТИРОВАНИЕ ЗАВЕРШЕНО")
    print("="*60)
    print("\n📝 Инструкции:")
    print("1. Убедитесь что scheduler запущен и работает")
    print("2. Сделайте тестовый звонок на/с номера +79843330712")
    print("3. Подождите 1-2 минуты (scheduler проверяет каждую минуту)")
    print("4. Проверьте Telegram группу -5007549435 на наличие протокола")
    print("5. Повторно запустите тест для проверки сохранения в БД")
    print("\n💡 Для просмотра логов:")
    print("   tail -f /var/log/supervisor/backend.err.log | grep Novofon")
    print()

if __name__ == "__main__":
    asyncio.run(main())
