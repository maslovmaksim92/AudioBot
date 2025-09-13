#!/usr/bin/env python3
"""
🔍 Проверка доступа к CRM Bitrix24
Скрипт для мониторинга когда обновятся права приложения
"""

import requests
import json
import time
from datetime import datetime

WEBHOOK_URL = "https://vas-dom.bitrix24.ru/rest/1/td813o0ym4tpp62j/"

def check_app_permissions():
    """Проверка прав приложения"""
    try:
        response = requests.get(f"{WEBHOOK_URL}app.info", timeout=10)
        data = response.json()
        
        scopes = data.get('result', {}).get('SCOPE', [])
        print(f"[{datetime.now().strftime('%H:%M:%S')}] Текущие права: {', '.join(scopes)}")
        
        return 'crm' in scopes
    except Exception as e:
        print(f"[{datetime.now().strftime('%H:%M:%S')}] Ошибка проверки прав: {e}")
        return False

def check_crm_access():
    """Проверка доступа к CRM данным"""
    try:
        response = requests.get(
            f"{WEBHOOK_URL}crm.deal.list",
            params={
                'select[]': ['ID', 'TITLE', 'UF_CRM_1669708345534'],
                'start': '0',
                'ORDER[ID]': 'DESC'
            },
            timeout=10
        )
        data = response.json()
        
        if 'error' in data:
            print(f"[{datetime.now().strftime('%H:%M:%S')}] ❌ CRM ошибка: {data['error']}")
            return False, []
        else:
            deals = data.get('result', [])
            print(f"[{datetime.now().strftime('%H:%M:%S')}] ✅ CRM доступен! Найдено сделок: {len(deals)}")
            
            # Извлекаем УК из реальных данных
            uk_set = set()
            for deal in deals:
                uk = deal.get('UF_CRM_1669708345534', '').strip()
                if uk:
                    uk_set.add(uk)
            
            return True, sorted(list(uk_set))
            
    except Exception as e:
        print(f"[{datetime.now().strftime('%H:%M:%S')}] Ошибка проверки CRM: {e}")
        return False, []

def main():
    """Основная функция мониторинга"""
    print("🔍 МОНИТОРИНГ ДОСТУПА К CRM BITRIX24")
    print("=" * 50)
    print("Проверяем когда обновятся права приложения...")
    print()
    
    max_attempts = 30  # 15 минут (30 попыток по 30 сек)
    attempt = 0
    
    while attempt < max_attempts:
        attempt += 1
        print(f"Попытка {attempt}/{max_attempts}")
        
        # Сначала проверяем права
        has_crm_permission = check_app_permissions()
        
        if has_crm_permission:
            print("🎉 CRM права обнаружены! Проверяем доступ к данным...")
            
            # Проверяем доступ к данным
            crm_works, uk_list = check_crm_access()
            
            if crm_works:
                print("\n" + "=" * 50)
                print("🎊 CRM ПОЛНОСТЬЮ РАБОТАЕТ!")
                print("=" * 50)
                
                if uk_list:
                    print(f"Найдено управляющих компаний: {len(uk_list)}")
                    for uk in uk_list:
                        print(f"  📋 {uk}")
                else:
                    print("⚠️  УК не найдены в сделках")
                
                print("\n✅ Теперь можно перезапустить backend для загрузки реальных данных:")
                print("   sudo supervisorctl restart backend")
                return True
        
        if attempt < max_attempts:
            print(f"   Ждем 30 секунд до следующей проверки...\n")
            time.sleep(30)
    
    print("\n❌ Права так и не обновились за 15 минут")
    print("Возможные причины:")
    print("1. Приложение нужно переустановить")
    print("2. Нужно больше времени для синхронизации")
    print("3. Проблема с Bitrix24 API")
    return False

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)