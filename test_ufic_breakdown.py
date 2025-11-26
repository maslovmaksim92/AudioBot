#!/usr/bin/env python3
"""
Focused test for УФИЦ модель expense breakdown as per review request

This test validates the specific requirements from the review request:
1. Endpoint returns 200 status
2. Expense breakdown contains SEVERAL categories (not just "labor")
3. Categories are taken from "Финансы - Расходы - УФИЦ модель"
4. Breakdown is present for all years 2026-2030
5. Each category is indexed at 4.8% annually for pessimistic scenario
6. Sum of all categories = total expenses for each year
"""

import asyncio
import httpx
import json
from datetime import datetime
from typing import Dict, List, Any, Optional

# Backend URL from environment
BACKEND_URL = "https://bitrix-audio-1.preview.emergentagent.com"
API_BASE = f"{BACKEND_URL}/api"

class TestResults:
    def __init__(self):
        self.finance_endpoints = {}
        self.errors = []

async def test_ufic_expense_breakdown():
    """Test УФИЦ модель forecast endpoint expense breakdown as per review request"""
    print("\n=== ТЕСТ ДЕТАЛИЗАЦИИ РАСХОДОВ УФИЦ МОДЕЛЬ В ПРОГНОЗЕ ===\n")
    
    results = TestResults()
    company = "УФИЦ модель"
    scenario = "pessimistic"
    
    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            print(f"🏢 Тестируем детализацию расходов для: {company}")
            print(f"📊 Сценарий: {scenario}")
            print("📋 Критерии успеха:")
            print("   1. Endpoint возвращает 200 статус")
            print("   2. Детализация расходов (expense_breakdown) содержит НЕСКОЛЬКО категорий (не только 'labor')")
            print("   3. Категории берутся из 'Финансы - Расходы - УФИЦ модель'")
            print("   4. Детализация присутствует для всех годов 2026-2030")
            print("   5. Каждая категория индексируется на 4.8% ежегодно для пессимистичного")
            print("   6. Сумма всех категорий = total expenses для каждого года")
            print("")
            print("🎯 Ожидаемые категории расходов:")
            print("   - Зарплата")
            print("   - Налоги")
            print("   - Аренда")
            print("   - Коммунальные услуги")
            print("   - И другие категории из УФИЦ модель")
            print("")
            
            # Test the forecast endpoint
            response = await client.get(
                f"{API_BASE}/finances/forecast",
                params={"company": company, "scenario": scenario}
            )
            
            print(f"📡 Ответ сервера: {response.status_code}")
            
            # 1. Check 200 status
            if response.status_code != 200:
                error_msg = f"❌ КРИТЕРИЙ 1 НЕ ВЫПОЛНЕН: Endpoint не возвращает 200 статус. Получен: {response.status_code} - {response.text}"
                results.errors.append(error_msg)
                print(error_msg)
                return results
            
            print("✅ КРИТЕРИЙ 1 ВЫПОЛНЕН: Endpoint возвращает 200 статус")
            
            data = response.json()
            results.finance_endpoints['ufic_expense_breakdown'] = data
            
            # Validate basic structure
            required_fields = ['company', 'scenario', 'forecast']
            for field in required_fields:
                if field not in data:
                    error_msg = f"❌ Отсутствует поле '{field}' в ответе"
                    results.errors.append(error_msg)
                    print(error_msg)
                    return results
            
            # Check forecast data
            forecast = data.get('forecast', [])
            if len(forecast) < 5:
                error_msg = f"❌ КРИТЕРИЙ 4 НЕ ВЫПОЛНЕН: Недостаточно лет в прогнозе. Ожидалось 5 (2026-2030), получено {len(forecast)}"
                results.errors.append(error_msg)
                print(error_msg)
                return results
            
            print(f"✅ Прогноз содержит {len(forecast)} лет")
            
            # Check each year for expense breakdown
            years_with_breakdown = 0
            years_with_multiple_categories = 0
            years_with_correct_sum = 0
            all_categories = set()
            indexation_errors = []
            
            print(f"\n📊 Проверяем детализацию расходов по годам:")
            
            prev_year_breakdown = None
            
            for i, year_data in enumerate(forecast):
                year = year_data.get('year')
                total_expenses = year_data.get('expenses', 0)
                expense_breakdown = year_data.get('expense_breakdown', {})
                
                print(f"\n📅 Год {year}:")
                print(f"   - Общие расходы: {total_expenses:,.0f} ₽")
                
                # 2. Check if expense_breakdown exists and has multiple categories
                if not expense_breakdown:
                    error_msg = f"❌ КРИТЕРИЙ 2 НЕ ВЫПОЛНЕН: Год {year} не содержит expense_breakdown"
                    results.errors.append(error_msg)
                    print(f"   ❌ Отсутствует expense_breakdown")
                    continue
                
                years_with_breakdown += 1
                
                # Check number of categories
                categories = list(expense_breakdown.keys())
                category_count = len(categories)
                
                print(f"   - Категорий в детализации: {category_count}")
                print(f"   - Категории: {', '.join(categories)}")
                
                if category_count <= 1:
                    error_msg = f"❌ КРИТЕРИЙ 2 НЕ ВЫПОЛНЕН: Год {year} содержит только {category_count} категорию(й). Ожидалось несколько категорий (не только 'labor')"
                    results.errors.append(error_msg)
                    print(f"   ❌ Недостаточно категорий")
                else:
                    years_with_multiple_categories += 1
                    print(f"   ✅ Содержит несколько категорий")
                
                # Collect all categories for analysis
                all_categories.update(categories)
                
                # 6. Check if sum of categories equals total expenses
                breakdown_sum = sum(expense_breakdown.values())
                sum_diff = abs(breakdown_sum - total_expenses)
                sum_diff_pct = (sum_diff / total_expenses * 100) if total_expenses > 0 else 0
                
                print(f"   - Сумма детализации: {breakdown_sum:,.0f} ₽")
                print(f"   - Разница с общими расходами: {sum_diff:,.0f} ₽ ({sum_diff_pct:.2f}%)")
                
                if sum_diff_pct > 1.0:  # Allow 1% tolerance
                    error_msg = f"❌ КРИТЕРИЙ 6 НЕ ВЫПОЛНЕН: Год {year} - сумма категорий ({breakdown_sum:,.0f}) не равна общим расходам ({total_expenses:,.0f}). Разница: {sum_diff:,.0f} ₽"
                    results.errors.append(error_msg)
                    print(f"   ❌ Сумма не совпадает")
                else:
                    years_with_correct_sum += 1
                    print(f"   ✅ Сумма корректна")
                
                # 5. Check indexation (4.8% annually for pessimistic scenario)
                if prev_year_breakdown and i > 0:
                    print(f"   📈 Проверяем индексацию 4.8% относительно предыдущего года:")
                    
                    for category, current_amount in expense_breakdown.items():
                        if category in prev_year_breakdown:
                            prev_amount = prev_year_breakdown[category]
                            expected_amount = prev_amount * 1.048  # 4.8% increase
                            actual_growth = (current_amount / prev_amount - 1) * 100 if prev_amount > 0 else 0
                            growth_diff = abs(actual_growth - 4.8)
                            
                            print(f"     - {category}: {prev_amount:,.0f} → {current_amount:,.0f} (рост: {actual_growth:.1f}%)")
                            
                            if growth_diff > 0.5:  # Allow 0.5% tolerance
                                error_msg = f"❌ КРИТЕРИЙ 5 НЕ ВЫПОЛНЕН: Год {year}, категория '{category}' - неверная индексация. Ожидался рост 4.8%, получен {actual_growth:.1f}%"
                                indexation_errors.append(error_msg)
                                print(f"       ❌ Неверная индексация")
                            else:
                                print(f"       ✅ Индексация корректна")
                
                prev_year_breakdown = expense_breakdown.copy()
            
            # Summary of criteria checks
            print(f"\n📋 ИТОГОВАЯ ПРОВЕРКА КРИТЕРИЕВ:")
            
            # Criterion 1: Already checked above
            print(f"✅ КРИТЕРИЙ 1: Endpoint возвращает 200 статус")
            
            # Criterion 2: Multiple categories
            if years_with_multiple_categories == len(forecast):
                print(f"✅ КРИТЕРИЙ 2: Детализация расходов содержит несколько категорий во всех годах")
            else:
                error_msg = f"❌ КРИТЕРИЙ 2 НЕ ВЫПОЛНЕН: Только {years_with_multiple_categories} из {len(forecast)} лет содержат несколько категорий"
                results.errors.append(error_msg)
                print(error_msg)
            
            # Criterion 3: Categories from УФИЦ модель
            print(f"✅ КРИТЕРИЙ 3: Найдены категории из УФИЦ модель:")
            expected_categories = ['зарплата', 'налоги', 'аренда', 'коммунальные']
            found_expected = []
            
            for category in all_categories:
                category_lower = category.lower()
                for expected in expected_categories:
                    if expected in category_lower:
                        found_expected.append(category)
                        break
            
            print(f"   - Всего категорий найдено: {len(all_categories)}")
            print(f"   - Категории: {', '.join(sorted(all_categories))}")
            print(f"   - Ожидаемые категории найдены: {', '.join(found_expected) if found_expected else 'Нет'}")
            
            if len(found_expected) >= 2:
                print(f"✅ КРИТЕРИЙ 3 ВЫПОЛНЕН: Найдено {len(found_expected)} ожидаемых категорий")
            else:
                error_msg = f"❌ КРИТЕРИЙ 3 НЕ ВЫПОЛНЕН: Найдено только {len(found_expected)} ожидаемых категорий из {len(expected_categories)}"
                results.errors.append(error_msg)
                print(error_msg)
            
            # Criterion 4: All years 2026-2030
            if years_with_breakdown == len(forecast):
                print(f"✅ КРИТЕРИЙ 4: Детализация присутствует для всех {len(forecast)} лет (2026-2030)")
            else:
                error_msg = f"❌ КРИТЕРИЙ 4 НЕ ВЫПОЛНЕН: Детализация присутствует только в {years_with_breakdown} из {len(forecast)} лет"
                results.errors.append(error_msg)
                print(error_msg)
            
            # Criterion 5: 4.8% indexation
            if indexation_errors:
                for error in indexation_errors:
                    results.errors.append(error)
                    print(error)
            else:
                print(f"✅ КРИТЕРИЙ 5: Индексация 4.8% ежегодно применяется корректно")
            
            # Criterion 6: Sum equals total
            if years_with_correct_sum == len(forecast):
                print(f"✅ КРИТЕРИЙ 6: Сумма категорий равна общим расходам во всех {len(forecast)} годах")
            else:
                error_msg = f"❌ КРИТЕРИЙ 6 НЕ ВЫПОЛНЕН: Сумма корректна только в {years_with_correct_sum} из {len(forecast)} лет"
                results.errors.append(error_msg)
                print(error_msg)
            
            # Final summary
            print(f"\n🎯 ФИНАЛЬНАЯ ОЦЕНКА:")
            criteria_passed = 0
            total_criteria = 6
            
            if response.status_code == 200:
                criteria_passed += 1
            if years_with_multiple_categories == len(forecast):
                criteria_passed += 1
            if len(found_expected) >= 2:
                criteria_passed += 1
            if years_with_breakdown == len(forecast):
                criteria_passed += 1
            if not indexation_errors:
                criteria_passed += 1
            if years_with_correct_sum == len(forecast):
                criteria_passed += 1
            
            print(f"📊 Критериев выполнено: {criteria_passed}/{total_criteria}")
            
            if criteria_passed == total_criteria:
                print(f"🎉 ВСЕ КРИТЕРИИ УСПЕХА ВЫПОЛНЕНЫ!")
                print(f"✅ Детализация расходов УФИЦ модель работает корректно")
            else:
                print(f"⚠️ НЕ ВСЕ КРИТЕРИИ ВЫПОЛНЕНЫ: {total_criteria - criteria_passed} проблем обнаружено")
            
    except Exception as e:
        error_msg = f"❌ Ошибка при тестировании детализации расходов УФИЦ: {str(e)}"
        results.errors.append(error_msg)
        print(error_msg)
    
    return results

async def main():
    """Main test runner for УФИЦ expense breakdown"""
    print("🚀 ТЕСТИРОВАНИЕ ДЕТАЛИЗАЦИИ РАСХОДОВ УФИЦ МОДЕЛЬ")
    print("=" * 80)
    print(f"🌐 Backend URL: {BACKEND_URL}")
    print(f"📡 API Base: {API_BASE}")
    print("=" * 80)
    
    # Run the specific test
    result = await test_ufic_expense_breakdown()
    
    # Print summary
    print("\n" + "=" * 80)
    print("📊 ИТОГОВЫЙ ОТЧЁТ")
    print("=" * 80)
    
    if result.errors:
        print(f"❌ Обнаружено {len(result.errors)} ошибок:")
        for i, error in enumerate(result.errors, 1):
            print(f"  {i}. {error}")
        print("\n⚠️ ТЕСТИРОВАНИЕ НЕ ПРОЙДЕНО")
    else:
        print("🎉 ВСЕ КРИТЕРИИ УСПЕХА ВЫПОЛНЕНЫ!")
        print("✅ ТЕСТИРОВАНИЕ ПРОЙДЕНО УСПЕШНО")
    
    print("=" * 80)

if __name__ == "__main__":
    asyncio.run(main())