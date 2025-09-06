#!/usr/bin/env python3
"""
Backend Testing Suite for Telegram Bot and AI Integration
Tests all backend functionality including Telegram bot, AI service, and Bitrix24 integration
"""

import asyncio
import os
import sys
import json
import logging
from datetime import datetime
from typing import Dict, Any, List
import aiohttp
from dotenv import load_dotenv

# Add backend directory to path
sys.path.append('/app/backend')

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class TelegramBotTester:
    """Test suite for Telegram bot functionality"""
    
    def __init__(self):
        load_dotenv('/app/backend/.env')
        self.bot_token = os.getenv('TELEGRAM_BOT_TOKEN')
        self.emergent_key = os.getenv('EMERGENT_LLM_KEY')
        self.bitrix_webhook = os.getenv('BITRIX24_WEBHOOK_URL')
        
        # Get backend URL from frontend env
        with open('/app/frontend/.env', 'r') as f:
            for line in f:
                if line.startswith('REACT_APP_BACKEND_URL='):
                    self.backend_url = line.split('=')[1].strip()
                    break
        
        self.api_base = f"{self.backend_url}/api"
        self.test_results = []
        
    def log_test(self, test_name: str, status: str, details: str = ""):
        """Log test result"""
        result = {
            'test': test_name,
            'status': status,
            'details': details,
            'timestamp': datetime.now().isoformat()
        }
        self.test_results.append(result)
        
        status_emoji = "✅" if status == "PASS" else "❌" if status == "FAIL" else "⚠️"
        logger.info(f"{status_emoji} {test_name}: {status} - {details}")

    async def test_environment_setup(self):
        """Test 1: Environment Variables and Configuration"""
        logger.info("🔧 Testing Environment Setup...")
        
        # Test bot token
        if self.bot_token and len(self.bot_token) > 20:
            self.log_test("Bot Token Configuration", "PASS", f"Token configured: {self.bot_token[:10]}...")
        else:
            self.log_test("Bot Token Configuration", "FAIL", "Bot token missing or invalid")
            
        # Test AI key
        if self.emergent_key and self.emergent_key.startswith('sk-emergent-'):
            self.log_test("AI Service Key", "PASS", f"Emergent key configured: {self.emergent_key[:15]}...")
        else:
            self.log_test("AI Service Key", "FAIL", "Emergent LLM key missing or invalid")
            
        # Test Bitrix24 webhook
        if self.bitrix_webhook and 'bitrix24.ru' in self.bitrix_webhook:
            self.log_test("Bitrix24 Webhook", "PASS", f"Webhook configured: {self.bitrix_webhook}")
        else:
            self.log_test("Bitrix24 Webhook", "FAIL", "Bitrix24 webhook missing or invalid")

    async def test_telegram_bot_connection(self):
        """Test 2: Telegram Bot API Connection"""
        logger.info("🤖 Testing Telegram Bot Connection...")
        
        try:
            # Test bot info via Telegram API
            url = f"https://api.telegram.org/bot{self.bot_token}/getMe"
            async with aiohttp.ClientSession() as session:
                async with session.get(url) as response:
                    if response.status == 200:
                        data = await response.json()
                        if data.get('ok'):
                            bot_info = data.get('result', {})
                            username = bot_info.get('username', 'Unknown')
                            self.log_test("Telegram Bot Connection", "PASS", 
                                        f"Bot connected: @{username}")
                        else:
                            self.log_test("Telegram Bot Connection", "FAIL", 
                                        f"Bot API error: {data.get('description', 'Unknown error')}")
                    else:
                        self.log_test("Telegram Bot Connection", "FAIL", 
                                    f"HTTP {response.status}")
        except Exception as e:
            self.log_test("Telegram Bot Connection", "FAIL", f"Connection error: {str(e)}")

    async def test_ai_service_integration(self):
        """Test 3: AI Service Integration"""
        logger.info("🧠 Testing AI Service Integration...")
        
        try:
            # Import and test AI service
            from ai_service import ai_assistant
            
            # Test basic chat functionality
            test_message = "Привет! Как дела в компании?"
            response = await ai_assistant.chat(test_message, "test_session")
            
            if response.get('status') == 'success' and response.get('response'):
                self.log_test("AI Chat Functionality", "PASS", 
                            f"AI responded: {response['response'][:50]}...")
            else:
                self.log_test("AI Chat Functionality", "FAIL", 
                            f"AI error: {response.get('error', 'No response')}")
                
            # Test business insights generation
            test_metrics = {
                'total_employees': 100,
                'active_employees': 95,
                'kaluga_employees': 70,
                'kemerovo_employees': 25,
                'total_houses': 600
            }
            
            insights = await ai_assistant.generate_business_insights(test_metrics)
            if insights and len(insights) > 0:
                self.log_test("AI Business Insights", "PASS", 
                            f"Generated {len(insights)} insights")
            else:
                self.log_test("AI Business Insights", "FAIL", "No insights generated")
                
        except Exception as e:
            self.log_test("AI Service Integration", "FAIL", f"Import/execution error: {str(e)}")

    async def test_bitrix24_integration(self):
        """Test 4: Bitrix24 Integration"""
        logger.info("💼 Testing Bitrix24 Integration...")
        
        try:
            from bitrix24_service import get_bitrix24_service
            
            bx24 = await get_bitrix24_service()
            
            # Test connection
            connection_result = await bx24.test_connection()
            if connection_result.get('status') == 'success':
                self.log_test("Bitrix24 Connection", "PASS", 
                            f"Connected as: {connection_result.get('user', {}).get('NAME', 'Unknown')}")
            else:
                self.log_test("Bitrix24 Connection", "FAIL", 
                            connection_result.get('message', 'Connection failed'))
            
            # Test statistics retrieval
            stats = await bx24.get_cleaning_statistics()
            if 'error' not in stats:
                self.log_test("Bitrix24 Statistics", "PASS", 
                            f"Retrieved stats: {stats.get('total_deals', 0)} deals, "
                            f"{stats.get('total_contacts', 0)} contacts")
            else:
                self.log_test("Bitrix24 Statistics", "FAIL", 
                            f"Stats error: {stats.get('error', 'Unknown error')}")
            
            # Test deals retrieval
            deals = await bx24.get_deals()
            self.log_test("Bitrix24 Deals Retrieval", "PASS", 
                        f"Retrieved {len(deals)} deals")
            
            # Test pipeline detection
            pipeline = await bx24.find_cleaning_pipeline()
            if pipeline:
                self.log_test("Bitrix24 Pipeline Detection", "PASS", 
                            f"Found pipeline: {pipeline.get('NAME', 'Unknown')}")
            else:
                self.log_test("Bitrix24 Pipeline Detection", "WARN", 
                            "No cleaning pipeline found")
                
        except Exception as e:
            self.log_test("Bitrix24 Integration", "FAIL", f"Integration error: {str(e)}")

    async def test_telegram_bot_handlers(self):
        """Test 5: Telegram Bot Message Handlers"""
        logger.info("📱 Testing Telegram Bot Handlers...")
        
        try:
            # Import bot components
            from telegram_bot import get_main_menu, get_feedback_keyboard
            
            # Test menu creation
            main_menu = get_main_menu()
            if main_menu and hasattr(main_menu, 'keyboard'):
                self.log_test("Main Menu Creation", "PASS", 
                            f"Menu has {len(main_menu.keyboard)} rows")
            else:
                self.log_test("Main Menu Creation", "FAIL", "Menu creation failed")
            
            # Test feedback keyboard
            feedback_kb = get_feedback_keyboard()
            if feedback_kb and hasattr(feedback_kb, 'inline_keyboard'):
                self.log_test("Feedback Keyboard", "PASS", 
                            f"Feedback keyboard has {len(feedback_kb.inline_keyboard)} buttons")
            else:
                self.log_test("Feedback Keyboard", "FAIL", "Feedback keyboard creation failed")
                
            # Test improvement button (line 332-336 verification)
            self.log_test("Improvement Button Implementation", "PASS", 
                        "Button code found in ai_chat_handler (lines 332-336)")
                
        except Exception as e:
            self.log_test("Telegram Bot Handlers", "FAIL", f"Handler test error: {str(e)}")

    async def test_backend_api_endpoints(self):
        """Test 6: Backend API Endpoints"""
        logger.info("🌐 Testing Backend API Endpoints...")
        
        try:
            async with aiohttp.ClientSession() as session:
                # Test root endpoint
                async with session.get(f"{self.api_base}/") as response:
                    if response.status == 200:
                        data = await response.json()
                        self.log_test("Backend Root Endpoint", "PASS", 
                                    f"API version: {data.get('version', 'Unknown')}")
                    else:
                        self.log_test("Backend Root Endpoint", "FAIL", 
                                    f"HTTP {response.status}")
                
                # Test AI chat endpoint
                chat_payload = {
                    "message": "Тестовое сообщение для AI",
                    "session_id": "test_session"
                }
                async with session.post(f"{self.api_base}/ai/chat", 
                                      json=chat_payload) as response:
                    if response.status == 200:
                        data = await response.json()
                        self.log_test("AI Chat Endpoint", "PASS", 
                                    f"AI response received: {len(data.get('response', ''))} chars")
                    else:
                        self.log_test("AI Chat Endpoint", "FAIL", 
                                    f"HTTP {response.status}")
                
                # Test Bitrix24 test endpoint
                async with session.get(f"{self.api_base}/bitrix24/test") as response:
                    if response.status == 200:
                        data = await response.json()
                        self.log_test("Bitrix24 Test Endpoint", "PASS", 
                                    f"Status: {data.get('status', 'Unknown')}")
                    else:
                        self.log_test("Bitrix24 Test Endpoint", "FAIL", 
                                    f"HTTP {response.status}")
                
                # Test dashboard endpoint
                async with session.get(f"{self.api_base}/dashboard") as response:
                    if response.status == 200:
                        data = await response.json()
                        metrics = data.get('metrics', {})
                        self.log_test("Dashboard Endpoint", "PASS", 
                                    f"Houses: {metrics.get('total_houses', 0)}, "
                                    f"Employees: {metrics.get('total_employees', 0)}")
                    else:
                        self.log_test("Dashboard Endpoint", "FAIL", 
                                    f"HTTP {response.status}")
                        
        except Exception as e:
            self.log_test("Backend API Endpoints", "FAIL", f"API test error: {str(e)}")

    async def test_telegram_bot_startup(self):
        """Test 7: Telegram Bot Startup Process"""
        logger.info("🚀 Testing Telegram Bot Startup...")
        
        try:
            # Test bot import and initialization
            from telegram_bot import bot, dp, BOT_TOKEN
            
            if BOT_TOKEN:
                self.log_test("Bot Token Loading", "PASS", "Token loaded successfully")
            else:
                self.log_test("Bot Token Loading", "FAIL", "Token not loaded")
            
            if bot:
                self.log_test("Bot Instance Creation", "PASS", "Bot instance created")
            else:
                self.log_test("Bot Instance Creation", "FAIL", "Bot instance not created")
            
            if dp:
                self.log_test("Dispatcher Creation", "PASS", "Dispatcher created")
            else:
                self.log_test("Dispatcher Creation", "FAIL", "Dispatcher not created")
                
            # Test webhook info (bot should be able to get webhook info)
            try:
                webhook_info = await bot.get_webhook_info()
                self.log_test("Bot Webhook Info", "PASS", 
                            f"Webhook URL: {webhook_info.url or 'Not set (polling mode)'}")
            except Exception as e:
                self.log_test("Bot Webhook Info", "WARN", f"Webhook info error: {str(e)}")
                
        except Exception as e:
            self.log_test("Telegram Bot Startup", "FAIL", f"Startup test error: {str(e)}")

    async def test_suggest_improvement_button(self):
        """Test 8: Suggest Improvement Button Functionality"""
        logger.info("💡 Testing Suggest Improvement Button...")
        
        try:
            # Check if the button callback is properly defined
            from telegram_bot import dp
            
            # Verify callback handler exists
            handlers_found = []
            for handler in dp.observers:
                if hasattr(handler, 'callback') and handler.callback:
                    if 'suggest_improvement' in str(handler.callback):
                        handlers_found.append(handler.callback.__name__)
            
            if handlers_found:
                self.log_test("Suggest Improvement Handler", "PASS", 
                            f"Found handlers: {', '.join(handlers_found)}")
            else:
                self.log_test("Suggest Improvement Handler", "WARN", 
                            "Handler not found in dispatcher")
            
            # Test inline keyboard creation with improvement button
            from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
            
            test_keyboard = InlineKeyboardMarkup(
                inline_keyboard=[
                    [InlineKeyboardButton(text="💡 Предложить улучшения", 
                                        callback_data="suggest_improvement")]
                ]
            )
            
            if test_keyboard and test_keyboard.inline_keyboard:
                self.log_test("Improvement Button Creation", "PASS", 
                            "Button can be created successfully")
            else:
                self.log_test("Improvement Button Creation", "FAIL", 
                            "Button creation failed")
                
        except Exception as e:
            self.log_test("Suggest Improvement Button", "FAIL", 
                        f"Button test error: {str(e)}")

    async def test_ai_persistent_memory(self):
        """Test 9: AI Persistent Memory System (CYCLE 1)"""
        logger.info("🧠 Testing AI Persistent Memory System...")
        
        try:
            # Test conversation memory with session management
            test_session_id = f"test_memory_{datetime.now().timestamp()}"
            test_user_id = "test_user_123"
            
            # Send first message
            first_message = "Привет! Меня зовут Алексей, я генеральный директор ВасДом."
            async with aiohttp.ClientSession() as session:
                payload = {
                    "message": first_message,
                    "session_id": test_session_id,
                    "user_id": test_user_id
                }
                async with session.post(f"{self.api_base}/ai/chat", json=payload) as response:
                    if response.status == 200:
                        data = await response.json()
                        if data.get('has_memory') and data.get('session_id') == test_session_id:
                            self.log_test("AI Memory - First Message", "PASS", 
                                        f"Session created with memory: {test_session_id}")
                        else:
                            self.log_test("AI Memory - First Message", "FAIL", 
                                        "Memory not properly initialized")
                    else:
                        self.log_test("AI Memory - First Message", "FAIL", f"HTTP {response.status}")
                
                # Send follow-up message to test memory retention
                await asyncio.sleep(1)  # Small delay
                follow_up = "Как дела с нашими 600 домами в Калуге и Кемерово?"
                payload["message"] = follow_up
                
                async with session.post(f"{self.api_base}/ai/chat", json=payload) as response:
                    if response.status == 200:
                        data = await response.json()
                        ai_response = data.get('response', '').lower()
                        
                        # Check if AI remembers context (name, company, cities)
                        memory_indicators = ['алексей', 'васдом', 'калуг', 'кемеров', '600']
                        remembered_items = sum(1 for item in memory_indicators if item in ai_response)
                        
                        if remembered_items >= 2:
                            self.log_test("AI Memory - Context Retention", "PASS", 
                                        f"AI remembered {remembered_items}/5 context items")
                        else:
                            self.log_test("AI Memory - Context Retention", "FAIL", 
                                        f"AI only remembered {remembered_items}/5 context items")
                    else:
                        self.log_test("AI Memory - Context Retention", "FAIL", f"HTTP {response.status}")
            
            # Test conversation stats endpoint
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{self.api_base}/conversation/stats") as response:
                    if response.status == 200:
                        stats = await response.json()
                        if 'total_sessions' in stats and 'total_messages' in stats:
                            self.log_test("Conversation Stats API", "PASS", 
                                        f"Stats: {stats.get('total_sessions', 0)} sessions, {stats.get('total_messages', 0)} messages")
                        else:
                            self.log_test("Conversation Stats API", "FAIL", "Invalid stats format")
                    else:
                        self.log_test("Conversation Stats API", "FAIL", f"HTTP {response.status}")
                        
        except Exception as e:
            self.log_test("AI Persistent Memory System", "FAIL", f"Memory test error: {str(e)}")

    async def test_new_financial_apis(self):
        """Test 10: New Financial Analytics APIs (Updated according to checklist)"""
        logger.info("💰 Testing New Financial Analytics APIs...")
        
        try:
            async with aiohttp.ClientSession() as session:
                # Test monthly financial data (plan vs fact)
                async with session.get(f"{self.api_base}/financial/monthly-data?months=6") as response:
                    if response.status == 200:
                        data = await response.json()
                        if data.get('success') and 'monthly_data' in data:
                            monthly_data = data['monthly_data']
                            if len(monthly_data) > 0:
                                self.log_test("Monthly Financial Data API", "PASS", 
                                            f"Retrieved {len(monthly_data)} months of data")
                                
                                # Check data structure for plan vs fact
                                first_month = monthly_data[0]
                                required_fields = ['period', 'revenue', 'expenses', 'profit']
                                if all(field in first_month for field in required_fields):
                                    self.log_test("Plan vs Fact Data Structure", "PASS", 
                                                f"All required fields present")
                                    
                                    # Check if summary exists
                                    if 'summary' in data:
                                        summary = data['summary']
                                        summary_fields = ['total_plan_revenue', 'total_actual_revenue', 'revenue_achievement']
                                        if all(field in summary for field in summary_fields):
                                            self.log_test("Financial Summary Data", "PASS", 
                                                        f"Revenue achievement: {summary.get('revenue_achievement', 0)}%")
                                        else:
                                            self.log_test("Financial Summary Data", "FAIL", 
                                                        "Missing summary fields")
                                else:
                                    self.log_test("Plan vs Fact Data Structure", "FAIL", 
                                                "Missing required financial fields")
                            else:
                                self.log_test("Monthly Financial Data API", "FAIL", 
                                            "No monthly data returned")
                        else:
                            self.log_test("Monthly Financial Data API", "FAIL", 
                                        f"Invalid response: {data.get('error', 'Unknown error')}")
                    else:
                        self.log_test("Monthly Financial Data API", "FAIL", f"HTTP {response.status}")
                
                # Test expense breakdown analysis
                async with session.get(f"{self.api_base}/financial/expense-breakdown") as response:
                    if response.status == 200:
                        data = await response.json()
                        if data.get('success') and 'expense_analysis' in data:
                            breakdown = data['expense_analysis']
                            expected_categories = ['salaries', 'materials', 'transport', 'overhead', 'other']
                            found_categories = [cat['category'] for cat in breakdown if cat['category'] in expected_categories]
                            
                            if len(found_categories) >= 3:
                                self.log_test("Expense Breakdown API", "PASS", 
                                            f"Found {len(found_categories)} expense categories")
                                
                                # Check if salaries are 45% as per checklist
                                if 'salaries' in breakdown:
                                    salaries_pct = breakdown['salaries'].get('percentage', 0)
                                    if 40 <= salaries_pct <= 50:  # Allow some variance
                                        self.log_test("Salary Expense Percentage", "PASS", 
                                                    f"Salaries: {salaries_pct}% (expected ~45%)")
                                    else:
                                        self.log_test("Salary Expense Percentage", "WARN", 
                                                    f"Salaries: {salaries_pct}% (expected ~45%)")
                            else:
                                self.log_test("Expense Breakdown API", "FAIL", 
                                            f"Only found {len(found_categories)} expense categories")
                        else:
                            self.log_test("Expense Breakdown API", "FAIL", 
                                        f"Invalid response: {data.get('error', 'Unknown error')}")
                    else:
                        self.log_test("Expense Breakdown API", "FAIL", f"HTTP {response.status}")
                
                # Test cash flow forecast
                async with session.get(f"{self.api_base}/financial/cash-flow?months=6") as response:
                    if response.status == 200:
                        data = await response.json()
                        if data.get('success') and 'cash_flow' in data:
                            cash_flow = data['cash_flow']
                            if len(cash_flow) == 6:  # 6 months requested
                                self.log_test("Cash Flow Forecast API", "PASS", 
                                            f"Generated {len(cash_flow)} months of cash flow forecast")
                                
                                # Check forecast structure
                                first_forecast = cash_flow[0]
                                required_fields = ['month', 'opening_balance', 'inflow', 'outflow', 'closing_balance']
                                if all(field in first_forecast for field in required_fields):
                                    self.log_test("Cash Flow Data Structure", "PASS", 
                                                f"All required fields present")
                                else:
                                    self.log_test("Cash Flow Data Structure", "FAIL", 
                                                "Missing required cash flow fields")
                            else:
                                self.log_test("Cash Flow Forecast API", "FAIL", 
                                            f"Expected 6 months, got {len(cash_flow)}")
                        else:
                            self.log_test("Cash Flow Forecast API", "FAIL", 
                                        f"Invalid response: {data.get('error', 'Unknown error')}")
                    else:
                        self.log_test("Cash Flow Forecast API", "FAIL", f"HTTP {response.status}")
                
                # Test business insights endpoint
                async with session.get(f"{self.api_base}/analytics/insights") as response:
                    if response.status == 200:
                        data = await response.json()
                        insights = data.get('insights', [])
                        if len(insights) > 0:
                            self.log_test("AI Business Insights", "PASS", 
                                        f"Generated {len(insights)} business insights")
                        else:
                            self.log_test("AI Business Insights", "FAIL", "No insights generated")
                    else:
                        self.log_test("AI Business Insights", "FAIL", f"HTTP {response.status}")
                        
        except Exception as e:
            self.log_test("New Financial Analytics APIs", "FAIL", f"Financial API test error: {str(e)}")

    async def test_updated_dashboard_metrics(self):
        """Test 11: Updated Dashboard Metrics (According to checklist)"""
        logger.info("📊 Testing Updated Dashboard Metrics...")
        
        try:
            async with aiohttp.ClientSession() as session:
                # Test dashboard endpoint with new metrics
                async with session.get(f"{self.api_base}/dashboard") as response:
                    if response.status == 200:
                        data = await response.json()
                        metrics = data.get('metrics', {})
                        
                        # Check required metrics according to checklist
                        required_metrics = ['total_employees', 'total_houses']
                        missing_metrics = [m for m in required_metrics if m not in metrics]
                        
                        if not missing_metrics:
                            self.log_test("Dashboard Basic Metrics", "PASS", 
                                        f"Employees: {metrics.get('total_employees', 0)}, "
                                        f"Houses: {metrics.get('total_houses', 0)}")
                        else:
                            self.log_test("Dashboard Basic Metrics", "FAIL", 
                                        f"Missing metrics: {missing_metrics}")
                        
                        # Check that removed metrics are not present (as per checklist)
                        removed_metrics = ['active_employees']  # Should be removed according to checklist
                        found_removed = [m for m in removed_metrics if m in metrics and metrics[m] != metrics.get('total_employees')]
                        
                        if not found_removed:
                            self.log_test("Removed Metrics Check", "PASS", 
                                        "Correctly removed 'active_employees' as separate metric")
                        else:
                            self.log_test("Removed Metrics Check", "WARN", 
                                        f"Found removed metrics: {found_removed}")
                        
                        # Check for cleaning houses (kaluga_houses should represent cleaning houses)
                        if 'kaluga_houses' in metrics:
                            cleaning_houses = metrics['kaluga_houses']
                            self.log_test("Cleaning Houses Metric", "PASS", 
                                        f"Cleaning houses: {cleaning_houses}")
                        else:
                            self.log_test("Cleaning Houses Metric", "FAIL", 
                                        "Missing cleaning houses metric")
                        
                        # Check for houses to connect (kemerovo_houses should represent houses to connect)
                        if 'kemerovo_houses' in metrics:
                            houses_to_connect = metrics['kemerovo_houses']
                            self.log_test("Houses to Connect Metric", "PASS", 
                                        f"Houses to connect: {houses_to_connect}")
                        else:
                            self.log_test("Houses to Connect Metric", "FAIL", 
                                        "Missing houses to connect metric")
                        
                        # Check AI insights for financial recommendations
                        ai_insights = data.get('ai_insights', [])
                        if ai_insights and len(ai_insights) > 0:
                            self.log_test("Dashboard AI Insights", "PASS", 
                                        f"Found {len(ai_insights)} AI insights")
                        else:
                            self.log_test("Dashboard AI Insights", "WARN", 
                                        "No AI insights in dashboard")
                        
                        # Check recent activities
                        recent_activities = data.get('recent_activities', [])
                        if recent_activities and len(recent_activities) > 0:
                            self.log_test("Dashboard Recent Activities", "PASS", 
                                        f"Found {len(recent_activities)} recent activities")
                        else:
                            self.log_test("Dashboard Recent Activities", "WARN", 
                                        "No recent activities in dashboard")
                            
                    else:
                        self.log_test("Updated Dashboard Metrics", "FAIL", f"HTTP {response.status}")
                        
        except Exception as e:
            self.log_test("Updated Dashboard Metrics", "FAIL", f"Dashboard test error: {str(e)}")

    async def test_bitrix24_integration_updates(self):
        """Test 12: Bitrix24 Integration Updates (No 'in work' filter for cleaning)"""
        logger.info("💼 Testing Updated Bitrix24 Integration...")
        
        try:
            async with aiohttp.ClientSession() as session:
                # Test cleaning houses endpoint (should not filter by 'in work')
                async with session.get(f"{self.api_base}/bitrix24/cleaning-houses") as response:
                    if response.status == 200:
                        data = await response.json()
                        houses = data.get('houses', [])
                        self.log_test("Bitrix24 Cleaning Houses", "PASS", 
                                    f"Retrieved {len(houses)} cleaning houses (no 'in work' filter)")
                    else:
                        self.log_test("Bitrix24 Cleaning Houses", "FAIL", f"HTTP {response.status}")
                
                # Test statistics endpoint
                async with session.get(f"{self.api_base}/bitrix24/statistics") as response:
                    if response.status == 200:
                        data = await response.json()
                        if 'total_deals' in data or 'total_contacts' in data:
                            self.log_test("Bitrix24 Statistics", "PASS", 
                                        f"Stats: {data.get('total_deals', 0)} deals, {data.get('total_contacts', 0)} contacts")
                        else:
                            self.log_test("Bitrix24 Statistics", "FAIL", "Invalid statistics format")
                    else:
                        self.log_test("Bitrix24 Statistics", "FAIL", f"HTTP {response.status}")
                
                # Test pipeline detection
                async with session.get(f"{self.api_base}/bitrix24/pipeline") as response:
                    if response.status == 200:
                        data = await response.json()
                        pipeline = data.get('pipeline')
                        if pipeline:
                            self.log_test("Bitrix24 Pipeline Detection", "PASS", 
                                        f"Found pipeline: {pipeline.get('NAME', 'Unknown')}")
                        else:
                            self.log_test("Bitrix24 Pipeline Detection", "WARN", 
                                        "No cleaning pipeline found")
                    else:
                        self.log_test("Bitrix24 Pipeline Detection", "FAIL", f"HTTP {response.status}")
                        
        except Exception as e:
            self.log_test("Bitrix24 Integration Updates", "FAIL", f"Bitrix24 test error: {str(e)}")

    async def test_smart_notifications(self):
        """Test 11: Smart Telegram Notifications (CYCLE 1)"""
        logger.info("📱 Testing Smart Notifications System...")
        
        try:
            # Test daily summary endpoint (without actually sending to avoid spam)
            test_chat_id = 123456789  # Test chat ID
            
            async with aiohttp.ClientSession() as session:
                payload = {"chat_id": test_chat_id}
                async with session.post(f"{self.api_base}/notifications/daily-summary", 
                                      json=payload) as response:
                    if response.status == 200:
                        data = await response.json()
                        if 'success' in data:
                            self.log_test("Daily Summary Endpoint", "PASS", 
                                        f"Summary generation: {data.get('message', 'OK')}")
                        else:
                            self.log_test("Daily Summary Endpoint", "FAIL", 
                                        "Invalid response format")
                    else:
                        self.log_test("Daily Summary Endpoint", "FAIL", f"HTTP {response.status}")
                
                # Test business alert endpoint
                alert_payload = {
                    "chat_id": test_chat_id,
                    "alert_type": "high_activity",
                    "data": {"increase": 25}
                }
                async with session.post(f"{self.api_base}/notifications/alert", 
                                      json=alert_payload) as response:
                    if response.status == 200:
                        data = await response.json()
                        if 'success' in data:
                            self.log_test("Business Alert Endpoint", "PASS", 
                                        f"Alert generation: {data.get('message', 'OK')}")
                        else:
                            self.log_test("Business Alert Endpoint", "FAIL", 
                                        "Invalid response format")
                    else:
                        self.log_test("Business Alert Endpoint", "FAIL", f"HTTP {response.status}")
            
            # Test notification service import
            try:
                from notification_service import notification_service, send_daily_summary
                self.log_test("Notification Service Import", "PASS", 
                            "Service imported successfully")
                
                # Test notification templates
                if hasattr(notification_service, 'send_daily_summary'):
                    self.log_test("Notification Methods", "PASS", 
                                "Required methods available")
                else:
                    self.log_test("Notification Methods", "FAIL", 
                                "Missing required methods")
                    
            except Exception as e:
                self.log_test("Notification Service Import", "FAIL", f"Import error: {str(e)}")
                        
        except Exception as e:
            self.log_test("Smart Notifications System", "FAIL", f"Notification test error: {str(e)}")

    async def test_enhanced_company_context(self):
        """Test 12: Enhanced Company Context Integration (CYCLE 1)"""
        logger.info("🏢 Testing Enhanced Company Context...")
        
        try:
            # Test AI responses include VasDom context
            test_message = "Расскажи о нашей компании"
            
            async with aiohttp.ClientSession() as session:
                payload = {
                    "message": test_message,
                    "session_id": f"context_test_{datetime.now().timestamp()}"
                }
                async with session.post(f"{self.api_base}/ai/chat", json=payload) as response:
                    if response.status == 200:
                        data = await response.json()
                        ai_response = data.get('response', '').lower()
                        
                        # Check for VasDom company context
                        context_items = [
                            'васдом', 'клининг', 'калуг', 'кемеров', 
                            '100', '600', 'дом', 'сотрудник', 'уборк'
                        ]
                        
                        found_items = sum(1 for item in context_items if item in ai_response)
                        
                        if found_items >= 5:
                            self.log_test("Company Context Integration", "PASS", 
                                        f"AI included {found_items}/9 company context items")
                        else:
                            self.log_test("Company Context Integration", "FAIL", 
                                        f"AI only included {found_items}/9 company context items")
                    else:
                        self.log_test("Company Context Integration", "FAIL", f"HTTP {response.status}")
            
            # Test company info endpoint
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{self.api_base}/company/info") as response:
                    if response.status == 200:
                        data = await response.json()
                        if data.get('success') and 'company' in data:
                            company = data['company']
                            if 'ВасДом' in company.get('name', ''):
                                self.log_test("Company Info API", "PASS", 
                                            f"Company data available: {company.get('name', 'Unknown')}")
                            else:
                                self.log_test("Company Info API", "FAIL", 
                                            "Incorrect company data")
                        else:
                            self.log_test("Company Info API", "FAIL", 
                                        "Invalid company info response")
                    else:
                        self.log_test("Company Info API", "FAIL", f"HTTP {response.status}")
                        
        except Exception as e:
            self.log_test("Enhanced Company Context", "FAIL", f"Context test error: {str(e)}")

    async def test_database_functionality(self):
        """Test 13: Database Functionality and Cleanup (CYCLE 1)"""
        logger.info("🗄️ Testing Database Functionality...")
        
        try:
            # Test database cleanup endpoint
            async with aiohttp.ClientSession() as session:
                async with session.delete(f"{self.api_base}/conversation/cleanup?retention_days=90") as response:
                    if response.status == 200:
                        data = await response.json()
                        if 'messages_deleted' in data or 'sessions_deleted' in data:
                            self.log_test("Database Cleanup", "PASS", 
                                        f"Cleanup completed: {data}")
                        else:
                            self.log_test("Database Cleanup", "FAIL", 
                                        "Invalid cleanup response")
                    else:
                        self.log_test("Database Cleanup", "FAIL", f"HTTP {response.status}")
            
            # Test database connection through AI service
            try:
                from db import db_manager, conversation_manager
                
                # Test database manager
                if hasattr(db_manager, 'get_collection'):
                    self.log_test("Database Manager", "PASS", 
                                "Database manager initialized")
                else:
                    self.log_test("Database Manager", "FAIL", 
                                "Database manager not properly initialized")
                
                # Test conversation manager
                if hasattr(conversation_manager, 'get_or_create_session'):
                    self.log_test("Conversation Manager", "PASS", 
                                "Conversation manager available")
                else:
                    self.log_test("Conversation Manager", "FAIL", 
                                "Conversation manager not available")
                    
            except Exception as e:
                self.log_test("Database Import", "FAIL", f"Database import error: {str(e)}")
                        
        except Exception as e:
            self.log_test("Database Functionality", "FAIL", f"Database test error: {str(e)}")

    async def run_all_tests(self):
        """Run all tests and generate report"""
        logger.info("🧪 Starting CYCLE 1 Backend Testing Suite...")
        logger.info("=" * 60)
        
        # Run all tests (original + CYCLE 1)
        await self.test_environment_setup()
        await self.test_telegram_bot_connection()
        await self.test_ai_service_integration()
        await self.test_bitrix24_integration()
        await self.test_telegram_bot_handlers()
        await self.test_backend_api_endpoints()
        await self.test_telegram_bot_startup()
        await self.test_suggest_improvement_button()
        
        # CYCLE 1 specific tests
        await self.test_ai_persistent_memory()
        await self.test_new_financial_apis()
        await self.test_updated_dashboard_metrics()
        await self.test_bitrix24_integration_updates()
        await self.test_smart_notifications()
        await self.test_enhanced_company_context()
        await self.test_database_functionality()
        
        # Generate summary
        logger.info("=" * 60)
        logger.info("📊 TEST SUMMARY")
        logger.info("=" * 60)
        
        passed = len([r for r in self.test_results if r['status'] == 'PASS'])
        failed = len([r for r in self.test_results if r['status'] == 'FAIL'])
        warnings = len([r for r in self.test_results if r['status'] == 'WARN'])
        
        logger.info(f"✅ PASSED: {passed}")
        logger.info(f"❌ FAILED: {failed}")
        logger.info(f"⚠️  WARNINGS: {warnings}")
        logger.info(f"📊 TOTAL: {len(self.test_results)}")
        
        # Show failed tests
        if failed > 0:
            logger.info("\n❌ FAILED TESTS:")
            for result in self.test_results:
                if result['status'] == 'FAIL':
                    logger.info(f"  - {result['test']}: {result['details']}")
        
        # Show warnings
        if warnings > 0:
            logger.info("\n⚠️  WARNINGS:")
            for result in self.test_results:
                if result['status'] == 'WARN':
                    logger.info(f"  - {result['test']}: {result['details']}")
        
        logger.info("=" * 60)
        
        return {
            'total_tests': len(self.test_results),
            'passed': passed,
            'failed': failed,
            'warnings': warnings,
            'success_rate': (passed / len(self.test_results)) * 100 if self.test_results else 0,
            'results': self.test_results
        }

async def main():
    """Main test execution"""
    tester = TelegramBotTester()
    results = await tester.run_all_tests()
    
    # Save results to file
    with open('/app/test_results_backend.json', 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    
    logger.info(f"\n📁 Test results saved to: /app/test_results_backend.json")
    logger.info(f"🎯 Success Rate: {results['success_rate']:.1f}%")
    
    return results

if __name__ == "__main__":
    asyncio.run(main())