"""
AI Ассистент для VasDom - знает все о домах, сотрудниках, финансах
"""
import logging
import os
import json
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone
import httpx

logger = logging.getLogger(__name__)
from backend.app.services.bitrix24_service import bitrix24_service


class AIAssistant:
    """AI ассистент с контекстом приложения"""
    
    def __init__(self):
        self.openai_key = os.environ.get('OPENAI_API_KEY')
        self.context_cache = {}
    
    async def get_context(self, user_query: str) -> Dict[str, Any]:
        """
        Получить контекст из базы данных и Bitrix24 на основе запроса
        
        Args:
            user_query: Запрос пользователя (может содержать адрес)
        
        Returns:
            Контекст с данными о домах, сотрудниках, финансах и совпавших адресах
        """
        context: Dict[str, Any] = {}

        # Быстрый контекст адреса из Bitrix, если указан в запросе
        try:
            if user_query:
                data = await bitrix24_service.list_houses(address=user_query, limit=20)
                if data and isinstance(data.get('houses'), list):
                    context['matched_houses'] = [
                        {
                            'id': h.get('id'),
                            'title': h.get('title'),
                            'address': h.get('address'),
                            'brigade': h.get('brigade_name') or h.get('brigade'),
                            'periodicity': h.get('periodicity'),
                            'cleaning_dates': h.get('cleaning_dates'),
                            'bitrix_url': h.get('bitrix_url')
                        }
                        for h in data['houses'] if h.get('address')
                    ]
        except Exception as e:
            logger.warning(f"Bitrix quick address context failed: {e}")

        # Подтягиваем статистику из БД (если доступна)
        try:
            import asyncpg
            db_url = os.environ.get('DATABASE_URL', '').replace('postgresql+asyncpg://', 'postgresql://')
            if not db_url:
                return context
            conn = await asyncpg.connect(db_url)
            try:
                # Статистика по домам
                houses_stats = await conn.fetchrow("""
                    SELECT 
                        COUNT(*) as total_houses,
                        COUNT(CASE WHEN status = 'active' THEN 1 END) as active_houses,
                        COUNT(CASE WHEN status = 'completed' THEN 1 END) as completed_houses
                    FROM houses
                """)
                if houses_stats:
                    context['houses'] = {
                        'total': houses_stats['total_houses'] or 0,
                        'active': houses_stats['active_houses'] or 0,
                        'completed': houses_stats['completed_houses'] or 0
                    }

                # Топ домов
                top_houses = await conn.fetch("""
                    SELECT title, address, status, client_name
                    FROM houses
                    ORDER BY created_at DESC
                    LIMIT 5
                """)
                context['top_houses'] = [
                    {
                        'title': h['title'],
                        'address': h['address'],
                        'status': h['status'],
                        'client': h['client_name']
                    }
                    for h in top_houses
                ]

                # Статистика по сотрудникам
                employees_stats = await conn.fetchrow("""
                    SELECT 
                        COUNT(*) as total_employees,
                        COUNT(CASE WHEN is_active = true THEN 1 END) as active_employees
                    FROM employees
                """)
                if employees_stats:
                    context['employees'] = {
                        'total': employees_stats['total_employees'] or 0,
                        'active': employees_stats['active_employees'] or 0
                    }

                # Список сотрудников
                employees = await conn.fetch("""
                    SELECT full_name, position, phone, email, is_active
                    FROM employees
                    WHERE is_active = true
                    ORDER BY full_name
                    LIMIT 10
                """)
                context['employees_list'] = [
                    {
                        'name': e['full_name'],
                        'position': e['position'],
                        'phone': e['phone'],
                        'email': e['email']
                    }
                    for e in employees
                ]

                # Финансовая статистика
                finance_stats = await conn.fetchrow("""
                    SELECT 
                        COUNT(*) as total_transactions,
                        SUM(CASE WHEN type = 'income' THEN amount ELSE 0 END) as total_income,
                        SUM(CASE WHEN type = 'expense' THEN amount ELSE 0 END) as total_expense
                    FROM financial_transactions
                    WHERE date >= NOW() - INTERVAL '30 days'
                """)
                if finance_stats:
                    context['finance'] = {
                        'transactions_30d': finance_stats['total_transactions'] or 0,
                        'income_30d': float(finance_stats['total_income'] or 0),
                        'expense_30d': float(finance_stats['total_expense'] or 0),
                        'profit_30d': float((finance_stats['total_income'] or 0) - (finance_stats['total_expense'] or 0))
                    }

                # Статистика по агентам
                agents_stats = await conn.fetchrow("""
                    SELECT 
                        COUNT(*) as total_agents,
                        COUNT(CASE WHEN status = 'active' THEN 1 END) as active_agents,
                        SUM(executions_total) as total_executions
                    FROM agents
                """)
                if agents_stats:
                    context['agents'] = {
                        'total': agents_stats['total_agents'] or 0,
                        'active': agents_stats['active_agents'] or 0,
                        'executions': agents_stats['total_executions'] or 0
                    }

                logger.info(f"✅ Context gathered: {len(context)} sections")
            finally:
                await conn.close()
        except Exception as e:
            logger.error(f"❌ Error gathering DB context: {e}")

        return context
    
    async def chat(
        self, 
        user_query: str, 
        conversation_history: List[Dict[str, str]] = None,
        voice_mode: bool = False
    ) -> Dict[str, Any]:
        """
        Общение с AI ассистентом
        
        Args:
            user_query: Запрос пользователя
            conversation_history: История разговора
            voice_mode: Режим для голосовых команд (более краткие ответы)
            
        Returns:
            Ответ AI с контекстом
        """
        # Получаем контекст из источников
        context = await self.get_context(user_query)

        # Если запрос похож на вопрос по адресу — попробуем быстрый ответ без LLM
        quick = self._try_answer_cleaning_dates_quick(user_query, context)
        if quick:
            return quick

        if not self.openai_key:
            return {
                'success': False,
                'error': 'OpenAI API key not configured'
            }

        try:
            
            # Формируем системный промпт
            system_prompt = self._build_system_prompt(context, voice_mode)
            
            # Формируем историю сообщений
            messages = [{'role': 'system', 'content': system_prompt}]
            
            if conversation_history:
                messages.extend(conversation_history[-10:])  # Последние 10 сообщений
            
            messages.append({'role': 'user', 'content': user_query})
            
            # Запрос к OpenAI
            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.post(
                    'https://api.openai.com/v1/chat/completions',
                    headers={'Authorization': f'Bearer {self.openai_key}'},
                    json={
                        'model': 'gpt-4',
                        'messages': messages,
                        'max_tokens': 800 if voice_mode else 1500,
                        'temperature': 0.7
                    }
                )
                
                if response.status_code == 200:
                    data = response.json()
                    ai_response = data['choices'][0]['message']['content']
                    
                    return {
                        'success': True,
                        'response': ai_response,
                        'context_used': context,
                        'tokens_used': data['usage']['total_tokens']
                    }
                else:
                    logger.error(f"OpenAI API error: {response.status_code} - {response.text}")
                    return {
                        'success': False,
                        'error': f"OpenAI API error: {response.status_code}"
                    }
        
        except Exception as e:
            logger.error(f"❌ AI assistant error: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def _build_system_prompt(self, context: Dict[str, Any], voice_mode: bool) -> str:
        """
        Построить системный промпт с контекстом
        
        Args:
            context: Контекст из БД
            voice_mode: Режим для голосовых команд
            
        Returns:
            Системный промпт
        """
        prompt = """Ты AI ассистент VasDom - системы управления домами и сотрудниками.

Твоя задача:
- Помогать с данными о домах, сотрудниках, финансах
- Анализировать информацию и давать рекомендации
- Отвечать на вопросы о системе
- Выполнять команды (создать отчёт, найти информацию, проанализировать данные)

"""
        
        if voice_mode:
            prompt += "ВАЖНО: Отвечай кратко и по делу (максимум 2-3 предложения), так как это голосовой режим.\n\n"
        
        # Добавляем контекст
        prompt += "ТЕКУЩИЙ КОНТЕКСТ СИСТЕМЫ:\n\n"
        
        if 'houses' in context:
            prompt += f"""ДОМА:
- Всего домов: {context['houses']['total']}
- Активных: {context['houses']['active']}
- Завершённых: {context['houses']['completed']}

"""
        
        if 'top_houses' in context and context['top_houses']:
            prompt += "Последние дома:\n"
            for house in context['top_houses']:
                prompt += f"- {house['title']} ({house['address']}) - {house['status']}\n"
            prompt += "\n"
        
        if 'employees' in context:
            prompt += f"""СОТРУДНИКИ:
- Всего: {context['employees']['total']}
- Активных: {context['employees']['active']}
"""

        # Если в контексте найден дом по адресу, добавим краткую подсказку в промпт
        if context.get('matched_houses'):
            try:
                h = context['matched_houses'][0]
                addr_line = f"Найден дом: {h.get('title') or ''} — {h.get('address') or ''}. Периодичность: {h.get('periodicity') or 'не указана'}."
                cd = h.get('cleaning_dates') or {}
                def _short_month(k: str):
                    v = cd.get(k) or {}
                    ds = v.get('dates') or []
                    if not ds:
                        return None
                    return f"{k}: {', '.join(ds[:4])}{'…' if len(ds) > 4 else ''} ({v.get('type') or ''})"
                octo = _short_month('october_1') or _short_month('october_2')
                if octo:
                    addr_line += f" Октябрь: {octo}."
                prompt += addr_line + "\n\n"
            except Exception:
                pass
        
        if 'employees_list' in context and context['employees_list']:
            prompt += "Список сотрудников:\n"
            for emp in context['employees_list'][:5]:
                prompt += f"- {emp['name']} ({emp['position']})\n"
            prompt += "\n"
        
        if 'finance' in context:
            prompt += f"""ФИНАНСЫ (последние 30 дней):
- Транзакций: {context['finance']['transactions_30d']}
- Доход: {context['finance']['income_30d']:,.2f} ₽
- Расход: {context['finance']['expense_30d']:,.2f} ₽
- Прибыль: {context['finance']['profit_30d']:,.2f} ₽

"""
        
        if 'agents' in context:
            prompt += f"""АГЕНТЫ АВТОМАТИЗАЦИИ:
- Всего агентов: {context['agents']['total']}
- Активных: {context['agents']['active']}
- Выполнений: {context['agents']['executions']}

"""
        
        prompt += """
Используй этот контекст для ответов. Если нужной информации нет, скажи об этом.
Всегда форматируй числа с разделителями тысяч и валютой.
Используй эмодзи для наглядности: 🏠 дома, 👤 сотрудники, 💰 финансы, 🤖 агенты.
"""
        
        return prompt
    
    def _try_answer_cleaning_dates_quick(self, user_query: str, context: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Если найден дом по адресу (matched_houses), вернём подробный список дат уборок за октябрь без вызова LLM.
        Формат: список дат и тип для october_1 и october_2.
        """
        try:
            if not user_query:
                return None
            houses = context.get('matched_houses') or []
            if not houses:
                return None
            h = houses[0]
            cd = (h.get('cleaning_dates') or {})
            def _fmt_month(key: str) -> Optional[str]:
                v = cd.get(key) or {}
                ds = v.get('dates') or []
                t = v.get('type') or ''
                if not ds:
                    return None
                dates_txt = ', '.join(ds)
                return f"{key}: {dates_txt} — {t}" if t else f"{key}: {dates_txt}"
            parts: List[str] = []
            m1 = _fmt_month('october_1')
            m2 = _fmt_month('october_2')
            if m1:
                parts.append(m1)
            if m2:
                parts.append(m2)
            if not parts:
                return None
            detailed = "\n".join(parts)
            text = (
                f"🏠 Адрес: {h.get('title') or h.get('address')}.\n"
                f"Периодичность: {h.get('periodicity') or 'не указана'}.\n"
                f"Октябрь — даты уборок:\n{detailed}"
            )
            return {'success': True, 'response': text, 'source': 'bitrix', 'context_used': {'matched_houses': houses[:1]}}
        except Exception:
            return None

    async def analyze_data(self, analysis_type: str) -> Dict[str, Any]:
        """
        Автоматический анализ данных
        
        Args:
            analysis_type: Тип анализа (financial, performance, predictions)
            
        Returns:
            Результат анализа
        """
        try:
            context = await self.get_context("анализ данных")
            
            if analysis_type == 'financial':
                return await self._analyze_financial(context)
            elif analysis_type == 'performance':
                return await self._analyze_performance(context)
            elif analysis_type == 'predictions':
                return await self._generate_predictions(context)
            else:
                return {'success': False, 'error': 'Unknown analysis type'}
        
        except Exception as e:
            logger.error(f"❌ Data analysis error: {e}")
            return {'success': False, 'error': str(e)}
    
    async def _analyze_financial(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Финансовый анализ"""
        if 'finance' not in context:
            return {'success': False, 'error': 'No financial data'}
        
        finance = context['finance']
        
        analysis = {
            'success': True,
            'type': 'financial',
            'insights': []
        }
        
        # Анализ прибыльности
        if finance['profit_30d'] > 0:
            roi = (finance['profit_30d'] / finance['expense_30d'] * 100) if finance['expense_30d'] > 0 else 0
            analysis['insights'].append({
                'title': 'Прибыльность',
                'value': f"{finance['profit_30d']:,.2f} ₽",
                'status': 'positive',
                'description': f"ROI: {roi:.1f}%. Компания работает в плюс."
            })
        else:
            analysis['insights'].append({
                'title': 'Убыточность',
                'value': f"{finance['profit_30d']:,.2f} ₽",
                'status': 'negative',
                'description': "Расходы превышают доходы. Требуется оптимизация."
            })
        
        # Анализ соотношения доход/расход
        if finance['expense_30d'] > 0:
            ratio = finance['income_30d'] / finance['expense_30d']
            if ratio > 1.5:
                analysis['insights'].append({
                    'title': 'Отличное соотношение',
                    'value': f"{ratio:.2f}",
                    'status': 'positive',
                    'description': "Доходы значительно превышают расходы."
                })
            elif ratio > 1.0:
                analysis['insights'].append({
                    'title': 'Здоровое соотношение',
                    'value': f"{ratio:.2f}",
                    'status': 'neutral',
                    'description': "Доходы превышают расходы."
                })
            else:
                analysis['insights'].append({
                    'title': 'Критичное соотношение',
                    'value': f"{ratio:.2f}",
                    'status': 'negative',
                    'description': "Расходы слишком высоки относительно доходов."
                })
        
        return analysis
    
    async def _analyze_performance(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Анализ производительности"""
        analysis = {
            'success': True,
            'type': 'performance',
            'insights': []
        }
        
        # Анализ домов
        if 'houses' in context:
            completion_rate = (context['houses']['completed'] / context['houses']['total'] * 100) if context['houses']['total'] > 0 else 0
            analysis['insights'].append({
                'title': 'Завершённость проектов',
                'value': f"{completion_rate:.1f}%",
                'status': 'positive' if completion_rate > 50 else 'neutral',
                'description': f"{context['houses']['completed']} из {context['houses']['total']} домов завершены."
            })
        
        # Анализ агентов
        if 'agents' in context:
            agent_efficiency = (context['agents']['executions'] / context['agents']['active']) if context['agents']['active'] > 0 else 0
            analysis['insights'].append({
                'title': 'Эффективность автоматизации',
                'value': f"{agent_efficiency:.0f} выполнений/агент",
                'status': 'positive' if agent_efficiency > 10 else 'neutral',
                'description': f"Агенты выполнили {context['agents']['executions']} задач."
            })
        
        return analysis
    
    async def _generate_predictions(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Генерация прогнозов"""
        if not self.openai_key:
            return {'success': False, 'error': 'OpenAI API key required'}
        
        # Используем AI для генерации прогнозов
        prompt = f"""На основе данных:
{json.dumps(context, ensure_ascii=False, indent=2)}

Создай 3 краткие прогноза/рекомендации для бизнеса VasDom (управление домами).
Формат: JSON массив объектов с полями: title, prediction, confidence (low/medium/high), timeframe."""
        
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    'https://api.openai.com/v1/chat/completions',
                    headers={'Authorization': f'Bearer {self.openai_key}'},
                    json={
                        'model': 'gpt-4',
                        'messages': [
                            {'role': 'system', 'content': 'Ты аналитик данных. Отвечай только валидным JSON.'},
                            {'role': 'user', 'content': prompt}
                        ],
                        'temperature': 0.5
                    }
                )
                
                if response.status_code == 200:
                    data = response.json()
                    predictions_text = data['choices'][0]['message']['content']
                    
                    # Парсим JSON
                    import re
                    json_match = re.search(r'\[.*\]', predictions_text, re.DOTALL)
                    if json_match:
                        predictions = json.loads(json_match.group())
                        return {
                            'success': True,
                            'type': 'predictions',
                            'predictions': predictions
                        }
        
        except Exception as e:
            logger.error(f"❌ Predictions error: {e}")
        
        return {'success': False, 'error': 'Failed to generate predictions'}


# Глобальный экземпляр
ai_assistant = AIAssistant()
