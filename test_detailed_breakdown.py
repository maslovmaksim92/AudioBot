#!/usr/bin/env python3
"""
Test script for УФИЦ модель forecast endpoint with detailed breakdown
"""

import asyncio
import httpx
import json
from typing import Dict, List, Any, Optional

# Backend URL from environment
BACKEND_URL = "https://finreport-dashboard.preview.emergentagent.com"
API_BASE = f"{BACKEND_URL}/api"

class TestResults:
    def __init__(self):
        self.errors = []

async def test_ufic_forecast_detailed_breakdown():
    """Test УФИЦ модель forecast endpoint with detailed revenue and expense breakdown"""
    print("\n=== ТЕСТ ПРОГНОЗА УФИЦ МОДЕЛЬ С ДЕТАЛИЗАЦИЕЙ ДОХОДОВ И РАСХОДОВ ===\n")
    
    results = TestResults()
    company = "УФИЦ модель"
    scenario = "realistic"
    
    # Expected detailed breakdown for 2026 realistic scenario
    expected_2026_breakdown = {
        "revenue_breakdown": {
            "sewing": 15739136,
            "cleaning": 24615780,
            "outsourcing": 14332500
        },
        "expense_breakdown": {
            "labor": 36947205
        }
    }
    
    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            print(f"🏢 Тестируем детализированный прогноз для: {company}")
            print(f"📋 Сценарий: {scenario}")
            print("🎯 Проверяемые критерии:")
            print("   1. Endpoint возвращает 200 статус")
            print("   2. Каждый год в массиве forecast содержит:")
            print("      - revenue_breakdown с полями: sewing, cleaning, outsourcing")
            print("      - expense_breakdown с полем: labor")
            print("   3. Проверить детализацию на 2026 год (реалистичный сценарий):")
            print(f"      - sewing ~{expected_2026_breakdown['revenue_breakdown']['sewing']:,}")
            print(f"      - cleaning ~{expected_2026_breakdown['revenue_breakdown']['cleaning']:,}")
            print(f"      - outsourcing ~{expected_2026_breakdown['revenue_breakdown']['outsourcing']:,}")
            print(f"      - labor ~{expected_2026_breakdown['expense_breakdown']['labor']:,}")
            print("   4. Проверить индексацию 6% ежегодно для 2027-2030")
            print("   5. Суммы детализации совпадают с общими показателями")
            print("")
            
            # Test the forecast endpoint
            response = await client.get(
                f"{API_BASE}/finances/forecast",
                params={"company": company, "scenario": scenario}
            )
            
            print(f"📡 Ответ сервера: {response.status_code}")
            
            # Criterion 1: Check 200 status
            if response.status_code != 200:
                error_msg = f"❌ Ошибка {response.status_code} - {response.text}"
                results.errors.append(error_msg)
                print(error_msg)
                return results
            
            data = response.json()
            print(f"✅ Endpoint возвращает 200 статус")
            
            # Check forecast array exists
            forecast = data.get('forecast', [])
            if not forecast:
                error_msg = "❌ Отсутствует массив forecast"
                results.errors.append(error_msg)
                print(error_msg)
                return results
            
            print(f"📊 Прогноз содержит {len(forecast)} лет")
            
            # Criterion 2: Check each year has breakdown fields
            breakdown_errors = []
            for year_data in forecast:
                year = year_data.get('year')
                
                # Check revenue_breakdown
                revenue_breakdown = year_data.get('revenue_breakdown')
                if not revenue_breakdown:
                    breakdown_errors.append(f"❌ Год {year}: отсутствует revenue_breakdown")
                else:
                    required_revenue_fields = ['sewing', 'cleaning', 'outsourcing']
                    for field in required_revenue_fields:
                        if field not in revenue_breakdown:
                            breakdown_errors.append(f"❌ Год {year}: отсутствует поле {field} в revenue_breakdown")
                
                # Check expense_breakdown
                expense_breakdown = year_data.get('expense_breakdown')
                if not expense_breakdown:
                    breakdown_errors.append(f"❌ Год {year}: отсутствует expense_breakdown")
                else:
                    if 'labor' not in expense_breakdown:
                        breakdown_errors.append(f"❌ Год {year}: отсутствует поле labor в expense_breakdown")
            
            if breakdown_errors:
                results.errors.extend(breakdown_errors)
                for error in breakdown_errors:
                    print(error)
            else:
                print("✅ Все годы содержат корректную структуру детализации")
            
            # Criterion 3: Check 2026 detailed breakdown values
            year_2026 = None
            for year_data in forecast:
                if year_data.get('year') == 2026:
                    year_2026 = year_data
                    break
            
            if not year_2026:
                error_msg = "❌ Не найден год 2026 в прогнозе"
                results.errors.append(error_msg)
                print(error_msg)
            else:
                print(f"📊 Проверяем детализацию 2026 года:")
                
                # Check revenue breakdown 2026
                revenue_breakdown_2026 = year_2026.get('revenue_breakdown', {})
                for category, expected_value in expected_2026_breakdown['revenue_breakdown'].items():
                    actual_value = revenue_breakdown_2026.get(category, 0)
                    tolerance = expected_value * 0.05  # 5% tolerance
                    
                    print(f"   - {category}: {actual_value:,.0f} (ожидалось ~{expected_value:,})")
                    
                    if abs(actual_value - expected_value) > tolerance:
                        error_msg = f"❌ 2026 {category}: {actual_value:,.0f} не соответствует ожидаемому ~{expected_value:,}"
                        results.errors.append(error_msg)
                        print(f"     {error_msg}")
                    else:
                        print(f"     ✅ Значение в пределах допустимого отклонения")
                
                # Check expense breakdown 2026
                expense_breakdown_2026 = year_2026.get('expense_breakdown', {})
                expected_labor = expected_2026_breakdown['expense_breakdown']['labor']
                actual_labor = expense_breakdown_2026.get('labor', 0)
                labor_tolerance = expected_labor * 0.05  # 5% tolerance
                
                print(f"   - labor: {actual_labor:,.0f} (ожидалось ~{expected_labor:,})")
                
                if abs(actual_labor - expected_labor) > labor_tolerance:
                    error_msg = f"❌ 2026 labor: {actual_labor:,.0f} не соответствует ожидаемому ~{expected_labor:,}"
                    results.errors.append(error_msg)
                    print(f"     {error_msg}")
                else:
                    print(f"     ✅ Значение в пределах допустимого отклонения")
            
            # Criterion 4: Check 6% indexation for 2027-2030
            print(f"\n📈 Проверяем индексацию 6% ежегодно для 2027-2030:")
            
            if year_2026:
                base_revenue_breakdown = year_2026.get('revenue_breakdown', {})
                base_expense_breakdown = year_2026.get('expense_breakdown', {})
                
                for year_data in forecast:
                    year = year_data.get('year')
                    if year in [2027, 2028, 2029, 2030]:
                        years_from_2026 = year - 2026
                        expected_multiplier = 1.06 ** years_from_2026
                        
                        print(f"   Год {year} (индексация {expected_multiplier:.4f}):")
                        
                        # Check revenue breakdown indexation
                        current_revenue_breakdown = year_data.get('revenue_breakdown', {})
                        for category, base_value in base_revenue_breakdown.items():
                            expected_indexed_value = base_value * expected_multiplier
                            actual_indexed_value = current_revenue_breakdown.get(category, 0)
                            indexation_tolerance = expected_indexed_value * 0.02  # 2% tolerance for rounding
                            
                            if abs(actual_indexed_value - expected_indexed_value) > indexation_tolerance:
                                error_msg = f"❌ {year} {category}: {actual_indexed_value:,.0f} не соответствует индексированному значению {expected_indexed_value:,.0f}"
                                results.errors.append(error_msg)
                                print(f"     {error_msg}")
                            else:
                                print(f"     ✅ {category}: {actual_indexed_value:,.0f} (ожидалось {expected_indexed_value:,.0f})")
                        
                        # Check expense breakdown indexation
                        current_expense_breakdown = year_data.get('expense_breakdown', {})
                        for category, base_value in base_expense_breakdown.items():
                            expected_indexed_value = base_value * expected_multiplier
                            actual_indexed_value = current_expense_breakdown.get(category, 0)
                            indexation_tolerance = expected_indexed_value * 0.02  # 2% tolerance for rounding
                            
                            if abs(actual_indexed_value - expected_indexed_value) > indexation_tolerance:
                                error_msg = f"❌ {year} {category}: {actual_indexed_value:,.0f} не соответствует индексированному значению {expected_indexed_value:,.0f}"
                                results.errors.append(error_msg)
                                print(f"     {error_msg}")
                            else:
                                print(f"     ✅ {category}: {actual_indexed_value:,.0f} (ожидалось {expected_indexed_value:,.0f})")
            
            # Criterion 5: Check that breakdown sums match total revenue and expenses
            print(f"\n🧮 Проверяем соответствие сумм детализации общим показателям:")
            
            for year_data in forecast:
                year = year_data.get('year')
                total_revenue = year_data.get('revenue', 0)
                total_expenses = year_data.get('expenses', 0)
                
                # Sum revenue breakdown
                revenue_breakdown = year_data.get('revenue_breakdown', {})
                breakdown_revenue_sum = sum(revenue_breakdown.values())
                
                # Sum expense breakdown
                expense_breakdown = year_data.get('expense_breakdown', {})
                breakdown_expense_sum = sum(expense_breakdown.values())
                
                # Check revenue sum
                revenue_tolerance = max(total_revenue * 0.01, 1)  # 1% tolerance or 1 ruble minimum
                if abs(breakdown_revenue_sum - total_revenue) > revenue_tolerance:
                    error_msg = f"❌ {year}: сумма детализации выручки ({breakdown_revenue_sum:,.0f}) не равна общей выручке ({total_revenue:,.0f})"
                    results.errors.append(error_msg)
                    print(f"   {error_msg}")
                else:
                    print(f"   ✅ {year}: сумма детализации выручки = общая выручка ({total_revenue:,.0f})")
                
                # Check expense sum
                expense_tolerance = max(total_expenses * 0.01, 1)  # 1% tolerance or 1 ruble minimum
                if abs(breakdown_expense_sum - total_expenses) > expense_tolerance:
                    error_msg = f"❌ {year}: сумма детализации расходов ({breakdown_expense_sum:,.0f}) не равна общим расходам ({total_expenses:,.0f})"
                    results.errors.append(error_msg)
                    print(f"   {error_msg}")
                else:
                    print(f"   ✅ {year}: сумма детализации расходов = общие расходы ({total_expenses:,.0f})")
            
            # Summary
            if not results.errors:
                print(f"\n🎉 ВСЕ КРИТЕРИИ ДЕТАЛИЗАЦИИ ВЫПОЛНЕНЫ УСПЕШНО!")
                print("✅ Детализация присутствует для всех годов")
                print("✅ Числа соответствуют ожидаемым значениям")
                print("✅ Индексация применяется к детализации")
                print("✅ Суммы детализации = общие показатели")
            else:
                print(f"\n⚠️ Обнаружены проблемы с детализацией: {len(results.errors)} ошибок")
            
    except Exception as e:
        error_msg = f"❌ Ошибка при тестировании детализированного прогноза: {str(e)}"
        results.errors.append(error_msg)
        print(error_msg)
    
    return results

async def main():
    """Main test runner"""
    print("🚀 ТЕСТИРОВАНИЕ ДЕТАЛИЗАЦИИ ПРОГНОЗА УФИЦ МОДЕЛЬ")
    print("=" * 80)
    print(f"🌐 Backend URL: {BACKEND_URL}")
    print(f"📡 API Base: {API_BASE}")
    print("=" * 80)
    
    # Run the detailed breakdown test
    result = await test_ufic_forecast_detailed_breakdown()
    
    # Print summary
    print("\n" + "=" * 80)
    print("📊 ИТОГОВЫЙ ОТЧЁТ")
    print("=" * 80)
    
    if not result.errors:
        print("🎉 ВСЕ ТЕСТЫ ДЕТАЛИЗАЦИИ ПРОШЛИ УСПЕШНО!")
    else:
        print(f"⚠️ ОБНАРУЖЕНЫ ПРОБЛЕМЫ ({len(result.errors)}):")
        for i, error in enumerate(result.errors, 1):
            print(f"   {i}. {error}")
    
    print("\n" + "=" * 80)
    print("🏁 ТЕСТИРОВАНИЕ ЗАВЕРШЕНО")
    print("=" * 80)

if __name__ == "__main__":
    asyncio.run(main())