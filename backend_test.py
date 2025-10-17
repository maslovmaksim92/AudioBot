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
BACKEND_URL = "https://airealtime.preview.emergentagent.com"
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
    
    results = PlannerkaTestResults()
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
    
    results = PlannerkaTestResults()
    
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

async def main():
    """Main test function"""
    print("🚀 Запуск тестирования системы Планёрок VasDom")
    print(f"🌐 Backend URL: {BACKEND_URL}")
    print(f"📡 API Base: {API_BASE}")
    print("=" * 60)
    
    all_errors = []
    
    # Test database connection first
    db_working = await test_database_connection()
    if not db_working:
        all_errors.append("❌ База данных недоступна")
    
    # Test OpenAI configuration
    await test_openai_configuration()
    
    # Test plannerka creation
    create_results = await test_plannerka_create_endpoint()
    all_errors.extend(create_results.errors)
    
    # Test AI analysis (only if creation was successful)
    analysis_results = None
    if create_results.created_meeting_id and not create_results.errors:
        analysis_results = await test_plannerka_analyze_endpoint(create_results.created_meeting_id)
        all_errors.extend(analysis_results.errors)
    else:
        print("\n⚠️ Пропускаем тест AI-анализа из-за ошибок создания планёрки")
    
    # Test list endpoint
    list_results = await test_plannerka_list_endpoint()
    all_errors.extend(list_results.errors)
    
    # Final summary
    print("\n" + "=" * 60)
    print("📋 ИТОГОВЫЙ ОТЧЕТ ТЕСТИРОВАНИЯ ПЛАНЁРОК:")
    print("=" * 60)
    
    if all_errors:
        print("❌ ОБНАРУЖЕНЫ ОШИБКИ:")
        for error in all_errors:
            print(f"   {error}")
    else:
        print("✅ ВСЕ ТЕСТЫ ПРОЙДЕНЫ УСПЕШНО")
    
    print(f"\n📊 Статистика тестирования:")
    print(f"   - База данных работает: {db_working}")
    print(f"   - Планёрка создана: {create_results.created_meeting_id is not None}")
    print(f"   - OpenAI анализ работает: {analysis_results.openai_working if analysis_results else False}")
    print(f"   - Саммари сгенерировано: {analysis_results.summary_generated if analysis_results else False}")
    print(f"   - Задач извлечено: {len(analysis_results.tasks_extracted) if analysis_results else 0}")
    print(f"   - Планёрок в списке: {len(list_results.meetings_list)}")
    
    # Detailed results
    if create_results.created_meeting_id:
        print(f"\n🆔 ID созданной планёрки: {create_results.created_meeting_id}")
    
    if analysis_results and analysis_results.tasks_extracted:
        print(f"\n📋 Извлеченные задачи:")
        for i, task in enumerate(analysis_results.tasks_extracted, 1):
            print(f"   {i}. {task.get('title', 'Без названия')} → {task.get('assignee', 'Не назначен')}")
    
    # Return success/failure
    return len(all_errors) == 0

if __name__ == "__main__":
    success = asyncio.run(main())
    exit(0 if success else 1)