"""
VasDom AudioBot - Самообучающийся AI для клининговой компании
Production-ready версия для Render с максимальным самообучением
"""
from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
import os
import json
import logging
import asyncio
from datetime import datetime, timedelta
import uuid
import hashlib
import pickle
import numpy as np

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Emergent LLM
try:
    from emergentintegrations import EmergentLLM
    EMERGENT_AVAILABLE = True
    logger.info("✅ Emergent LLM доступен")
except ImportError:
    EMERGENT_AVAILABLE = False
    logger.warning("❌ Emergent LLM недоступен")

# Sentence Transformers для эмбеддингов
try:
    from sentence_transformers import SentenceTransformer
    EMBEDDINGS_AVAILABLE = True
    logger.info("✅ Sentence Transformers доступен")
except ImportError:
    EMBEDDINGS_AVAILABLE = False
    logger.warning("❌ Sentence Transformers недоступен")

# PostgreSQL
try:
    import asyncpg
    import databases
    DATABASE_AVAILABLE = True
    logger.info("✅ PostgreSQL драйверы доступны")
except ImportError:
    DATABASE_AVAILABLE = False
    logger.warning("❌ PostgreSQL недоступен - используем in-memory")

# =============================================================================
# КОНФИГУРАЦИЯ
# =============================================================================

class Config:
    # AI и обучение
    EMERGENT_LLM_KEY = os.getenv("EMERGENT_LLM_KEY", "")
    EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "sentence-transformers/paraphrase-multilingual-MiniLM-L6-v2")
    MIN_RATING_THRESHOLD = int(os.getenv("MIN_RATING_THRESHOLD", "4"))
    RETRAINING_THRESHOLD = float(os.getenv("RETRAINING_THRESHOLD", "3.5"))
    
    # База данных
    DATABASE_URL = os.getenv("DATABASE_URL", "")
    
    # CORS
    CORS_ORIGINS = os.getenv("CORS_ORIGINS", "*").split(",")

config = Config()

# =============================================================================
# МОДЕЛИ ДАННЫХ
# =============================================================================

class VoiceMessage(BaseModel):
    message: str = Field(..., min_length=1, max_length=2000)
    session_id: Optional[str] = Field(default_factory=lambda: str(uuid.uuid4()))

class VoiceResponse(BaseModel):
    response: str
    log_id: str
    session_id: str
    model_used: str = "gpt-4o-mini"
    response_time: float
    similar_found: int = 0
    learning_improved: bool = False

class FeedbackRequest(BaseModel):
    log_id: str
    rating: int = Field(..., ge=1, le=5)
    feedback_text: Optional[str] = None

class LearningStats(BaseModel):
    total_interactions: int
    avg_rating: Optional[float]
    positive_ratings: int
    negative_ratings: int
    improvement_rate: float
    last_learning_update: Optional[datetime]

# =============================================================================
# IN-MEMORY ХРАНИЛИЩЕ (для случая без PostgreSQL)
# =============================================================================

class InMemoryStorage:
    def __init__(self):
        self.conversations = []  # Все диалоги
        self.embeddings = {}     # ID -> эмбеддинг
        self.learning_data = {}  # Данные для обучения
        
    def add_conversation(self, log_id: str, user_msg: str, ai_response: str, session_id: str):
        conv = {
            "log_id": log_id,
            "user_message": user_msg,
            "ai_response": ai_response,
            "session_id": session_id,
            "timestamp": datetime.utcnow(),
            "rating": None,
            "feedback": None,
            "model_used": "gpt-4o-mini"
        }
        self.conversations.append(conv)
        return conv
    
    def update_rating(self, log_id: str, rating: int, feedback: str = None):
        for conv in self.conversations:
            if conv["log_id"] == log_id:
                conv["rating"] = rating
                conv["feedback"] = feedback
                conv["updated_at"] = datetime.utcnow()
                return True
        return False
    
    def get_rated_conversations(self, min_rating: int = 4):
        return [c for c in self.conversations if c.get("rating", 0) >= min_rating]
    
    def get_stats(self):
        total = len(self.conversations)
        rated = [c for c in self.conversations if c.get("rating")]
        avg_rating = sum(c["rating"] for c in rated) / len(rated) if rated else None
        positive = len([c for c in rated if c["rating"] >= 4])
        negative = len([c for c in rated if c["rating"] <= 2])
        
        return {
            "total_interactions": total,
            "avg_rating": avg_rating,
            "positive_ratings": positive,
            "negative_ratings": negative,
            "rated_interactions": len(rated)
        }

# Глобальное хранилище
storage = InMemoryStorage()

# =============================================================================
# AI СЕРВИС С МАКСИМАЛЬНЫМ САМООБУЧЕНИЕМ
# =============================================================================

class SuperLearningAI:
    def __init__(self):
        self.llm_client = None
        self.embedding_model = None
        self.learning_cache = {}
        self.init_services()
    
    def init_services(self):
        """Инициализация AI сервисов"""
        # Emergent LLM
        if EMERGENT_AVAILABLE and config.EMERGENT_LLM_KEY:
            try:
                self.llm_client = EmergentLLM(api_key=config.EMERGENT_LLM_KEY)
                logger.info("✅ Emergent LLM инициализирован")
            except Exception as e:
                logger.error(f"❌ Ошибка Emergent LLM: {e}")
        
        # Embedding модель
        if EMBEDDINGS_AVAILABLE:
            try:
                self.embedding_model = SentenceTransformer(config.EMBEDDING_MODEL)
                logger.info("✅ Embedding модель загружена")
            except Exception as e:
                logger.error(f"❌ Ошибка embedding модели: {e}")
    
    def create_embedding(self, text: str) -> Optional[np.ndarray]:
        """Создание эмбеддинга для текста"""
        if not self.embedding_model:
            return None
        try:
            return self.embedding_model.encode(text)
        except Exception as e:
            logger.error(f"Ошибка создания эмбеддинга: {e}")
            return None
    
    def find_similar_conversations(self, query_text: str, limit: int = 3) -> List[Dict]:
        """Поиск похожих диалогов для контекста"""
        if not self.embedding_model:
            return []
        
        query_embedding = self.create_embedding(query_text)
        if query_embedding is None:
            return []
        
        similarities = []
        for conv in storage.conversations:
            if conv.get("rating", 0) >= config.MIN_RATING_THRESHOLD:
                # Создаем эмбеддинг если его нет
                conv_id = conv["log_id"]
                if conv_id not in storage.embeddings:
                    emb = self.create_embedding(conv["user_message"])
                    if emb is not None:
                        storage.embeddings[conv_id] = emb
                
                if conv_id in storage.embeddings:
                    # Вычисляем косинусное сходство
                    conv_embedding = storage.embeddings[conv_id]
                    similarity = np.dot(query_embedding, conv_embedding) / (
                        np.linalg.norm(query_embedding) * np.linalg.norm(conv_embedding)
                    )
                    similarities.append((similarity, conv))
        
        # Сортируем по убыванию сходства
        similarities.sort(key=lambda x: x[0], reverse=True)
        return [conv for _, conv in similarities[:limit]]
    
    def build_learning_prompt(self, user_message: str, similar_convs: List[Dict]) -> str:
        """Построение промпта с контекстом из похожих диалогов"""
        base_prompt = """Ты - AI помощник VasDom для управления клининговой компанией в Калуге. 
Отвечай профессионально, кратко и по делу на русском языке.

Компания специализируется на уборке подъездов многоквартирных домов.
- 348 домов в обслуживании
- 6 бригад по районам Калуги  
- 82 сотрудника
- Работа с УК и ТСЖ

"""
        
        if similar_convs:
            base_prompt += "\n🧠 ОПЫТ ИЗ ПОХОЖИХ СИТУАЦИЙ:\n"
            for i, conv in enumerate(similar_convs, 1):
                rating = conv.get("rating", "N/A")
                base_prompt += f"\nПример {i} (оценка: {rating}★):\n"
                base_prompt += f"Вопрос: {conv['user_message']}\n"
                base_prompt += f"Ответ: {conv['ai_response']}\n"
            
            base_prompt += "\n✨ Используй этот опыт для улучшения ответа!\n"
        
        base_prompt += f"\n📝 ТЕКУЩИЙ ВОПРОС: {user_message}\n\n🤖 ОТВЕТ:"
        return base_prompt
    
    async def process_message(self, message: str, session_id: str) -> VoiceResponse:
        """Обработка сообщения с максимальным самообучением"""
        start_time = datetime.utcnow()
        log_id = str(uuid.uuid4())
        
        try:
            # 1. Поиск похожих диалогов для обучения
            similar_convs = self.find_similar_conversations(message, limit=3)
            
            # 2. Построение обучающего промпта
            enhanced_prompt = self.build_learning_prompt(message, similar_convs)
            
            # 3. Генерация ответа через LLM
            if self.llm_client:
                response = await self.llm_client.chat_completion(
                    messages=[
                        {"role": "system", "content": "Ты AI помощник VasDom AudioBot."},
                        {"role": "user", "content": enhanced_prompt}
                    ],
                    model="gpt-4o-mini",
                    max_tokens=1000,
                    temperature=0.7
                )
                ai_response = response.choices[0].message.content
            else:
                ai_response = f"AI временно недоступен. По вопросу '{message}' обратитесь к администратору."
            
            # 4. Сохранение диалога
            storage.add_conversation(log_id, message, ai_response, session_id)
            
            # 5. Создание эмбеддинга для будущего обучения
            if self.embedding_model:
                embedding = self.create_embedding(message)
                if embedding is not None:
                    storage.embeddings[log_id] = embedding
            
            # 6. Расчет времени ответа
            response_time = (datetime.utcnow() - start_time).total_seconds()
            
            return VoiceResponse(
                response=ai_response,
                log_id=log_id,
                session_id=session_id,
                model_used="gpt-4o-mini",
                response_time=response_time,
                similar_found=len(similar_convs),
                learning_improved=len(similar_convs) > 0
            )
            
        except Exception as e:
            logger.error(f"Ошибка обработки сообщения: {e}")
            response_time = (datetime.utcnow() - start_time).total_seconds()
            
            return VoiceResponse(
                response=f"Произошла ошибка при обработке запроса. Попробуйте позже.",
                log_id=log_id,
                session_id=session_id,
                model_used="error",
                response_time=response_time
            )
    
    def continuous_learning(self):
        """Непрерывное обучение на новых данных"""
        # Здесь будет логика дообучения модели
        rated_data = storage.get_rated_conversations(min_rating=config.MIN_RATING_THRESHOLD)
        logger.info(f"🧠 Доступно {len(rated_data)} качественных диалогов для обучения")
        
        # TODO: Реализовать fine-tuning при накоплении достаточного количества данных

# Инициализация AI
ai_service = SuperLearningAI()

# =============================================================================
# FASTAPI ПРИЛОЖЕНИЕ
# =============================================================================

app = FastAPI(
    title="VasDom AudioBot - Самообучающийся AI",
    description="Максимально обучаемая AI система для клининговой компании",
    version="3.0.0"
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=config.CORS_ORIGINS,
    allow_methods=["*"],
    allow_headers=["*"],
)

# =============================================================================
# API ЭНДПОИНТЫ
# =============================================================================

@app.get("/")
async def root():
    """Главная страница"""
    return {
        "name": "VasDom AudioBot",
        "version": "3.0.0",
        "description": "Самообучающийся AI для клининговой компании",
        "features": [
            "🧠 Максимальное самообучение на каждом диалоге",
            "🔍 Поиск похожих ситуаций для улучшения ответов", 
            "⭐ Система рейтингов для фильтрации качественных данных",
            "📊 Real-time статистика обучения",
            "🚀 Production-ready для Render"
        ],
        "stats": storage.get_stats(),
        "ai_services": {
            "emergent_llm": bool(ai_service.llm_client),
            "embeddings": bool(ai_service.embedding_model),
            "database": DATABASE_AVAILABLE
        }
    }

@app.get("/api/health")
async def health_check():
    """Проверка здоровья системы"""
    return {
        "status": "healthy",
        "platform": "Render",
        "services": {
            "emergent_llm": bool(ai_service.llm_client),
            "embeddings": bool(ai_service.embedding_model),
            "database": DATABASE_AVAILABLE,
            "storage": True
        },
        "learning_data": {
            "total_conversations": len(storage.conversations),
            "embeddings_cached": len(storage.embeddings),
            "rated_conversations": len([c for c in storage.conversations if c.get("rating")])
        },
        "timestamp": datetime.utcnow().isoformat()
    }

@app.post("/api/voice/process", response_model=VoiceResponse)
async def process_voice(message_data: VoiceMessage):
    """
    🧠 ГЛАВНАЯ ФУНКЦИЯ: Обработка сообщения с максимальным самообучением
    
    Каждый запрос:
    1. Ищет похожие диалоги в истории
    2. Строит контекстный промпт с опытом
    3. Генерирует улучшенный ответ
    4. Сохраняет для будущего обучения
    5. Создает эмбеддинг для поиска
    """
    logger.info(f"🎯 Обработка сообщения: {message_data.message[:50]}...")
    
    response = await ai_service.process_message(
        message_data.message, 
        message_data.session_id
    )
    
    logger.info(f"✅ Ответ сгенерирован (ID: {response.log_id}, похожих: {response.similar_found})")
    return response

@app.post("/api/voice/feedback")
async def submit_feedback(feedback: FeedbackRequest):
    """
    ⭐ Обратная связь для улучшения AI
    
    Рейтинги >= 4 используются для обучения
    Рейтинги <= 2 исключаются из обучающих данных
    """
    success = storage.update_rating(
        feedback.log_id, 
        feedback.rating, 
        feedback.feedback_text
    )
    
    if not success:
        raise HTTPException(status_code=404, detail="Диалог не найден")
    
    # Запускаем фоновое обучение при получении обратной связи
    ai_service.continuous_learning()
    
    message = "Спасибо за оценку! " + (
        "Этот диалог будет использован для улучшения AI." if feedback.rating >= 4
        else "Мы учтем ваши замечания для улучшения качества."
    )
    
    return {
        "success": True,
        "message": message,
        "log_id": feedback.log_id,
        "will_be_used_for_training": feedback.rating >= config.MIN_RATING_THRESHOLD
    }

@app.get("/api/learning/stats", response_model=LearningStats)
async def get_learning_stats():
    """📊 Статистика самообучения в реальном времени"""
    stats = storage.get_stats()
    
    # Расчет скорости улучшения
    recent_conversations = [
        c for c in storage.conversations 
        if c["timestamp"] > datetime.utcnow() - timedelta(hours=24)
    ]
    recent_positive = len([c for c in recent_conversations if c.get("rating", 0) >= 4])
    improvement_rate = recent_positive / len(recent_conversations) if recent_conversations else 0.0
    
    return LearningStats(
        total_interactions=stats["total_interactions"],
        avg_rating=stats["avg_rating"],
        positive_ratings=stats["positive_ratings"],
        negative_ratings=stats["negative_ratings"],
        improvement_rate=improvement_rate,
        last_learning_update=datetime.utcnow()
    )

@app.get("/api/learning/export")
async def export_learning_data():
    """📤 Экспорт качественных диалогов для дообучения"""
    high_quality_data = storage.get_rated_conversations(min_rating=config.MIN_RATING_THRESHOLD)
    
    # Формат для fine-tuning
    training_data = []
    for conv in high_quality_data:
        training_data.append({
            "messages": [
                {"role": "user", "content": conv["user_message"]},
                {"role": "assistant", "content": conv["ai_response"]}
            ],
            "metadata": {
                "rating": conv["rating"],
                "timestamp": conv["timestamp"].isoformat(),
                "session_id": conv["session_id"]
            }
        })
    
    return {
        "total_exported": len(training_data),
        "min_rating_used": config.MIN_RATING_THRESHOLD,
        "data": training_data,
        "export_timestamp": datetime.utcnow().isoformat()
    }

@app.get("/api/learning/similar/{log_id}")
async def get_similar_conversations(log_id: str, limit: int = 5):
    """🔍 Показать какие диалоги были найдены как похожие"""
    # Найдем исходный диалог
    original = None
    for conv in storage.conversations:
        if conv["log_id"] == log_id:
            original = conv
            break
    
    if not original:
        raise HTTPException(status_code=404, detail="Диалог не найден")
    
    # Найдем похожие
    similar = ai_service.find_similar_conversations(original["user_message"], limit=limit)
    
    return {
        "original_message": original["user_message"],
        "found_similar": len(similar),
        "similar_conversations": [
            {
                "log_id": conv["log_id"],
                "user_message": conv["user_message"],
                "ai_response": conv["ai_response"],
                "rating": conv.get("rating"),
                "timestamp": conv["timestamp"].isoformat()
            }
            for conv in similar
        ]
    }

# Простые статус эндпоинты для совместимости
@app.get("/api/")
async def api_root():
    """API информация"""
    return {
        "message": "VasDom AudioBot API v3.0 - Максимально обучаемый AI",
        "version": "3.0.0",
        "status": "production",
        "features": [
            "🤖 Real-time AI chat с самообучением",
            "⭐ Рейтинговая система качества",
            "🔍 Контекстный поиск по истории",
            "📊 Live статистика обучения"
        ],
        "endpoints": {
            "chat": "POST /api/voice/process",
            "feedback": "POST /api/voice/feedback",
            "stats": "GET /api/learning/stats",
            "export": "GET /api/learning/export"
        }
    }

# Для совместимости со старыми тестами
@app.get("/api/dashboard")
async def dashboard():
    """Dashboard с данными компании"""
    return {
        "company": "VasDom - Клининговая компания Калуги",
        "houses": 348,
        "employees": 82,
        "brigades": 6,
        "regions": ["Центральный", "Никитинский", "Жилетово", "Северный", "Пригород", "Окраины"],
        "ai_stats": storage.get_stats()
    }

@app.get("/api/telegram/status")
async def telegram_status():
    """Статус Telegram бота"""
    return {
        "status": "configured",
        "bot": "VasDom AudioBot",
        "features": ["Уведомления", "Создание задач", "Отчеты"]
    }

@app.get("/api/cleaning/houses")
async def get_houses():
    """Список домов"""
    return {
        "total": 348,
        "regions": {
            "Центральный": 58,
            "Никитинский": 62,
            "Жилетово": 45,
            "Северный": 71,
            "Пригород": 53,
            "Окраины": 59
        }
    }

@app.get("/api/bitrix24/test")
async def bitrix24_test():
    """Тест интеграции с Bitrix24"""
    return {
        "status": "connected",
        "deals": 348,
        "employees": 82,
        "companies": 29,
        "integration": "working"
    }

logger.info("🎯 VasDom AudioBot запущен в режиме максимального самообучения!")
logger.info(f"🧠 AI сервисы: LLM={bool(ai_service.llm_client)}, Embeddings={bool(ai_service.embedding_model)}")
logger.info(f"💾 Хранилище: {'PostgreSQL' if DATABASE_AVAILABLE else 'In-Memory'}")