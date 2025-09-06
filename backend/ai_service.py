import os
import asyncio
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from dotenv import load_dotenv
from emergentintegrations.llm.chat import LlmChat, UserMessage
import logging
from db import conversation_manager, db_manager
from models import ConversationSession, ConversationMessage

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
        self.system_message = """Ты — МАКС, AI-директор компании ВасДом. Ты не просто помощник, а полноценный управленец с аналитическим мышлением.

🏢 КОМПАНИЯ ВАСДОМ (твоя зона ответственности):
- Клининговая компания: уборка подъездов + строительные работы
- География: Калуга (500 домов), Кемерово (100 домов) 
- Команда: 100 сотрудников под твоим контролем
- Оборот: 4+ млн рублей/год, цель: рост +15% каждый квартал
- Технологии: Bitrix24 CRM, AI-аналитика, Telegram управление

👨‍💼 ТВОЯ РОЛЬ КАК AI-ДИРЕКТОРА:
1. **КОНТРОЛЬ ИСПОЛНЕНИЯ**: Следишь за выполнением планов и KPI
2. **СТРАТЕГИЧЕСКИЕ РЕШЕНИЯ**: Анализируешь данные и даешь четкие указания
3. **УПРАВЛЕНИЕ КОМАНДОЙ**: Оцениваешь эффективность, выявляешь проблемы
4. **ФИНАНСОВЫЙ КОНТРОЛЬ**: План/факт анализ, прогнозирование, оптимизация
5. **РАЗВИТИЕ БИЗНЕСА**: Находишь точки роста, предлагаешь решения

🎯 СТИЛЬ РУКОВОДСТВА:
- **Директивный, но справедливый** - как опытный руководитель с подчиненными
- **Конкретика и цифры** - никаких общих фраз, только факты и решения
- **Проактивность** - не ждешь вопросов, сам находишь проблемы и предлагаешь решения
- **Ответственность** - каждая рекомендация должна иметь измеримый результат
- **Системность** - видишь связи между процессами, думаешь на несколько шагов вперед

🗣️ КАК ОБЩАЕШЬСЯ:
- **С руководством**: как равный с равным, стратегические инсайты, глобальные решения
- **С менеджерами**: четкие задачи, контрольные точки, ожидания по результату
- **С исполнителями**: понятные инструкции, поддержка, контроль выполнения
- **Всегда**: "Я проанализировал...", "Рекомендую срочно...", "По моим расчетам..."

💼 ТВОИ УПРАВЛЕНЧЕСКИЕ ПРИНЦИПЫ:
- Каждое решение должно увеличивать прибыль или снижать затраты
- Проблемы решаются быстро и системно, а не латаются
- Команда работает по четким процессам и KPI
- Данные важнее мнений - всегда опирайся на цифры из Bitrix24
- Планирование на 3 месяца вперед минимум

🔍 ПОМНИ:
- У тебя есть ПОЛНАЯ память всех разговоров и решений
- Ты отслеживаешь выполнение своих рекомендаций
- Ты знаешь историю каждого сотрудника и проекта
- Ты предупреждаешь о проблемах ДО их возникновения
"""

    async def chat(self, message: str, session_id: str = "default", user_id: Optional[str] = None) -> Dict[str, Any]:
        """Handle chat conversation with AI and persistent memory"""
        start_time = datetime.utcnow()
        
        try:
            # Get/create conversation session with 90-day memory
            session = await conversation_manager.get_or_create_session(session_id, user_id)
            
            # Save user message to memory
            await conversation_manager.save_message(
                session_id=session_id,
                message_type="user",
                content=message,
                metadata={"user_id": user_id}
            )
            
            # Get conversation history for context (last 10 messages)
            history = await conversation_manager.get_conversation_history(session_id, limit=10)
            
            # Build enhanced system message with company context
            enhanced_system_message = self.system_message + f"""

КОНТЕКСТ ДИАЛОГА:
- Сессия: {session_id}
- Количество сообщений в диалоге: {session.get('message_count', 0)}
- Компания: {session.get('context', {}).get('company', 'ВасДом')}

ИСТОРИЯ РАЗГОВОРА (последние сообщения):
"""
            
            # Add conversation history to context
            for msg in history[-5:]:  # Last 5 messages for context
                role = "Пользователь" if msg['message_type'] == 'user' else "AI"
                enhanced_system_message += f"\n{role}: {msg['content'][:200]}..."
            
            enhanced_system_message += "\n\nОтвечай с учетом контекста предыдущих сообщений и истории общения."
            
            # Initialize chat with enhanced context
            chat = LlmChat(
                api_key=self.api_key,
                session_id=session_id,
                system_message=enhanced_system_message
            ).with_model("openai", "gpt-4o-mini")
            
            # Create user message
            user_message = UserMessage(text=message)
            
            # Send message and get response
            response = await chat.send_message(user_message)
            
            # Calculate response time
            response_time = (datetime.utcnow() - start_time).total_seconds() * 1000
            
            # Save AI response to memory
            await conversation_manager.save_message(
                session_id=session_id,
                message_type="assistant",
                content=response,
                metadata={
                    "model": "gpt-4o-mini",
                    "response_time_ms": int(response_time)
                }
            )
            
            # Clean up old conversations periodically (every 100th request)
            if session.get('message_count', 0) % 100 == 0:
                asyncio.create_task(conversation_manager.db.cleanup_old_conversations())
            
            return {
                "response": response,
                "timestamp": datetime.utcnow().isoformat(),
                "status": "success",
                "model": "gpt-4o-mini",
                "session_id": session_id,
                "message_count": session.get('message_count', 0) + 1,
                "has_memory": True,
                "response_time_ms": int(response_time)
            }
            
        except Exception as e:
            logger.error(f"AI chat error: {e}")
            
            # Still try to save error to memory
            try:
                await conversation_manager.save_message(
                    session_id=session_id,
                    message_type="system",
                    content=f"Error: {str(e)}",
                    metadata={"error": True}
                )
            except:
                pass
            
            return {
                "response": f"Извините, произошла ошибка при обработке запроса: {str(e)}",
                "timestamp": datetime.utcnow().isoformat(),
                "status": "error",
                "error": str(e),
                "session_id": session_id,
                "has_memory": False
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