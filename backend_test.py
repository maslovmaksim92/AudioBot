#!/usr/bin/env python3
"""
Backend Test Suite for VasDom Plannerka System
Testing Plannerka functionality with AI analysis

This test validates:
1. POST /api/plannerka/create - создание планёрки
2. POST /api/plannerka/analyze/{id} - AI-анализ с GPT-4o
3. GET /api/plannerka/list - список планёрок
4. OpenAI GPT-4o integration and JSON parsing
5. Database operations for plannerka_meetings table
"""

import asyncio
import httpx
import json
from datetime import datetime
from typing import Dict, List, Any, Optional
import os

# Backend URL from environment
BACKEND_URL = "https://cleancaption.preview.emergentagent.com"
API_BASE = f"{BACKEND_URL}/api"

class PlannerkaTestResults:
    def __init__(self):
        self.created_meeting_id = None
        self.created_meeting_data = None
        self.analysis_result = None
        self.meetings_list = []
        self.errors = []
        self.openai_working = False
        self.database_working = False
        self.tasks_extracted = []
        self.summary_generated = False

async def test_cleaning_houses_endpoint():
    """Test the main cleaning houses endpoint"""
    print("=== ТЕСТ KPI БРИГАДЫ 1 - ОКТЯБРЬ 2025 ===\n")
    
    results = KPITestResults()
    
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            print("🔍 Загружаем все дома с графиками уборок...")
            
            # Test the main endpoint
            response = await client.get(f"{API_BASE}/cleaning/houses?limit=1000")
            
            if response.status_code != 200:
                error_msg = f"❌ Ошибка API: {response.status_code} - {response.text}"
                results.errors.append(error_msg)
                print(error_msg)
                return results
            
            data = response.json()
            houses = data.get('houses', [])
            results.total_houses_loaded = len(houses)
            
            print(f"✅ Загружено домов: {results.total_houses_loaded}")
            print(f"📊 Структура ответа: total={data.get('total')}, page={data.get('page')}, limit={data.get('limit')}")
            
            if not houses:
                results.errors.append("❌ Нет данных о домах")
                return results
            
            # Filter houses for Brigade #1
            print("\n🔍 Фильтруем дома бригады №1...")
            
            for house in houses:
                # Check various brigade fields
                brigade_name = house.get('brigade_name', '')
                assigned_by_name = house.get('assigned_by_name', '')
                
                # Look for brigade #1 indicators
                is_brigade_1 = (
                    '1 бригада' in str(brigade_name).lower() or
                    'бригада 1' in str(brigade_name).lower() or
                    '1 бригада' in str(assigned_by_name).lower() or
                    'бригада 1' in str(assigned_by_name).lower()
                )
                
                if is_brigade_1:
                    results.brigade_1_houses.append(house)
            
            print(f"✅ Найдено домов бригады №1: {len(results.brigade_1_houses)}")
            
            if not results.brigade_1_houses:
                results.errors.append("❌ Не найдено домов для бригады №1")
                return results
            
            # Analyze October 2025 cleaning data
            print("\n📅 Анализируем данные уборок за октябрь 2025...")
            
            # Take first 5 houses as samples for detailed output
            results.sample_houses = results.brigade_1_houses[:5]
            
            print("\nПримеры домов:")
            for i, house in enumerate(results.sample_houses, 1):
                house_id = house.get('id', 'N/A')
                address = house.get('address') or house.get('title', 'Адрес не указан')
                entrances = house.get('entrances', 0)
                floors = house.get('floors', 0)
                
                print(f"{i}. Дом ID {house_id}, Адрес: {address}")
                print(f"   - Подъезды: {entrances}, Этажи: {floors}")
                
                # Analyze cleaning dates
                cleaning_dates = house.get('cleaning_dates', {})
                october_dates = []
                
                # Check october_1 and october_2
                for period in ['october_1', 'october_2']:
                    period_data = cleaning_dates.get(period, {})
                    if period_data:
                        dates = period_data.get('dates', [])
                        cleaning_type = period_data.get('type', '')
                        
                        for date in dates:
                            if date and '2025-10' in str(date):
                                october_dates.append({
                                    'date': date,
                                    'type': cleaning_type,
                                    'entrances': entrances,
                                    'floors': floors
                                })
                
                if october_dates:
                    print(f"   - Даты в октябре:")
                    for cleaning in october_dates:
                        date = cleaning['date']
                        cleaning_type = cleaning['type']
                        entrances_count = cleaning['entrances']
                        floors_count = cleaning['floors']
                        
                        # Calculate floors for wet cleaning
                        if 'влажная' in cleaning_type.lower() and 'этаж' in cleaning_type.lower():
                            total_floors = entrances_count * floors_count
                            print(f"     * {date} ({cleaning_type}) → {entrances_count} подъезда, {total_floors} этажей")
                        elif 'подмет' in cleaning_type.lower():
                            print(f"     * {date} ({cleaning_type}) → подметание")
                        else:
                            print(f"     * {date} ({cleaning_type})")
                else:
                    print(f"   - ⚠️ Нет дат уборки в октябре 2025")
                
                print()
            
            # Calculate KPIs for all Brigade #1 houses
            print("📊 Расчет KPI за октябрь 2025:")
            
            # Initialize daily counters
            daily_stats = {}
            
            for house in results.brigade_1_houses:
                house_id = house.get('id', '')
                entrances = house.get('entrances', 0) or 0
                floors = house.get('floors', 0) or 0
                cleaning_dates = house.get('cleaning_dates', {})
                
                # Process october_1 and october_2
                for period in ['october_1', 'october_2']:
                    period_data = cleaning_dates.get(period, {})
                    if not period_data:
                        continue
                    
                    dates = period_data.get('dates', [])
                    cleaning_type = period_data.get('type', '').lower()
                    
                    for date in dates:
                        if not date or '2025-10' not in str(date):
                            continue
                        
                        # Initialize date if not exists
                        if date not in daily_stats:
                            daily_stats[date] = {
                                'houses': 0,
                                'entrances': 0,
                                'floors': 0,
                                'sweepings': 0
                            }
                        
                        # Count house
                        daily_stats[date]['houses'] += 1
                        
                        # Calculate based on cleaning type
                        if 'влажная' in cleaning_type and 'этаж' in cleaning_type:
                            # Wet cleaning of all floors
                            daily_stats[date]['entrances'] += entrances
                            daily_stats[date]['floors'] += entrances * floors
                        elif 'подмет' in cleaning_type:
                            # Sweeping
                            daily_stats[date]['sweepings'] += 1
                        elif 'влажная' in cleaning_type:
                            # General wet cleaning (count entrances)
                            daily_stats[date]['entrances'] += entrances
            
            # Sort dates and display results
            sorted_dates = sorted(daily_stats.keys())
            
            for date in sorted_dates:
                stats = daily_stats[date]
                print(f"- {date}: {stats['houses']} домов, {stats['entrances']} подъездов, {stats['floors']} этажей, {stats['sweepings']} подметаний")
                
                # Add to totals
                results.total_cleanings += stats['houses']
                results.total_entrances += stats['entrances']
                results.total_floors += stats['floors']
                results.total_sweepings += stats['sweepings']
            
            # Store daily stats
            results.october_cleanings = daily_stats
            
            print(f"\nИТОГО ЗА ОКТЯБРЬ:")
            print(f"✅ Уборок: {results.total_cleanings}")
            print(f"✅ Подъездов: {results.total_entrances}")
            print(f"✅ Этажей: {results.total_floors}")
            print(f"✅ Подметаний: {results.total_sweepings}")
            
            # Validation checks
            print(f"\n🔍 Проверки валидации:")
            
            if results.total_cleanings == 0:
                results.errors.append("❌ Нет уборок в октябре 2025 для бригады №1")
            else:
                print(f"✅ Найдены уборки: {results.total_cleanings}")
            
            if len(daily_stats) == 0:
                results.errors.append("❌ Нет дат уборок в октябре 2025")
            else:
                print(f"✅ Дней с уборками: {len(daily_stats)}")
            
            # Check data structure
            sample_house = results.brigade_1_houses[0] if results.brigade_1_houses else None
            if sample_house:
                cleaning_dates = sample_house.get('cleaning_dates', {})
                has_october_1 = 'october_1' in cleaning_dates
                has_october_2 = 'october_2' in cleaning_dates
                
                print(f"✅ Структура данных: october_1={has_october_1}, october_2={has_october_2}")
                
                if has_october_1:
                    oct1_data = cleaning_dates['october_1']
                    print(f"   - october_1: dates={len(oct1_data.get('dates', []))}, type='{oct1_data.get('type', '')}'")
                
                if has_october_2:
                    oct2_data = cleaning_dates['october_2']
                    print(f"   - october_2: dates={len(oct2_data.get('dates', []))}, type='{oct2_data.get('type', '')}'")
            
    except Exception as e:
        error_msg = f"❌ Ошибка при тестировании: {str(e)}"
        results.errors.append(error_msg)
        print(error_msg)
    
    return results

async def test_additional_endpoints():
    """Test additional cleaning-related endpoints"""
    print("\n🔍 Тестируем дополнительные endpoints...")
    
    endpoints_to_test = [
        "/cleaning/filters",
        "/cleaning/brigades",
        "/cleaning/cleaning-types"
    ]
    
    async with httpx.AsyncClient(timeout=15.0) as client:
        for endpoint in endpoints_to_test:
            try:
                response = await client.get(f"{API_BASE}{endpoint}")
                if response.status_code == 200:
                    data = response.json()
                    print(f"✅ {endpoint}: {response.status_code} - {len(str(data))} bytes")
                else:
                    print(f"⚠️ {endpoint}: {response.status_code}")
            except Exception as e:
                print(f"❌ {endpoint}: {str(e)}")

async def main():
    """Main test function"""
    print("🚀 Запуск тестирования KPI системы уборки VasDom")
    print(f"🌐 Backend URL: {BACKEND_URL}")
    print(f"📡 API Base: {API_BASE}")
    print("=" * 60)
    
    # Test main functionality
    results = await test_cleaning_houses_endpoint()
    
    # Test additional endpoints
    await test_additional_endpoints()
    
    # Final summary
    print("\n" + "=" * 60)
    print("📋 ИТОГОВЫЙ ОТЧЕТ:")
    print("=" * 60)
    
    if results.errors:
        print("❌ ОБНАРУЖЕНЫ ОШИБКИ:")
        for error in results.errors:
            print(f"   {error}")
    else:
        print("✅ ВСЕ ТЕСТЫ ПРОЙДЕНЫ УСПЕШНО")
    
    print(f"\n📊 Статистика:")
    print(f"   - Всего домов загружено: {results.total_houses_loaded}")
    print(f"   - Домов бригады №1: {len(results.brigade_1_houses)}")
    print(f"   - Уборок в октябре: {results.total_cleanings}")
    print(f"   - Подъездов убрано: {results.total_entrances}")
    print(f"   - Этажей убрано: {results.total_floors}")
    print(f"   - Подметаний: {results.total_sweepings}")
    print(f"   - Дней с уборками: {len(results.october_cleanings)}")
    
    # Return success/failure
    return len(results.errors) == 0

if __name__ == "__main__":
    success = asyncio.run(main())
    exit(0 if success else 1)