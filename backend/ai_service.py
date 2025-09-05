import os
import asyncio
from typing import Dict, List, Optional, Any
from datetime import datetime
from dotenv import load_dotenv
from emergentintegrations.llm.chat import LlmChat, UserMessage
import logging

# Load environment variables
load_dotenv()

logger = logging.getLogger(__name__)

class AIAssistant:
    """AI Assistant for business management"""
    
    def __init__(self):
        self.api_key = os.getenv("EMERGENT_LLM_KEY")
        if not self.api_key:
            raise ValueError("EMERGENT_LLM_KEY not found in environment variables")
        
        # Business context for the AI
        self.system_message = """Ты — AI-ассистент для управления клининговой компанией. 

КОНТЕКСТ БИЗНЕСА:
- Компания занимается уборкой подъездов и строительными работами
- 100 сотрудников в двух городах: Калуга (500+ домов) и Кемерово (100 домов)
- Должности: генеральный директор, директор, бухгалтер, HR менеджеры, менеджеры по клинингу и стройке, архитектор-сметчик, уборщицы
- Используется Bitrix24 CRM, Telegram для коммуникаций

ТВОИ ЗАДАЧИ:
1. Помогать с управлением сотрудниками и анализом их работы
2. Предоставлять бизнес-аналитику и рекомендации
3. Анализировать финансовые показатели (план/факт)
4. Помогать с планированием и оптимизацией процессов
5. Отвечать на вопросы о работе компании

СТИЛЬ ОБЩЕНИЯ:
- Говори по-русски
- Будь профессиональным и деловым
- Давай конкретные рекомендации
- Используй эмодзи для наглядности
- Будь кратким, но информативным
"""

    async def chat(self, message: str, session_id: str = "default") -> Dict[str, Any]:
        """Handle chat conversation with AI"""
        try:
            # Initialize chat with session
            chat = LlmChat(
                api_key=self.api_key,
                session_id=session_id,
                system_message=self.system_message
            ).with_model("openai", "gpt-4o-mini")
            
            # Create user message
            user_message = UserMessage(text=message)
            
            # Send message and get response
            response = await chat.send_message(user_message)
            
            return {
                "response": response,
                "timestamp": datetime.utcnow().isoformat(),
                "status": "success",
                "model": "gpt-4o-mini",
                "session_id": session_id
            }
            
        except Exception as e:
            logger.error(f"AI chat error: {e}")
            return {
                "response": f"Извините, произошла ошибка при обработке запроса: {str(e)}",
                "timestamp": datetime.utcnow().isoformat(),
                "status": "error",
                "error": str(e)
            }

    async def analyze_employee_data(self, employee_data: Dict) -> Dict[str, Any]:
        """Analyze employee data and provide insights"""
        try:
            # Prepare employee analysis prompt
            analysis_prompt = f"""
Проанализируй данные сотрудника и дай рекомендации:

Данные сотрудника:
- Имя: {employee_data.get('name', 'Не указано')}
- Должность: {employee_data.get('position', 'Не указано')}
- Город: {employee_data.get('city', 'Не указано')}
- Дата найма: {employee_data.get('hire_date', 'Не указано')}
- Активность: {employee_data.get('is_active', 'Не указано')}

Дай краткий анализ и 2-3 рекомендации по работе с этим сотрудником.
"""

            chat = LlmChat(
                api_key=self.api_key,
                session_id="employee_analysis",
                system_message="Ты HR-аналитик. Анализируй данные сотрудников и давай практические рекомендации."
            ).with_model("openai", "gpt-4o-mini")
            
            response = await chat.send_message(UserMessage(text=analysis_prompt))
            
            return {
                "analysis": response,
                "employee_id": employee_data.get('id'),
                "timestamp": datetime.utcnow().isoformat(),
                "status": "success"
            }
            
        except Exception as e:
            logger.error(f"Employee analysis error: {e}")
            return {
                "analysis": "Ошибка при анализе данных сотрудника",
                "status": "error",
                "error": str(e)
            }

    async def generate_business_insights(self, metrics: Dict) -> List[str]:
        """Generate business insights based on company metrics"""
        try:
            insights_prompt = f"""
На основе метрик компании дай 3-5 бизнес-инсайтов и рекомендаций:

Метрики:
- Всего сотрудников: {metrics.get('total_employees', 0)}
- Активные сотрудники: {metrics.get('active_employees', 0)}
- Сотрудники в Калуге: {metrics.get('kaluga_employees', 0)}
- Сотрудники в Кемерово: {metrics.get('kemerovo_employees', 0)}
- Дома в Калуге: {metrics.get('kaluga_houses', 500)}
- Дома в Кемерово: {metrics.get('kemerovo_houses', 100)}

Каждый инсайт должен быть в одном предложении с конкретной рекомендацией.
"""

            chat = LlmChat(
                api_key=self.api_key,
                session_id="business_insights",
                system_message="Ты бизнес-аналитик. Анализируй метрики и давай конкретные рекомендации."
            ).with_model("openai", "gpt-4o-mini")
            
            response = await chat.send_message(UserMessage(text=insights_prompt))
            
            # Split response into individual insights
            insights = [insight.strip() for insight in response.split('\n') if insight.strip() and not insight.strip().startswith('-')]
            return insights[:5]  # Return max 5 insights
            
        except Exception as e:
            logger.error(f"Business insights error: {e}")
            return [
                "Производительность команды требует дополнительного анализа",
                "Рекомендуется провести аудит текущих процессов",
                "Необходимо оптимизировать распределение ресурсов"
            ]

    async def analyze_meeting_transcript(self, transcript: str) -> Dict[str, Any]:
        """Analyze meeting transcript and extract key points"""
        try:
            analysis_prompt = f"""
Проанализируй запись планерки и выдели:

1. Ключевые решения
2. Поставленные задачи
3. Важные проблемы
4. Следующие шаги

Транскрипт:
{transcript}

Ответ дай в структурированном виде.
"""

            chat = LlmChat(
                api_key=self.api_key,
                session_id="meeting_analysis",
                system_message="Ты анализируешь планерки. Выделяй ключевые решения и задачи."
            ).with_model("openai", "gpt-4o-mini")
            
            response = await chat.send_message(UserMessage(text=analysis_prompt))
            
            return {
                "summary": response,
                "timestamp": datetime.utcnow().isoformat(),
                "status": "success"
            }
            
        except Exception as e:
            logger.error(f"Meeting analysis error: {e}")
            return {
                "summary": "Ошибка при анализе планерки",
                "status": "error",
                "error": str(e)
            }

    async def generate_financial_report(self, financial_data: Dict) -> str:
        """Generate financial analysis report"""
        try:
            report_prompt = f"""
Создай финансовый отчет на основе данных:

Финансовые показатели:
- Выручка: {financial_data.get('revenue', 0)} руб
- Расходы: {financial_data.get('expenses', 0)} руб  
- Прибыль: {financial_data.get('profit', 0)} руб

Дай анализ и рекомендации по улучшению финансовых показателей.
"""

            chat = LlmChat(
                api_key=self.api_key,
                session_id="financial_report",
                system_message="Ты финансовый аналитик. Анализируй показатели и давай рекомендации."
            ).with_model("openai", "gpt-4o-mini")
            
            response = await chat.send_message(UserMessage(text=report_prompt))
            return response
            
        except Exception as e:
            logger.error(f"Financial report error: {e}")
            return "Ошибка при генерации финансового отчета"

# Global AI assistant instance
ai_assistant = AIAssistant()