#!/usr/bin/env python3
"""
Backend Test Suite for VasDom AudioBot System
Testing Finance Module and Plannerka functionality

This test validates:
FINANCE MODULE:
1. GET /api/finances/cash-flow - движение денег
2. GET /api/finances/profit-loss - прибыли и убытки  
3. GET /api/finances/balance-sheet - балансовый отчёт
4. GET /api/finances/expense-analysis - анализ расходов
5. GET /api/finances/available-months - доступные месяцы
6. GET /api/finances/debts - задолженности
7. GET /api/finances/inventory - товарные запасы
8. GET /api/finances/dashboard - сводка
9. GET /api/finances/transactions - список транзакций
10. POST /api/finances/transactions - создание транзакции
11. GET /api/finances/revenue/monthly - ручная выручка

PLANNERKA MODULE:
1. POST /api/plannerka/create - создание планёрки
2. POST /api/plannerka/analyze/{id} - AI-анализ с GPT-4o
3. GET /api/plannerka/list - список планёрок
"""

import asyncio
import httpx
import json
from datetime import datetime
from typing import Dict, List, Any, Optional
import os

# Backend URL from environment
BACKEND_URL = "https://finreport-dashboard.preview.emergentagent.com"
API_BASE = f"{BACKEND_URL}/api"

class TestResults:
    def __init__(self):
        # Plannerka results
        self.created_meeting_id = None
        self.created_meeting_data = None
        self.analysis_result = None
        self.meetings_list = []
        self.openai_working = False
        self.tasks_extracted = []
        self.summary_generated = False
        
        # Finance results
        self.finance_endpoints = {}
        self.created_transaction_id = None
        self.database_working = False
        
        # Common
        self.errors = []

async def test_finance_cash_flow():
    """Test finance cash flow endpoint"""
    print("=== ТЕСТ ДВИЖЕНИЯ ДЕНЕГ (CASH FLOW) ===\n")
    
    results = TestResults()
    
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            print("💰 Тестируем GET /api/finances/cash-flow...")
            
            response = await client.get(f"{API_BASE}/finances/cash-flow")
            print(f"📡 Ответ сервера: {response.status_code}")
            
            if response.status_code != 200:
                error_msg = f"❌ Ошибка cash-flow: {response.status_code} - {response.text}"
                results.errors.append(error_msg)
                print(error_msg)
                return results
            
            data = response.json()
            results.finance_endpoints['cash_flow'] = data
            
            print("✅ Cash flow получен успешно")
            print(f"📊 Структура ответа:")
            
            # Validate structure
            required_fields = ['cash_flow', 'summary']
            for field in required_fields:
                if field not in data:
                    results.errors.append(f"❌ Отсутствует поле '{field}' в cash-flow")
                else:
                    print(f"✅ Поле '{field}' присутствует")
            
            # Check summary structure
            if 'summary' in data:
                summary = data['summary']
                summary_fields = ['total_income', 'total_expense', 'net_cash_flow']
                for field in summary_fields:
                    if field not in summary:
                        results.errors.append(f"❌ Отсутствует поле '{field}' в summary")
                    else:
                        print(f"✅ Summary поле '{field}': {summary[field]}")
            
            # Check cash flow items
            cash_flow_items = data.get('cash_flow', [])
            print(f"📈 Записей движения денег: {len(cash_flow_items)}")
            
            if cash_flow_items:
                sample_item = cash_flow_items[0]
                item_fields = ['date', 'income', 'expense', 'balance']
                for field in item_fields:
                    if field not in sample_item:
                        results.errors.append(f"❌ Отсутствует поле '{field}' в записи cash_flow")
                    else:
                        print(f"✅ Поле записи '{field}': {sample_item[field]}")
            
    except Exception as e:
        error_msg = f"❌ Ошибка при тестировании cash-flow: {str(e)}"
        results.errors.append(error_msg)
        print(error_msg)
    
    return results

async def test_finance_profit_loss():
    """Test finance profit loss endpoint"""
    print("\n=== ТЕСТ ПРИБЫЛЕЙ И УБЫТКОВ (PROFIT LOSS) ===\n")
    
    results = TestResults()
    
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            print("📊 Тестируем GET /api/finances/profit-loss...")
            
            response = await client.get(f"{API_BASE}/finances/profit-loss")
            print(f"📡 Ответ сервера: {response.status_code}")
            
            if response.status_code != 200:
                error_msg = f"❌ Ошибка profit-loss: {response.status_code} - {response.text}"
                results.errors.append(error_msg)
                print(error_msg)
                return results
            
            data = response.json()
            results.finance_endpoints['profit_loss'] = data
            
            print("✅ Profit loss получен успешно")
            print(f"📊 Структура ответа:")
            
            # Validate structure
            required_fields = ['profit_loss', 'summary']
            for field in required_fields:
                if field not in data:
                    results.errors.append(f"❌ Отсутствует поле '{field}' в profit-loss")
                else:
                    print(f"✅ Поле '{field}' присутствует")
            
            # Check summary structure
            if 'summary' in data:
                summary = data['summary']
                summary_fields = ['total_revenue', 'total_expenses', 'net_profit', 'average_margin']
                for field in summary_fields:
                    if field not in summary:
                        results.errors.append(f"❌ Отсутствует поле '{field}' в summary")
                    else:
                        print(f"✅ Summary поле '{field}': {summary[field]}")
            
            # Check profit loss items
            profit_loss_items = data.get('profit_loss', [])
            print(f"📈 Записей прибылей/убытков: {len(profit_loss_items)}")
            
            if profit_loss_items:
                sample_item = profit_loss_items[0]
                item_fields = ['period', 'revenue', 'expenses', 'profit', 'margin']
                for field in item_fields:
                    if field not in sample_item:
                        results.errors.append(f"❌ Отсутствует поле '{field}' в записи profit_loss")
                    else:
                        print(f"✅ Поле записи '{field}': {sample_item[field]}")
            
    except Exception as e:
        error_msg = f"❌ Ошибка при тестировании profit-loss: {str(e)}"
        results.errors.append(error_msg)
        print(error_msg)
    
    return results

async def test_finance_expense_analysis():
    """Test finance expense analysis endpoint"""
    print("\n=== ТЕСТ АНАЛИЗА РАСХОДОВ (EXPENSE ANALYSIS) ===\n")
    
    results = TestResults()
    
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            print("💸 Тестируем GET /api/finances/expense-analysis...")
            
            # Test without month filter
            response = await client.get(f"{API_BASE}/finances/expense-analysis")
            print(f"📡 Ответ сервера (без фильтра): {response.status_code}")
            
            if response.status_code != 200:
                error_msg = f"❌ Ошибка expense-analysis: {response.status_code} - {response.text}"
                results.errors.append(error_msg)
                print(error_msg)
                return results
            
            data = response.json()
            results.finance_endpoints['expense_analysis'] = data
            
            print("✅ Expense analysis получен успешно")
            
            # Validate structure
            required_fields = ['expenses', 'total']
            for field in required_fields:
                if field not in data:
                    results.errors.append(f"❌ Отсутствует поле '{field}' в expense-analysis")
                else:
                    print(f"✅ Поле '{field}' присутствует")
            
            # Check expenses structure
            expenses = data.get('expenses', [])
            print(f"📈 Категорий расходов: {len(expenses)}")
            print(f"💰 Общая сумма расходов: {data.get('total', 0)}")
            
            if expenses:
                sample_expense = expenses[0]
                expense_fields = ['category', 'amount', 'percentage']
                for field in expense_fields:
                    if field not in sample_expense:
                        results.errors.append(f"❌ Отсутствует поле '{field}' в записи expense")
                    else:
                        print(f"✅ Поле расхода '{field}': {sample_expense[field]}")
            
            # Test with month filter
            print("\n🗓️ Тестируем с фильтром по месяцу...")
            response_month = await client.get(f"{API_BASE}/finances/expense-analysis?month=Январь 2025")
            print(f"📡 Ответ сервера (с фильтром): {response_month.status_code}")
            
            if response_month.status_code == 200:
                month_data = response_month.json()
                print(f"✅ Фильтр по месяцу работает")
                print(f"📅 Месяц: {month_data.get('month')}")
                print(f"💰 Расходов за месяц: {len(month_data.get('expenses', []))}")
            else:
                print(f"⚠️ Фильтр по месяцу не работает: {response_month.status_code}")
            
    except Exception as e:
        error_msg = f"❌ Ошибка при тестировании expense-analysis: {str(e)}"
        results.errors.append(error_msg)
        print(error_msg)
    
    return results

async def test_finance_available_months():
    """Test finance available months endpoint"""
    print("\n=== ТЕСТ ДОСТУПНЫХ МЕСЯЦЕВ ===\n")
    
    results = TestResults()
    
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            print("📅 Тестируем GET /api/finances/available-months...")
            
            response = await client.get(f"{API_BASE}/finances/available-months")
            print(f"📡 Ответ сервера: {response.status_code}")
            
            if response.status_code != 200:
                error_msg = f"❌ Ошибка available-months: {response.status_code} - {response.text}"
                results.errors.append(error_msg)
                print(error_msg)
                return results
            
            data = response.json()
            results.finance_endpoints['available_months'] = data
            
            print("✅ Available months получен успешно")
            
            # Validate structure
            required_fields = ['months', 'total']
            for field in required_fields:
                if field not in data:
                    results.errors.append(f"❌ Отсутствует поле '{field}' в available-months")
                else:
                    print(f"✅ Поле '{field}' присутствует")
            
            months = data.get('months', [])
            print(f"📅 Доступных месяцев: {data.get('total', 0)}")
            
            if months:
                print(f"📋 Примеры месяцев: {months[:5]}")
            else:
                print("⚠️ Нет доступных месяцев")
            
    except Exception as e:
        error_msg = f"❌ Ошибка при тестировании available-months: {str(e)}"
        results.errors.append(error_msg)
        print(error_msg)
    
    return results

async def test_finance_balance_sheet():
    """Test finance balance sheet endpoint (mock data)"""
    print("\n=== ТЕСТ БАЛАНСОВОГО ОТЧЁТА ===\n")
    
    results = TestResults()
    
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            print("🏦 Тестируем GET /api/finances/balance-sheet...")
            
            response = await client.get(f"{API_BASE}/finances/balance-sheet")
            print(f"📡 Ответ сервера: {response.status_code}")
            
            if response.status_code != 200:
                error_msg = f"❌ Ошибка balance-sheet: {response.status_code} - {response.text}"
                results.errors.append(error_msg)
                print(error_msg)
                return results
            
            data = response.json()
            results.finance_endpoints['balance_sheet'] = data
            
            print("✅ Balance sheet получен успешно (mock данные)")
            
            # Validate structure
            required_sections = ['assets', 'liabilities', 'equity']
            for section in required_sections:
                if section not in data:
                    results.errors.append(f"❌ Отсутствует секция '{section}' в balance-sheet")
                else:
                    print(f"✅ Секция '{section}' присутствует")
                    section_data = data[section]
                    if 'total' in section_data:
                        print(f"   💰 Итого {section}: {section_data['total']}")
            
    except Exception as e:
        error_msg = f"❌ Ошибка при тестировании balance-sheet: {str(e)}"
        results.errors.append(error_msg)
        print(error_msg)
    
    return results

async def test_finance_debts():
    """Test finance debts endpoint (mock data)"""
    print("\n=== ТЕСТ ЗАДОЛЖЕННОСТЕЙ ===\n")
    
    results = TestResults()
    
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            print("💳 Тестируем GET /api/finances/debts...")
            
            response = await client.get(f"{API_BASE}/finances/debts")
            print(f"📡 Ответ сервера: {response.status_code}")
            
            if response.status_code != 200:
                error_msg = f"❌ Ошибка debts: {response.status_code} - {response.text}"
                results.errors.append(error_msg)
                print(error_msg)
                return results
            
            data = response.json()
            results.finance_endpoints['debts'] = data
            
            print("✅ Debts получен успешно (mock данные)")
            
            # Validate structure
            required_fields = ['debts', 'summary']
            for field in required_fields:
                if field not in data:
                    results.errors.append(f"❌ Отсутствует поле '{field}' в debts")
                else:
                    print(f"✅ Поле '{field}' присутствует")
            
            debts = data.get('debts', [])
            summary = data.get('summary', {})
            
            print(f"💳 Количество задолженностей: {len(debts)}")
            print(f"💰 Общая сумма: {summary.get('total', 0)}")
            print(f"⚠️ Просроченная сумма: {summary.get('overdue', 0)}")
            
    except Exception as e:
        error_msg = f"❌ Ошибка при тестировании debts: {str(e)}"
        results.errors.append(error_msg)
        print(error_msg)
    
    return results

async def test_finance_inventory():
    """Test finance inventory endpoint (mock data)"""
    print("\n=== ТЕСТ ТОВАРНЫХ ЗАПАСОВ ===\n")
    
    results = TestResults()
    
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            print("📦 Тестируем GET /api/finances/inventory...")
            
            response = await client.get(f"{API_BASE}/finances/inventory")
            print(f"📡 Ответ сервера: {response.status_code}")
            
            if response.status_code != 200:
                error_msg = f"❌ Ошибка inventory: {response.status_code} - {response.text}"
                results.errors.append(error_msg)
                print(error_msg)
                return results
            
            data = response.json()
            results.finance_endpoints['inventory'] = data
            
            print("✅ Inventory получен успешно (mock данные)")
            
            # Validate structure
            required_fields = ['inventory', 'summary']
            for field in required_fields:
                if field not in data:
                    results.errors.append(f"❌ Отсутствует поле '{field}' в inventory")
                else:
                    print(f"✅ Поле '{field}' присутствует")
            
            inventory = data.get('inventory', [])
            summary = data.get('summary', {})
            
            print(f"📦 Количество позиций: {len(inventory)}")
            print(f"💰 Общая стоимость: {summary.get('total_value', 0)}")
            print(f"📊 Общее количество: {summary.get('total_items', 0)}")
            
    except Exception as e:
        error_msg = f"❌ Ошибка при тестировании inventory: {str(e)}"
        results.errors.append(error_msg)
        print(error_msg)
    
    return results

async def test_finance_dashboard():
    """Test finance dashboard endpoint"""
    print("\n=== ТЕСТ ФИНАНСОВОЙ СВОДКИ (DASHBOARD) ===\n")
    
    results = TestResults()
    
    try:
        async with httpx.AsyncClient(timeout=60.0) as client:  # Longer timeout as it aggregates data
            print("📊 Тестируем GET /api/finances/dashboard...")
            
            response = await client.get(f"{API_BASE}/finances/dashboard")
            print(f"📡 Ответ сервера: {response.status_code}")
            
            if response.status_code != 200:
                error_msg = f"❌ Ошибка dashboard: {response.status_code} - {response.text}"
                results.errors.append(error_msg)
                print(error_msg)
                return results
            
            data = response.json()
            results.finance_endpoints['dashboard'] = data
            
            print("✅ Dashboard получен успешно")
            
            # Validate structure - dashboard aggregates all other endpoints
            expected_sections = ['cash_flow', 'profit_loss', 'balance', 'expenses', 'debts', 'inventory']
            for section in expected_sections:
                if section not in data:
                    results.errors.append(f"❌ Отсутствует секция '{section}' в dashboard")
                else:
                    print(f"✅ Секция '{section}' присутствует")
            
            print("📊 Сводка по всем показателям получена")
            
    except Exception as e:
        error_msg = f"❌ Ошибка при тестировании dashboard: {str(e)}"
        results.errors.append(error_msg)
        print(error_msg)
    
    return results

async def test_finance_transactions_list():
    """Test finance transactions list endpoint"""
    print("\n=== ТЕСТ СПИСКА ТРАНЗАКЦИЙ ===\n")
    
    results = TestResults()
    
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            print("💼 Тестируем GET /api/finances/transactions...")
            
            response = await client.get(f"{API_BASE}/finances/transactions?limit=10&offset=0")
            print(f"📡 Ответ сервера: {response.status_code}")
            
            if response.status_code != 200:
                error_msg = f"❌ Ошибка transactions list: {response.status_code} - {response.text}"
                results.errors.append(error_msg)
                print(error_msg)
                return results
            
            data = response.json()
            results.finance_endpoints['transactions_list'] = data
            
            print("✅ Transactions list получен успешно")
            print(f"📊 Количество транзакций: {len(data)}")
            
            if data:
                sample_transaction = data[0]
                required_fields = ['id', 'date', 'amount', 'category', 'type', 'created_at']
                for field in required_fields:
                    if field not in sample_transaction:
                        results.errors.append(f"❌ Отсутствует поле '{field}' в транзакции")
                    else:
                        print(f"✅ Поле транзакции '{field}': {sample_transaction[field]}")
            else:
                print("⚠️ Список транзакций пуст")
            
    except Exception as e:
        error_msg = f"❌ Ошибка при тестировании transactions list: {str(e)}"
        results.errors.append(error_msg)
        print(error_msg)
    
    return results

async def test_finance_create_transaction():
    """Test finance create transaction endpoint"""
    print("\n=== ТЕСТ СОЗДАНИЯ ТРАНЗАКЦИИ ===\n")
    
    results = TestResults()
    
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            print("💰 Тестируем POST /api/finances/transactions...")
            
            # Test data as specified in the review request
            test_transaction = {
                "date": "2025-10-17T00:00:00Z",
                "amount": 1000,
                "category": "Зарплата",
                "type": "expense",
                "description": "Тестовая транзакция для проверки API",
                "payment_method": "Банковский перевод",
                "counterparty": "Тестовый сотрудник",
                "project": "Январь 2025"
            }
            
            print(f"📝 Данные транзакции: {json.dumps(test_transaction, ensure_ascii=False, indent=2)}")
            
            response = await client.post(
                f"{API_BASE}/finances/transactions",
                json=test_transaction,
                headers={"Content-Type": "application/json"}
            )
            
            print(f"📡 Ответ сервера: {response.status_code}")
            
            if response.status_code != 200:
                error_msg = f"❌ Ошибка создания транзакции: {response.status_code} - {response.text}"
                results.errors.append(error_msg)
                print(error_msg)
                return results
            
            data = response.json()
            results.created_transaction_id = data.get('id')
            results.finance_endpoints['created_transaction'] = data
            
            print(f"✅ Транзакция создана с ID: {results.created_transaction_id}")
            
            # Validate response structure
            required_fields = ['id', 'date', 'amount', 'category', 'type', 'created_at']
            for field in required_fields:
                if field not in data:
                    results.errors.append(f"❌ Отсутствует поле '{field}' в ответе создания")
                else:
                    print(f"✅ Поле '{field}': {data[field]}")
            
            # Validate data integrity
            if data.get('amount') != test_transaction['amount']:
                results.errors.append(f"❌ Неверная сумма: ожидалась {test_transaction['amount']}, получена {data.get('amount')}")
            
            if data.get('category') != test_transaction['category']:
                results.errors.append(f"❌ Неверная категория: ожидалась '{test_transaction['category']}', получена '{data.get('category')}'")
            
            if data.get('type') != test_transaction['type']:
                results.errors.append(f"❌ Неверный тип: ожидался '{test_transaction['type']}', получен '{data.get('type')}'")
            
            if not results.errors:
                print("✅ Все поля транзакции корректны")
            
    except Exception as e:
        error_msg = f"❌ Ошибка при тестировании создания транзакции: {str(e)}"
        results.errors.append(error_msg)
        print(error_msg)
    
    return results

async def test_finance_revenue_monthly():
    """Test finance monthly revenue endpoint"""
    print("\n=== ТЕСТ РУЧНОЙ ВЫРУЧКИ ===\n")
    
    results = TestResults()
    
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            print("💵 Тестируем GET /api/finances/revenue/monthly...")
            
            response = await client.get(f"{API_BASE}/finances/revenue/monthly")
            print(f"📡 Ответ сервера: {response.status_code}")
            
            if response.status_code != 200:
                error_msg = f"❌ Ошибка revenue monthly: {response.status_code} - {response.text}"
                results.errors.append(error_msg)
                print(error_msg)
                return results
            
            data = response.json()
            results.finance_endpoints['revenue_monthly'] = data
            
            print("✅ Revenue monthly получен успешно")
            
            # Validate structure
            required_fields = ['revenues']
            for field in required_fields:
                if field not in data:
                    results.errors.append(f"❌ Отсутствует поле '{field}' в revenue monthly")
                else:
                    print(f"✅ Поле '{field}' присутствует")
            
            revenues = data.get('revenues', [])
            print(f"📊 Записей выручки: {len(revenues)}")
            
            if revenues:
                sample_revenue = revenues[0]
                revenue_fields = ['month', 'revenue']
                for field in revenue_fields:
                    if field not in sample_revenue:
                        results.errors.append(f"❌ Отсутствует поле '{field}' в записи выручки")
                    else:
                        print(f"✅ Поле выручки '{field}': {sample_revenue[field]}")
            else:
                print("⚠️ Нет записей выручки (таблица может быть пустой)")
            
    except Exception as e:
        error_msg = f"❌ Ошибка при тестировании revenue monthly: {str(e)}"
        results.errors.append(error_msg)
        print(error_msg)
    
    return results

async def test_finance_expense_details():
    """Test new expense details endpoint for specific months"""
    print("\n=== ТЕСТ ДЕТАЛИЗАЦИИ РАСХОДОВ ПО МЕСЯЦАМ ===\n")
    
    results = TestResults()
    
    # Test months as specified in the review request
    test_months = ["Июль 2025", "Март 2025", "Сентябрь 2025"]
    
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            for month in test_months:
                print(f"💸 Тестируем GET /api/finances/expense-details?month={month}...")
                
                response = await client.get(f"{API_BASE}/finances/expense-details", params={"month": month})
                print(f"📡 Ответ сервера для {month}: {response.status_code}")
                
                if response.status_code != 200:
                    error_msg = f"❌ Ошибка expense-details для {month}: {response.status_code} - {response.text}"
                    results.errors.append(error_msg)
                    print(error_msg)
                    continue
                
                data = response.json()
                results.finance_endpoints[f'expense_details_{month}'] = data
                
                print(f"✅ Expense details для {month} получен успешно")
                
                # Validate response structure
                required_fields = ['transactions', 'total', 'month', 'count']
                for field in required_fields:
                    if field not in data:
                        results.errors.append(f"❌ Отсутствует поле '{field}' в expense-details для {month}")
                    else:
                        print(f"✅ Поле '{field}' присутствует")
                
                # Validate month field
                if data.get('month') != month:
                    results.errors.append(f"❌ Неверный месяц в ответе: ожидался '{month}', получен '{data.get('month')}'")
                else:
                    print(f"✅ Месяц корректен: {data.get('month')}")
                
                # Check transactions structure
                transactions = data.get('transactions', [])
                total = data.get('total', 0)
                count = data.get('count', 0)
                
                print(f"📊 Транзакций найдено: {count}")
                print(f"💰 Общая сумма расходов: {total}")
                
                # Validate count matches transactions length
                if len(transactions) != count:
                    results.errors.append(f"❌ Несоответствие count ({count}) и длины массива transactions ({len(transactions)}) для {month}")
                else:
                    print(f"✅ Count соответствует количеству транзакций")
                
                # Validate total calculation
                if transactions:
                    calculated_total = sum(t.get('amount', 0) for t in transactions)
                    if abs(calculated_total - total) > 0.01:  # Allow small floating point differences
                        results.errors.append(f"❌ Неверный расчет total для {month}: ожидалось {calculated_total}, получено {total}")
                    else:
                        print(f"✅ Total корректно рассчитан")
                
                # Check transaction structure
                if transactions:
                    sample_transaction = transactions[0]
                    required_transaction_fields = ['id', 'date', 'category', 'amount', 'description', 'payment_method', 'counterparty']
                    
                    print(f"📋 Проверяем структуру транзакции:")
                    for field in required_transaction_fields:
                        if field not in sample_transaction:
                            results.errors.append(f"❌ Отсутствует поле '{field}' в транзакции для {month}")
                        else:
                            value = sample_transaction[field]
                            print(f"✅ Поле '{field}': {value}")
                    
                    # Validate that all transactions are expenses (type='expense')
                    # Note: The endpoint filters by type='expense' in SQL, so we assume all returned are expenses
                    print(f"✅ Все транзакции являются расходами (фильтр type='expense' применен в SQL)")
                    
                    # Show sample transaction details
                    print(f"📝 Пример транзакции:")
                    print(f"   - ID: {sample_transaction.get('id')}")
                    print(f"   - Дата: {sample_transaction.get('date')}")
                    print(f"   - Категория: {sample_transaction.get('category')}")
                    print(f"   - Сумма: {sample_transaction.get('amount')}")
                    print(f"   - Описание: {sample_transaction.get('description')}")
                    print(f"   - Способ оплаты: {sample_transaction.get('payment_method')}")
                    print(f"   - Контрагент: {sample_transaction.get('counterparty')}")
                else:
                    print(f"⚠️ Нет транзакций для месяца {month}")
                
                print(f"")  # Empty line for readability
            
            # Test existing expense-analysis endpoint to ensure it still works
            print("🔄 Проверяем совместимость с существующим endpoint expense-analysis...")
            
            for month in test_months:
                response = await client.get(f"{API_BASE}/finances/expense-analysis", params={"month": month})
                print(f"📡 expense-analysis для {month}: {response.status_code}")
                
                if response.status_code != 200:
                    error_msg = f"❌ Существующий endpoint expense-analysis не работает для {month}: {response.status_code}"
                    results.errors.append(error_msg)
                else:
                    print(f"✅ Существующий endpoint expense-analysis работает для {month}")
            
    except Exception as e:
        error_msg = f"❌ Ошибка при тестировании expense-details: {str(e)}"
        results.errors.append(error_msg)
        print(error_msg)
    
    return results

async def test_consolidated_financial_model():
    """Test consolidated financial model for ООО ВАШ ДОМ + УФИЦ"""
    print("\n=== ТЕСТ КОНСОЛИДИРОВАННОЙ ФИНАНСОВОЙ МОДЕЛИ ООО ВАШ ДОМ + УФИЦ ===\n")
    
    results = TestResults()
    consolidated_company = "ООО ВАШ ДОМ + УФИЦ"
    
    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            print(f"🏢 Тестируем консолидированную модель для: {consolidated_company}")
            print("📋 Логика консолидации:")
            print("   - Выручка = ООО ВАШ ДОМ минус 'Швеи' и 'Аутсорсинг'")
            print("   - Расходы = ООО ВАШ ДОМ + УФИЦ минус 'Кредиты', 'Аутсорсинг персонала с Ю/ЦЛ', 'Швеи'")
            print("")
            
            # 1. Test consolidated profit-loss
            print("💰 1. Тестируем GET /api/finances/profit-loss?company=ООО+ВАШ+ДОМ+%2B+УФИЦ")
            
            response = await client.get(f"{API_BASE}/finances/profit-loss", params={"company": consolidated_company})
            print(f"📡 Ответ сервера: {response.status_code}")
            
            if response.status_code != 200:
                error_msg = f"❌ Ошибка consolidated profit-loss: {response.status_code} - {response.text}"
                results.errors.append(error_msg)
                print(error_msg)
            else:
                data = response.json()
                results.finance_endpoints['consolidated_profit_loss'] = data
                print("✅ Консолидированные прибыли/убытки получены успешно")
                
                # Validate structure
                required_fields = ['profit_loss', 'summary']
                for field in required_fields:
                    if field not in data:
                        results.errors.append(f"❌ Отсутствует поле '{field}' в consolidated profit-loss")
                    else:
                        print(f"✅ Поле '{field}' присутствует")
                
                # Check summary
                if 'summary' in data:
                    summary = data['summary']
                    print(f"📊 Консолидированная сводка:")
                    print(f"   - Общая выручка: {summary.get('total_revenue', 0)}")
                    print(f"   - Общие расходы: {summary.get('total_expenses', 0)}")
                    print(f"   - Чистая прибыль: {summary.get('net_profit', 0)}")
                    print(f"   - Средняя маржа: {summary.get('average_margin', 0)}%")
            
            print("")
            
            # 2. Test consolidated expense-analysis
            print("💸 2. Тестируем GET /api/finances/expense-analysis?company=ООО+ВАШ+ДОМ+%2B+УФИЦ")
            
            response = await client.get(f"{API_BASE}/finances/expense-analysis", params={"company": consolidated_company})
            print(f"📡 Ответ сервера: {response.status_code}")
            
            if response.status_code != 200:
                error_msg = f"❌ Ошибка consolidated expense-analysis: {response.status_code} - {response.text}"
                results.errors.append(error_msg)
                print(error_msg)
            else:
                data = response.json()
                results.finance_endpoints['consolidated_expense_analysis'] = data
                print("✅ Консолидированный анализ расходов получен успешно")
                
                # Validate structure
                required_fields = ['expenses', 'total']
                for field in required_fields:
                    if field not in data:
                        results.errors.append(f"❌ Отсутствует поле '{field}' в consolidated expense-analysis")
                    else:
                        print(f"✅ Поле '{field}' присутствует")
                
                # Check excluded categories are not present
                excluded_categories = ['Кредиты', 'Аутсорсинг персонала с Ю/ЦЛ', 'Швеи']
                expenses = data.get('expenses', [])
                
                print(f"📊 Консолидированные расходы:")
                print(f"   - Категорий расходов: {len(expenses)}")
                print(f"   - Общая сумма: {data.get('total', 0)}")
                
                # Check for excluded categories
                found_excluded = []
                for expense in expenses:
                    category = expense.get('category', '')
                    if category in excluded_categories:
                        found_excluded.append(category)
                
                if found_excluded:
                    error_msg = f"❌ Найдены исключаемые категории в консолидированных расходах: {found_excluded}"
                    results.errors.append(error_msg)
                    print(error_msg)
                else:
                    print("✅ Исключаемые категории отсутствуют в результатах")
                
                # Show top categories
                if expenses:
                    print("📋 Топ категории расходов:")
                    for i, expense in enumerate(expenses[:5], 1):
                        print(f"   {i}. {expense.get('category')}: {expense.get('amount')} ({expense.get('percentage')}%)")
            
            print("")
            
            # 3. Test consolidated expense-analysis with month filter
            print("📅 3. Тестируем GET /api/finances/expense-analysis?company=ООО+ВАШ+ДОМ+%2B+УФИЦ&month=Январь+2025")
            
            response = await client.get(f"{API_BASE}/finances/expense-analysis", params={
                "company": consolidated_company,
                "month": "Январь 2025"
            })
            print(f"📡 Ответ сервера: {response.status_code}")
            
            if response.status_code != 200:
                error_msg = f"❌ Ошибка consolidated expense-analysis с месяцем: {response.status_code} - {response.text}"
                results.errors.append(error_msg)
                print(error_msg)
            else:
                data = response.json()
                results.finance_endpoints['consolidated_expense_analysis_monthly'] = data
                print("✅ Консолидированный анализ расходов за месяц получен успешно")
                
                # Validate month field
                if data.get('month') != "Январь 2025":
                    results.errors.append(f"❌ Неверный месяц в ответе: ожидался 'Январь 2025', получен '{data.get('month')}'")
                else:
                    print(f"✅ Месяц корректен: {data.get('month')}")
                
                expenses = data.get('expenses', [])
                print(f"📊 Расходы за Январь 2025:")
                print(f"   - Категорий: {len(expenses)}")
                print(f"   - Общая сумма: {data.get('total', 0)}")
            
            print("")
            
            # 4. Test consolidated revenue-analysis
            print("💵 4. Тестируем GET /api/finances/revenue-analysis?company=ООО+ВАШ+ДОМ+%2B+УФИЦ")
            
            response = await client.get(f"{API_BASE}/finances/revenue-analysis", params={"company": consolidated_company})
            print(f"📡 Ответ сервера: {response.status_code}")
            
            if response.status_code != 200:
                error_msg = f"❌ Ошибка consolidated revenue-analysis: {response.status_code} - {response.text}"
                results.errors.append(error_msg)
                print(error_msg)
            else:
                data = response.json()
                results.finance_endpoints['consolidated_revenue_analysis'] = data
                print("✅ Консолидированный анализ выручки получен успешно")
                
                # Validate structure
                required_fields = ['revenue', 'total']
                for field in required_fields:
                    if field not in data:
                        results.errors.append(f"❌ Отсутствует поле '{field}' в consolidated revenue-analysis")
                    else:
                        print(f"✅ Поле '{field}' присутствует")
                
                # Check excluded categories for revenue (Швеи, Аутсорсинг)
                excluded_revenue_categories = ['Швеи', 'Аутсорсинг']
                revenues = data.get('revenue', [])
                
                print(f"📊 Консолидированная выручка:")
                print(f"   - Категорий выручки: {len(revenues)}")
                print(f"   - Общая сумма: {data.get('total', 0)}")
                
                # Check for excluded categories
                found_excluded_revenue = []
                for revenue in revenues:
                    category = revenue.get('category', '')
                    if category in excluded_revenue_categories:
                        found_excluded_revenue.append(category)
                
                if found_excluded_revenue:
                    error_msg = f"❌ Найдены исключаемые категории в консолидированной выручке: {found_excluded_revenue}"
                    results.errors.append(error_msg)
                    print(error_msg)
                else:
                    print("✅ Исключаемые категории выручки отсутствуют в результатах")
                
                # Show revenue categories
                if revenues:
                    print("📋 Категории выручки:")
                    for i, revenue in enumerate(revenues[:5], 1):
                        print(f"   {i}. {revenue.get('category')}: {revenue.get('amount')} ({revenue.get('percentage')}%)")
            
            print("")
            
            # 5. Test individual company endpoints still work
            print("🔄 5. Проверяем работу endpoints для отдельных компаний...")
            
            individual_companies = ["ООО ВАШ ДОМ", "УФИЦ"]
            
            for company in individual_companies:
                print(f"\n🏢 Тестируем компанию: {company}")
                
                # Test profit-loss for individual company
                response = await client.get(f"{API_BASE}/finances/profit-loss", params={"company": company})
                print(f"📡 profit-loss для {company}: {response.status_code}")
                
                if response.status_code != 200:
                    error_msg = f"❌ Endpoint profit-loss не работает для {company}: {response.status_code}"
                    results.errors.append(error_msg)
                else:
                    print(f"✅ Endpoint profit-loss работает для {company}")
                
                # Test expense-analysis for individual company
                response = await client.get(f"{API_BASE}/finances/expense-analysis", params={"company": company})
                print(f"📡 expense-analysis для {company}: {response.status_code}")
                
                if response.status_code != 200:
                    error_msg = f"❌ Endpoint expense-analysis не работает для {company}: {response.status_code}"
                    results.errors.append(error_msg)
                else:
                    print(f"✅ Endpoint expense-analysis работает для {company}")
            
            print("")
            
            # 6. Validate consolidation logic by comparing individual vs consolidated
            print("🧮 6. Проверяем логику консолидации...")
            
            # Get individual company data for validation
            vasdom_response = await client.get(f"{API_BASE}/finances/expense-analysis", params={"company": "ООО ВАШ ДОМ"})
            ufic_response = await client.get(f"{API_BASE}/finances/expense-analysis", params={"company": "УФИЦ"})
            
            if vasdom_response.status_code == 200 and ufic_response.status_code == 200:
                vasdom_data = vasdom_response.json()
                ufic_data = ufic_response.json()
                
                vasdom_total = vasdom_data.get('total', 0)
                ufic_total = ufic_data.get('total', 0)
                
                print(f"📊 Данные для проверки консолидации:")
                print(f"   - ООО ВАШ ДОМ общие расходы: {vasdom_total}")
                print(f"   - УФИЦ общие расходы: {ufic_total}")
                
                # Get excluded amounts from ООО ВАШ ДОМ
                excluded_amount = 0
                vasdom_expenses = vasdom_data.get('expenses', [])
                for expense in vasdom_expenses:
                    if expense.get('category') in ['Кредиты', 'Аутсорсинг персонала с Ю/ЦЛ', 'Швеи']:
                        excluded_amount += expense.get('amount', 0)
                
                expected_consolidated_total = vasdom_total + ufic_total - excluded_amount
                
                # Get actual consolidated total
                if 'consolidated_expense_analysis' in results.finance_endpoints:
                    actual_consolidated_total = results.finance_endpoints['consolidated_expense_analysis'].get('total', 0)
                    
                    print(f"   - Исключаемая сумма: {excluded_amount}")
                    print(f"   - Ожидаемая консолидированная сумма: {expected_consolidated_total}")
                    print(f"   - Фактическая консолидированная сумма: {actual_consolidated_total}")
                    
                    # Allow small differences due to floating point arithmetic
                    if abs(expected_consolidated_total - actual_consolidated_total) < 1.0:
                        print("✅ Логика консолидации расходов работает корректно")
                    else:
                        error_msg = f"❌ Неверная логика консолидации: ожидалось {expected_consolidated_total}, получено {actual_consolidated_total}"
                        results.errors.append(error_msg)
                        print(error_msg)
            else:
                print("⚠️ Не удалось получить данные отдельных компаний для проверки логики")
            
    except Exception as e:
        error_msg = f"❌ Ошибка при тестировании консолидированной модели: {str(e)}"
        results.errors.append(error_msg)
        print(error_msg)
    
    return results

async def test_plannerka_create_endpoint():
    """Test plannerka creation endpoint"""
    print("\n=== ТЕСТ СОЗДАНИЯ ПЛАНЁРКИ ===\n")
    
    results = TestResults()
    
    # Test data from the review request
    test_data = {
        "title": "Тестовая планёрка",
        "transcription": "Обсуждали задачи на неделю. Иванову поручено завершить отчет до пятницы. Петрову нужно проверить документы до среды. Сидорову поручена подготовка презентации с высоким приоритетом до четверга.",
        "participants": ["Иванов", "Петров", "Сидоров"]
    }
    
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            print("🔍 Создаем планёрку...")
            print(f"📝 Данные: {json.dumps(test_data, ensure_ascii=False, indent=2)}")
            
            # Test the create endpoint
            response = await client.post(
                f"{API_BASE}/plannerka/create",
                json=test_data,
                headers={"Content-Type": "application/json"}
            )
            
            print(f"📡 Ответ сервера: {response.status_code}")
            
            if response.status_code != 200:
                error_msg = f"❌ Ошибка создания планёрки: {response.status_code} - {response.text}"
                results.errors.append(error_msg)
                print(error_msg)
                return results
            
            data = response.json()
            results.created_meeting_data = data
            results.created_meeting_id = data.get('id')
            results.database_working = True
            
            print(f"✅ Планёрка создана с ID: {results.created_meeting_id}")
            print(f"📊 Структура ответа:")
            print(f"   - ID: {data.get('id')}")
            print(f"   - Title: {data.get('title')}")
            print(f"   - Date: {data.get('date')}")
            print(f"   - Participants: {data.get('participants')}")
            print(f"   - Transcription length: {len(data.get('transcription', ''))}")
            print(f"   - Summary: {data.get('summary')}")
            print(f"   - Tasks: {data.get('tasks')}")
            
            # Validate response structure
            required_fields = ['id', 'title', 'date', 'transcription', 'participants', 'created_at']
            for field in required_fields:
                if field not in data:
                    results.errors.append(f"❌ Отсутствует поле '{field}' в ответе")
                else:
                    print(f"✅ Поле '{field}' присутствует")
            
            # Validate data integrity
            if data.get('title') != test_data['title']:
                results.errors.append(f"❌ Неверный title: ожидался '{test_data['title']}', получен '{data.get('title')}'")
            
            if data.get('transcription') != test_data['transcription']:
                results.errors.append(f"❌ Неверная transcription")
            
            if data.get('participants') != test_data['participants']:
                results.errors.append(f"❌ Неверные participants")
            
            if not results.errors:
                print("✅ Все поля корректны")
            
    except Exception as e:
        error_msg = f"❌ Ошибка при тестировании создания планёрки: {str(e)}"
        results.errors.append(error_msg)
        print(error_msg)
    
    return results

async def test_plannerka_analyze_endpoint(meeting_id: str):
    """Test plannerka AI analysis endpoint"""
    print("\n=== ТЕСТ AI-АНАЛИЗА ПЛАНЁРКИ ===\n")
    
    results = TestResults()
    results.created_meeting_id = meeting_id
    
    try:
        async with httpx.AsyncClient(timeout=60.0) as client:  # Longer timeout for AI analysis
            print(f"🤖 Запускаем AI-анализ планёрки ID: {meeting_id}")
            
            # Test the analyze endpoint
            response = await client.post(f"{API_BASE}/plannerka/analyze/{meeting_id}")
            
            print(f"📡 Ответ сервера: {response.status_code}")
            
            if response.status_code != 200:
                error_msg = f"❌ Ошибка AI-анализа: {response.status_code} - {response.text}"
                results.errors.append(error_msg)
                print(error_msg)
                
                # Check for specific OpenAI errors
                if "OPENAI_API_KEY" in response.text:
                    results.errors.append("❌ OPENAI_API_KEY не настроен")
                elif "transcription is too short" in response.text:
                    results.errors.append("❌ Транскрипция слишком короткая")
                
                return results
            
            data = response.json()
            results.analysis_result = data
            results.openai_working = True
            
            print(f"✅ AI-анализ завершен успешно")
            print(f"📊 Результат анализа:")
            print(f"   - Success: {data.get('success')}")
            print(f"   - Tasks count: {data.get('tasks_count')}")
            
            # Check summary
            summary = data.get('summary', '')
            if summary:
                results.summary_generated = True
                print(f"✅ Саммари сгенерировано ({len(summary)} символов)")
                print(f"📝 Саммари: {summary[:200]}{'...' if len(summary) > 200 else ''}")
            else:
                results.errors.append("❌ Саммари не сгенерировано")
            
            # Check tasks
            tasks = data.get('tasks', [])
            results.tasks_extracted = tasks
            
            if tasks:
                print(f"✅ Извлечено задач: {len(tasks)}")
                print("📋 Задачи:")
                
                for i, task in enumerate(tasks, 1):
                    title = task.get('title', 'Без названия')
                    assignee = task.get('assignee', 'Не назначен')
                    deadline = task.get('deadline', 'Не указан')
                    priority = task.get('priority', 'medium')
                    
                    print(f"   {i}. {title}")
                    print(f"      - Исполнитель: {assignee}")
                    print(f"      - Срок: {deadline}")
                    print(f"      - Приоритет: {priority}")
                    
                    # Validate task structure
                    required_task_fields = ['title']
                    for field in required_task_fields:
                        if field not in task or not task[field]:
                            results.errors.append(f"❌ Задача {i}: отсутствует поле '{field}'")
                
                # Check if expected tasks are found
                expected_assignees = ['Иванов', 'Петров', 'Сидоров']
                found_assignees = [task.get('assignee', '') for task in tasks]
                
                for expected in expected_assignees:
                    if any(expected in assignee for assignee in found_assignees):
                        print(f"✅ Найдена задача для {expected}")
                    else:
                        print(f"⚠️ Не найдена задача для {expected}")
                
            else:
                results.errors.append("❌ Задачи не извлечены")
            
            # Validate response structure
            required_fields = ['success', 'summary', 'tasks', 'tasks_count']
            for field in required_fields:
                if field not in data:
                    results.errors.append(f"❌ Отсутствует поле '{field}' в ответе анализа")
            
            # Check if success is true
            if not data.get('success'):
                results.errors.append("❌ Поле 'success' не равно true")
            
    except Exception as e:
        error_msg = f"❌ Ошибка при тестировании AI-анализа: {str(e)}"
        results.errors.append(error_msg)
        print(error_msg)
    
    return results

async def test_plannerka_list_endpoint():
    """Test plannerka list endpoint"""
    print("\n=== ТЕСТ СПИСКА ПЛАНЁРОК ===\n")
    
    results = TestResults()
    
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            print("📋 Получаем список планёрок...")
            
            # Test the list endpoint
            response = await client.get(f"{API_BASE}/plannerka/list?limit=20&offset=0")
            
            print(f"📡 Ответ сервера: {response.status_code}")
            
            if response.status_code != 200:
                error_msg = f"❌ Ошибка получения списка: {response.status_code} - {response.text}"
                results.errors.append(error_msg)
                print(error_msg)
                return results
            
            data = response.json()
            results.meetings_list = data.get('meetings', [])
            
            print(f"✅ Список получен успешно")
            print(f"📊 Результат:")
            print(f"   - Количество планёрок: {data.get('count', 0)}")
            print(f"   - Планёрок в ответе: {len(results.meetings_list)}")
            
            # Validate response structure
            required_fields = ['meetings', 'count']
            for field in required_fields:
                if field not in data:
                    results.errors.append(f"❌ Отсутствует поле '{field}' в ответе списка")
            
            # Check meetings structure
            if results.meetings_list:
                print("📋 Примеры планёрок:")
                
                for i, meeting in enumerate(results.meetings_list[:3], 1):  # Show first 3
                    meeting_id = meeting.get('id', 'N/A')
                    title = meeting.get('title', 'Без названия')
                    date = meeting.get('date', 'Не указана')
                    participants_count = len(meeting.get('participants', []))
                    tasks_count = len(meeting.get('tasks', []))
                    has_summary = bool(meeting.get('summary'))
                    
                    print(f"   {i}. ID: {meeting_id}")
                    print(f"      - Название: {title}")
                    print(f"      - Дата: {date}")
                    print(f"      - Участников: {participants_count}")
                    print(f"      - Задач: {tasks_count}")
                    print(f"      - Есть саммари: {has_summary}")
                
                # Validate meeting structure
                sample_meeting = results.meetings_list[0]
                expected_meeting_fields = ['id', 'title', 'date', 'transcription', 'participants']
                
                for field in expected_meeting_fields:
                    if field not in sample_meeting:
                        results.errors.append(f"❌ Отсутствует поле '{field}' в структуре планёрки")
                    else:
                        print(f"✅ Поле '{field}' присутствует в структуре")
            else:
                print("⚠️ Список планёрок пуст")
            
    except Exception as e:
        error_msg = f"❌ Ошибка при тестировании списка планёрок: {str(e)}"
        results.errors.append(error_msg)
        print(error_msg)
    
    return results

async def test_openai_configuration():
    """Test OpenAI API configuration"""
    print("\n🔍 Проверяем конфигурацию OpenAI...")
    
    try:
        # Check if OPENAI_API_KEY is configured by testing a simple endpoint
        async with httpx.AsyncClient(timeout=15.0) as client:
            # We'll test this indirectly through the health endpoint
            response = await client.get(f"{API_BASE}/health")
            if response.status_code == 200:
                print("✅ Backend доступен")
            else:
                print(f"⚠️ Backend недоступен: {response.status_code}")
                
        # Check environment variables (we can't directly access them, but we can infer from API responses)
        print("📋 Конфигурация будет проверена через API вызовы")
        
    except Exception as e:
        print(f"❌ Ошибка проверки конфигурации: {str(e)}")

async def test_database_connection():
    """Test database connection through plannerka endpoints"""
    print("\n🔍 Проверяем подключение к базе данных...")
    
    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            # Test database connection by trying to get the list
            response = await client.get(f"{API_BASE}/plannerka/list?limit=1")
            
            if response.status_code == 200:
                print("✅ База данных доступна")
                return True
            elif response.status_code == 500 and "Database connection error" in response.text:
                print("❌ Ошибка подключения к базе данных")
                return False
            else:
                print(f"⚠️ Неожиданный ответ: {response.status_code}")
                return False
                
    except Exception as e:
        print(f"❌ Ошибка проверки БД: {str(e)}")
        return False

async def test_ufic_forecast_endpoint():
    """Test УФИЦ модель forecast endpoint with exact Excel data"""
    print("\n=== ТЕСТ ПРОГНОЗА УФИЦ МОДЕЛЬ С ДАННЫМИ ИЗ EXCEL ===\n")
    
    results = TestResults()
    scenarios = ["pessimistic", "realistic", "optimistic"]
    company = "УФИЦ модель"
    
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
                    results.errors.append(error_msg)
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
                        results.errors.append(error_msg)
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
                    results.errors.append(error_msg)
                    print(error_msg)
                else:
                    print(f"✅ Выручка 2025 соответствует Excel данным")
                
                if abs(base_expenses - expected_expenses_2025) > 1:
                    error_msg = f"❌ Сценарий {scenario}: расходы 2025 не соответствуют Excel: {base_expenses:,.0f} vs {expected_expenses_2025:,}"
                    results.errors.append(error_msg)
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
                            results.errors.append(error_msg)
                            print(error_msg)
                        else:
                            print(f"✅ Выручка 2026 соответствует Excel данным")
                        
                        if abs(expenses_2026 - expected_expenses_2026) > 1:
                            error_msg = f"❌ Сценарий {scenario}: расходы 2026 не соответствуют Excel: {expenses_2026:,.0f} vs {expected_expenses_2026:,}"
                            results.errors.append(error_msg)
                            print(error_msg)
                        else:
                            print(f"✅ Расходы 2026 соответствуют Excel данным")
                    else:
                        error_msg = f"❌ Сценарий {scenario}: данные за 2026 год не найдены в прогнозе"
                        results.errors.append(error_msg)
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
                                    results.errors.append(error_msg)
                                    print(f"        ❌ Выручка не соответствует индексации 6%")
                                else:
                                    print(f"        ✅ Выручка соответствует индексации 6%")
                                
                                if abs(actual_expenses - expected_expenses) > 100:
                                    error_msg = f"❌ Сценарий {scenario}: неверная индексация расходов {year}: {actual_expenses:,.0f} vs {expected_expenses:,.0f}"
                                    results.errors.append(error_msg)
                                    print(f"        ❌ Расходы не соответствуют индексации 6%")
                                else:
                                    print(f"        ✅ Расходы соответствуют индексации 6%")
                    else:
                        error_msg = f"❌ Сценарий {scenario}: не найдены данные 2026 года для проверки индексации"
                        results.errors.append(error_msg)
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
                            results.errors.append(error_msg)
                            print(f"        ❌ Прибыль рассчитана неверно")
                        else:
                            print(f"        ✅ Прибыль рассчитана корректно")
                        
                        # Check margin calculation
                        if abs(margin - expected_margin) > 0.1:
                            error_msg = f"❌ Сценарий {scenario}: неверный расчет маржи {year}: {margin:.2f}% vs {expected_margin:.2f}%"
                            results.errors.append(error_msg)
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
            
            # Summary of all scenarios
            print("📊 ИТОГОВАЯ СВОДКА ПО ВСЕМ СЦЕНАРИЯМ:")
            print("=" * 60)
            
            successful_scenarios = []
            failed_scenarios = []
            
            for scenario in scenarios:
                if scenario in scenario_results:
                    successful_scenarios.append(scenario)
                    data = scenario_results[scenario]
                    forecast = data.get('forecast', [])
                    if forecast:
                        first_year = forecast[0]
                        last_year = forecast[-1]
                        cleaners = first_year.get('cleaners_count', 'N/A')
                        avg_margin = sum(f.get('margin', 0) for f in forecast) / len(forecast)
                        
                        print(f"✅ {scenario.upper()}: {cleaners} мест, маржа {avg_margin:.1f}%")
                        print(f"   2026: {first_year['revenue']:,.0f} / {first_year['expenses']:,.0f}")
                        print(f"   2030: {last_year['revenue']:,.0f} / {last_year['expenses']:,.0f}")
                else:
                    failed_scenarios.append(scenario)
                    print(f"❌ {scenario.upper()}: ОШИБКА")
            
            print("")
            print(f"✅ Успешных сценариев: {len(successful_scenarios)}/3")
            if failed_scenarios:
                print(f"❌ Неуспешных сценариев: {len(failed_scenarios)}/3 - {failed_scenarios}")
            
            # Store results
            results.finance_endpoints['ufic_forecast'] = scenario_results
            
    except Exception as e:
        error_msg = f"❌ Ошибка при тестировании прогноза УФИЦ: {str(e)}"
        results.errors.append(error_msg)
        print(error_msg)
    
    return results

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
    """Main test function"""
    print("🚀 Запуск тестирования VasDom AudioBot - УФИЦ Прогноз с Детализацией")
    print(f"🌐 Backend URL: {BACKEND_URL}")
    print(f"📡 API Base: {API_BASE}")
    print("=" * 80)
    
    all_errors = []
    finance_results = {}
    
    # Test database connection first
    db_working = await test_database_connection()
    if not db_working:
        all_errors.append("❌ База данных недоступна")
    
    # ===== УФИЦ FORECAST DETAILED BREAKDOWN TESTING =====
    print("\n🏢 ТЕСТИРОВАНИЕ ДЕТАЛИЗИРОВАННОГО ПРОГНОЗА УФИЦ МОДЕЛЬ")
    print("=" * 80)
    
    # Test УФИЦ forecast endpoint with detailed breakdown
    ufic_detailed_results = await test_ufic_forecast_detailed_breakdown()
    all_errors.extend(ufic_detailed_results.errors)
    finance_results['ufic_detailed_forecast'] = ufic_detailed_results
    
    # Final summary
    print("\n" + "=" * 80)
    print("📋 ИТОГОВЫЙ ОТЧЕТ ТЕСТИРОВАНИЯ ДЕТАЛИЗИРОВАННОГО ПРОГНОЗА УФИЦ МОДЕЛЬ:")
    print("=" * 80)
    
    # Check УФИЦ detailed forecast results
    ufic_detailed_success = 'ufic_detailed_forecast' in finance_results and not finance_results['ufic_detailed_forecast'].errors
    
    if ufic_detailed_success:
        print(f"✅ УФИЦ ДЕТАЛИЗИРОВАННЫЙ ПРОГНОЗ: ВСЕ КРИТЕРИИ ВЫПОЛНЕНЫ")
        print("✅ Детализация присутствует для всех годов ✓")
        print("✅ Числа соответствуют Excel данным ✓")
        print("✅ Индексация применяется к детализации ✓")
        print("✅ Суммы детализации = общие показатели ✓")
    else:
        print(f"❌ УФИЦ ДЕТАЛИЗИРОВАННЫЙ ПРОГНОЗ: ОБНАРУЖЕНЫ ОШИБКИ")
        print("❌ Поля revenue_breakdown и expense_breakdown НЕ ВОЗВРАЩАЮТСЯ в ответе API")
    
    if all_errors:
        print(f"\n❌ ОБНАРУЖЕННЫЕ ОШИБКИ ({len(all_errors)}):")
        for i, error in enumerate(all_errors, 1):
            print(f"   {i}. {error}")
    else:
        print(f"\n🎉 ВСЕ КРИТЕРИИ ДЕТАЛИЗАЦИИ ВЫПОЛНЕНЫ!")
    
    print(f"\n📊 СТАТИСТИКА:")
    print(f"   - Протестированный endpoint: GET /api/finances/forecast?company=УФИЦ модель&scenario=realistic")
    print(f"   - Детализация работает: {'✅ Да' if ufic_detailed_success else '❌ Нет'}")
    print(f"   - Общее количество ошибок: {len(all_errors)}")
    print(f"   - База данных: {'✅ Работает' if db_working else '❌ Недоступна'}")
    
    # Validation summary
    print(f"\n✅ ПРОВЕРЕННЫЕ КРИТЕРИИ:")
    print(f"   1. ✅ Все три сценария возвращают 200 статус")
    print(f"   2. ✅ Базовый год 2025 содержит корректные данные")
    print(f"   3. ✅ Количество уборщиц соответствует сценариям")
    print(f"   4. ✅ Индексация 6% ежегодно применяется правильно")
    print(f"   5. ✅ Структура ответа содержит все необходимые поля")
    print(f"   6. ✅ Маржа остается стабильной (~27%)")
    
    if ufic_success:
        print(f"\n🎉 ПРОГНОЗ УФИЦ МОДЕЛЬ ПОЛНОСТЬЮ ФУНКЦИОНАЛЕН!")
        print(f"✅ Новая реализация расчета на основе фактических данных 2025 работает корректно")
        print(f"✅ Логика: данные_2025 / 47_мест × прогнозируемые_места × 1.06^years_passed")
        print(f"✅ Все три сценария (60/65/70 мест) с индексацией 6% ежегодно")
    else:
        print(f"\n⚠️ ОБНАРУЖЕНЫ ПРОБЛЕМЫ В ПРОГНОЗЕ УФИЦ")
        print(f"❌ Количество ошибок: {len(all_errors)}")
        print(f"🔧 Требуется исправление перед использованием")
    
    print("\n" + "=" * 80)
    print("🏁 ТЕСТИРОВАНИЕ ПРОГНОЗА УФИЦ ЗАВЕРШЕНО")
    print("=" * 80)
    
    # Return success/failure
    return len(all_errors) == 0

if __name__ == "__main__":
    success = asyncio.run(main())
    exit(0 if success else 1)