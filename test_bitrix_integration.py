#!/usr/bin/env python3
"""
🧪 Скрипт тестирования интеграции с Bitrix24
Используется для проверки работы нового локального приложения
"""

import requests
import json
import os
from datetime import datetime
import sys

def test_bitrix_webhook(webhook_url):
    """Тестирование базового подключения к Bitrix24"""
    print(f"🔍 Тестирование webhook: {webhook_url}")
    
    # Тест 1: Информация о приложении
    try:
        response = requests.get(f"{webhook_url}app.info")
        if response.status_code == 200:
            app_info = response.json()
            print(f"✅ Приложение работает: {app_info.get('result', {}).get('ID', 'Unknown')}")
            return True
        else:
            print(f"❌ Ошибка подключения: {response.status_code} - {response.text}")
            return False
    except Exception as e:
        print(f"❌ Исключение при подключении: {e}")
        return False

def test_crm_access(webhook_url):
    """Тестирование доступа к CRM"""
    print(f"\n🏠 Тестирование доступа к CRM...")
    
    # Тест загрузки сделок (домов)
    try:
        params = {
            'select[]': ['ID', 'TITLE', 'UF_CRM_1669704529022', 'UF_CRM_1669705507390', 'UF_CRM_1669704631166'],
            'filter[CATEGORY_ID]': '0',
            'start': '0'
        }
        
        response = requests.get(f"{webhook_url}crm.deal.list", params=params)
        
        if response.status_code == 200:
            data = response.json()
            deals = data.get('result', [])
            print(f"✅ Загружено домов: {len(deals)}")
            
            if deals:
                house = deals[0]
                print(f"   Пример дома: {house.get('TITLE', 'Без названия')}")
                print(f"   ID: {house.get('ID')}")
                apartments = house.get('UF_CRM_1669704529022', '0')
                entrances = house.get('UF_CRM_1669705507390', '0') 
                floors = house.get('UF_CRM_1669704631166', '0')
                print(f"   Квартиры: {apartments}, Подъезды: {entrances}, Этажи: {floors}")
            
            return len(deals)
        else:
            print(f"❌ Ошибка загрузки CRM: {response.status_code} - {response.text}")
            return 0
            
    except Exception as e:
        print(f"❌ Исключение при загрузке CRM: {e}")
        return 0

def test_users_access(webhook_url):
    """Тестирование доступа к пользователям"""
    print(f"\n👥 Тестирование доступа к пользователям...")
    
    try:
        response = requests.get(f"{webhook_url}user.get")
        
        if response.status_code == 200:
            data = response.json()
            users = data.get('result', [])
            print(f"✅ Загружено пользователей: {len(users)}")
            
            if users:
                user = users[0]
                print(f"   Пример пользователя: {user.get('NAME', '')} {user.get('LAST_NAME', '')}")
                print(f"   Email: {user.get('EMAIL', 'Не указан')}")
                print(f"   Должность: {user.get('WORK_POSITION', 'Не указана')}")
            
            return len(users)
        else:
            print(f"❌ Ошибка загрузки пользователей: {response.status_code} - {response.text}")
            return 0
            
    except Exception as e:
        print(f"❌ Исключение при загрузке пользователей: {e}")
        return 0

def test_departments_access(webhook_url):
    """Тестирование доступа к подразделениям"""
    print(f"\n🏢 Тестирование доступа к подразделениям...")
    
    try:
        response = requests.get(f"{webhook_url}department.get")
        
        if response.status_code == 200:
            data = response.json()
            departments = data.get('result', [])
            print(f"✅ Загружено подразделений: {len(departments)}")
            
            if departments:
                dept = departments[0]
                print(f"   Пример подразделения: {dept.get('NAME', 'Без названия')}")
                print(f"   ID: {dept.get('ID')}")
                print(f"   Родитель: {dept.get('PARENT', 'Корневое')}")
            
            return len(departments)
        else:
            print(f"❌ Ошибка загрузки подразделений: {response.status_code} - {response.text}")
            return 0
            
    except Exception as e:
        print(f"❌ Исключение при загрузке подразделений: {e}")
        return 0

def main():
    """Основная функция тестирования"""
    print("🚀 ТЕСТИРОВАНИЕ ИНТЕГРАЦИИ BITRIX24 для AudioBot")
    print("=" * 60)
    
    # Получение webhook URL из аргументов или переменной среды
    webhook_url = None
    
    if len(sys.argv) > 1:
        webhook_url = sys.argv[1]
    else:
        webhook_url = os.environ.get('BITRIX_WEBHOOK_URL')
    
    if not webhook_url:
        print("❌ Не указан WEBHOOK_URL!")
        print("\nИспользование:")
        print("  python test_bitrix_integration.py https://vas-dom.bitrix24.ru/rest/USER_ID/TOKEN/")
        print("или установите переменную среды BITRIX_WEBHOOK_URL")
        return False
    
    # Убеждаемся что URL заканчивается на /
    if not webhook_url.endswith('/'):
        webhook_url += '/'
    
    print(f"🔗 Тестируемый URL: {webhook_url}")
    print(f"⏰ Время тестирования: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # Запуск тестов
    results = {}
    
    # Тест 1: Базовое подключение
    results['connection'] = test_bitrix_webhook(webhook_url)
    
    if not results['connection']:
        print("\n❌ КРИТИЧЕСКАЯ ОШИБКА: Не удается подключиться к Bitrix24")
        print("Проверьте:")
        print("1. Корректность webhook URL")
        print("2. Права доступа приложения")
        print("3. Статус портала Bitrix24")
        return False
    
    # Тест 2: Доступ к CRM
    results['houses'] = test_crm_access(webhook_url)
    
    # Тест 3: Доступ к пользователям
    results['users'] = test_users_access(webhook_url)
    
    # Тест 4: Доступ к подразделениям  
    results['departments'] = test_departments_access(webhook_url)
    
    # Итоговый отчет
    print("\n" + "=" * 60)
    print("📊 ИТОГОВЫЙ ОТЧЕТ ТЕСТИРОВАНИЯ")
    print("=" * 60)
    
    print(f"🔗 Подключение к Bitrix24: {'✅ ОК' if results['connection'] else '❌ ОШИБКА'}")
    print(f"🏠 Загружено домов: {results['houses']}")
    print(f"👥 Загружено пользователей: {results['users']}")
    print(f"🏢 Загружено подразделений: {results['departments']}")
    
    # Проверка целевых значений
    success = True
    if results['houses'] < 400:  # Ожидаем минимум 400 домов
        print(f"⚠️  Предупреждение: Домов меньше ожидаемого (минимум 400)")
        success = False
        
    if results['users'] < 50:  # Ожидаем минимум 50 пользователей
        print(f"⚠️  Предупреждение: Пользователей меньше ожидаемого (минимум 50)")
        success = False
    
    if success:
        print("\n🎉 ВСЕ ТЕСТЫ ПРОЙДЕНЫ УСПЕШНО!")
        print("AudioBot готов к работе с новым приложением Bitrix24")
    else:
        print("\n⚠️  ЕСТЬ ПРОБЛЕМЫ - проверьте права доступа приложения")
    
    return success

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)