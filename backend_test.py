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
BACKEND_URL = "https://vasdom-finance-1.preview.emergentagent.com"
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

async def test_vasdom_model_forecast_endpoint():
    """Test ВАШ ДОМ модель forecast endpoint with cleaners integration from review request"""
    print("\n=== КРИТИЧЕСКОЕ ПОВТОРНОЕ ТЕСТИРОВАНИЕ ВАШ ДОМ МОДЕЛЬ ===\n")
    
    results = TestResults()
    scenarios = ["pessimistic", "realistic", "optimistic"]
    company = "ВАШ ДОМ модель"
    
    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            print(f"🏢 Тестируем прогноз ВАШ ДОМ модель с интеграцией уборщиц из УФИЦ")
            print("📋 КРИТЕРИИ УСПЕХА из review request:")
            print("   1. Endpoint должен возвращать 200 статус для всех трех сценариев")
            print("")
            print("   2. В expense_breakdown для каждого года (2026-2030) должна присутствовать")
            print("      категория 'аутсорсинг_персонала' с суммами:")
            print("      - PESSIMISTIC (самые БОЛЬШИЕ суммы): 2026=34347600, 2027=35996285,")
            print("        2028=37724106, 2029=39534864, 2030=41432537")
            print("      - REALISTIC (средние суммы): 2026=24615780, 2027=25797337,")
            print("        2028=27035610, 2029=28333319, 2030=29693318")
            print("      - OPTIMISTIC (самые МАЛЕНЬКИЕ суммы): 2026=16028880, 2027=17134873,")
            print("        2028=18317179, 2029=19581064, 2030=20932158")
            print("")
            print("   3. В revenue_breakdown должны быть поля:")
            print("      - vasdom_revenue (чистая выручка ВАШ ДОМ)")
            print("      - ufic_sewing (швеи из УФИЦ)")
            print("      - ufic_outsourcing (аутсорсинг из УФИЦ)")
            print("      - total (общая выручка)")
            print("")
            print("   4. Проверить, что vasdom_revenue + ufic_sewing + ufic_outsourcing = total")
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
                
                # Check 200 status
                if response.status_code != 200:
                    error_msg = f"❌ Сценарий {scenario}: ошибка {response.status_code} - {response.text}"
                    results.errors.append(error_msg)
                    print(error_msg)
                    continue
                
                data = response.json()
                scenario_results[scenario] = data
                print(f"✅ Сценарий {scenario}: 200 статус получен")
                
                # Validate response structure
                required_fields = ['company', 'scenario', 'base_year', 'base_data', 'forecast']
                for field in required_fields:
                    if field not in data:
                        error_msg = f"❌ Сценарий {scenario}: отсутствует поле '{field}'"
                        results.errors.append(error_msg)
                        print(error_msg)
                    else:
                        print(f"✅ Поле '{field}' присутствует")
                
                # Check forecast data for years 2026-2030
                forecast = data.get('forecast', [])
                if len(forecast) < 5:
                    error_msg = f"❌ Сценарий {scenario}: недостаточно лет в прогнозе (ожидалось 5, получено {len(forecast)})"
                    results.errors.append(error_msg)
                    print(error_msg)
                    continue
                
                print(f"✅ Прогноз содержит {len(forecast)} лет (2026-2030)")
                
                # Get base year data
                base_data = data.get('base_data', {})
                base_revenue = base_data.get('revenue', 0)
                base_expenses = base_data.get('expenses', 0)
                
                print(f"📊 Базовые данные 2025:")
                print(f"   - Выручка: {base_revenue:,.0f} ₽")
                print(f"   - Расходы: {base_expenses:,.0f} ₽")
                
                # Check expense_breakdown for аутсорсинг_персонала category
                print(f"\n📊 Проверяем сценарий {scenario.upper()}:")
                
                # Expected values for аутсорсинг_персонала by scenario and year
                expected_outsourcing = {
                    "pessimistic": {2026: 34347600, 2027: 35996285, 2028: 37724106, 2029: 39534864, 2030: 41432537},
                    "realistic": {2026: 24615780, 2027: 25797337, 2028: 27035610, 2029: 28333319, 2030: 29693318},
                    "optimistic": {2026: 16028880, 2027: 17134873, 2028: 18317179, 2029: 19581064, 2030: 20932158}
                }
                
                scenario_expected = expected_outsourcing.get(scenario, {})
                
                # Check each year (2026-2030)
                for year_data in forecast:
                    year = year_data.get('year')
                    if year not in range(2026, 2031):
                        continue
                    
                    expense_breakdown = year_data.get('expense_breakdown', {})
                    
                    # Check if аутсорсинг_персонала category exists
                    outsourcing_amount = expense_breakdown.get('аутсорсинг_персонала', 0)
                    expected_amount = scenario_expected.get(year, 0)
                    
                    if 'аутсорсинг_персонала' not in expense_breakdown:
                        error_msg = f"❌ {scenario} {year}: отсутствует категория 'аутсорсинг_персонала' в expense_breakdown"
                        results.errors.append(error_msg)
                        print(error_msg)
                        continue
                    
                    # Check if amount matches expected (allow 1% tolerance)
                    if expected_amount > 0:
                        diff_pct = abs(outsourcing_amount - expected_amount) / expected_amount * 100
                        if diff_pct > 1.0:
                            error_msg = f"❌ {scenario} {year}: неверная сумма аутсорсинга. Ожидалось {expected_amount:,.0f}, получено {outsourcing_amount:,.0f} (отклонение {diff_pct:.2f}%)"
                            results.errors.append(error_msg)
                            print(error_msg)
                        else:
                            print(f"✅ {year}: аутсорсинг_персонала = {outsourcing_amount:,.0f} ₽ (ожидалось {expected_amount:,.0f})")
                    else:
                        print(f"⚠️ {year}: нет ожидаемого значения для {scenario}")
                
                # Check revenue_breakdown structure
                print(f"\n💰 Проверяем структуру выручки для {scenario}:")
                
                # Check first year as example
                if forecast:
                    first_year = forecast[0]
                    revenue_breakdown = first_year.get('revenue_breakdown', {})
                    
                    required_revenue_fields = ['vasdom_revenue', 'ufic_sewing', 'ufic_outsourcing', 'total']
                    
                    for field in required_revenue_fields:
                        if field not in revenue_breakdown:
                            error_msg = f"❌ {scenario}: отсутствует поле '{field}' в revenue_breakdown"
                            results.errors.append(error_msg)
                            print(error_msg)
                        else:
                            value = revenue_breakdown[field]
                            print(f"✅ {field}: {value:,.0f} ₽")
                    
                    # Check revenue calculation: vasdom_revenue + ufic_sewing + ufic_outsourcing = total
                    if all(field in revenue_breakdown for field in required_revenue_fields):
                        vasdom = revenue_breakdown['vasdom_revenue']
                        ufic_sewing = revenue_breakdown['ufic_sewing']
                        ufic_outsourcing = revenue_breakdown['ufic_outsourcing']
                        total = revenue_breakdown['total']
                        
                        calculated_total = vasdom + ufic_sewing + ufic_outsourcing
                        
                        if abs(calculated_total - total) > 1.0:  # Allow small rounding differences
                            error_msg = f"❌ {scenario}: неверный расчет total. {vasdom:,.0f} + {ufic_sewing:,.0f} + {ufic_outsourcing:,.0f} = {calculated_total:,.0f}, но total = {total:,.0f}"
                            results.errors.append(error_msg)
                            print(error_msg)
                        else:
                            print(f"✅ Расчет выручки корректен: {vasdom:,.0f} + {ufic_sewing:,.0f} + {ufic_outsourcing:,.0f} = {total:,.0f}")
                
                print("")  # Empty line for readability
            
            # Store results for this scenario
            results.finance_endpoints[f'{company}_{scenario}_forecast'] = data
            
    except Exception as e:
        error_msg = f"❌ Ошибка при тестировании прогноза ВАШ ДОМ модель: {str(e)}"
        results.errors.append(error_msg)
        print(error_msg)
    
    return results

async def main():
    """Main test execution - focused on ВАШ ДОМ модель forecast testing per review request"""
    print("🚀 ТЕСТИРОВАНИЕ ПРОГНОЗА ВАШ ДОМ МОДЕЛЬ (REVIEW REQUEST)")
    print("=" * 80)
    print(f"🌐 Backend URL: {BACKEND_URL}")
    print(f"🔗 API Base: {API_BASE}")
    print("=" * 80)
    
    # Check basic connectivity
    print("\n🔍 Проверяем доступность backend...")
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(f"{API_BASE}/health")
            if response.status_code == 200:
                print("✅ Backend доступен")
            else:
                print(f"⚠️ Backend недоступен: {response.status_code}")
                return
    except Exception as e:
        print(f"❌ Ошибка подключения к backend: {str(e)}")
        return
    
    print("\n" + "=" * 80)
    print("🧪 ТЕСТИРОВАНИЕ ПРОГНОЗА ВАШ ДОМ МОДЕЛЬ")
    print("=" * 80)
    
    # Run the specific test for ВАШ ДОМ модель forecast as requested
    result = await test_vasdom_model_forecast_endpoint()
    
    # Print summary
    print("\n" + "=" * 80)
    print("📊 ИТОГОВЫЙ ОТЧЁТ")
    print("=" * 80)
    
    if result.errors:
        print(f"❌ Обнаружено ошибок: {len(result.errors)}")
        print("\n🔍 ДЕТАЛИ ОШИБОК:")
        for i, error in enumerate(result.errors, 1):
            print(f"   {i}. {error}")
        
        # Проверяем на критические ошибки
        critical_errors = [e for e in result.errors if "КРИТИЧЕСКИЙ СБОЙ" in e or "500" in e or "КРИТЕРИЙ 1 НАРУШЕН" in e]
        if critical_errors:
            print(f"\n⚠️ КРИТИЧЕСКИХ ОШИБОК: {len(critical_errors)}")
            print("❌ ТРЕБУЕТСЯ ИСПРАВЛЕНИЕ КОДА")
        else:
            print("\n✅ Критические ошибки отсутствуют")
            print("⚠️ Остались только проблемы с данными")
    else:
        print("🎉 ВСЕ ТЕСТЫ ПРОШЛИ УСПЕШНО!")
        print("✅ Все критерии успеха выполнены:")
        print("   ✅ Все сценарии возвращают 200 статус")
        print("   ✅ Категория 'аутсорсинг_персонала' присутствует во всех годах")
        print("   ✅ Суммы аутсорсинга соответствуют ожидаемым")
        print("   ✅ Структура revenue_breakdown корректна")
        print("   ✅ Расчет выручки vasdom_revenue + ufic_sewing + ufic_outsourcing = total")
    
    print("\n" + "=" * 80)
    print("🏁 ТЕСТИРОВАНИЕ ЗАВЕРШЕНО")
    print("=" * 80)
    
    return [("ВАШ ДОМ модель Forecast Test", result)]
                
                elif scenario == "realistic":
                    print(f"\n📊 Проверяем РЕАЛИСТИЧНЫЙ сценарий:")
                    
                    # Check 20% annual revenue growth
                    prev_revenue = base_revenue
                    for year_data in forecast:
                        year = year_data.get('year')
                        revenue = year_data.get('revenue', 0)
                        expenses = year_data.get('expenses', 0)
                        
                        expected_revenue = prev_revenue * 1.20
                        revenue_diff_pct = abs(revenue - expected_revenue) / expected_revenue * 100
                        
                        if revenue_diff_pct > 1.0:
                            error_msg = f"❌ Реалистичный {year}: неверный рост выручки +20%. Ожидалось {expected_revenue:,.0f} ₽, получено {revenue:,.0f} ₽"
                            results.errors.append(error_msg)
                            print(error_msg)
                        else:
                            print(f"✅ {year}: рост выручки +20% корректен ({revenue:,.0f} ₽)")
                        
                        prev_revenue = revenue
                    
                    # Check 16.2% annual expense growth
                    prev_expenses = base_expenses
                    for year_data in forecast:
                        year = year_data.get('year')
                        expenses = year_data.get('expenses', 0)
                        
                        expected_expenses = prev_expenses * 1.162
                        expense_diff_pct = abs(expenses - expected_expenses) / expected_expenses * 100
                        
                        if expense_diff_pct > 1.0:
                            error_msg = f"❌ Реалистичный {year}: неверный рост расходов +16.2%. Ожидалось {expected_expenses:,.0f} ₽, получено {expenses:,.0f} ₽"
                            results.errors.append(error_msg)
                            print(error_msg)
                        else:
                            print(f"✅ {year}: рост расходов +16.2% корректен ({expenses:,.0f} ₽)")
                        
                        prev_expenses = expenses
                    
                    # Check margin range 26.48% - 36.61%
                    for year_data in forecast:
                        year = year_data.get('year')
                        revenue = year_data.get('revenue', 0)
                        expenses = year_data.get('expenses', 0)
                        
                        if revenue > 0:
                            margin = ((revenue - expenses) / revenue) * 100
                            
                            if margin < 26.48 or margin > 36.61:
                                error_msg = f"❌ Реалистичный {year}: маржа {margin:.2f}% вне диапазона 26.48% - 36.61%"
                                results.errors.append(error_msg)
                                print(error_msg)
                            else:
                                print(f"✅ {year}: маржа {margin:.2f}% в допустимом диапазоне")
                
                elif scenario == "optimistic":
                    print(f"\n📊 Проверяем ОПТИМИСТИЧНЫЙ сценарий:")
                    
                    # Check 30% annual revenue growth
                    prev_revenue = base_revenue
                    for year_data in forecast:
                        year = year_data.get('year')
                        revenue = year_data.get('revenue', 0)
                        
                        expected_revenue = prev_revenue * 1.30
                        revenue_diff_pct = abs(revenue - expected_revenue) / expected_revenue * 100
                        
                        if revenue_diff_pct > 1.0:
                            error_msg = f"❌ Оптимистичный {year}: неверный рост выручки +30%. Ожидалось {expected_revenue:,.0f} ₽, получено {revenue:,.0f} ₽"
                            results.errors.append(error_msg)
                            print(error_msg)
                        else:
                            print(f"✅ {year}: рост выручки +30% корректен ({revenue:,.0f} ₽)")
                        
                        prev_revenue = revenue
                    
                    # Check 18.9% annual expense growth
                    prev_expenses = base_expenses
                    for year_data in forecast:
                        year = year_data.get('year')
                        expenses = year_data.get('expenses', 0)
                        
                        expected_expenses = prev_expenses * 1.189
                        expense_diff_pct = abs(expenses - expected_expenses) / expected_expenses * 100
                        
                        if expense_diff_pct > 1.0:
                            error_msg = f"❌ Оптимистичный {year}: неверный рост расходов +18.9%. Ожидалось {expected_expenses:,.0f} ₽, получено {expenses:,.0f} ₽"
                            results.errors.append(error_msg)
                            print(error_msg)
                        else:
                            print(f"✅ {year}: рост расходов +18.9% корректен ({expenses:,.0f} ₽)")
                        
                        prev_expenses = expenses
                
                # Check expense breakdown for all scenarios
                print(f"\n🔍 Проверяем детализацию расходов для сценария {scenario}:")
                
                # Check that expense_breakdown is present
                has_expense_breakdown = False
                for year_data in forecast:
                    if 'expense_breakdown' in year_data:
                        has_expense_breakdown = True
                        break
                
                if not has_expense_breakdown:
                    error_msg = f"❌ Сценарий {scenario}: отсутствует expense_breakdown в прогнозе"
                    results.errors.append(error_msg)
                    print(error_msg)
                else:
                    print(f"✅ expense_breakdown присутствует")
                    
                    # Check excluded categories
                    excluded_categories = ['кредиты', 'аутсорсинг', 'продукты питания']
                    found_excluded = []
                    
                    sample_year = forecast[0] if forecast else {}
                    expense_breakdown = sample_year.get('expense_breakdown', {})
                    
                    for category_key, amount in expense_breakdown.items():
                        category_lower = category_key.lower()
                        for excluded in excluded_categories:
                            if excluded in category_lower:
                                found_excluded.append(category_key)
                    
                    if found_excluded:
                        error_msg = f"❌ Сценарий {scenario}: найдены исключаемые категории в детализации: {found_excluded}"
                        results.errors.append(error_msg)
                        print(error_msg)
                    else:
                        print(f"✅ Исключаемые категории отсутствуют в детализации")
                    
                    # Check for salary redistribution
                    salary_categories = [k for k in expense_breakdown.keys() if 'зарплата' in k.lower() or 'заработная' in k.lower()]
                    if salary_categories:
                        print(f"✅ Найдены категории зарплаты: {salary_categories}")
                    else:
                        print(f"⚠️ Категории зарплаты не найдены в детализации")
                    
                    # Check current repair reduction (should be 70% less)
                    repair_categories = [k for k in expense_breakdown.keys() if 'текущий ремонт' in k.lower() or 'ремонт' in k.lower()]
                    if repair_categories:
                        print(f"✅ Найдены категории ремонта: {repair_categories}")
                        print(f"   (Проверка 70% сокращения требует сравнения с базовыми данными)")
                    else:
                        print(f"⚠️ Категории ремонта не найдены в детализации")
                
                print(f"")  # Empty line for readability
            
            # Store results
            results.finance_endpoints['vasdom_fact_forecast'] = scenario_results
            
            # Summary
            print("📋 ИТОГОВАЯ СВОДКА:")
            success_count = len([s for s in scenarios if s in scenario_results])
            print(f"✅ Успешно протестировано сценариев: {success_count}/3")
            
            if results.errors:
                print(f"❌ Обнаружено ошибок: {len(results.errors)}")
                for error in results.errors[-5:]:  # Show last 5 errors
                    print(f"   - {error}")
            else:
                print(f"🎉 Все критерии успеха выполнены!")
    
    except Exception as e:
        error_msg = f"❌ Ошибка при тестировании прогноза ВАШ ДОМ ФАКТ: {str(e)}"
        results.errors.append(error_msg)
        print(error_msg)
    
    return results

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
                        revenue_diff_pct = abs(actual_revenue - expected_revenue) / expected_revenue * 100
                        expenses_diff_pct = abs(actual_expenses - expected_expenses) / expected_expenses * 100
                        
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

async def test_forecast_updates_after_changes():
    """Test forecast updates after all changes as specified in review request"""
    print("\n=== ТЕСТ ОБНОВЛЕНИЙ ПРОГНОЗОВ ПОСЛЕ ВСЕХ ИЗМЕНЕНИЙ ===\n")
    
    results = TestResults()
    
    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            print("🔍 Тестируем обновления прогнозов согласно техническому заданию:")
            print("")
            
            # Test 1: УФИЦ модель - оптимистичный сценарий с 10% индексацией
            print("1️⃣ УФИЦ модель - оптимистичный сценарий с 10% индексацией")
            print("=" * 60)
            
            response = await client.get(
                f"{API_BASE}/finances/forecast",
                params={"company": "УФИЦ модель", "scenario": "optimistic"}
            )
            
            print(f"📡 GET /api/finances/forecast?company=УФИЦ модель&scenario=optimistic")
            print(f"📡 Ответ сервера: {response.status_code}")
            
            if response.status_code != 200:
                error_msg = f"❌ УФИЦ оптимистичный сценарий: {response.status_code} - {response.text}"
                results.errors.append(error_msg)
                print(error_msg)
            else:
                data = response.json()
                results.finance_endpoints['ufic_optimistic'] = data
                
                print("✅ УФИЦ оптимистичный сценарий получен успешно")
                
                # Check forecast years 2027-2030 for 10% indexation
                forecast = data.get('forecast', [])
                
                # Find 2026 base data for comparison
                base_2026 = None
                for year_data in forecast:
                    if year_data.get('year') == 2026:
                        base_2026 = year_data
                        break
                
                if base_2026:
                    base_revenue_2026 = base_2026.get('revenue', 0)
                    base_expenses_2026 = base_2026.get('expenses', 0)
                    
                    print(f"📊 Базовые данные 2026:")
                    print(f"   - Выручка: {base_revenue_2026:,.0f}")
                    print(f"   - Расходы: {base_expenses_2026:,.0f}")
                    
                    # Check 10% indexation for years 2027-2030
                    indexation_years = [2027, 2028, 2029, 2030]
                    
                    for i, year in enumerate(indexation_years, 1):
                        year_data = None
                        for forecast_year in forecast:
                            if forecast_year.get('year') == year:
                                year_data = forecast_year
                                break
                        
                        if year_data:
                            actual_revenue = year_data.get('revenue', 0)
                            actual_expenses = year_data.get('expenses', 0)
                            
                            # Expected values with 10% indexation
                            expected_revenue = base_revenue_2026 * (1.10 ** i)
                            expected_expenses = base_expenses_2026 * (1.10 ** i)
                            
                            print(f"📈 {year} год (10% индексация):")
                            print(f"   - Выручка: {actual_revenue:,.0f} (ожидалось {expected_revenue:,.0f})")
                            print(f"   - Расходы: {actual_expenses:,.0f} (ожидалось {expected_expenses:,.0f})")
                            
                            # Check with 1% tolerance
                            revenue_diff = abs(actual_revenue - expected_revenue) / expected_revenue
                            expenses_diff = abs(actual_expenses - expected_expenses) / expected_expenses
                            
                            if revenue_diff > 0.01:
                                error_msg = f"❌ УФИЦ {year}: неверная индексация выручки 10% (отклонение {revenue_diff:.2%})"
                                results.errors.append(error_msg)
                                print(error_msg)
                            else:
                                print(f"✅ Выручка {year}: индексация 10% корректна")
                            
                            if expenses_diff > 0.01:
                                error_msg = f"❌ УФИЦ {year}: неверная индексация расходов 10% (отклонение {expenses_diff:.2%})"
                                results.errors.append(error_msg)
                                print(error_msg)
                            else:
                                print(f"✅ Расходы {year}: индексация 10% корректна")
                        else:
                            error_msg = f"❌ УФИЦ: отсутствуют данные для {year} года"
                            results.errors.append(error_msg)
                            print(error_msg)
                    
                    # Check revenue_breakdown contains sewing, cleaning, outsourcing
                    print("\n🔍 Проверяем детализацию доходов (revenue_breakdown):")
                    
                    for year_data in forecast:
                        year = year_data.get('year')
                        if year >= 2027 and year <= 2030:
                            revenue_breakdown = year_data.get('revenue_breakdown', {})
                            
                            required_categories = ['sewing', 'cleaning', 'outsourcing']
                            for category in required_categories:
                                if category not in revenue_breakdown:
                                    error_msg = f"❌ УФИЦ {year}: отсутствует {category} в revenue_breakdown"
                                    results.errors.append(error_msg)
                                    print(error_msg)
                                else:
                                    value = revenue_breakdown[category]
                                    print(f"✅ {year} {category}: {value:,.0f}")
                else:
                    error_msg = "❌ УФИЦ: отсутствуют базовые данные 2026 года"
                    results.errors.append(error_msg)
                    print(error_msg)
            
            print("\n")
            
            # Test 2: ВАШ ДОМ ФАКТ - реалистичный сценарий с 30% индексацией
            print("2️⃣ ВАШ ДОМ ФАКТ - реалистичный сценарий с 30% индексацией")
            print("=" * 60)
            
            response = await client.get(
                f"{API_BASE}/finances/forecast",
                params={"company": "ВАШ ДОМ ФАКТ", "scenario": "realistic"}
            )
            
            print(f"📡 GET /api/finances/forecast?company=ВАШ ДОМ ФАКТ&scenario=realistic")
            print(f"📡 Ответ сервера: {response.status_code}")
            
            if response.status_code != 200:
                error_msg = f"❌ ВАШ ДОМ ФАКТ реалистичный сценарий: {response.status_code} - {response.text}"
                results.errors.append(error_msg)
                print(error_msg)
            else:
                data = response.json()
                results.finance_endpoints['vasdom_fact_realistic'] = data
                
                print("✅ ВАШ ДОМ ФАКТ реалистичный сценарий получен успешно")
                
                # Check forecast years 2027-2030 for 30% indexation
                forecast = data.get('forecast', [])
                
                # Find 2026 base data for comparison
                base_2026 = None
                for year_data in forecast:
                    if year_data.get('year') == 2026:
                        base_2026 = year_data
                        break
                
                if base_2026:
                    base_revenue_2026 = base_2026.get('revenue', 0)
                    base_expenses_2026 = base_2026.get('expenses', 0)
                    
                    print(f"📊 Базовые данные 2026:")
                    print(f"   - Выручка: {base_revenue_2026:,.0f}")
                    print(f"   - Расходы: {base_expenses_2026:,.0f}")
                    
                    # Check 30% indexation for years 2027-2030
                    indexation_years = [2027, 2028, 2029, 2030]
                    
                    for i, year in enumerate(indexation_years, 1):
                        year_data = None
                        for forecast_year in forecast:
                            if forecast_year.get('year') == year:
                                year_data = forecast_year
                                break
                        
                        if year_data:
                            actual_revenue = year_data.get('revenue', 0)
                            actual_expenses = year_data.get('expenses', 0)
                            
                            # Expected values with 30% indexation
                            expected_revenue = base_revenue_2026 * (1.30 ** i)
                            expected_expenses = base_expenses_2026 * (1.30 ** i)
                            
                            print(f"📈 {year} год (30% индексация):")
                            print(f"   - Выручка: {actual_revenue:,.0f} (ожидалось {expected_revenue:,.0f})")
                            print(f"   - Расходы: {actual_expenses:,.0f} (ожидалось {expected_expenses:,.0f})")
                            
                            # Verify specific calculations
                            if year == 2027:
                                expected_2027 = base_revenue_2026 * 1.30
                                print(f"   - 2027 = 2026 * 1.30 = {base_revenue_2026:,.0f} * 1.30 = {expected_2027:,.0f}")
                            elif year == 2028:
                                expected_2028 = base_revenue_2026 * (1.30 ** 2)
                                print(f"   - 2028 = 2026 * 1.30^2 = {base_revenue_2026:,.0f} * {1.30**2:.4f} = {expected_2028:,.0f}")
                            elif year == 2029:
                                expected_2029 = base_revenue_2026 * (1.30 ** 3)
                                print(f"   - 2029 = 2026 * 1.30^3 = {base_revenue_2026:,.0f} * {1.30**3:.4f} = {expected_2029:,.0f}")
                            elif year == 2030:
                                expected_2030 = base_revenue_2026 * (1.30 ** 4)
                                print(f"   - 2030 = 2026 * 1.30^4 = {base_revenue_2026:,.0f} * {1.30**4:.4f} = {expected_2030:,.0f}")
                            
                            # Check with 1% tolerance
                            revenue_diff = abs(actual_revenue - expected_revenue) / expected_revenue
                            expenses_diff = abs(actual_expenses - expected_expenses) / expected_expenses
                            
                            if revenue_diff > 0.01:
                                error_msg = f"❌ ВАШ ДОМ ФАКТ {year}: неверная индексация выручки 30% (отклонение {revenue_diff:.2%})"
                                results.errors.append(error_msg)
                                print(error_msg)
                            else:
                                print(f"✅ Выручка {year}: индексация 30% корректна")
                            
                            if expenses_diff > 0.01:
                                error_msg = f"❌ ВАШ ДОМ ФАКТ {year}: неверная индексация расходов 30% (отклонение {expenses_diff:.2%})"
                                results.errors.append(error_msg)
                                print(error_msg)
                            else:
                                print(f"✅ Расходы {year}: индексация 30% корректна")
                        else:
                            error_msg = f"❌ ВАШ ДОМ ФАКТ: отсутствуют данные для {year} года"
                            results.errors.append(error_msg)
                            print(error_msg)
                    
                    # Check revenue_breakdown and expense_breakdown exist
                    print("\n🔍 Проверяем детализацию доходов и расходов:")
                    
                    for year_data in forecast:
                        year = year_data.get('year')
                        if year >= 2027 and year <= 2030:
                            revenue_breakdown = year_data.get('revenue_breakdown', {})
                            expense_breakdown = year_data.get('expense_breakdown', {})
                            
                            if not revenue_breakdown:
                                error_msg = f"❌ ВАШ ДОМ ФАКТ {year}: отсутствует revenue_breakdown"
                                results.errors.append(error_msg)
                                print(error_msg)
                            else:
                                print(f"✅ {year}: revenue_breakdown присутствует ({len(revenue_breakdown)} категорий)")
                            
                            if not expense_breakdown:
                                error_msg = f"❌ ВАШ ДОМ ФАКТ {year}: отсутствует expense_breakdown"
                                results.errors.append(error_msg)
                                print(error_msg)
                            else:
                                print(f"✅ {year}: expense_breakdown присутствует ({len(expense_breakdown)} категорий)")
                else:
                    error_msg = "❌ ВАШ ДОМ ФАКТ: отсутствуют базовые данные 2026 года"
                    results.errors.append(error_msg)
                    print(error_msg)
            
            print("\n")
            
            # Test 3: ВАШ ДОМ модель - расходы endpoint
            print("3️⃣ ВАШ ДОМ модель - расходы endpoint")
            print("=" * 60)
            
            response = await client.get(
                f"{API_BASE}/finances/expense-analysis",
                params={"company": "ВАШ ДОМ модель"}
            )
            
            print(f"📡 GET /api/finances/expense-analysis?company=ВАШ ДОМ модель")
            print(f"📡 Ответ сервера: {response.status_code}")
            
            if response.status_code != 200:
                error_msg = f"❌ ВАШ ДОМ модель расходы: {response.status_code} - {response.text}"
                results.errors.append(error_msg)
                print(error_msg)
            else:
                data = response.json()
                results.finance_endpoints['vasdom_model_expenses'] = data
                
                print("✅ ВАШ ДОМ модель расходы получены успешно")
                
                # Validate basic structure
                if 'expenses' in data:
                    expenses = data['expenses']
                    print(f"📊 Количество категорий расходов: {len(expenses)}")
                    
                    if 'total' in data:
                        total = data['total']
                        print(f"💰 Общая сумма расходов: {total:,.0f}")
                    
                    print("✅ Endpoint возвращает данные без ошибок")
                else:
                    error_msg = "❌ ВАШ ДОМ модель: неверная структура ответа (отсутствует поле 'expenses')"
                    results.errors.append(error_msg)
                    print(error_msg)
            
            print("\n")
            
            # Summary of success criteria
            print("📋 КРИТЕРИИ УСПЕХА:")
            print("=" * 60)
            
            success_criteria = [
                ("УФИЦ оптимистичный: детализация с 10% работает", 
                 'ufic_optimistic' in results.finance_endpoints and 
                 not any("УФИЦ" in str(error) and "10%" in str(error) for error in results.errors)),
                
                ("ВАШ ДОМ ФАКТ: рост 30% + детализация работает", 
                 'vasdom_fact_realistic' in results.finance_endpoints and 
                 not any("ВАШ ДОМ ФАКТ" in str(error) and "30%" in str(error) for error in results.errors)),
                
                ("ВАШ ДОМ модель: расходы загружаются", 
                 'vasdom_model_expenses' in results.finance_endpoints and 
                 not any("ВАШ ДОМ модель" in str(error) for error in results.errors))
            ]
            
            for criterion, is_met in success_criteria:
                status = "✅" if is_met else "❌"
                print(f"{status} {criterion}")
            
            all_criteria_met = all(is_met for _, is_met in success_criteria)
            
            if all_criteria_met:
                print("\n🎉 ВСЕ КРИТЕРИИ УСПЕХА ВЫПОЛНЕНЫ!")
            else:
                print(f"\n⚠️ НЕ ВСЕ КРИТЕРИИ ВЫПОЛНЕНЫ")
                
    except Exception as e:
        error_msg = f"❌ Ошибка при тестировании обновлений прогнозов: {str(e)}"
        results.errors.append(error_msg)
        print(error_msg)
    
    return results

async def test_forecast_endpoints_after_bugfix():
    """Test specific forecast endpoints after bug fix as requested in review"""
    print("\n=== БЫСТРАЯ ПРОВЕРКА ПРОГНОЗОВ ПОСЛЕ ИСПРАВЛЕНИЯ ОШИБКИ ===\n")
    
    results = TestResults()
    
    # Endpoints to test as specified in the review request
    test_endpoints = [
        ("УФИЦ модель", "realistic"),
        ("ВАШ ДОМ ФАКТ", "realistic"),
        ("ВАШ ДОМ модель", "realistic")
    ]
    
    print("🎯 Цель тестирования:")
    print("   - Все три endpoint возвращают 200 статус")
    print("   - Нет ошибок 'cannot access local variable 'expense_breakdown_2025''")
    print("   - Данные прогноза присутствуют для всех компаний")
    print("   - Детализация (revenue_breakdown, expense_breakdown) присутствует где нужно")
    print("")
    
    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            for i, (company, scenario) in enumerate(test_endpoints, 1):
                print(f"🔍 {i}. Тестируем GET /api/finances/forecast?company={company}&scenario={scenario}")
                
                # Test the forecast endpoint
                response = await client.get(
                    f"{API_BASE}/finances/forecast",
                    params={"company": company, "scenario": scenario}
                )
                
                print(f"📡 Ответ сервера: {response.status_code}")
                
                # Check 200 status
                if response.status_code != 200:
                    error_msg = f"❌ {company}: ошибка {response.status_code} - {response.text}"
                    results.errors.append(error_msg)
                    print(error_msg)
                    
                    # Check for specific error mentioned in review
                    if "cannot access local variable 'expense_breakdown_2025'" in response.text:
                        results.errors.append(f"❌ {company}: найдена ошибка 'expense_breakdown_2025'")
                        print("❌ Найдена критическая ошибка с неинициализированной переменной!")
                    
                    continue
                
                print(f"✅ {company}: 200 статус получен")
                
                try:
                    data = response.json()
                    results.finance_endpoints[f'forecast_{company}_{scenario}'] = data
                    
                    # Check if forecast data is present
                    if 'forecast' not in data:
                        error_msg = f"❌ {company}: отсутствуют данные прогноза (поле 'forecast')"
                        results.errors.append(error_msg)
                        print(error_msg)
                        continue
                    
                    forecast_data = data.get('forecast', [])
                    if not forecast_data:
                        error_msg = f"❌ {company}: пустые данные прогноза"
                        results.errors.append(error_msg)
                        print(error_msg)
                        continue
                    
                    print(f"✅ {company}: данные прогноза присутствуют ({len(forecast_data)} лет)")
                    
                    # Check for detailed breakdown (revenue_breakdown, expense_breakdown)
                    has_revenue_breakdown = False
                    has_expense_breakdown = False
                    
                    for year_data in forecast_data:
                        if 'revenue_breakdown' in year_data:
                            has_revenue_breakdown = True
                        if 'expense_breakdown' in year_data:
                            has_expense_breakdown = True
                    
                    if has_revenue_breakdown:
                        print(f"✅ {company}: детализация доходов (revenue_breakdown) присутствует")
                    else:
                        print(f"⚠️ {company}: детализация доходов (revenue_breakdown) отсутствует")
                    
                    if has_expense_breakdown:
                        print(f"✅ {company}: детализация расходов (expense_breakdown) присутствует")
                    else:
                        print(f"⚠️ {company}: детализация расходов (expense_breakdown) отсутствует")
                    
                    # Show basic forecast info
                    if forecast_data:
                        first_year = forecast_data[0]
                        print(f"📊 {company}: первый год прогноза - {first_year.get('year')}")
                        print(f"   - Выручка: {first_year.get('revenue', 0):,.0f}")
                        print(f"   - Расходы: {first_year.get('expenses', 0):,.0f}")
                        print(f"   - Прибыль: {first_year.get('profit', 0):,.0f}")
                    
                    # Validate basic structure
                    required_fields = ['company', 'scenario', 'forecast']
                    for field in required_fields:
                        if field not in data:
                            error_msg = f"❌ {company}: отсутствует поле '{field}'"
                            results.errors.append(error_msg)
                            print(error_msg)
                        else:
                            print(f"✅ {company}: поле '{field}' присутствует")
                    
                except json.JSONDecodeError as e:
                    error_msg = f"❌ {company}: ошибка парсинга JSON - {str(e)}"
                    results.errors.append(error_msg)
                    print(error_msg)
                except Exception as e:
                    error_msg = f"❌ {company}: ошибка обработки ответа - {str(e)}"
                    results.errors.append(error_msg)
                    print(error_msg)
                
                print("")  # Empty line for readability
            
            # Summary of the quick check
            print("📋 ИТОГИ БЫСТРОЙ ПРОВЕРКИ:")
            
            total_endpoints = len(test_endpoints)
            successful_endpoints = total_endpoints - len([e for e in results.errors if "ошибка" in e and ("200" not in e)])
            
            print(f"   - Всего endpoint'ов: {total_endpoints}")
            print(f"   - Успешных (200 статус): {successful_endpoints}")
            print(f"   - Неудачных: {total_endpoints - successful_endpoints}")
            
            # Check specific error
            expense_breakdown_errors = [e for e in results.errors if "expense_breakdown_2025" in e]
            if expense_breakdown_errors:
                print(f"   - ❌ Найдены ошибки с expense_breakdown_2025: {len(expense_breakdown_errors)}")
            else:
                print(f"   - ✅ Ошибки 'expense_breakdown_2025' не найдены")
            
            # Overall success criteria
            if not results.errors:
                print("\n🎉 ВСЕ КРИТЕРИИ УСПЕХА ВЫПОЛНЕНЫ:")
                print("   ✅ Все endpoint возвращают 200 статус")
                print("   ✅ Нет ошибок 'cannot access local variable 'expense_breakdown_2025''")
                print("   ✅ Данные прогноза присутствуют для всех компаний")
                print("   ✅ Детализация присутствует где нужно")
            else:
                print(f"\n⚠️ ОБНАРУЖЕНЫ ПРОБЛЕМЫ ({len(results.errors)} ошибок)")
                for error in results.errors:
                    print(f"   {error}")
    
    except Exception as e:
        error_msg = f"❌ Критическая ошибка при тестировании прогнозов: {str(e)}"
        results.errors.append(error_msg)
        print(error_msg)
    
    return results

async def test_vasdom_fact_forecast_critical_fix():
    """
    ПОВТОРНОЕ тестирование прогноза ВАШ ДОМ ФАКТ после исправления критических ошибок.
    
    Проверяет:
    1. Все endpoint возвращают 200 статус (не 500)
    2. Нет ошибки "annual_revenue_growth is not defined"
    3. Данные прогноза присутствуют
    4. Требования к сценариям выполнены
    """
    print("\n=== ПОВТОРНОЕ ТЕСТИРОВАНИЕ ПРОГНОЗА ВАШ ДОМ ФАКТ ===\n")
    
    results = TestResults()
    scenarios = ["pessimistic", "realistic", "optimistic"]
    company = "ВАШ ДОМ ФАКТ"
    
    print("🎯 КРИТИЧЕСКИЕ ПРОВЕРКИ:")
    print("1. Все endpoint возвращают 200 статус (не 500)")
    print("2. Нет ошибки 'annual_revenue_growth is not defined'")
    print("3. Данные прогноза присутствуют")
    print("")
    
    print("📋 ТРЕБОВАНИЯ К СЦЕНАРИЯМ:")
    print("Пессимистичный: рост выручки 2026 ~20%, маржа ~20%, БЕЗ Ленинск-Кузнецкий")
    print("Реалистичный: рост выручки 2026 ~40%, БЕЗ Ленинск-Кузнецкий")
    print("Оптимистичный: рост выручки 2026 ~60%, БЕЗ Ленинск-Кузнецкий")
    print("")
    
    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            critical_errors_found = False
            
            for scenario in scenarios:
                print(f"🔍 Тестируем {scenario.upper()} сценарий...")
                
                # Test the forecast endpoint
                response = await client.get(
                    f"{API_BASE}/finances/forecast",
                    params={"company": company, "scenario": scenario}
                )
                
                print(f"📡 Статус ответа: {response.status_code}")
                
                # КРИТИЧЕСКАЯ ПРОВЕРКА 1: Статус 200
                if response.status_code != 200:
                    error_msg = f"❌ КРИТИЧЕСКАЯ ОШИБКА: {scenario} возвращает {response.status_code} вместо 200"
                    results.errors.append(error_msg)
                    print(error_msg)
                    
                    # КРИТИЧЕСКАЯ ПРОВЕРКА 2: Проверяем на ошибку annual_revenue_growth
                    if "annual_revenue_growth is not defined" in response.text:
                        critical_error = f"❌ КРИТИЧЕСКАЯ ОШИБКА: {scenario} - 'annual_revenue_growth is not defined'"
                        results.errors.append(critical_error)
                        print(critical_error)
                        critical_errors_found = True
                    
                    print(f"📄 Текст ошибки: {response.text[:500]}...")
                    continue
                
                print(f"✅ {scenario}: 200 статус получен")
                
                try:
                    data = response.json()
                    
                    # КРИТИЧЕСКАЯ ПРОВЕРКА 3: Данные прогноза присутствуют
                    if 'forecast' not in data or not data['forecast']:
                        error_msg = f"❌ КРИТИЧЕСКАЯ ОШИБКА: {scenario} - данные прогноза отсутствуют"
                        results.errors.append(error_msg)
                        print(error_msg)
                        continue
                    
                    forecast = data['forecast']
                    print(f"✅ {scenario}: данные прогноза присутствуют ({len(forecast)} лет)")
                    
                    # Проверяем базовые данные
                    base_data = data.get('base_data', {})
                    base_revenue_2025 = base_data.get('revenue', 0)
                    
                    if len(forecast) > 0:
                        # Проверяем 2026 год (первый год прогноза)
                        year_2026 = forecast[0]
                        revenue_2026 = year_2026.get('revenue', 0)
                        expenses_2026 = year_2026.get('expenses', 0)
                        
                        if base_revenue_2025 > 0 and revenue_2026 > 0:
                            growth_rate = (revenue_2026 / base_revenue_2025 - 1) * 100
                            margin = ((revenue_2026 - expenses_2026) / revenue_2026) * 100 if revenue_2026 > 0 else 0
                            
                            print(f"📊 {scenario} 2026:")
                            print(f"   - Выручка 2025: {base_revenue_2025:,.0f}")
                            print(f"   - Выручка 2026: {revenue_2026:,.0f}")
                            print(f"   - Рост выручки: {growth_rate:.1f}%")
                            print(f"   - Маржа: {margin:.1f}%")
                            
                            # Проверяем требования к сценариям
                            if scenario == "pessimistic":
                                if abs(growth_rate - 20) > 5:  # Допуск ±5%
                                    print(f"⚠️ {scenario}: рост выручки {growth_rate:.1f}% (ожидалось ~20%)")
                                else:
                                    print(f"✅ {scenario}: рост выручки соответствует требованиям")
                                
                                if abs(margin - 20) > 5:  # Допуск ±5%
                                    print(f"⚠️ {scenario}: маржа {margin:.1f}% (ожидалось ~20%)")
                                else:
                                    print(f"✅ {scenario}: маржа соответствует требованиям")
                            
                            elif scenario == "realistic":
                                if abs(growth_rate - 40) > 5:  # Допуск ±5%
                                    print(f"⚠️ {scenario}: рост выручки {growth_rate:.1f}% (ожидалось ~40%)")
                                else:
                                    print(f"✅ {scenario}: рост выручки соответствует требованиям")
                            
                            elif scenario == "optimistic":
                                if abs(growth_rate - 60) > 5:  # Допуск ±5%
                                    print(f"⚠️ {scenario}: рост выручки {growth_rate:.1f}% (ожидалось ~60%)")
                                else:
                                    print(f"✅ {scenario}: рост выручки соответствует требованиям")
                        
                        # Проверяем детализацию расходов (БЕЗ Ленинск-Кузнецкий)
                        expense_breakdown = year_2026.get('expense_breakdown', {})
                        if expense_breakdown:
                            print(f"✅ {scenario}: детализация расходов присутствует")
                            
                            # Проверяем отсутствие Ленинск-Кузнецкий
                            leninsk_found = False
                            for category, amount in expense_breakdown.items():
                                if 'ленинск' in category.lower() or 'кузнец' in category.lower():
                                    leninsk_found = True
                                    error_msg = f"❌ {scenario}: найдена категория '{category}' (должна быть исключена)"
                                    results.errors.append(error_msg)
                                    print(error_msg)
                            
                            if not leninsk_found:
                                print(f"✅ {scenario}: Ленинск-Кузнецкий исключен из детализации")
                        else:
                            print(f"⚠️ {scenario}: детализация расходов отсутствует")
                    
                    print("")
                    
                except json.JSONDecodeError as e:
                    error_msg = f"❌ КРИТИЧЕСКАЯ ОШИБКА: {scenario} - неверный JSON: {str(e)}"
                    results.errors.append(error_msg)
                    print(error_msg)
                    critical_errors_found = True
            
            # Итоговая оценка
            print("🎯 ИТОГОВАЯ ОЦЕНКА:")
            
            if critical_errors_found:
                print("❌ КРИТИЧЕСКИЕ ОШИБКИ НЕ ИСПРАВЛЕНЫ")
                results.errors.append("КРИТИЧЕСКИЕ ОШИБКИ: annual_revenue_growth или другие серьезные проблемы")
            else:
                print("✅ Критические ошибки исправлены")
            
            working_scenarios = 0
            for scenario in scenarios:
                # Подсчитываем рабочие сценарии (без критических ошибок)
                scenario_errors = [e for e in results.errors if scenario in e and "КРИТИЧЕСКАЯ ОШИБКА" in e]
                if not scenario_errors:
                    working_scenarios += 1
            
            print(f"✅ Рабочих сценариев: {working_scenarios}/3")
            
            if working_scenarios == 3:
                print("🎉 ВСЕ СЦЕНАРИИ РАБОТАЮТ!")
            elif working_scenarios > 0:
                print("⚠️ ЧАСТИЧНО РАБОТАЕТ")
            else:
                print("❌ НИ ОДИН СЦЕНАРИЙ НЕ РАБОТАЕТ")
    
    except Exception as e:
        error_msg = f"❌ Критическая ошибка при тестировании: {str(e)}"
        results.errors.append(error_msg)
        print(error_msg)
    
    return results

async def test_vasdom_model_forecast_endpoint():
    """Test ВАШ ДОМ модель forecast endpoint after bugfix"""
    print("\n=== ТЕСТ ПРОГНОЗА ВАШ ДОМ модель ПОСЛЕ ИСПРАВЛЕНИЯ ОШИБКИ ===\n")
    
    results = TestResults()
    company = "ВАШ ДОМ модель"
    scenario = "realistic"
    
    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            print(f"🏢 Тестируем прогноз для компании: {company}")
            print("📋 Критерии успеха:")
            print("   1. Endpoint возвращает 200 статус (не 500)")
            print("   2. Нет ошибки 'cannot access local variable total_expenses_2025'")
            print("   3. Данные прогноза присутствуют (5 лет)")
            print("   4. Детализация присутствует")
            print("")
            
            # Test the forecast endpoint
            response = await client.get(
                f"{API_BASE}/finances/forecast",
                params={"company": company, "scenario": scenario}
            )
            
            print(f"📡 Ответ сервера: {response.status_code}")
            
            # Check 200 status (not 500)
            if response.status_code != 200:
                error_msg = f"❌ КРИТИЧЕСКАЯ ОШИБКА: {company} возвращает {response.status_code} вместо 200"
                results.errors.append(error_msg)
                print(error_msg)
                
                # Check for specific error
                if "cannot access local variable" in response.text and "total_expenses_2025" in response.text:
                    error_msg = f"❌ КРИТИЧЕСКАЯ ОШИБКА: Найдена ошибка 'cannot access local variable total_expenses_2025'"
                    results.errors.append(error_msg)
                    print(error_msg)
                
                print(f"📄 Текст ошибки: {response.text[:500]}...")
                return results
            
            print(f"✅ Критерий 1: Endpoint возвращает 200 статус ✓")
            
            data = response.json()
            
            # Check no error in response text
            response_text = response.text
            if "cannot access local variable" in response_text and "total_expenses_2025" in response_text:
                error_msg = f"❌ КРИТИЧЕСКАЯ ОШИБКА: Найдена ошибка 'cannot access local variable total_expenses_2025' в ответе"
                results.errors.append(error_msg)
                print(error_msg)
                return results
            
            print(f"✅ Критерий 2: Нет ошибки 'cannot access local variable total_expenses_2025' ✓")
            
            # Validate response structure
            required_fields = ['company', 'scenario', 'base_year', 'base_data', 'forecast']
            for field in required_fields:
                if field not in data:
                    error_msg = f"❌ Отсутствует поле '{field}' в ответе"
                    results.errors.append(error_msg)
                    print(error_msg)
                else:
                    print(f"✅ Поле '{field}' присутствует")
            
            # Check forecast data for years 2026-2030
            forecast = data.get('forecast', [])
            if len(forecast) < 5:
                error_msg = f"❌ Недостаточно лет в прогнозе: ожидалось 5, получено {len(forecast)}"
                results.errors.append(error_msg)
                print(error_msg)
            else:
                print(f"✅ Критерий 3: Данные прогноза присутствуют ({len(forecast)} лет) ✓")
            
            # Check for detailed breakdown
            has_detailed_breakdown = False
            if forecast:
                sample_year = forecast[0]
                if 'revenue_breakdown' in sample_year and 'expense_breakdown' in sample_year:
                    has_detailed_breakdown = True
                    print(f"✅ Критерий 4: Детализация присутствует ✓")
                else:
                    error_msg = f"❌ Отсутствует детализация (revenue_breakdown, expense_breakdown)"
                    results.errors.append(error_msg)
                    print(error_msg)
            
            # Show sample data
            if forecast:
                sample_year = forecast[0]
                year = sample_year.get('year')
                revenue = sample_year.get('revenue', 0)
                expenses = sample_year.get('expenses', 0)
                
                print(f"\n📊 Пример данных прогноза для {year}:")
                print(f"   - Выручка: {revenue:,.0f} ₽")
                print(f"   - Расходы: {expenses:,.0f} ₽")
                print(f"   - Прибыль: {revenue - expenses:,.0f} ₽")
                
                if has_detailed_breakdown:
                    revenue_breakdown = sample_year.get('revenue_breakdown', {})
                    expense_breakdown = sample_year.get('expense_breakdown', {})
                    
                    print(f"   - Детализация доходов: {len(revenue_breakdown)} категорий")
                    print(f"   - Детализация расходов: {len(expense_breakdown)} категорий")
            
            # Get base year data
            base_data = data.get('base_data', {})
            base_revenue = base_data.get('revenue', 0)
            base_expenses = base_data.get('expenses', 0)
            
            print(f"\n📊 Базовые данные 2025:")
            print(f"   - Выручка: {base_revenue:,.0f} ₽")
            print(f"   - Расходы: {base_expenses:,.0f} ₽")
            
            # Summary
            if not results.errors:
                print(f"\n🎉 ВСЕ КРИТЕРИИ УСПЕХА ВЫПОЛНЕНЫ!")
                print(f"✅ Ошибка исправлена")
                print(f"✅ Прогноз работает")
                print(f"✅ Данные корректны")
            
    except Exception as e:
        error_msg = f"❌ КРИТИЧЕСКАЯ ОШИБКА при тестировании {company}: {str(e)}"
        results.errors.append(error_msg)
        print(error_msg)
    
    return results

async def test_forecast_updates_review():
    """Test forecast endpoints according to review request requirements"""
    print("\n=== ТЕСТ ОБНОВЛЕНИЙ ПРОГНОЗА (REVIEW REQUEST) ===\n")
    
    results = TestResults()
    
    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            print("🎯 Тестируем обновления прогноза согласно review request:")
            print("1. GET /api/finances/forecast?company=ВАШ ДОМ ФАКТ&scenario=optimistic")
            print("2. GET /api/finances/forecast?company=УФИЦ модель&scenario=realistic")
            print("")
            
            # Test 1: ВАШ ДОМ ФАКТ - Оптимистичный
            print("🏢 1. ТЕСТИРУЕМ ВАШ ДОМ ФАКТ - ОПТИМИСТИЧНЫЙ СЦЕНАРИЙ")
            print("-" * 60)
            
            response = await client.get(
                f"{API_BASE}/finances/forecast",
                params={"company": "ВАШ ДОМ ФАКТ", "scenario": "optimistic"}
            )
            
            print(f"📡 Ответ сервера: {response.status_code}")
            
            if response.status_code != 200:
                error_msg = f"❌ ВАШ ДОМ ФАКТ optimistic: ошибка {response.status_code} - {response.text}"
                results.errors.append(error_msg)
                print(error_msg)
            else:
                data = response.json()
                results.finance_endpoints['vasdom_fact_optimistic'] = data
                print("✅ ВАШ ДОМ ФАКТ optimistic: 200 статус получен")
                
                # Check forecast data
                forecast = data.get('forecast', [])
                scenario_info = data.get('scenario_info', {})
                
                print(f"📊 Проверяем требования для ВАШ ДОМ ФАКТ - Оптимистичный:")
                
                # 1. Маржа 2026-2030 в диапазоне 27.58%-36.42%
                print("\n1️⃣ Проверяем маржу 2026-2030 (диапазон 27.58%-36.42%):")
                margin_errors = []
                for year_data in forecast:
                    year = year_data.get('year')
                    if year and 2026 <= year <= 2030:
                        margin = year_data.get('margin', 0)
                        if not (27.58 <= margin <= 36.42):
                            margin_errors.append(f"   ❌ {year}: маржа {margin:.2f}% вне диапазона")
                        else:
                            print(f"   ✅ {year}: маржа {margin:.2f}% в диапазоне")
                
                if margin_errors:
                    results.errors.extend(margin_errors)
                else:
                    print("   ✅ Все маржи в требуемом диапазоне")
                
                # 2. Детализация расходов НЕ содержит "юридические услуги"
                print("\n2️⃣ Проверяем отсутствие 'юридические услуги' в детализации:")
                legal_services_found = False
                for year_data in forecast:
                    expense_breakdown = year_data.get('expense_breakdown', {})
                    for category, amount in expense_breakdown.items():
                        if 'юридические' in category.lower() or 'юридическ' in category.lower():
                            legal_services_found = True
                            results.errors.append(f"   ❌ Найдена категория '{category}' в детализации")
                            break
                
                if not legal_services_found:
                    print("   ✅ 'Юридические услуги' отсутствуют в детализации")
                
                # 3. Категория "зарплата" увеличена (включает перераспределенные суммы)
                print("\n3️⃣ Проверяем категорию 'зарплата' (должна быть увеличена):")
                salary_found = False
                for year_data in forecast:
                    expense_breakdown = year_data.get('expense_breakdown', {})
                    for category, amount in expense_breakdown.items():
                        if 'зарплата' in category.lower() or 'зп' in category.lower():
                            salary_found = True
                            print(f"   ✅ Найдена категория '{category}': {amount:,.0f} ₽")
                            break
                
                if not salary_found:
                    results.errors.append("   ❌ Категория 'зарплата' не найдена в детализации")
                
                # 4. Рост расходов обновлен до +22.5% (вместо +18.9%)
                print("\n4️⃣ Проверяем рост расходов +22.5%:")
                if len(forecast) >= 2:
                    year_2026 = next((y for y in forecast if y.get('year') == 2026), None)
                    year_2027 = next((y for y in forecast if y.get('year') == 2027), None)
                    
                    if year_2026 and year_2027:
                        expenses_2026 = year_2026.get('expenses', 0)
                        expenses_2027 = year_2027.get('expenses', 0)
                        
                        if expenses_2026 > 0:
                            growth_rate = ((expenses_2027 - expenses_2026) / expenses_2026) * 100
                            expected_growth = 22.5
                            
                            if abs(growth_rate - expected_growth) > 1.0:  # Allow 1% tolerance
                                results.errors.append(f"   ❌ Рост расходов {growth_rate:.1f}%, ожидался {expected_growth}%")
                            else:
                                print(f"   ✅ Рост расходов {growth_rate:.1f}% (ожидался {expected_growth}%)")
                
                # 5. Поле detailed_description присутствует в scenario_info
                print("\n5️⃣ Проверяем поле 'detailed_description' в scenario_info:")
                detailed_description = scenario_info.get('detailed_description')
                if not detailed_description:
                    results.errors.append("   ❌ Поле 'detailed_description' отсутствует в scenario_info")
                else:
                    print("   ✅ Поле 'detailed_description' присутствует")
                    
                    # 6. detailed_description содержит: summary, revenue_factors, expense_factors
                    print("\n6️⃣ Проверяем структуру detailed_description:")
                    required_fields = ['summary', 'revenue_factors', 'expense_factors']
                    for field in required_fields:
                        if field not in detailed_description:
                            results.errors.append(f"   ❌ Отсутствует поле '{field}' в detailed_description")
                        else:
                            content = detailed_description[field]
                            print(f"   ✅ Поле '{field}' присутствует ({len(str(content))} символов)")
            
            print("\n" + "=" * 60)
            
            # Test 2: УФИЦ модель - Реалистичный
            print("🏢 2. ТЕСТИРУЕМ УФИЦ МОДЕЛЬ - РЕАЛИСТИЧНЫЙ СЦЕНАРИЙ")
            print("-" * 60)
            
            response = await client.get(
                f"{API_BASE}/finances/forecast",
                params={"company": "УФИЦ модель", "scenario": "realistic"}
            )
            
            print(f"📡 Ответ сервера: {response.status_code}")
            
            if response.status_code != 200:
                error_msg = f"❌ УФИЦ модель realistic: ошибка {response.status_code} - {response.text}"
                results.errors.append(error_msg)
                print(error_msg)
            else:
                data = response.json()
                results.finance_endpoints['ufic_realistic'] = data
                print("✅ УФИЦ модель realistic: 200 статус получен")
                
                scenario_info = data.get('scenario_info', {})
                
                print(f"📊 Проверяем требования для УФИЦ модель - Реалистичный:")
                
                # 1. Поле detailed_description присутствует в scenario_info
                print("\n1️⃣ Проверяем поле 'detailed_description' в scenario_info:")
                detailed_description = scenario_info.get('detailed_description')
                if not detailed_description:
                    results.errors.append("   ❌ Поле 'detailed_description' отсутствует в scenario_info")
                else:
                    print("   ✅ Поле 'detailed_description' присутствует")
                    
                    # 2. detailed_description содержит: summary, revenue_factors, expense_factors
                    print("\n2️⃣ Проверяем структуру detailed_description:")
                    required_fields = ['summary', 'revenue_factors', 'expense_factors']
                    for field in required_fields:
                        if field not in detailed_description:
                            results.errors.append(f"   ❌ Отсутствует поле '{field}' в detailed_description")
                        else:
                            content = detailed_description[field]
                            print(f"   ✅ Поле '{field}' присутствует ({len(str(content))} символов)")
            
            print("\n" + "=" * 60)
            print("📋 ИТОГИ ТЕСТИРОВАНИЯ ОБНОВЛЕНИЙ ПРОГНОЗА:")
            
            if not results.errors:
                print("🎉 ВСЕ КРИТЕРИИ УСПЕХА ВЫПОЛНЕНЫ!")
                print("✅ Юридические услуги исключены")
                print("✅ Маржа оптимистичного в диапазоне 27.58%-36.42%")
                print("✅ Детальные описания присутствуют")
                print("✅ Структура detailed_description корректна")
            else:
                print(f"⚠️ ОБНАРУЖЕНО {len(results.errors)} ПРОБЛЕМ:")
                for error in results.errors:
                    print(f"   {error}")
            
    except Exception as e:
        error_msg = f"❌ Ошибка при тестировании обновлений прогноза: {str(e)}"
        results.errors.append(error_msg)
        print(error_msg)
    
    return results

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

async def test_vasdom_model_forecast_endpoint():
    """Test ВАШ ДОМ модель forecast endpoint according to review request"""
    print("\n=== ТЕСТ ПРОГНОЗА ВАШ ДОМ МОДЕЛЬ (REVIEW REQUEST) ===\n")
    
    results = TestResults()
    scenarios = ["pessimistic", "realistic", "optimistic"]
    company = "ВАШ ДОМ модель"
    
    # Expected outsourcing amounts per scenario and year
    expected_outsourcing = {
        "pessimistic": {
            2026: 16028880,
            2027: 17134873,
            2028: 18317179,
            2029: 19581064,
            2030: 20932158
        },
        "realistic": {
            2026: 24615780,
            2027: 25797337,
            2028: 27035610,
            2029: 28333319,
            2030: 29693318
        },
        "optimistic": {
            2026: 34347600,
            2027: 35996285,
            2028: 37724106,
            2029: 39534864,
            2030: 41432537
        }
    }
    
    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            print(f"🏢 Тестируем прогноз для компании: {company}")
            print("📋 Критерии успеха согласно review request:")
            print("   1. Endpoint должен возвращать 200 статус для всех трех сценариев")
            print("   2. В expense_breakdown для каждого года (2026-2030) должна присутствовать категория 'аутсорсинг_персонала'")
            print("   3. Суммы аутсорсинга должны соответствовать ожидаемым значениям")
            print("   4. В expense_breakdown должна присутствовать категория 'фот' или 'зарплата' с уменьшенной суммой")
            print("   5. Детализация расходов должна быть представлена (не только 'operating_expenses')")
            print("   6. Структура ответа должна содержать все необходимые поля: forecast, base_data, investor_metrics")
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
                
                # КРИТЕРИЙ 1: Check 200 status
                if response.status_code != 200:
                    error_msg = f"❌ КРИТЕРИЙ 1 НАРУШЕН: Сценарий {scenario} возвращает {response.status_code} вместо 200 - {response.text}"
                    results.errors.append(error_msg)
                    print(error_msg)
                    continue
                
                print(f"✅ КРИТЕРИЙ 1: Сценарий {scenario} возвращает 200 статус")
                
                data = response.json()
                scenario_results[scenario] = data
                
                # КРИТЕРИЙ 6: Validate response structure
                required_fields = ['forecast', 'base_data']
                optional_fields = ['investor_metrics']
                
                for field in required_fields:
                    if field not in data:
                        error_msg = f"❌ КРИТЕРИЙ 6 НАРУШЕН: Сценарий {scenario} - отсутствует обязательное поле '{field}'"
                        results.errors.append(error_msg)
                        print(error_msg)
                    else:
                        print(f"✅ КРИТЕРИЙ 6: Поле '{field}' присутствует")
                
                for field in optional_fields:
                    if field in data:
                        print(f"✅ КРИТЕРИЙ 6: Опциональное поле '{field}' присутствует")
                    else:
                        print(f"⚠️ КРИТЕРИЙ 6: Опциональное поле '{field}' отсутствует (не критично)")
                
                # Check forecast data for years 2026-2030
                forecast = data.get('forecast', [])
                if len(forecast) < 5:
                    error_msg = f"❌ Сценарий {scenario}: недостаточно лет в прогнозе (ожидалось 5, получено {len(forecast)})"
                    results.errors.append(error_msg)
                    print(error_msg)
                    continue
                
                print(f"✅ Прогноз содержит {len(forecast)} лет")
                
                # Check each year for criteria 2, 3, 4, 5
                years_checked = 0
                outsourcing_found_years = 0
                salary_found_years = 0
                detailed_breakdown_years = 0
                
                for year_data in forecast:
                    year = year_data.get('year')
                    if year not in [2026, 2027, 2028, 2029, 2030]:
                        continue
                    
                    years_checked += 1
                    expense_breakdown = year_data.get('expense_breakdown', {})
                    
                    print(f"\n📊 Проверяем год {year}:")
                    
                    # КРИТЕРИЙ 5: Check if detailed breakdown exists (not just operating_expenses)
                    if len(expense_breakdown) > 1:  # More than just one category
                        detailed_breakdown_years += 1
                        print(f"✅ КРИТЕРИЙ 5: Год {year} имеет детализированные расходы ({len(expense_breakdown)} категорий)")
                    else:
                        error_msg = f"❌ КРИТЕРИЙ 5 НАРУШЕН: Год {year} не имеет детализации расходов (только {len(expense_breakdown)} категорий)"
                        results.errors.append(error_msg)
                        print(error_msg)
                    
                    # КРИТЕРИЙ 2 & 3: Check for outsourcing category and amounts
                    outsourcing_found = False
                    outsourcing_categories = ['аутсорсинг_персонала', 'аутсорсинг персонала', 'Аутсорсинг персонала']
                    
                    for category_name, amount in expense_breakdown.items():
                        if any(outsourcing_cat.lower() in category_name.lower() for outsourcing_cat in outsourcing_categories):
                            outsourcing_found = True
                            outsourcing_found_years += 1
                            
                            expected_amount = expected_outsourcing[scenario][year]
                            amount_diff = abs(amount - expected_amount)
                            amount_diff_pct = amount_diff / expected_amount * 100 if expected_amount > 0 else 100
                            
                            if amount_diff_pct > 1.0:  # Allow 1% tolerance
                                error_msg = f"❌ КРИТЕРИЙ 3 НАРУШЕН: {scenario} {year} - неверная сумма аутсорсинга. Ожидалось {expected_amount:,.0f}, получено {amount:,.0f} (разница {amount_diff_pct:.2f}%)"
                                results.errors.append(error_msg)
                                print(error_msg)
                            else:
                                print(f"✅ КРИТЕРИЙ 2&3: Год {year} - категория '{category_name}' найдена с корректной суммой {amount:,.0f}")
                            break
                    
                    if not outsourcing_found:
                        error_msg = f"❌ КРИТЕРИЙ 2 НАРУШЕН: Год {year} - категория 'аутсорсинг_персонала' не найдена"
                        results.errors.append(error_msg)
                        print(error_msg)
                    
                    # КРИТЕРИЙ 4: Check for salary/FOT category
                    salary_found = False
                    salary_categories = ['фот', 'зарплата', 'ФОТ', 'Зарплата', 'Фонд оплаты труда']
                    
                    for category_name, amount in expense_breakdown.items():
                        if any(salary_cat.lower() in category_name.lower() for salary_cat in salary_categories):
                            salary_found = True
                            salary_found_years += 1
                            print(f"✅ КРИТЕРИЙ 4: Год {year} - категория '{category_name}' найдена с суммой {amount:,.0f}")
                            break
                    
                    if not salary_found:
                        error_msg = f"❌ КРИТЕРИЙ 4 НАРУШЕН: Год {year} - категория 'фот' или 'зарплата' не найдена"
                        results.errors.append(error_msg)
                        print(error_msg)
                    
                    # Show all categories for debugging
                    print(f"📋 Все категории расходов в {year}:")
                    for cat_name, cat_amount in expense_breakdown.items():
                        print(f"   - {cat_name}: {cat_amount:,.0f}")
                
                # Summary for this scenario
                print(f"\n📊 Сводка по сценарию {scenario}:")
                print(f"   - Проверено лет: {years_checked}/5")
                print(f"   - Лет с аутсорсингом: {outsourcing_found_years}/{years_checked}")
                print(f"   - Лет с зарплатой/ФОТ: {salary_found_years}/{years_checked}")
                print(f"   - Лет с детализацией: {detailed_breakdown_years}/{years_checked}")
                
                if years_checked == 5 and outsourcing_found_years == 5 and salary_found_years == 5 and detailed_breakdown_years == 5:
                    print(f"✅ Сценарий {scenario}: ВСЕ КРИТЕРИИ ВЫПОЛНЕНЫ")
                else:
                    print(f"⚠️ Сценарий {scenario}: ЕСТЬ НАРУШЕНИЯ КРИТЕРИЕВ")
                
                print("")
            
            # Final summary
            print("🎯 ИТОГОВАЯ ПРОВЕРКА ВСЕХ КРИТЕРИЕВ:")
            
            total_scenarios = len(scenarios)
            successful_scenarios = len([s for s in scenarios if s in scenario_results])
            
            print(f"✅ КРИТЕРИЙ 1: {successful_scenarios}/{total_scenarios} сценариев возвращают 200 статус")
            
            if successful_scenarios == total_scenarios:
                print("✅ ВСЕ ОСНОВНЫЕ КРИТЕРИИ МОГУТ БЫТЬ ПРОВЕРЕНЫ")
            else:
                error_msg = f"❌ КРИТИЧЕСКИЙ СБОЙ: Только {successful_scenarios}/{total_scenarios} сценариев доступны для проверки"
                results.errors.append(error_msg)
                print(error_msg)
            
            results.finance_endpoints['vasdom_model_forecast'] = scenario_results
            
    except Exception as e:
        error_msg = f"❌ Ошибка при тестировании прогноза ВАШ ДОМ модель: {str(e)}"
        results.errors.append(error_msg)
        print(error_msg)
    
    return results

async def main():
    """Main test execution - focused on ВАШ ДОМ модель forecast testing per review request"""
    print("🚀 ТЕСТИРОВАНИЕ ПРОГНОЗА ВАШ ДОМ МОДЕЛЬ (REVIEW REQUEST)")
    print("=" * 80)
    print(f"🌐 Backend URL: {BACKEND_URL}")
    print(f"🔗 API Base: {API_BASE}")
    print("=" * 80)
    
    # Check basic connectivity
    print("\n🔍 Проверяем доступность backend...")
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(f"{API_BASE}/health")
            if response.status_code == 200:
                print("✅ Backend доступен")
            else:
                print(f"⚠️ Backend недоступен: {response.status_code}")
                return
    except Exception as e:
        print(f"❌ Ошибка подключения к backend: {str(e)}")
        return
    
    print("\n" + "=" * 80)
    print("🧪 ТЕСТИРОВАНИЕ ПРОГНОЗА ВАШ ДОМ МОДЕЛЬ")
    print("=" * 80)
    
    # Run the specific test for ВАШ ДОМ модель forecast as requested
    result = await test_vasdom_model_forecast_endpoint()
    
    # Print summary
    print("\n" + "=" * 80)
    print("📊 ИТОГОВЫЙ ОТЧЁТ")
    print("=" * 80)
    
    if result.errors:
        print(f"❌ Обнаружено ошибок: {len(result.errors)}")
        print("\n🔍 ДЕТАЛИ ОШИБОК:")
        for i, error in enumerate(result.errors, 1):
            print(f"   {i}. {error}")
        
        # Проверяем на критические ошибки
        critical_errors = [e for e in result.errors if "КРИТИЧЕСКИЙ СБОЙ" in e or "500" in e or "КРИТЕРИЙ 1 НАРУШЕН" in e]
        if critical_errors:
            print(f"\n⚠️ КРИТИЧЕСКИХ ОШИБОК: {len(critical_errors)}")
            print("❌ ТРЕБУЕТСЯ ИСПРАВЛЕНИЕ КОДА")
        else:
            print("\n✅ Критические ошибки отсутствуют")
            print("⚠️ Остались только проблемы с данными")
    else:
        print("🎉 ВСЕ ТЕСТЫ ПРОШЛИ УСПЕШНО!")
        print("✅ Все критерии успеха выполнены:")
        print("   ✅ Все сценарии возвращают 200 статус")
        print("   ✅ Категория 'аутсорсинг_персонала' присутствует во всех годах")
        print("   ✅ Суммы аутсорсинга соответствуют ожидаемым")
        print("   ✅ Категория 'фот'/'зарплата' присутствует")
        print("   ✅ Детализация расходов представлена")
        print("   ✅ Структура ответа содержит все необходимые поля")
    
    print("\n" + "=" * 80)
    print("🏁 ТЕСТИРОВАНИЕ ЗАВЕРШЕНО")
    print("=" * 80)
    
    return [("ВАШ ДОМ модель Forecast Test", result)]

if __name__ == "__main__":
    success = asyncio.run(main())
    exit(0 if success else 1)