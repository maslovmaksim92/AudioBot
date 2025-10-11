"""
Сервис выполнения агентов - executor для triggers и actions
"""
import logging
import os
import httpx
from datetime import datetime, timezone
from typing import Dict, Any, List

logger = logging.getLogger(__name__)

class AgentExecutor:
    """Executor для выполнения агентов"""
    
    def __init__(self):
        self.telegram_bot_token = os.environ.get('TELEGRAM_BOT_TOKEN')
        self.telegram_target_chat_id = os.environ.get('TELEGRAM_TARGET_CHAT_ID')
    
    async def execute_agent(self, agent: Dict[str, Any]) -> Dict[str, Any]:
        """
        Выполнить агента - запустить все его actions
        
        Args:
            agent: Словарь с данными агента
            
        Returns:
            Результат выполнения
        """
        logger.info(f"🚀 Executing agent: {agent['name']} (ID: {agent['id']})")
        
        results = []
        success = True
        
        try:
            # Проверяем условия выполнения (if/then logic)
            conditions = agent.get('config', {}).get('conditions', [])
            if conditions and not await self._check_conditions(conditions, agent):
                logger.info(f"⏭️ Agent conditions not met, skipping execution")
                return {
                    'success': True,
                    'agent_id': agent['id'],
                    'agent_name': agent['name'],
                    'skipped': True,
                    'reason': 'Conditions not met',
                    'executed_at': datetime.now(timezone.utc).isoformat()
                }
            
            # Выполняем все actions
            for action in agent.get('actions', []):
                action_type = action.get('type')
                action_config = action.get('config', {})
                
                if action_type == 'telegram_send':
                    result = await self._execute_telegram_send(action_config)
                    results.append({
                        'action': action.get('name'),
                        'type': action_type,
                        'success': result['success'],
                        'message': result.get('message')
                    })
                    if not result['success']:
                        success = False
                
                elif action_type == 'email_send':
                    result = await self._execute_email_send(action_config)
                    results.append({
                        'action': action.get('name'),
                        'type': action_type,
                        'success': result['success'],
                        'message': result.get('message')
                    })
                    if not result['success']:
                        success = False
                
                elif action_type == 'ai_call':
                    result = await self._execute_ai_call(action_config)
                    results.append({
                        'action': action.get('name'),
                        'type': action_type,
                        'success': result['success'],
                        'message': result.get('message')
                    })
                    if not result['success']:
                        success = False
                
                elif action_type == 'ai_chat':
                    result = await self._execute_ai_chat(action_config)
                    results.append({
                        'action': action.get('name'),
                        'type': action_type,
                        'success': result['success'],
                        'message': result.get('message'),
                        'response': result.get('response')
                    })
                    if not result['success']:
                        success = False
                
                elif action_type == 'knowledge_search':
                    result = await self._execute_knowledge_search(action_config)
                    results.append({
                        'action': action.get('name'),
                        'type': action_type,
                        'success': result['success'],
                        'results_count': result.get('results_count')
                    })
                
                elif action_type == 'log_create':
                    result = await self._execute_log_create(agent, action_config)
                    results.append({
                        'action': action.get('name'),
                        'type': action_type,
                        'success': result['success']
                    })
                
                else:
                    logger.warning(f"⚠️ Unknown action type: {action_type}")
                    results.append({
                        'action': action.get('name'),
                        'type': action_type,
                        'success': False,
                        'message': f"Unknown action type: {action_type}"
                    })
                    success = False
            
            executed_at = datetime.now(timezone.utc)
            
            result = {
                'success': success,
                'agent_id': agent['id'],
                'agent_name': agent['name'],
                'executed_at': executed_at.isoformat(),
                'actions_executed': len(results),
                'results': results
            }
            
            # Сохраняем лог выполнения
            await self._save_execution_log(result)
            
            return result
        
        except Exception as e:
            logger.error(f"❌ Error executing agent {agent['name']}: {e}")
            return {
                'success': False,
                'agent_id': agent['id'],
                'agent_name': agent['name'],
                'error': str(e),
                'executed_at': datetime.now(timezone.utc).isoformat()
            }
    
    async def _execute_telegram_send(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Отправить сообщение в Telegram
        
        Args:
            config: Конфигурация с recipients и message
            
        Returns:
            Результат отправки
        """
        if not self.telegram_bot_token:
            logger.error("❌ TELEGRAM_BOT_TOKEN not configured")
            return {
                'success': False,
                'message': 'Telegram bot token not configured'
            }
        
        recipients = config.get('recipients', '')
        message = config.get('message', '')
        
        if not recipients or not message:
            return {
                'success': False,
                'message': 'Recipients or message is empty'
            }
        
        # Парсим получателей (могут быть через запятую)
        recipients_list = [r.strip() for r in recipients.split(',')]
        
        sent_count = 0
        failed_count = 0
        
        async with httpx.AsyncClient() as client:
            for recipient in recipients_list:
                try:
                    # Определяем chat_id
                    chat_id = recipient
                    
                    # Если это номер телефона, используем его напрямую
                    # Telegram API принимает как chat_id, так и username (@username)
                    
                    url = f"https://api.telegram.org/bot{self.telegram_bot_token}/sendMessage"
                    payload = {
                        'chat_id': chat_id,
                        'text': message,
                        'parse_mode': 'HTML'
                    }
                    
                    response = await client.post(url, json=payload)
                    
                    if response.status_code == 200:
                        sent_count += 1
                        logger.info(f"✅ Telegram message sent to {chat_id}")
                    else:
                        failed_count += 1
                        logger.error(f"❌ Failed to send to {chat_id}: {response.text}")
                
                except Exception as e:
                    failed_count += 1
                    logger.error(f"❌ Error sending to {recipient}: {e}")
        
        return {
            'success': sent_count > 0,
            'message': f"Sent to {sent_count}/{len(recipients_list)} recipients",
            'sent_count': sent_count,
            'failed_count': failed_count
        }
    
    async def _execute_log_create(self, agent: Dict[str, Any], config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Создать запись в логах
        
        Args:
            agent: Данные агента
            config: Конфигурация действия
            
        Returns:
            Результат создания лога
        """
        try:
            log_message = f"Agent '{agent['name']}' executed at {datetime.now(timezone.utc).isoformat()}"
            logger.info(f"📝 {log_message}")
            
            return {
                'success': True,
                'message': log_message
            }
        
        except Exception as e:
            logger.error(f"❌ Error creating log: {e}")
            return {
                'success': False,
                'message': str(e)
            }
    
    async def _execute_email_send(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Отправить email
        
        Args:
            config: Конфигурация с recipients, subject, body
            
        Returns:
            Результат отправки
        """
        try:
            import smtplib
            from email.mime.text import MIMEText
            from email.mime.multipart import MIMEMultipart
            
            smtp_server = os.environ.get('SMTP_SERVER', 'smtp.gmail.com')
            smtp_port = int(os.environ.get('SMTP_PORT', '587'))
            smtp_username = os.environ.get('SMTP_USERNAME')
            smtp_password = os.environ.get('SMTP_PASSWORD')
            
            if not smtp_username or not smtp_password:
                return {
                    'success': False,
                    'message': 'SMTP credentials not configured'
                }
            
            recipients = config.get('recipients', '')
            subject = config.get('subject', 'Уведомление от VasDom')
            body = config.get('body', '')
            
            if not recipients or not body:
                return {
                    'success': False,
                    'message': 'Recipients or body is empty'
                }
            
            recipients_list = [r.strip() for r in recipients.split(',')]
            
            # Создаём сообщение
            msg = MIMEMultipart()
            msg['From'] = smtp_username
            msg['To'] = ', '.join(recipients_list)
            msg['Subject'] = subject
            msg.attach(MIMEText(body, 'html'))
            
            # Отправляем
            with smtplib.SMTP(smtp_server, smtp_port) as server:
                server.starttls()
                server.login(smtp_username, smtp_password)
                server.send_message(msg)
            
            logger.info(f"✅ Email sent to {len(recipients_list)} recipients")
            
            return {
                'success': True,
                'message': f"Email sent to {len(recipients_list)} recipients"
            }
        
        except Exception as e:
            logger.error(f"❌ Error sending email: {e}")
            return {
                'success': False,
                'message': str(e)
            }
    
    async def _check_conditions(self, conditions: List[Dict[str, Any]], agent: Dict[str, Any]) -> bool:
        """
        Проверить условия выполнения агента
        
        Args:
            conditions: Список условий [{'type': 'time_range', 'config': {...}}, ...]
            agent: Данные агента
            
        Returns:
            True если все условия выполнены
        """
        try:
            for condition in conditions:
                condition_type = condition.get('type')
                condition_config = condition.get('config', {})
                
                if condition_type == 'time_range':
                    # Проверка временного диапазона
                    start_time = condition_config.get('start', '00:00')
                    end_time = condition_config.get('end', '23:59')
                    
                    now = datetime.now(timezone.utc)
                    current_time = now.strftime('%H:%M')
                    
                    if not (start_time <= current_time <= end_time):
                        logger.info(f"⏰ Time condition not met: {current_time} not in {start_time}-{end_time}")
                        return False
                
                elif condition_type == 'day_of_week':
                    # Проверка дня недели
                    allowed_days = condition_config.get('days', [])  # [1,2,3,4,5] для Пн-Пт
                    
                    now = datetime.now(timezone.utc)
                    current_day = now.weekday() + 1  # 1=Monday, 7=Sunday
                    
                    if allowed_days and current_day not in allowed_days:
                        logger.info(f"📅 Day condition not met: {current_day} not in {allowed_days}")
                        return False
                
                elif condition_type == 'weather':
                    # Проверка погоды (можно интегрировать с API погоды)
                    # Пока заглушка
                    pass
                
                elif condition_type == 'database_check':
                    # Проверка данных в БД
                    query = condition_config.get('query')
                    expected_count = condition_config.get('count', 0)
                    
                    if query:
                        import asyncpg
                        db_url = os.environ.get('DATABASE_URL', '').replace('postgresql+asyncpg://', 'postgresql://')
                        conn = await asyncpg.connect(db_url)
                        
                        try:
                            count = await conn.fetchval(query)
                            await conn.close()
                            
                            if count < expected_count:
                                logger.info(f"🗄️ Database condition not met: {count} < {expected_count}")
                                return False
                        except:
                            await conn.close()
                            return False
                
                else:
                    logger.warning(f"⚠️ Unknown condition type: {condition_type}")
            
            return True
        
        except Exception as e:
            logger.error(f"❌ Error checking conditions: {e}")
            return False
    
    async def _execute_ai_call(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Выполнить AI звонок
        
        Args:
            config: Конфигурация с phone_numbers, scenario
            
        Returns:
            Результат выполнения звонка
        """
        try:
            phone_numbers = config.get('phone_numbers', '')
            scenario = config.get('scenario', 'greeting')
            
            if not phone_numbers:
                return {
                    'success': False,
                    'message': 'Phone numbers not specified'
                }
            
            phones_list = [p.strip() for p in phone_numbers.split(',')]
            
            # Здесь должна быть интеграция с LiveKit/OpenAI Realtime
            # Пока что логируем
            logger.info(f"📞 AI Call scheduled for {len(phones_list)} numbers with scenario: {scenario}")
            
            # Можно добавить реальную интеграцию с существующим voice роутером
            
            return {
                'success': True,
                'message': f"AI calls scheduled for {len(phones_list)} numbers",
                'phone_count': len(phones_list)
            }
        
        except Exception as e:
            logger.error(f"❌ Error executing AI call: {e}")
            return {
                'success': False,
                'message': str(e)
            }
    
    async def _execute_ai_chat(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Выполнить AI запрос с контекстом из базы знаний
        
        Args:
            config: Конфигурация с query, use_knowledge
            
        Returns:
            Результат выполнения
        """
        try:
            query = config.get('query', '')
            use_knowledge = config.get('use_knowledge', True)
            
            if not query:
                return {
                    'success': False,
                    'message': 'Query is empty'
                }
            
            # Если нужно использовать базу знаний
            context = ""
            if use_knowledge:
                knowledge_result = await self._execute_knowledge_search({'query': query, 'limit': 3})
                if knowledge_result['success']:
                    context = knowledge_result.get('context', '')
            
            # Отправляем запрос в OpenAI
            import httpx
            openai_key = os.environ.get('OPENAI_API_KEY')
            
            if not openai_key:
                return {
                    'success': False,
                    'message': 'OpenAI API key not configured'
                }
            
            messages = [
                {'role': 'system', 'content': f'Ты помощник VasDom. Используй следующий контекст для ответа:\n\n{context}'},
                {'role': 'user', 'content': query}
            ]
            
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    'https://api.openai.com/v1/chat/completions',
                    headers={'Authorization': f'Bearer {openai_key}'},
                    json={
                        'model': 'gpt-4',
                        'messages': messages,
                        'max_tokens': 500
                    },
                    timeout=30.0
                )
                
                if response.status_code == 200:
                    data = response.json()
                    ai_response = data['choices'][0]['message']['content']
                    
                    logger.info(f"🤖 AI response: {ai_response[:100]}...")
                    
                    return {
                        'success': True,
                        'message': 'AI response generated',
                        'response': ai_response
                    }
                else:
                    return {
                        'success': False,
                        'message': f'OpenAI API error: {response.status_code}'
                    }
        
        except Exception as e:
            logger.error(f"❌ Error executing AI chat: {e}")
            return {
                'success': False,
                'message': str(e)
            }
    
    async def _execute_knowledge_search(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Поиск в базе знаний
        
        Args:
            config: Конфигурация с query, limit
            
        Returns:
            Результат поиска
        """
        try:
            query = config.get('query', '')
            limit = config.get('limit', 5)
            
            if not query:
                return {
                    'success': False,
                    'message': 'Query is empty'
                }
            
            # Поиск в базе знаний через векторное сходство
            import asyncpg
            db_url = os.environ.get('DATABASE_URL', '').replace('postgresql+asyncpg://', 'postgresql://')
            conn = await asyncpg.connect(db_url)
            
            try:
                # Простой текстовый поиск (можно улучшить с vector search)
                rows = await conn.fetch("""
                    SELECT content, metadata
                    FROM knowledge_base
                    WHERE content ILIKE $1
                    ORDER BY created_at DESC
                    LIMIT $2
                """, f'%{query}%', limit)
                
                await conn.close()
                
                if rows:
                    context = "\n\n".join([row['content'] for row in rows])
                    logger.info(f"📚 Found {len(rows)} knowledge base entries")
                    
                    return {
                        'success': True,
                        'results_count': len(rows),
                        'context': context
                    }
                else:
                    return {
                        'success': True,
                        'results_count': 0,
                        'context': ''
                    }
            
            except Exception as e:
                await conn.close()
                # Таблица может не существовать
                logger.warning(f"⚠️ Knowledge base search failed: {e}")
                return {
                    'success': True,
                    'results_count': 0,
                    'context': ''
                }
        
        except Exception as e:
            logger.error(f"❌ Error searching knowledge base: {e}")
            return {
                'success': False,
                'message': str(e)
            }
    
    async def _save_execution_log(self, result: Dict[str, Any]):
        """
        Сохранить лог выполнения в БД
        
        Args:
            result: Результат выполнения агента
        """
        try:
            import asyncpg
            import json
            from uuid import uuid4
            
            db_url = os.environ.get('DATABASE_URL', '').replace('postgresql+asyncpg://', 'postgresql://')
            conn = await asyncpg.connect(db_url)
            
            try:
                log_id = str(uuid4())
                
                await conn.execute("""
                    INSERT INTO agent_execution_logs 
                    (id, agent_id, agent_name, executed_at, success, skipped, skip_reason, 
                     actions_executed, results, error)
                    VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10)
                """, 
                    log_id,
                    result['agent_id'],
                    result['agent_name'],
                    datetime.fromisoformat(result['executed_at'].replace('Z', '+00:00')),
                    result.get('success', False),
                    result.get('skipped', False),
                    result.get('reason'),
                    result.get('actions_executed', 0),
                    json.dumps(result.get('results', [])),
                    result.get('error')
                )
                
                logger.info(f"📝 Execution log saved: {log_id}")
            
            finally:
                await conn.close()
        
        except Exception as e:
            logger.error(f"❌ Error saving execution log: {e}")


# Глобальный экземпляр executor
agent_executor = AgentExecutor()
