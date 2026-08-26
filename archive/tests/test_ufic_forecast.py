#!/usr/bin/env python3
"""
Test script for УФИЦ модель forecast endpoint with Excel data
"""

import asyncio
import httpx
import json
from typing import Dict, List, Any

# Backend URL from environment
BACKEND_URL = "https://bitrix-audio-1.preview.emergentagent.com"
API_BASE = f"{BACKEND_URL}/api"

async def test_ufic_forecast_endpoint():
    """Test УФИЦ модель forecast endpoint with exact Excel data"""
    print("\n=== ТЕСТ ПРОГНОЗА УФИЦ МОДЕЛЬ С ДАННЫМИ ИЗ EXCEL ===\n")
    
    scenarios = ["pessimistic", "realistic", "optimistic"]
    company = "УФИЦ модель"
    errors = []
    
    # Expected data from Excel file "Модель УФИЦ.xlsx"
    expected_data = {
        "pessimistic": {
            "revenue_2025": 38645410,
            "expenses_2025": 27289899,
            "revenue_2026": 51458491,
            "expenses_2026": 34101464
        },
        "realistic": {
            "revenue_2025": 38645410,
            "expenses_2025": 27289900,
            "revenue_2026": 54687416,
            "expenses_2026": 36947205
        },
        "optimistic": {
            "revenue_2025": 38865910,
            "expenses_2025": 27396013,
            "revenue_2026": 58491350,
            "expenses_2026": 39840376
        }
    }
    
    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            print(f"🏢 Тестируем прогноз для компании: {company}")
            print("📋 Проверяемые критерии из Excel файла 'Модель УФИЦ.xlsx':")
            print("   1. Все три сценария возвращают 200 статус")
            print("   2. Базовый год 2025 содержит правильные данные из Excel:")
            print("      - Пессимистичный: revenue 38,645,410, expenses 27,289,899")
            print("      - Реалистичный: revenue 38,645,410, expenses 27,289,900")
            print("      - Оптимистичный: revenue 38,865,910, expenses 27,396,013")
            print("   3. Для 2026 года проверить данные из Excel:")
            print("      - Пессимистичный: revenue 51,458,491, expenses 34,101,464")
            print("      - Реалистичный: revenue 54,687,416, expenses 36,947,205")
            print("      - Оптимистичный: revenue 58,491,350, expenses 39,840,376")
            print("   4. Для 2027-2030 проверить применение индексации 6% к данным 2026")
            print("   5. Структура ответа содержит все необходимые поля")
            print("   6. Маржа рассчитывается корректно")
            print("")
            
            scenario_results = {}
            
            for scenario in scenarios:
                print(f"🔍 Тестируем сценарий: {scenario}")
                
                # Test the forecast endpoint
                response = await client.get(
                    f"{API_BASE}/finances/forecast",
                    params={"company": company, "scenario": scenario}
                )
                
                print(f"📡 Ответ сервера для {scenario}: {response.status_code}")
                
                # Criterion 1: Check 200 status
                if response.status_code != 200:
                    error_msg = f"❌ Сценарий {scenario}: ошибка {response.status_code} - {response.text}"
                    errors.append(error_msg)
                    print(error_msg)
                    continue
                
                data = response.json()
                scenario_results[scenario] = data
                print(f"✅ Сценарий {scenario}: 200 статус получен")
                
                # Validate response structure (Criterion 5)
                required_fields = ['company', 'scenario', 'base_year', 'base_data', 'forecast', 'investor_metrics', 'scenario_info']
                for field in required_fields:
                    if field not in data:
                        error_msg = f"❌ Сценарий {scenario}: отсутствует поле '{field}'"
                        errors.append(error_msg)
                        print(error_msg)
                    else:
                        print(f"✅ Поле '{field}' присутствует")
                
                # Criterion 2: Check base year 2025 data from Excel
                base_data = data.get('base_data', {})
                base_revenue = base_data.get('revenue', 0)
                base_expenses = base_data.get('expenses', 0)
                
                expected_scenario_data = expected_data[scenario]
                expected_revenue_2025 = expected_scenario_data["revenue_2025"]
                expected_expenses_2025 = expected_scenario_data["expenses_2025"]
                
                print(f"📊 Базовые данные 2025 (из Excel):")
                print(f"   - Выручка: {base_revenue:,.0f} (ожидалось {expected_revenue_2025:,})")
                print(f"   - Расходы: {base_expenses:,.0f} (ожидалось {expected_expenses_2025:,})")
                
                # Check exact values from Excel (allow small rounding differences)
                if abs(base_revenue - expected_revenue_2025) > 1:
                    error_msg = f"❌ Сценарий {scenario}: выручка 2025 не соответствует Excel: {base_revenue:,.0f} vs {expected_revenue_2025:,}"
                    errors.append(error_msg)
                    print(error_msg)
                else:
                    print(f"✅ Выручка 2025 соответствует Excel данным")
                
                if abs(base_expenses - expected_expenses_2025) > 1:
                    error_msg = f"❌ Сценарий {scenario}: расходы 2025 не соответствуют Excel: {base_expenses:,.0f} vs {expected_expenses_2025:,}"
                    errors.append(error_msg)
                    print(error_msg)
                else:
                    print(f"✅ Расходы 2025 соответствуют Excel данным")
                
                # Criterion 3: Check 2026 data from Excel
                forecast = data.get('forecast', [])
                if forecast:
                    # Find 2026 data
                    year_2026_data = None
                    for year_data in forecast:
                        if year_data.get('year') == 2026:
                            year_2026_data = year_data
                            break
                    
                    if year_2026_data:
                        revenue_2026 = year_2026_data.get('revenue', 0)
                        expenses_2026 = year_2026_data.get('expenses', 0)
                        expected_revenue_2026 = expected_scenario_data["revenue_2026"]
                        expected_expenses_2026 = expected_scenario_data["expenses_2026"]
                        
                        print(f"📊 Данные 2026 года (из Excel):")
                        print(f"   - Выручка: {revenue_2026:,.0f} (ожидалось {expected_revenue_2026:,})")
                        print(f"   - Расходы: {expenses_2026:,.0f} (ожидалось {expected_expenses_2026:,})")
                        
                        # Check 2026 values from Excel
                        if abs(revenue_2026 - expected_revenue_2026) > 1:
                            error_msg = f"❌ Сценарий {scenario}: выручка 2026 не соответствует Excel: {revenue_2026:,.0f} vs {expected_revenue_2026:,}"
                            errors.append(error_msg)
                            print(error_msg)
                        else:
                            print(f"✅ Выручка 2026 соответствует Excel данным")
                        
                        if abs(expenses_2026 - expected_expenses_2026) > 1:
                            error_msg = f"❌ Сценарий {scenario}: расходы 2026 не соответствуют Excel: {expenses_2026:,.0f} vs {expected_expenses_2026:,}"
                            errors.append(error_msg)
                            print(error_msg)
                        else:
                            print(f"✅ Расходы 2026 соответствуют Excel данным")
                    else:
                        error_msg = f"❌ Сценарий {scenario}: данные за 2026 год не найдены в прогнозе"
                        errors.append(error_msg)
                        print(error_msg)
                
                # Criterion 4: Check 6% annual indexation for 2027-2030 based on 2026 data
                if len(forecast) >= 2:
                    print(f"📈 Проверяем индексацию 6% ежегодно с 2027 года (к данным 2026):")
                    
                    # Find 2026 as base for indexation
                    base_2026_data = None
                    for year_data in forecast:
                        if year_data.get('year') == 2026:
                            base_2026_data = year_data
                            break
                    
                    if base_2026_data:
                        base_revenue_2026 = base_2026_data.get('revenue', 0)
                        base_expenses_2026 = base_2026_data.get('expenses', 0)
                        
                        # Check indexation for years 2027-2030
                        for year_data in forecast:
                            year = year_data.get('year', 0)
                            if year >= 2027 and year <= 2030:
                                years_from_2026 = year - 2026
                                expected_revenue = base_revenue_2026 * (1.06 ** years_from_2026)
                                expected_expenses = base_expenses_2026 * (1.06 ** years_from_2026)
                                
                                actual_revenue = year_data.get('revenue', 0)
                                actual_expenses = year_data.get('expenses', 0)
                                
                                print(f"   {year}: выручка {actual_revenue:,.0f} (ожидалось {expected_revenue:,.0f})")
                                print(f"        расходы {actual_expenses:,.0f} (ожидалось {expected_expenses:,.0f})")
                                
                                # Allow small rounding differences
                                if abs(actual_revenue - expected_revenue) > 100:
                                    error_msg = f"❌ Сценарий {scenario}: неверная индексация выручки {year}: {actual_revenue:,.0f} vs {expected_revenue:,.0f}"
                                    errors.append(error_msg)
                                    print(f"        ❌ Выручка не соответствует индексации 6%")
                                else:
                                    print(f"        ✅ Выручка соответствует индексации 6%")
                                
                                if abs(actual_expenses - expected_expenses) > 100:
                                    error_msg = f"❌ Сценарий {scenario}: неверная индексация расходов {year}: {actual_expenses:,.0f} vs {expected_expenses:,.0f}"
                                    errors.append(error_msg)
                                    print(f"        ❌ Расходы не соответствуют индексации 6%")
                                else:
                                    print(f"        ✅ Расходы соответствуют индексации 6%")
                    else:
                        error_msg = f"❌ Сценарий {scenario}: не найдены данные 2026 года для проверки индексации"
                        errors.append(error_msg)
                        print(error_msg)
                
                # Criterion 6: Check margin calculation correctness
                if forecast:
                    print(f"📊 Проверяем корректность расчета маржи:")
                    
                    for year_data in forecast:
                        year = year_data.get('year', 0)
                        revenue = year_data.get('revenue', 0)
                        expenses = year_data.get('expenses', 0)
                        profit = year_data.get('profit', 0)
                        margin = year_data.get('margin', 0)
                        
                        # Calculate expected margin
                        expected_profit = revenue - expenses
                        expected_margin = (expected_profit / revenue * 100) if revenue > 0 else 0
                        
                        print(f"   {year}: маржа {margin:.2f}% (расчетная {expected_margin:.2f}%)")
                        
                        # Check profit calculation
                        if abs(profit - expected_profit) > 1:
                            error_msg = f"❌ Сценарий {scenario}: неверный расчет прибыли {year}: {profit:,.0f} vs {expected_profit:,.0f}"
                            errors.append(error_msg)
                            print(f"        ❌ Прибыль рассчитана неверно")
                        else:
                            print(f"        ✅ Прибыль рассчитана корректно")
                        
                        # Check margin calculation
                        if abs(margin - expected_margin) > 0.1:
                            error_msg = f"❌ Сценарий {scenario}: неверный расчет маржи {year}: {margin:.2f}% vs {expected_margin:.2f}%"
                            errors.append(error_msg)
                            print(f"        ❌ Маржа рассчитана неверно")
                        else:
                            print(f"        ✅ Маржа рассчитана корректно")
                    
                    # Show average margin
                    margins = [f.get('margin', 0) for f in forecast]
                    avg_margin = sum(margins) / len(margins) if margins else 0
                    print(f"📊 Средняя маржа: {avg_margin:.2f}%")
                
                # Show forecast summary
                if forecast:
                    print(f"📋 Прогноз {scenario} (2026-2030):")
                    for f in forecast:
                        print(f"   {f['year']}: выручка {f['revenue']:,.0f}, расходы {f['expenses']:,.0f}, прибыль {f['profit']:,.0f}, маржа {f['margin']:.1f}%")
                
                print("")  # Empty line for readability
            
            # Summary
            print("📊 ИТОГОВАЯ СВОДКА ПО ВСЕМ СЦЕНАРИЯМ:")
            print("=" * 60)
            
            if not errors:
                print("✅ ВСЕ КРИТЕРИИ УСПЕХА ВЫПОЛНЕНЫ:")
                print("   ✅ Все сценарии работают")
                print("   ✅ Данные 2025 и 2026 соответствуют Excel файлу")
                print("   ✅ Индексация 6% применяется с 2027 года к данным 2026")
                print("   ✅ Маржа рассчитывается корректно")
                print("   ✅ Структура ответа содержит все необходимые поля")
                print("\n🎉 ТЕСТ ПРОЙДЕН УСПЕШНО!")
            else:
                print("❌ ОБНАРУЖЕНЫ ОШИБКИ:")
                for i, error in enumerate(errors, 1):
                    print(f"   {i}. {error}")
                print(f"\n❌ ТЕСТ НЕ ПРОЙДЕН: {len(errors)} ошибок")
            
            return len(errors) == 0
            
    except Exception as e:
        error_msg = f"❌ Ошибка при тестировании прогноза УФИЦ: {str(e)}"
        print(error_msg)
        return False

async def main():
    """Main test function"""
    print("🚀 Запуск тестирования обновленного endpoint GET /api/finances/forecast для УФИЦ модель")
    
    success = await test_ufic_forecast_endpoint()
    
    if success:
        print("\n✅ Все тесты пройдены успешно!")
        return 0
    else:
        print("\n❌ Тесты завершились с ошибками!")
        return 1

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    exit(exit_code)