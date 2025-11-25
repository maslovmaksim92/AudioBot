#!/usr/bin/env python3
"""
Специальный тест для endpoint GET /api/finances/expense-analysis?company=ВАШ ДОМ модель

Критерии успеха из review request:
1. Endpoint должен возвращать 200 статус
2. Ответ должен содержать поле "expenses" (массив)
3. Ответ должен содержать поле "total" (число > 0)
4. В массиве "expenses" должны быть категории с полями: category, amount, percentage
5. Сумма всех amount должна примерно равняться total
6. Должны быть категории: "Зарплата" (уменьшенная), "Налоги" (5% от выручки), возможно "Аутсорсинг персонала"
7. НЕ должно быть категорий: "Кредиты", "Швеи", "Юридические услуги", "Продукты питания"

Backend URL: https://call-logger-6.preview.emergentagent.com
"""

import asyncio
import httpx
import json
from typing import Dict, List, Any, Optional

# Backend URL from review request
BACKEND_URL = "https://call-logger-6.preview.emergentagent.com"
API_BASE = f"{BACKEND_URL}/api"

class TestResults:
    def __init__(self):
        self.success_criteria = {
            "status_200": False,
            "has_expenses_field": False,
            "has_total_field": False,
            "total_greater_than_zero": False,
            "expenses_have_required_fields": False,
            "sum_matches_total": False,
            "has_required_categories": False,
            "no_forbidden_categories": False
        }
        self.errors = []
        self.warnings = []
        self.response_data = None
        self.found_categories = []
        self.forbidden_found = []
        self.required_found = []

async def test_vasdom_expense_analysis():
    """Test ВАШ ДОМ модель expense analysis endpoint according to review request"""
    print("=" * 80)
    print("ТЕСТ ENDPOINT: GET /api/finances/expense-analysis?company=ВАШ ДОМ модель")
    print("=" * 80)
    print()
    
    results = TestResults()
    company = "ВАШ ДОМ модель"
    
    # Required categories (should be present)
    required_categories = ["Зарплата", "Налоги"]
    possible_categories = ["Аутсорсинг персонала"]
    
    # Forbidden categories (should NOT be present)
    forbidden_categories = ["Кредиты", "Швеи", "Юридические услуги", "Продукты питания"]
    
    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            print(f"🏢 Тестируем компанию: {company}")
            print(f"🌐 Backend URL: {BACKEND_URL}")
            print(f"📡 Endpoint: GET /api/finances/expense-analysis?company={company}")
            print()
            
            # Make the API request
            print("📤 Отправляем запрос...")
            response = await client.get(
                f"{API_BASE}/finances/expense-analysis",
                params={"company": company}
            )
            
            print(f"📥 Получен ответ: {response.status_code}")
            
            # КРИТЕРИЙ 1: Endpoint должен возвращать 200 статус
            if response.status_code == 200:
                results.success_criteria["status_200"] = True
                print("✅ КРИТЕРИЙ 1: Статус 200 - ВЫПОЛНЕН")
            else:
                error_msg = f"❌ КРИТЕРИЙ 1: Ожидался статус 200, получен {response.status_code}"
                results.errors.append(error_msg)
                print(error_msg)
                print(f"📄 Текст ошибки: {response.text}")
                return results
            
            # Parse response
            try:
                data = response.json()
                results.response_data = data
                print("✅ JSON ответ успешно распарсен")
            except Exception as e:
                error_msg = f"❌ Ошибка парсинга JSON: {str(e)}"
                results.errors.append(error_msg)
                print(error_msg)
                return results
            
            print()
            print("📊 АНАЛИЗ СТРУКТУРЫ ОТВЕТА:")
            print("-" * 40)
            
            # КРИТЕРИЙ 2: Ответ должен содержать поле "expenses" (массив)
            if "expenses" in data and isinstance(data["expenses"], list):
                results.success_criteria["has_expenses_field"] = True
                print("✅ КРИТЕРИЙ 2: Поле 'expenses' (массив) - ВЫПОЛНЕН")
                print(f"   📋 Количество категорий расходов: {len(data['expenses'])}")
            else:
                error_msg = "❌ КРИТЕРИЙ 2: Отсутствует поле 'expenses' или оно не является массивом"
                results.errors.append(error_msg)
                print(error_msg)
            
            # КРИТЕРИЙ 3: Ответ должен содержать поле "total" (число > 0)
            if "total" in data:
                total_value = data["total"]
                if isinstance(total_value, (int, float)) and total_value > 0:
                    results.success_criteria["has_total_field"] = True
                    results.success_criteria["total_greater_than_zero"] = True
                    print("✅ КРИТЕРИЙ 3: Поле 'total' (число > 0) - ВЫПОЛНЕН")
                    print(f"   💰 Общая сумма расходов: {total_value:,.2f} ₽")
                else:
                    error_msg = f"❌ КРИТЕРИЙ 3: Поле 'total' должно быть числом > 0, получено: {total_value}"
                    results.errors.append(error_msg)
                    print(error_msg)
            else:
                error_msg = "❌ КРИТЕРИЙ 3: Отсутствует поле 'total'"
                results.errors.append(error_msg)
                print(error_msg)
            
            print()
            
            # КРИТЕРИЙ 4: В массиве "expenses" должны быть категории с полями: category, amount, percentage
            expenses = data.get("expenses", [])
            if expenses:
                print("📋 АНАЛИЗ КАТЕГОРИЙ РАСХОДОВ:")
                print("-" * 40)
                
                required_expense_fields = ["category", "amount", "percentage"]
                all_expenses_valid = True
                
                for i, expense in enumerate(expenses):
                    category_name = expense.get("category", f"Категория_{i}")
                    results.found_categories.append(category_name)
                    
                    # Check required fields for each expense
                    missing_fields = []
                    for field in required_expense_fields:
                        if field not in expense:
                            missing_fields.append(field)
                    
                    if missing_fields:
                        all_expenses_valid = False
                        error_msg = f"❌ Категория '{category_name}': отсутствуют поля {missing_fields}"
                        results.errors.append(error_msg)
                        print(error_msg)
                    else:
                        amount = expense.get("amount", 0)
                        percentage = expense.get("percentage", 0)
                        print(f"   📊 {category_name}: {amount:,.2f} ₽ ({percentage:.1f}%)")
                
                if all_expenses_valid:
                    results.success_criteria["expenses_have_required_fields"] = True
                    print("✅ КРИТЕРИЙ 4: Все категории имеют требуемые поля - ВЫПОЛНЕН")
                else:
                    print("❌ КРИТЕРИЙ 4: Не все категории имеют требуемые поля")
            
            print()
            
            # КРИТЕРИЙ 5: Сумма всех amount должна примерно равняться total
            if expenses and "total" in data:
                calculated_sum = sum(expense.get("amount", 0) for expense in expenses)
                total_value = data["total"]
                
                # Allow 1% difference for floating point precision
                difference = abs(calculated_sum - total_value)
                tolerance = total_value * 0.01  # 1% tolerance
                
                print(f"🧮 ПРОВЕРКА СУММЫ:")
                print(f"   📊 Сумма категорий: {calculated_sum:,.2f} ₽")
                print(f"   📊 Поле 'total': {total_value:,.2f} ₽")
                print(f"   📊 Разница: {difference:,.2f} ₽")
                print(f"   📊 Допустимая погрешность (1%): {tolerance:,.2f} ₽")
                
                if difference <= tolerance:
                    results.success_criteria["sum_matches_total"] = True
                    print("✅ КРИТЕРИЙ 5: Сумма категорий соответствует total - ВЫПОЛНЕН")
                else:
                    error_msg = f"❌ КРИТЕРИЙ 5: Сумма категорий ({calculated_sum:,.2f}) не соответствует total ({total_value:,.2f})"
                    results.errors.append(error_msg)
                    print(error_msg)
            
            print()
            
            # КРИТЕРИЙ 6: Должны быть категории: "Зарплата" (уменьшенная), "Налоги" (5% от выручки), возможно "Аутсорсинг персонала"
            print("🔍 ПРОВЕРКА ОБЯЗАТЕЛЬНЫХ КАТЕГОРИЙ:")
            print("-" * 40)
            
            found_required = []
            found_possible = []
            
            for category in results.found_categories:
                # Check for required categories (case-insensitive partial match)
                for req_cat in required_categories:
                    if req_cat.lower() in category.lower():
                        found_required.append(category)
                        results.required_found.append(category)
                        print(f"✅ Найдена обязательная категория: '{category}' (соответствует '{req_cat}')")
                        break
                
                # Check for possible categories
                for poss_cat in possible_categories:
                    if poss_cat.lower() in category.lower():
                        found_possible.append(category)
                        print(f"✅ Найдена возможная категория: '{category}' (соответствует '{poss_cat}')")
                        break
            
            # Check if all required categories are found
            if len(found_required) >= len(required_categories):
                results.success_criteria["has_required_categories"] = True
                print("✅ КРИТЕРИЙ 6: Все обязательные категории найдены - ВЫПОЛНЕН")
            else:
                missing_required = []
                for req_cat in required_categories:
                    found = False
                    for found_cat in found_required:
                        if req_cat.lower() in found_cat.lower():
                            found = True
                            break
                    if not found:
                        missing_required.append(req_cat)
                
                error_msg = f"❌ КРИТЕРИЙ 6: Отсутствуют обязательные категории: {missing_required}"
                results.errors.append(error_msg)
                print(error_msg)
            
            if found_possible:
                print(f"ℹ️ Найдены дополнительные категории: {found_possible}")
            
            print()
            
            # КРИТЕРИЙ 7: НЕ должно быть категорий: "Кредиты", "Швеи", "Юридические услуги", "Продукты питания"
            print("🚫 ПРОВЕРКА ЗАПРЕЩЕННЫХ КАТЕГОРИЙ:")
            print("-" * 40)
            
            found_forbidden = []
            
            for category in results.found_categories:
                for forbidden_cat in forbidden_categories:
                    if forbidden_cat.lower() in category.lower():
                        found_forbidden.append(category)
                        results.forbidden_found.append(category)
                        error_msg = f"❌ Найдена запрещенная категория: '{category}' (соответствует '{forbidden_cat}')"
                        results.errors.append(error_msg)
                        print(error_msg)
                        break
            
            if not found_forbidden:
                results.success_criteria["no_forbidden_categories"] = True
                print("✅ КРИТЕРИЙ 7: Запрещенные категории отсутствуют - ВЫПОЛНЕН")
            else:
                print(f"❌ КРИТЕРИЙ 7: Найдены запрещенные категории: {found_forbidden}")
            
            print()
            print("📋 ПОЛНЫЙ СПИСОК НАЙДЕННЫХ КАТЕГОРИЙ:")
            print("-" * 40)
            for i, category in enumerate(results.found_categories, 1):
                expense = expenses[i-1] if i-1 < len(expenses) else {}
                amount = expense.get("amount", 0)
                percentage = expense.get("percentage", 0)
                print(f"   {i:2d}. {category}: {amount:,.2f} ₽ ({percentage:.1f}%)")
            
    except Exception as e:
        error_msg = f"❌ Критическая ошибка при тестировании: {str(e)}"
        results.errors.append(error_msg)
        print(error_msg)
        import traceback
        print(f"📄 Traceback: {traceback.format_exc()}")
    
    return results

def print_final_summary(results: TestResults):
    """Print final test summary"""
    print()
    print("=" * 80)
    print("ИТОГОВЫЙ ОТЧЕТ ТЕСТИРОВАНИЯ")
    print("=" * 80)
    
    # Count successful criteria
    successful_criteria = sum(1 for success in results.success_criteria.values() if success)
    total_criteria = len(results.success_criteria)
    
    print(f"📊 РЕЗУЛЬТАТ: {successful_criteria}/{total_criteria} критериев выполнено")
    print()
    
    # Print each criterion status
    criterion_names = {
        "status_200": "1. Статус 200",
        "has_expenses_field": "2. Поле 'expenses' (массив)",
        "has_total_field": "3. Поле 'total' (число > 0)",
        "total_greater_than_zero": "3. Total > 0",
        "expenses_have_required_fields": "4. Поля category, amount, percentage",
        "sum_matches_total": "5. Сумма категорий = total",
        "has_required_categories": "6. Обязательные категории",
        "no_forbidden_categories": "7. Отсутствие запрещенных категорий"
    }
    
    print("📋 ДЕТАЛИЗАЦИЯ ПО КРИТЕРИЯМ:")
    for key, success in results.success_criteria.items():
        name = criterion_names.get(key, key)
        status = "✅ ВЫПОЛНЕН" if success else "❌ НЕ ВЫПОЛНЕН"
        print(f"   {name}: {status}")
    
    print()
    
    if results.errors:
        print("❌ ОБНАРУЖЕННЫЕ ОШИБКИ:")
        for i, error in enumerate(results.errors, 1):
            print(f"   {i}. {error}")
        print()
    
    if results.warnings:
        print("⚠️ ПРЕДУПРЕЖДЕНИЯ:")
        for i, warning in enumerate(results.warnings, 1):
            print(f"   {i}. {warning}")
        print()
    
    # Overall result
    if successful_criteria == total_criteria:
        print("🎉 ВСЕ КРИТЕРИИ УСПЕХА ВЫПОЛНЕНЫ!")
        print("✅ Endpoint GET /api/finances/expense-analysis?company=ВАШ ДОМ модель работает корректно")
    else:
        print(f"⚠️ ВЫПОЛНЕНО {successful_criteria} из {total_criteria} критериев")
        print("❌ Требуется исправление для полного соответствия требованиям")
    
    print()
    print("=" * 80)

async def main():
    """Main test function"""
    print("🚀 ЗАПУСК ТЕСТИРОВАНИЯ ENDPOINT ВАШ ДОМ МОДЕЛЬ")
    print()
    
    # Run the test
    results = await test_vasdom_expense_analysis()
    
    # Print final summary
    print_final_summary(results)
    
    # Return exit code based on results
    if all(results.success_criteria.values()):
        return 0  # Success
    else:
        return 1  # Failure

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    exit(exit_code)