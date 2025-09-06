import os
import asyncio
from typing import Dict, Any, List, Optional
from loguru import logger
import httpx
from dotenv import load_dotenv
from emergentintegrations.llm.chat import LlmChat, UserMessage

# Load environment variables
load_dotenv()

class AIService:
    """AI Service using Emergent LLM integration for smart responses"""
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.model = "gpt-4o-mini"  # Default model
        self.provider = "openai"
        self.system_message = """Ты - AI-помощник компании ВасДом, которая занимается:
- Уборкой подъездов и придомовых территорий
- Управлением недвижимостью  
- Клининговыми услугами
- Работой с ЖКХ

Отвечай дружелюбно, профессионально и по-русски. Помогай клиентам с:
- Вопросами об услугах
- Записью на уборку
- Информацией о ценах
- Решением проблем

Если нужна дополнительная информация, предложи связаться с менеджером."""
        
        if not api_key:
            logger.warning("⚠️ AI Service initialized without API key")
    
    async def health_check(self) -> Dict[str, Any]:
        """Check AI service health"""
        if not self.api_key:
            return {"status": "not_configured", "api_key": False}
        
        try:
            # Test with a simple request
            response = await self.generate_response("Тест")
            return {
                "status": "healthy",
                "api_key": True,
                "model": self.model,
                "provider": self.provider,
                "test_response_length": len(response)
            }
        except Exception as e:
            return {"status": "unhealthy", "error": str(e)}
    
    async def generate_response(self, user_message: str, context: str = "") -> str:
        """Generate AI response for user message"""
        if not self.api_key:
            return "🤖 AI сервис временно недоступен. Попробуйте позже."
        
        try:
            # Create system message with context
            system_msg = self.system_message
            if context:
                system_msg += f"\n\nКонтекст: {context}"
            
            # Initialize chat
            chat = LlmChat(
                api_key=self.api_key,
                session_id=f"vasdom_chat_{hash(user_message)}",
                system_message=system_msg
            ).with_model(self.provider, self.model)
            
            # Create user message
            message = UserMessage(text=user_message)
            
            # Get response
            response = await chat.send_message(message)
            
            if response and hasattr(response, 'text'):
                return response.text
            elif isinstance(response, str):
                return response
            else:
                return str(response)
                
        except Exception as e:
            logger.error(f"❌ AI generation error: {e}")
            return f"🤖 Извините, произошла ошибка при обработке запроса. Попробуйте еще раз или обратитесь к менеджеру."
    
    async def generate_smart_reply(self, user_message: str, user_data: Dict = None) -> str:
        """Generate context-aware smart reply"""
        
        # Build context from user data
        context_parts = []
        if user_data:
            if user_data.get("name"):
                context_parts.append(f"Имя пользователя: {user_data['name']}")
            if user_data.get("phone"):
                context_parts.append(f"Телефон: {user_data['phone']}")
            if user_data.get("address"):
                context_parts.append(f"Адрес: {user_data['address']}")
            if user_data.get("previous_requests"):
                context_parts.append(f"Предыдущие обращения: {user_data['previous_requests']}")
        
        context = "; ".join(context_parts) if context_parts else ""
        
        return await self.generate_response(user_message, context)
    
    async def analyze_user_intent(self, message: str) -> Dict[str, Any]:
        """Analyze user intent from message"""
        if not self.api_key:
            return {"intent": "unknown", "confidence": 0.0}
        
        try:
            analysis_prompt = f"""Проанализируй намерения пользователя в сообщении: "{message}"

Определи категорию:
- cleaning_request: хочет заказать уборку
- price_inquiry: спрашивает о ценах
- complaint: жалоба или проблема  
- general_info: общая информация
- support_request: нужна помощь менеджера
- other: другое

Ответь в формате: категория|уверенность(0-1)|краткое_объяснение"""
            
            response = await self.generate_response(analysis_prompt)
            
            # Parse response
            parts = response.split("|")
            if len(parts) >= 3:
                return {
                    "intent": parts[0].strip(),
                    "confidence": float(parts[1].strip()),
                    "explanation": parts[2].strip()
                }
            else:
                return {"intent": "other", "confidence": 0.5, "explanation": "Не удалось точно определить"}
                
        except Exception as e:
            logger.error(f"❌ Intent analysis error: {e}")
            return {"intent": "unknown", "confidence": 0.0, "explanation": str(e)}
    
    async def generate_summary(self, conversation: List[Dict]) -> str:
        """Generate conversation summary"""
        if not self.client or not conversation:
            return "Краткий разговор без особенностей"
        
        try:
            # Format conversation
            conv_text = "\n".join([
                f"{msg.get('sender', 'User')}: {msg.get('text', '')}"
                for msg in conversation[-10:]  # Last 10 messages
            ])
            
            summary_prompt = f"""Составь краткое резюме разговора с клиентом:

{conv_text}

Укажи:
- Основные вопросы клиента
- Предоставленные ответы
- Необходимые действия
- Статус обращения

Ответь кратко, до 200 слов."""
            
            return await self.generate_response(summary_prompt)
            
        except Exception as e:
            logger.error(f"❌ Summary generation error: {e}")
            return f"Ошибка при создании резюме: {str(e)}"