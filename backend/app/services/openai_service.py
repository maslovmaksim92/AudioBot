"""
Сервис для работы с OpenAI GPT-4o
AI агент для VasDom с функциями-инструментами
"""
import os
import json
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime, date
from dotenv import load_dotenv
from openai import AsyncOpenAI

load_dotenv()
logger = logging.getLogger(__name__)

class VasDomAIAgent:
    """AI агент VasDom с доступом к данным компании"""
    
    def __init__(self):
        # Используем напрямую OpenAI API ключ (настроен на Render)
        self.api_key = os.getenv("OPENAI_API_KEY")
        if not self.api_key or self.api_key == "sk-test-placeholder":
            logger.warning("OPENAI_API_KEY не настроен! Используйте реальный ключ на Render")
        self.model = "gpt-4o"  # GPT-4o с function calling
        self.client = AsyncOpenAI(api_key=self.api_key)
        
        # Системный промпт для AI агента
        self.system_prompt = """Ты - интеллектуальный AI ассистент компании VasDom (клининговая компания).

Твоя роль:
- Помогать сотрудникам с вопросами о графиках уборки домов
- Предоставлять информацию о загрузке бригад
- Создавать и планировать задачи
- Отправлять графики управляющим компаниям

У тебя есть доступ к следующим функциям для получения данных:
1. get_houses_for_date - получить список домов на определенную дату
2. get_brigade_workload - получить загрузку конкретной бригады
3. get_house_details - получить детали по конкретному дому
4. create_ai_task - создать AI задачу (напоминание, отчет, отправка графика)
5. send_schedule_email - отправить график на email управляющей компании

Всегда отвечай на русском языке, будь профессиональным и дружелюбным.
Используй функции когда нужна информация из базы данных.
Если не хватает информации для вызова функции - спрашивай у пользователя."""

        # Определение функций-инструментов для GPT
        self.tools = [
            {
                "type": "function",
                "function": {
                    "name": "get_houses_for_date",
                    "description": "Получить список домов, которые нужно убрать на указанную дату",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "date": {
                                "type": "string",
                                "description": "Дата в формате YYYY-MM-DD"
                            },
                            "brigade_number": {
                                "type": "string",
                                "description": "Номер бригады (опционально, для фильтрации)"
                            }
                        },
                        "required": ["date"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "get_brigade_workload",
                    "description": "Получить информацию о загрузке бригады: количество домов, подъездов, этажей",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "brigade_number": {
                                "type": "string",
                                "description": "Номер бригады (1-7)"
                            },
                            "date": {
                                "type": "string",
                                "description": "Дата для проверки загрузки (YYYY-MM-DD), по умолчанию сегодня"
                            }
                        },
                        "required": ["brigade_number"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "get_house_details",
                    "description": "Получить детальную информацию о конкретном доме",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "house_id": {
                                "type": "string",
                                "description": "ID дома в Bitrix24"
                            }
                        },
                        "required": ["house_id"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "create_ai_task",
                    "description": "Создать AI задачу (напоминание, отчет, уведомление)",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "task_type": {
                                "type": "string",
                                "enum": ["reminder", "report", "notification", "send_schedule", "custom"],
                                "description": "Тип задачи"
                            },
                            "title": {
                                "type": "string",
                                "description": "Заголовок задачи"
                            },
                            "description": {
                                "type": "string",
                                "description": "Описание задачи"
                            },
                            "scheduled_at": {
                                "type": "string",
                                "description": "Дата и время выполнения (ISO format)"
                            }
                        },
                        "required": ["task_type", "title"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "send_schedule_email",
                    "description": "Отправить график уборки на email управляющей компании",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "email": {
                                "type": "string",
                                "description": "Email управляющей компании"
                            },
                            "date_from": {
                                "type": "string",
                                "description": "Начальная дата периода (YYYY-MM-DD)"
                            },
                            "date_to": {
                                "type": "string",
                                "description": "Конечная дата периода (YYYY-MM-DD)"
                            },
                            "company_title": {
                                "type": "string",
                                "description": "Название управляющей компании"
                            }
                        },
                        "required": ["email", "date_from", "date_to"]
                    }
                }
            }
        ]
    
    async def chat(
        self,
        messages: List[Dict[str, str]],
        user_id: str,
        function_handlers: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Отправить сообщение AI агенту и получить ответ с поддержкой native OpenAI function calling
        
        Args:
            messages: История сообщений [{"role": "user", "content": "..."}]
            user_id: ID пользователя
            function_handlers: Словарь обработчиков функций
            
        Returns:
            {
                "content": "ответ AI",
                "function_calls": [...],
                "usage": {...}
            }
        """
        try:
            # Добавляем системный промпт
            full_messages = [{"role": "system", "content": self.system_prompt}] + messages
            
            # Первый вызов GPT-4o с tools
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=full_messages,
                tools=self.tools,
                tool_choice="auto",
                temperature=0.7,
                max_tokens=2000
            )
            
            message = response.choices[0].message
            
            # Если AI вызывает функции
            if message.tool_calls:
                logger.info(f"AI вызывает {len(message.tool_calls)} функций")
                
                function_responses = []
                function_results = []
                
                for tool_call in message.tool_calls:
                    function_name = tool_call.function.name
                    function_args = json.loads(tool_call.function.arguments)
                    
                    logger.info(f"Вызов: {function_name}({function_args})")
                    
                    # Вызываем обработчик
                    if function_name in function_handlers:
                        result = await function_handlers[function_name](**function_args, user_id=user_id)
                        function_responses.append({
                            "tool_call_id": tool_call.id,
                            "role": "tool",
                            "name": function_name,
                            "content": json.dumps(result, ensure_ascii=False)
                        })
                        function_results.append({
                            "name": function_name,
                            "arguments": function_args,
                            "result": result
                        })
                    else:
                        function_responses.append({
                            "tool_call_id": tool_call.id,
                            "role": "tool",
                            "name": function_name,
                            "content": json.dumps({"error": "Функция не найдена"}, ensure_ascii=False)
                        })
                
                # Добавляем ответ assistant и результаты функций
                full_messages.append({
                    "role": "assistant",
                    "content": message.content,
                    "tool_calls": [
                        {
                            "id": tc.id,
                            "type": "function",
                            "function": {
                                "name": tc.function.name,
                                "arguments": tc.function.arguments
                            }
                        }
                        for tc in message.tool_calls
                    ]
                })
                full_messages.extend(function_responses)
                
                # Второй вызов для финального ответа
                final_response = await self.client.chat.completions.create(
                    model=self.model,
                    messages=full_messages,
                    temperature=0.7,
                    max_tokens=2000
                )
                
                final_message = final_response.choices[0].message
                
                logger.info(f"AI финальный ответ: {final_message.content[:100]}...")
                
                return {
                    "content": final_message.content,
                    "function_calls": function_results,
                    "usage": {
                        "prompt_tokens": response.usage.prompt_tokens + final_response.usage.prompt_tokens,
                        "completion_tokens": response.usage.completion_tokens + final_response.usage.completion_tokens,
                        "total_tokens": response.usage.total_tokens + final_response.usage.total_tokens
                    }
                }
            else:
                # Простой ответ без функций
                logger.info(f"AI ответ (без функций): {message.content[:100]}...")
                
                return {
                    "content": message.content,
                    "function_calls": [],
                    "usage": {
                        "prompt_tokens": response.usage.prompt_tokens,
                        "completion_tokens": response.usage.completion_tokens,
                        "total_tokens": response.usage.total_tokens
                    }
                }
                
        except Exception as e:
            logger.error(f"Ошибка OpenAI: {e}", exc_info=True)
            return {
                "content": f"Извините, произошла ошибка при обработке вашего запроса: {str(e)}",
                "function_calls": [],
                "usage": {}
            }