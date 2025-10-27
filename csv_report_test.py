#!/usr/bin/env python3
"""
CSV Report Test Suite for VasDom Cleaning System
Testing /api/cleaning/missing-data-report endpoint

This test validates:
1. CSV file generation with all houses (~500 houses + header)
2. CSV structure with all required columns
3. Specific house ID 8674 (Кибальчича 3) contact verification
4. Statistics on houses with/without elder contacts
"""

import asyncio
import httpx
import csv
import io
from datetime import datetime
from typing import Dict, List, Any, Optional
import os

# Backend URL from environment
BACKEND_URL = "https://finance-forecast-14.preview.emergentagent.com"
API_BASE = f"{BACKEND_URL}/api"

class CSVReportResults:
    def __init__(self):
        self.csv_generated = False
        self.total_rows = 0
        self.header_columns = []
        self.expected_columns = [
            'ID', 'Адрес', 'УК', 'Бригада', 'Подъезды', 'Этажи', 
            'Квартиры', 'Периодичность', 'Старший (ФИО)', 'Старший (телефон)', 
            'Старший (email)', 'Недостающие поля'
        ]
        self.house_8674_found = False
        self.house_8674_data = {}
        self.houses_with_contacts = 0
        self.houses_without_contacts = 0
        self.sample_houses = []
        self.errors = []
        self.csv_content = ""

async def test_csv_report_generation():
    """Test the CSV missing data report endpoint"""
    print("=== ТЕСТ CSV ОТЧЕТА С КОНТАКТАМИ СТАРШЕГО ===\n")
    
    results = CSVReportResults()
    
    try:
        # Use 300 second timeout as specified
        timeout = httpx.Timeout(300.0)
        
        async with httpx.AsyncClient(timeout=timeout) as client:
            print("🔍 Запрашиваем CSV отчет с контактами старшего...")
            print(f"📡 URL: {API_BASE}/cleaning/missing-data-report")
            print("⏱️ Timeout: 300 секунд (5 минут)")
            
            # Request the CSV report
            response = await client.get(f"{API_BASE}/cleaning/missing-data-report")
            
            if response.status_code != 200:
                error_msg = f"❌ Ошибка API: {response.status_code} - {response.text}"
                results.errors.append(error_msg)
                print(error_msg)
                return results
            
            # Check if response is CSV
            content_type = response.headers.get('content-type', '')
            if 'csv' not in content_type.lower():
                error_msg = f"❌ Неверный тип контента: {content_type}, ожидался CSV"
                results.errors.append(error_msg)
                print(error_msg)
                return results
            
            print("✅ CSV файл успешно получен")
            results.csv_generated = True
            
            # Parse CSV content
            csv_content = response.content.decode('utf-8-sig')  # Handle BOM
            results.csv_content = csv_content
            
            # Parse CSV
            csv_reader = csv.DictReader(io.StringIO(csv_content), delimiter=';')
            
            # Get header columns
            results.header_columns = csv_reader.fieldnames or []
            print(f"📋 Колонки CSV: {results.header_columns}")
            
            # Check if all expected columns are present
            missing_columns = []
            for expected_col in results.expected_columns:
                if expected_col not in results.header_columns:
                    missing_columns.append(expected_col)
            
            if missing_columns:
                error_msg = f"❌ Отсутствуют колонки: {missing_columns}"
                results.errors.append(error_msg)
                print(error_msg)
            else:
                print("✅ Все ожидаемые колонки присутствуют")
            
            # Parse all rows
            houses = []
            for row in csv_reader:
                houses.append(row)
                results.total_rows += 1
            
            print(f"📊 Всего строк в CSV: {results.total_rows}")
            
            # Check if we have expected number of houses (~500)
            if results.total_rows < 400:
                error_msg = f"⚠️ Мало домов в отчете: {results.total_rows}, ожидалось ~500"
                results.errors.append(error_msg)
                print(error_msg)
            elif results.total_rows > 600:
                error_msg = f"⚠️ Слишком много домов: {results.total_rows}, ожидалось ~500"
                results.errors.append(error_msg)
                print(error_msg)
            else:
                print(f"✅ Количество домов в норме: {results.total_rows}")
            
            # Look for specific house ID 8674 (Кибальчича 3)
            print(f"\n🔍 Поиск дома ID 8674 (Кибальчича 3)...")
            
            for house in houses:
                house_id = house.get('ID', '')
                address = house.get('Адрес', '')
                elder_name = house.get('Старший (ФИО)', '')
                elder_phone = house.get('Старший (телефон)', '')
                
                # Check if this is house 8674
                if house_id == '8674' or 'кибальчича 3' in address.lower():
                    results.house_8674_found = True
                    results.house_8674_data = house
                    print(f"✅ Найден дом ID {house_id}: {address}")
                    print(f"   - Старший: {elder_name}")
                    print(f"   - Телефон: {elder_phone}")
                    print(f"   - Email: {house.get('Старший (email)', '')}")
                    
                    # Check if contact matches expected values
                    expected_name = "новая старшая Светлана"
                    expected_phone = "+79657005267"
                    
                    if expected_name.lower() in elder_name.lower():
                        print(f"✅ Имя старшего соответствует ожидаемому")
                    else:
                        print(f"⚠️ Имя старшего не соответствует: ожидалось '{expected_name}', получено '{elder_name}'")
                    
                    if expected_phone in elder_phone:
                        print(f"✅ Телефон старшего соответствует ожидаемому")
                    else:
                        print(f"⚠️ Телефон старшего не соответствует: ожидалось '{expected_phone}', получено '{elder_phone}'")
                    
                    break
            
            if not results.house_8674_found:
                error_msg = "❌ Дом ID 8674 (Кибальчича 3) не найден в отчете"
                results.errors.append(error_msg)
                print(error_msg)
            
            # Calculate statistics on contacts
            print(f"\n📊 Анализ контактов старших...")
            
            for house in houses:
                elder_name = house.get('Старший (ФИО)', '').strip()
                elder_phone = house.get('Старший (телефон)', '').strip()
                
                # Check if house has valid elder contact
                has_contact = (
                    elder_name and elder_name != 'Не указан' and len(elder_name) > 2 and
                    elder_phone and elder_phone != 'Не указан' and len(elder_phone) > 5
                )
                
                if has_contact:
                    results.houses_with_contacts += 1
                else:
                    results.houses_without_contacts += 1
            
            print(f"✅ Домов с контактами: {results.houses_with_contacts}")
            print(f"⚠️ Домов без контактов: {results.houses_without_contacts}")
            
            # Show sample houses with and without contacts
            print(f"\n📋 Примеры домов с контактами:")
            houses_with_contacts_sample = []
            houses_without_contacts_sample = []
            
            for house in houses[:50]:  # Check first 50 houses
                elder_name = house.get('Старший (ФИО)', '').strip()
                elder_phone = house.get('Старший (телефон)', '').strip()
                
                has_contact = (
                    elder_name and elder_name != 'Не указан' and len(elder_name) > 2 and
                    elder_phone and elder_phone != 'Не указан' and len(elder_phone) > 5
                )
                
                if has_contact and len(houses_with_contacts_sample) < 3:
                    houses_with_contacts_sample.append(house)
                elif not has_contact and len(houses_without_contacts_sample) < 3:
                    houses_without_contacts_sample.append(house)
                
                if len(houses_with_contacts_sample) >= 3 and len(houses_without_contacts_sample) >= 3:
                    break
            
            # Display samples
            for i, house in enumerate(houses_with_contacts_sample, 1):
                print(f"{i}. ID {house.get('ID')}: {house.get('Адрес')} - {house.get('Старший (ФИО)')}, {house.get('Старший (телефон)')}")
            
            print(f"\n📋 Примеры домов без контактов:")
            for i, house in enumerate(houses_without_contacts_sample, 1):
                print(f"{i}. ID {house.get('ID')}: {house.get('Адрес')} - {house.get('Старший (ФИО)')}, {house.get('Старший (телефон)')}")
            
            results.sample_houses = houses_with_contacts_sample + houses_without_contacts_sample
            
            # Validation checks
            print(f"\n🔍 Проверки валидации:")
            
            if results.total_rows == 0:
                results.errors.append("❌ CSV файл пустой")
            else:
                print(f"✅ CSV содержит данные: {results.total_rows} строк")
            
            if len(results.header_columns) != len(results.expected_columns):
                results.errors.append(f"❌ Неверное количество колонок: {len(results.header_columns)}, ожидалось {len(results.expected_columns)}")
            else:
                print(f"✅ Количество колонок корректно: {len(results.header_columns)}")
            
            if results.houses_with_contacts == 0:
                results.errors.append("❌ Нет домов с контактами старших")
            else:
                print(f"✅ Найдены дома с контактами: {results.houses_with_contacts}")
            
    except asyncio.TimeoutError:
        error_msg = "❌ Превышен timeout 300 секунд при генерации отчета"
        results.errors.append(error_msg)
        print(error_msg)
    except Exception as e:
        error_msg = f"❌ Ошибка при тестировании: {str(e)}"
        results.errors.append(error_msg)
        print(error_msg)
    
    return results

async def save_csv_sample():
    """Save a sample of the CSV for manual inspection"""
    try:
        print("\n💾 Сохраняем образец CSV файла...")
        
        timeout = httpx.Timeout(300.0)
        async with httpx.AsyncClient(timeout=timeout) as client:
            response = await client.get(f"{API_BASE}/cleaning/missing-data-report")
            
            if response.status_code == 200:
                # Save to /tmp/test_report.csv as specified in the request
                with open('/tmp/test_report.csv', 'wb') as f:
                    f.write(response.content)
                print("✅ CSV файл сохранен в /tmp/test_report.csv")
                
                # Show file size
                file_size = len(response.content)
                print(f"📁 Размер файла: {file_size} байт")
                
                return True
            else:
                print(f"❌ Не удалось сохранить CSV: {response.status_code}")
                return False
                
    except Exception as e:
        print(f"❌ Ошибка при сохранении CSV: {e}")
        return False

async def main():
    """Main test function"""
    print("🚀 Запуск тестирования CSV отчета с контактами старшего")
    print(f"🌐 Backend URL: {BACKEND_URL}")
    print(f"📡 API Base: {API_BASE}")
    print("=" * 70)
    
    # Test CSV report generation
    results = await test_csv_report_generation()
    
    # Save CSV sample
    await save_csv_sample()
    
    # Final summary
    print("\n" + "=" * 70)
    print("📋 ИТОГОВЫЙ ОТЧЕТ CSV:")
    print("=" * 70)
    
    if results.errors:
        print("❌ ОБНАРУЖЕНЫ ПРОБЛЕМЫ:")
        for error in results.errors:
            print(f"   {error}")
    else:
        print("✅ ВСЕ ТЕСТЫ ПРОЙДЕНЫ УСПЕШНО")
    
    print(f"\n📊 Статистика CSV отчета:")
    print(f"   - CSV файл создан: {'✅' if results.csv_generated else '❌'}")
    print(f"   - Количество строк: {results.total_rows}")
    print(f"   - Колонки в CSV: {len(results.header_columns)}")
    print(f"   - Дом 8674 найден: {'✅' if results.house_8674_found else '❌'}")
    print(f"   - Домов с контактами: {results.houses_with_contacts}")
    print(f"   - Домов без контактов: {results.houses_without_contacts}")
    
    if results.house_8674_found:
        house_data = results.house_8674_data
        print(f"\n🏠 Дом 8674 (Кибальчича 3):")
        print(f"   - Адрес: {house_data.get('Адрес', 'N/A')}")
        print(f"   - Старший: {house_data.get('Старший (ФИО)', 'N/A')}")
        print(f"   - Телефон: {house_data.get('Старший (телефон)', 'N/A')}")
        print(f"   - Email: {house_data.get('Старший (email)', 'N/A')}")
    
    # Return success/failure
    return len(results.errors) == 0

if __name__ == "__main__":
    success = asyncio.run(main())
    exit(0 if success else 1)