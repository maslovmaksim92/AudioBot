#!/usr/bin/env python3
"""
Test script for updated УФИЦ модель forecast endpoint with 10% optimistic indexation
"""

import asyncio
import httpx
import json
from typing import Dict, List, Any

# Backend URL from environment
BACKEND_URL = "https://bitrix-audio-1.preview.emergentagent.com"
API_BASE = f"{BACKEND_URL}/api"

class TestResults:
    def __init__(self):
        self.errors = []

async def test_ufic_forecast_updated_optimistic():
    """Test updated УФИЦ модель forecast endpoint with 10% indexation for optimistic scenario"""
    print("\n=== ТЕСТ ОБНОВЛЕННОГО ПРОГНОЗА УФИЦ МОДЕЛЬ (ОПТИМИСТИЧНЫЙ СЦЕНАРИЙ 10%) ===\n")
    
    results = TestResults()
    company = "УФИЦ модель"
    
    # Expected staff counts in descriptions
    expected_descriptions = {
        "pessimistic": "Швеи: 60, Уборщицы: 60, Аутсорсинг: 14",
        "realistic": "Швеи: 41, Уборщицы: 40, Аутсорсинг: 5", 
        "optimistic": "Швеи: 65, Уборщицы: 70, Аутсорсинг: 20"
    }
    
    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            print(f"🏢 Тестируем обновленный прогноз для компании: {company}")
            print("📋 Проверяемые критерии:")
            print("   1. Оптимистичный сценарий использует индексацию 10% (а не 6%)")
            print("   2. Описания содержат информацию о количестве персонала")
            print("   3. Для оптимистичного сценария проверить рост между годами")
            print("   4. Детализация (revenue_breakdown, expense_breakdown) индексируется на 10%")
            print("")
            
            # Test all three scenarios to check descriptions
            for scenario in ["pessimistic", "realistic", "optimistic"]:
                print(f"🔍 Тестируем сценарий: {scenario}")
                
                response = await client.get(
                    f"{API_BASE}/finances/forecast",
                    params={"company": company, "scenario": scenario}
                )
                
                print(f"📡 Ответ сервера для {scenario}: {response.status_code}")
                
                if response.status_code != 200:
                    error_msg = f"❌ Сценарий {scenario}: ошибка {response.status_code} - {response.text}"
                    results.errors.append(error_msg)
                    print(error_msg)
                    continue
                
                data = response.json()
                print(f"✅ Сценарий {scenario}: 200 статус получен")
                
                # Check scenario description contains staff counts
                scenario_info = data.get('scenario_info', {})
                description = scenario_info.get('description', '')
                expected_desc = expected_descriptions[scenario]
                
                print(f"📝 Описание сценария: {description}")
                print(f"🎯 Ожидаемое содержание: {expected_desc}")
                
                if expected_desc in description:
                    print(f"✅ Описание содержит правильную информацию о количестве персонала")
                else:
                    error_msg = f"❌ Сценарий {scenario}: описание не содержит ожидаемую информацию '{expected_desc}'"
                    results.errors.append(error_msg)
                    print(error_msg)
                
                # For optimistic scenario, check 10% indexation
                if scenario == "optimistic":
                    print(f"\n🔍 Детальная проверка оптимистичного сценария (10% индексация):")
                    
                    forecast = data.get('forecast', [])
                    if not forecast:
                        error_msg = f"❌ Отсутствует массив forecast для оптимистичного сценария"
                        results.errors.append(error_msg)
                        print(error_msg)
                        continue
                    
                    # Find 2026 and subsequent years
                    year_2026_data = None
                    year_data = {}
                    
                    for year_item in forecast:
                        year = year_item.get('year')
                        if year == 2026:
                            year_2026_data = year_item
                        if year >= 2026:
                            year_data[year] = year_item
                    
                    if not year_2026_data:
                        error_msg = f"❌ Не найдены данные для 2026 года в оптимистичном сценарии"
                        results.errors.append(error_msg)
                        print(error_msg)
                        continue
                    
                    # Get 2026 base values
                    revenue_2026 = year_2026_data.get('revenue', 0)
                    expenses_2026 = year_2026_data.get('expenses', 0)
                    
                    print(f"📊 Базовые значения 2026:")
                    print(f"   - Выручка: {revenue_2026:,.0f}")
                    print(f"   - Расходы: {expenses_2026:,.0f}")
                    
                    # Check 10% growth for subsequent years
                    for year in [2027, 2028, 2029, 2030]:
                        if year not in year_data:
                            error_msg = f"❌ Отсутствуют данные для {year} года"
                            results.errors.append(error_msg)
                            print(error_msg)
                            continue
                        
                        year_item = year_data[year]
                        actual_revenue = year_item.get('revenue', 0)
                        actual_expenses = year_item.get('expenses', 0)
                        
                        # Calculate expected values with 10% compound growth
                        years_passed = year - 2026
                        growth_factor = 1.10 ** years_passed
                        expected_revenue = revenue_2026 * growth_factor
                        expected_expenses = expenses_2026 * growth_factor
                        
                        print(f"📈 Проверка {year} года (рост {years_passed} лет с 10% индексацией):")
                        print(f"   - Выручка: {actual_revenue:,.0f} (ожидалось {expected_revenue:,.0f})")
                        print(f"   - Расходы: {actual_expenses:,.0f} (ожидалось {expected_expenses:,.0f})")
                        
                        # Allow small rounding differences (0.1%)
                        revenue_diff_pct = abs(actual_revenue - expected_revenue) / expected_revenue * 100 if expected_revenue > 0 else 0
                        expenses_diff_pct = abs(actual_expenses - expected_expenses) / expected_expenses * 100 if expected_expenses > 0 else 0
                        
                        if revenue_diff_pct > 0.1:
                            error_msg = f"❌ {year}: выручка не соответствует 10% росту: {actual_revenue:,.0f} vs {expected_revenue:,.0f} (отклонение {revenue_diff_pct:.2f}%)"
                            results.errors.append(error_msg)
                            print(error_msg)
                        else:
                            print(f"✅ Выручка {year} соответствует 10% росту")
                        
                        if expenses_diff_pct > 0.1:
                            error_msg = f"❌ {year}: расходы не соответствуют 10% росту: {actual_expenses:,.0f} vs {expected_expenses:,.0f} (отклонение {expenses_diff_pct:.2f}%)"
                            results.errors.append(error_msg)
                            print(error_msg)
                        else:
                            print(f"✅ Расходы {year} соответствуют 10% росту")
                    
                    # Check detailed breakdown indexation for optimistic scenario
                    print(f"\n🔍 Проверка детализации (revenue_breakdown, expense_breakdown):")
                    
                    # Check if 2026 has breakdown data
                    revenue_breakdown_2026 = year_2026_data.get('revenue_breakdown', {})
                    expense_breakdown_2026 = year_2026_data.get('expense_breakdown', {})
                    
                    if not revenue_breakdown_2026:
                        error_msg = f"❌ Отсутствует revenue_breakdown для 2026 года"
                        results.errors.append(error_msg)
                        print(error_msg)
                    else:
                        print(f"✅ revenue_breakdown присутствует для 2026")
                        print(f"   - sewing: {revenue_breakdown_2026.get('sewing', 0):,.0f}")
                        print(f"   - cleaning: {revenue_breakdown_2026.get('cleaning', 0):,.0f}")
                        print(f"   - outsourcing: {revenue_breakdown_2026.get('outsourcing', 0):,.0f}")
                    
                    if not expense_breakdown_2026:
                        error_msg = f"❌ Отсутствует expense_breakdown для 2026 года"
                        results.errors.append(error_msg)
                        print(error_msg)
                    else:
                        print(f"✅ expense_breakdown присутствует для 2026")
                        print(f"   - labor: {expense_breakdown_2026.get('labor', 0):,.0f}")
                    
                    # Check breakdown indexation for subsequent years
                    if revenue_breakdown_2026 and expense_breakdown_2026:
                        for year in [2027, 2028, 2029, 2030]:
                            if year not in year_data:
                                continue
                            
                            year_item = year_data[year]
                            revenue_breakdown = year_item.get('revenue_breakdown', {})
                            expense_breakdown = year_item.get('expense_breakdown', {})
                            
                            years_passed = year - 2026
                            growth_factor = 1.10 ** years_passed
                            
                            print(f"📊 Детализация {year} года:")
                            
                            # Check revenue breakdown
                            for category in ['sewing', 'cleaning', 'outsourcing']:
                                base_value = revenue_breakdown_2026.get(category, 0)
                                expected_value = base_value * growth_factor
                                actual_value = revenue_breakdown.get(category, 0)
                                
                                if base_value > 0:  # Only check if base value exists
                                    diff_pct = abs(actual_value - expected_value) / expected_value * 100 if expected_value > 0 else 0
                                    
                                    if diff_pct > 0.1:
                                        error_msg = f"❌ {year}: revenue {category} не соответствует 10% росту: {actual_value:,.0f} vs {expected_value:,.0f}"
                                        results.errors.append(error_msg)
                                        print(f"   ❌ {category}: {actual_value:,.0f} (ожидалось {expected_value:,.0f})")
                                    else:
                                        print(f"   ✅ {category}: {actual_value:,.0f}")
                            
                            # Check expense breakdown
                            base_labor = expense_breakdown_2026.get('labor', 0)
                            expected_labor = base_labor * growth_factor
                            actual_labor = expense_breakdown.get('labor', 0)
                            
                            if base_labor > 0:
                                diff_pct = abs(actual_labor - expected_labor) / expected_labor * 100 if expected_labor > 0 else 0
                                
                                if diff_pct > 0.1:
                                    error_msg = f"❌ {year}: expense labor не соответствует 10% росту: {actual_labor:,.0f} vs {expected_labor:,.0f}"
                                    results.errors.append(error_msg)
                                    print(f"   ❌ labor: {actual_labor:,.0f} (ожидалось {expected_labor:,.0f})")
                                else:
                                    print(f"   ✅ labor: {actual_labor:,.0f}")
                
                print("")  # Empty line for readability
            
            # Summary
            print("📋 ИТОГИ ТЕСТИРОВАНИЯ ОБНОВЛЕННОГО ПРОГНОЗА:")
            if not results.errors:
                print("🎉 ВСЕ КРИТЕРИИ УСПЕХА ВЫПОЛНЕНЫ:")
                print("✅ Оптимистичный сценарий: индексация 10%")
                print("✅ Описания всех сценариев содержат количество швей, уборщиц, аутсорсинга")
                print("✅ Расчеты корректны для всех годов")
                print("✅ Детализация индексируется правильно")
            else:
                print(f"❌ НАЙДЕНО ОШИБОК: {len(results.errors)}")
                for error in results.errors:
                    print(f"   - {error}")
            
    except Exception as e:
        error_msg = f"❌ Ошибка при тестировании обновленного прогноза УФИЦ: {str(e)}"
        results.errors.append(error_msg)
        print(error_msg)
    
    return results

async def main():
    """Main test runner"""
    print("🚀 ЗАПУСК ТЕСТИРОВАНИЯ ОБНОВЛЕННОГО ПРОГНОЗА УФИЦ МОДЕЛЬ")
    print("=" * 80)
    print("Тестируем endpoint GET /api/finances/forecast для УФИЦ модель после изменений")
    print("=" * 80)
    
    result = await test_ufic_forecast_updated_optimistic()
    
    print("\n" + "=" * 80)
    print("📊 ИТОГОВЫЙ ОТЧЁТ")
    print("=" * 80)
    
    if result.errors:
        print(f"❌ НАЙДЕНО ОШИБОК: {len(result.errors)}")
        for error in result.errors:
            print(f"   - {error}")
    else:
        print("🎉 ВСЕ ТЕСТЫ ПРОЙДЕНЫ УСПЕШНО!")
        print("✅ Оптимистичный сценарий использует индексацию 10%")
        print("✅ Описания содержат информацию о количестве персонала")
        print("✅ Расчеты корректны для всех годов")
        print("✅ Детализация индексируется правильно")
    
    print("=" * 80)
    print("🏁 ТЕСТИРОВАНИЕ ЗАВЕРШЕНО")
    print("=" * 80)

if __name__ == "__main__":
    asyncio.run(main())