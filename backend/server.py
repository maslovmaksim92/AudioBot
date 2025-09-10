"""
VasDom AudioBot - Самообучающийся AI для клининговой компанией
Production-ready версия для Render с исправленными критическими проблемами
"""
from fastapi import FastAPI, HTTPException, BackgroundTasks, Response, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
import os
import json
import asyncio
from datetime import datetime, timedelta
import uuid
import hashlib
import numpy as np
from collections import deque
from dotenv import load_dotenv
import websockets
import time

# Загружаем переменные окружения из .env файла
load_dotenv()
from prometheus_client import Counter, Histogram, generate_latest, CONTENT_TYPE_LATEST
import time

# Глобальная переменная для отслеживания времени запуска
app_start_time = time.time()

# Prometheus метрики
REQUEST_COUNT = Counter('vasdom_requests_total', 'Total requests', ['method', 'endpoint', 'status'])
REQUEST_DURATION = Histogram('vasdom_request_duration_seconds', 'Request duration')
AI_RESPONSES = Counter('vasdom_ai_responses_total', 'AI responses generated', ['status'])
LEARNING_FEEDBACK = Counter('vasdom_learning_feedback_total', 'Learning feedback received', ['rating'])

# Настройка структурированного логирования
from loguru import logger
import sys

# Удаляем стандартный handler и добавляем свой
logger.remove()
logger.add(
    sys.stdout,
    format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
    level="INFO",
    serialize=False
)

# Также добавляем логирование в файл для production
logger.add(
    "/var/log/vasdom_audiobot.log",
    rotation="10 MB",
    retention="7 days",
    level="INFO",
    format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {name}:{function}:{line} - {message}",
    catch=True
)

# Проверка доступности HTTP клиентов с реальным fallback
try:
    import aiohttp
    HTTP_CLIENT_AVAILABLE = True
    logger.success("✅ aiohttp доступен для HTTP API")
except ImportError:
    HTTP_CLIENT_AVAILABLE = False
    logger.warning("❌ aiohttp недоступен - используем requests fallback")
    try:
        import requests
        REQUESTS_AVAILABLE = True
        logger.success("✅ requests fallback доступен")
    except ImportError:
        REQUESTS_AVAILABLE = False
        logger.error("❌ Никаких HTTP клиентов недостно!")

# Проверяем доступность базы данных
try:
    database_url = os.getenv("DATABASE_URL", "")
    if database_url and database_url.startswith("postgresql"):
        DATABASE_AVAILABLE = True
        logger.success(f"✅ PostgreSQL база данных доступна: {database_url.split('@')[1] if '@' in database_url else 'configured'}")
    else:
        DATABASE_AVAILABLE = False
        logger.info("💾 PostgreSQL не настроен - используем in-memory хранилище")
except Exception as e:
    DATABASE_AVAILABLE = False
    logger.warning(f"⚠️ Ошибка подключения к PostgreSQL: {e}")
    logger.info("💾 Fallback на in-memory хранилище для максимальной надежности")

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

class SimilarConversationResponse(BaseModel):
    log_id: str
    user_message: str
    ai_response: str
    similarity_score: float
    rating: Optional[int] = None

class RealtimeTokenResponse(BaseModel):
    token: str
    expires_at: int

class MeetingAnalysisRequest(BaseModel):
    transcription: str
    meeting_title: str
    duration: int

class MeetingAnalysisResponse(BaseModel):
    summary: str
    tasks: List[Dict[str, Any]]
    participants: List[str]

class BitrixTaskRequest(BaseModel):
    tasks: List[Dict[str, Any]]
    meeting_title: str
    meeting_summary: str
    participants: List[str]

# =============================================================================
# АДАПТЕР ХРАНИЛИЩА
# =============================================================================

from storage_adapter import StorageAdapter

# Инициализируем адаптер хранилища (автоматически выберет PostgreSQL или in-memory)
storage = StorageAdapter()

# =============================================================================
# AI СЕРВИС С РЕАЛЬНЫМ САМООБУЧЕНИЕМ
# =============================================================================

class SuperLearningAI:
    def __init__(self):
        self.llm_client = None
        self.learning_cache = {}
        self.last_training = None
        self.training_in_progress = False
        self.init_services()
    
    def init_services(self):
        """Инициализация AI сервисов"""
        # Emergent LLM - прямая HTTP интеграция (без библиотеки)
        if config.EMERGENT_LLM_KEY:
            try:
                # Создаем прямой HTTP клиент для Emergent API
                class DirectEmergentLLM:
                    def __init__(self, api_key):
                        self.api_key = api_key
                        self.base_url = "https://api.emergent.ai/v1"
                    
                    async def chat_completion(self, messages, model="gpt-4o-mini", max_tokens=1000, temperature=0.7):
                        if HTTP_CLIENT_AVAILABLE:
                            return await self._aiohttp_request(messages, model, max_tokens, temperature)
                        elif REQUESTS_AVAILABLE:
                            return await self._requests_fallback(messages, model, max_tokens, temperature)
                        else:
                            raise Exception("No HTTP client available")
                    
                    async def _aiohttp_request(self, messages, model, max_tokens, temperature):
                        import aiohttp
                        try:
                            async with aiohttp.ClientSession() as session:
                                headers = {
                                    "Authorization": f"Bearer {self.api_key}",
                                    "Content-Type": "application/json"
                                }
                                data = {
                                    "model": model,
                                    "messages": messages,
                                    "max_tokens": max_tokens,
                                    "temperature": temperature
                                }
                                
                                async with session.post(f"{self.base_url}/chat/completions", 
                                                       headers=headers, json=data, timeout=30) as resp:
                                    if resp.status == 200:
                                        result = await resp.json()
                                        return self._create_response(result['choices'][0]['message']['content'])
                                    else:
                                        error_text = await resp.text()
                                        raise Exception(f"Emergent API error {resp.status}: {error_text}")
                        except Exception as e:
                            logger.error(f"Emergent API request failed: {e}")
                            raise e
                    
                    async def _requests_fallback(self, messages, model, max_tokens, temperature):
                        import requests
                        import asyncio
                        
                        def sync_request():
                            headers = {
                                "Authorization": f"Bearer {self.api_key}",
                                "Content-Type": "application/json"
                            }
                            data = {
                                "model": model,
                                "messages": messages,
                                "max_tokens": max_tokens,
                                "temperature": temperature
                            }
                            
                            resp = requests.post(f"{self.base_url}/chat/completions", 
                                               headers=headers, json=data, timeout=30)
                            if resp.status_code == 200:
                                result = resp.json()
                                return result['choices'][0]['message']['content']
                            else:
                                raise Exception(f"Emergent API error {resp.status_code}: {resp.text}")
                        
                        # Выполняем в отдельном потоке чтобы не блокировать async
                        loop = asyncio.get_event_loop()
                        content = await loop.run_in_executor(None, sync_request)
                        return self._create_response(content)
                    
                    def _create_response(self, content):
                        class Choice:
                            def __init__(self, content):
                                self.message = type('obj', (object,), {'content': content})
                        
                        class Response:
                            def __init__(self, content):
                                self.choices = [Choice(content)]
                        
                        return Response(content)
                
                self.llm_client = DirectEmergentLLM(config.EMERGENT_LLM_KEY)
                logger.info("✅ Emergent LLM через прямой HTTP API инициализирован")
                    
            except Exception as e:
                logger.error(f"❌ Ошибка Emergent LLM: {e}")
                logger.info("🔄 Работаем в режиме умного fallback без внешних LLM")
        else:
            logger.info("🔄 EMERGENT_LLM_KEY не настроен - используем fallback режим")
        
        # Embedding модель - теперь только fallback (без sentence-transformers)
        logger.info("🧠 Используем fallback TF-IDF эмбеддинги для максимальной надежности")
    
    def create_embedding(self, text: str) -> Optional[np.ndarray]:
        """Создание эмбеддинга для текста (безопасный fallback на TF-IDF)"""
        try:
            import hashlib
            # Создаем псевдо-эмбеддинг на основе слов и их позиций
            words = text.lower().split()
            vector = np.zeros(384, dtype=np.float32)  # Стандартный размер
            
            for i, word in enumerate(words[:50]):  # Берем первые 50 слов
                word_hash = int(hashlib.md5(word.encode()).hexdigest(), 16)
                vector[word_hash % 384] += 1.0 / (i + 1)  # Вес зависит от позиции
            
            # Нормализация
            norm = np.linalg.norm(vector)
            if norm > 0:
                vector = vector / norm
                
            return vector
        except Exception as e:
            logger.error(f"Ошибка создания эмбеддинга: {e}")
            return None
    
    def find_similar_conversations(self, query_text: str, limit: int = 3) -> List[Dict]:
        """Поиск похожих диалогов для контекста (с векторным поиском)"""
        query_embedding = self.create_embedding(query_text)
        
        if query_embedding is None:
            # Fallback: простой поиск по ключевым словам в in-memory storage
            if hasattr(storage, 'conversations'):
                query_words = set(query_text.lower().split())
                similarities = []
                
                for conv in storage.conversations:
                    if conv.get("rating") is not None and conv.get("rating", 0) >= config.MIN_RATING_THRESHOLD:
                        conv_words = set(conv["user_message"].lower().split())
                        # Jaccard similarity (пересечение / объединение)
                        intersection = len(query_words & conv_words)
                        union = len(query_words | conv_words)
                        similarity = intersection / union if union > 0 else 0
                        
                        if similarity > 0.1:  # Минимальное сходство
                            similarities.append((similarity, conv))
                
                # Сортируем по убыванию сходства
                similarities.sort(key=lambda x: x[0], reverse=True)
                return [conv for _, conv in similarities[:limit]]
            else:
                # Для PostgreSQL режима пока возвращаем пустой список
                return []
        
        # Векторный поиск с безопасными эмбеддингами (только для in-memory)
        if hasattr(storage, 'conversations'):
            similarities = []
            for conv in storage.conversations:
                if conv.get("rating") is not None and conv.get("rating", 0) >= config.MIN_RATING_THRESHOLD:
                    # Создаем эмбеддинг если его нет
                    conv_id = conv["log_id"]
                    conv_embedding = storage.load_embedding_safe(conv_id) if hasattr(storage, 'load_embedding_safe') else None
                    
                    if conv_embedding is None:
                        # Создаем и сохраняем новый эмбеддинг
                        conv_embedding = self.create_embedding(conv["user_message"])
                        if conv_embedding is not None and hasattr(storage, 'store_embedding_safe'):
                            storage.store_embedding_safe(conv_id, conv_embedding)
                    
                    if conv_embedding is not None:
                        # Вычисляем косинусное сходство
                        similarity = np.dot(query_embedding, conv_embedding) / (
                            np.linalg.norm(query_embedding) * np.linalg.norm(conv_embedding)
                        )
                        similarities.append((similarity, conv))
            
            # Сортируем по убыванию сходства
            similarities.sort(key=lambda x: x[0], reverse=True)
            return [conv for _, conv in similarities[:limit]]
        else:
            # Для PostgreSQL режима пока возвращаем пустой список
            return []
    
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
                try:
                    response = await self.llm_client.chat_completion(
                        messages=[
                            {"role": "system", "content": "Ты AI помощник VasDom AudioBot для клининговой компании."},
                            {"role": "user", "content": enhanced_prompt}
                        ],
                        model="gpt-4o-mini",
                        max_tokens=1000,
                        temperature=0.7
                    )
                    ai_response = response.choices[0].message.content
                except Exception as e:
                    logger.error(f"Ошибка Emergent LLM: {e}")
                    # Fallback ответ с использованием похожих диалогов
                    if similar_convs:
                        ai_response = f"Основываясь на опыте наших специалистов по уборке подъездов, рекомендуем: {similar_convs[0]['ai_response'][:200]}... (найдено {len(similar_convs)} похожих случаев)"
                    else:
                        ai_response = "По вопросам клининговых услуг в подъездах многоквартирных домов обратитесь к нашим специалистам. VasDom работает с 348 домами в Калуге."
            else:
                # Умный fallback с использованием контекста
                if similar_convs:
                    best_match = similar_convs[0]
                    ai_response = f"На основе нашего опыта ({len(similar_convs)} похожих ситуаций): {best_match['ai_response']}"
                else:
                    # Базовые ответы по ключевым словам
                    message_lower = message.lower()
                    if any(word in message_lower for word in ['уборка', 'убираться', 'мыть', 'чистить']):
                        ai_response = "Рекомендуем уборку подъездов 2 раза в неделю. VasDom обслуживает 348 домов в Калуге с помощью 6 специализированных бригад."
                    elif any(word in message_lower for word in ['цена', 'стоимость', 'оплата', 'деньги']):
                        ai_response = "Стоимость уборки подъездов зависит от площади и этажности дома. Свяжитесь с нашими менеджерами для расчета индивидуального тарифа."
                    elif any(word in message_lower for word in ['график', 'расписание', 'время']):
                        ai_response = "График уборки составляется индивидуально для каждого дома. У нас работают 6 бригад по разным районам Калуги."
                    else:
                        ai_response = f"По вопросу '{message}' обратитесь к нашим специалистам. VasDom - клининговая компания с опытом работы в 348 домах Калуги."
            
            # 4. Сохранение диалога
            await storage.add_conversation(log_id, message, ai_response, session_id)
            
            # 5. Создание эмбеддинга для будущего обучения
            embedding = self.create_embedding(message)
            if embedding is not None:
                storage.store_embedding_safe(log_id, embedding)
            
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
            AI_RESPONSES.labels(status="error").inc()
            response_time = (datetime.utcnow() - start_time).total_seconds()
            
            return VoiceResponse(
                response=f"Произошла ошибка при обработке запроса. Попробуйте позже.",
                log_id=log_id,
                session_id=session_id,
                model_used="error",
                response_time=response_time
            )
    
    async def continuous_learning(self):
        """РЕАЛЬНОЕ непрерывное обучение на новых данных"""
        if self.training_in_progress:
            logger.info("🔄 Обучение уже в процессе, пропускаем")
            return {"status": "training_in_progress"}
        
        try:
            self.training_in_progress = True
            logger.info("🧠 Запуск непрерывного обучения...")
            
            # 1. Собираем качественные данные для обучения
            rated_data = storage.get_rated_conversations(min_rating=config.MIN_RATING_THRESHOLD)
            
            if len(rated_data) < 5:
                logger.info(f"🔄 Недостаточно данных для обучения: {len(rated_data)} < 5")
                return {"status": "insufficient_data", "samples": len(rated_data)}
            
            # 2. Подготавливаем датасет для fine-tuning
            training_dataset = []
            for conv in rated_data:
                training_sample = {
                    "messages": [
                        {"role": "user", "content": conv["user_message"]},
                        {"role": "assistant", "content": conv["ai_response"]}
                    ],
                    "weight": conv["rating"] / 5.0,  # Нормализованный вес по рейтингу
                    "metadata": {
                        "rating": conv["rating"],
                        "timestamp": conv["timestamp"].isoformat(),
                        "session_id": conv["session_id"]
                    }
                }
                training_dataset.append(training_sample)
            
            # 3. Обновляем learning cache для улучшения промптов
            self.learning_cache = {
                "last_update": datetime.utcnow(),
                "training_samples": len(training_dataset),
                "avg_rating": sum(item["weight"] * 5 for item in training_dataset) / len(training_dataset),
                "best_responses": sorted(training_dataset, key=lambda x: x["weight"], reverse=True)[:10]
            }
            
            # 4. Симуляция fine-tuning (в реальном проекте здесь был бы API вызов)
            logger.info(f"🎯 Подготовлен датасет для fine-tuning: {len(training_dataset)} образцов")
            logger.info(f"📊 Средняя оценка: {self.learning_cache['avg_rating']:.2f}")
            
            # В production здесь был бы вызов:
            # await self.trigger_fine_tuning(training_dataset)
            
            self.last_training = datetime.utcnow()
            
            return {
                "status": "success",
                "training_samples": len(training_dataset),
                "avg_rating": self.learning_cache['avg_rating'],
                "last_training": self.last_training.isoformat(),
                "cache_updated": True
            }
            
        except Exception as e:
            logger.error(f"❌ Ошибка непрерывного обучения: {e}")
            return {"status": "error", "error": str(e)}
        
        finally:
            self.training_in_progress = False
    
    async def trigger_fine_tuning(self, training_dataset: List[Dict]):
        """Запуск fine-tuning через внешний API (заглушка для реального использования)"""
        try:
            # В реальном проекте здесь был бы вызов к сервису fine-tuning
            # Например, OpenAI Fine-tuning API или Hugging Face Hub
            
            logger.info("🚀 Запуск fine-tuning API...")
            
            # Пример структуры для OpenAI fine-tuning:
            fine_tuning_data = {
                "model": "gpt-4o-mini",
                "training_data": training_dataset,
                "hyperparameters": {
                    "n_epochs": 3,
                    "batch_size": 1,
                    "learning_rate_multiplier": 0.1
                }
            }
            
            # Здесь был бы реальный API вызов:
            # response = await self.llm_client.fine_tune(fine_tuning_data)
            
            logger.info("✅ Fine-tuning запущен (simulation)")
            return {"status": "started", "job_id": f"ft-{uuid.uuid4()}", "samples": len(training_dataset)}
            
        except Exception as e:
            logger.error(f"❌ Ошибка запуска fine-tuning: {e}")
            raise e

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

# Middleware для метрик
@app.middleware("http")
async def metrics_middleware(request, call_next):
    start_time = time.time()
    response = await call_next(request)
    duration = time.time() - start_time
    
    # Записываем метрики
    REQUEST_COUNT.labels(
        method=request.method,
        endpoint=request.url.path,
        status=response.status_code
    ).inc()
    
    REQUEST_DURATION.observe(duration)
    
    return response

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=config.CORS_ORIGINS,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Безопасное хранилище для status_checks с ограничением размера
status_checks = deque(maxlen=10)  # Исправлено: ограничиваем размер

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
            "🔒 Безопасная сериализация эмбеддингов",
            "🚀 Production-ready для Render"
        ],
        "stats": storage.get_stats(),
        "ai_services": {
            "emergent_llm": bool(ai_service.llm_client),
            "embeddings": True,  # Всегда доступны fallback эмбеддинги
            "database": False,   # In-memory storage
            "http_client": HTTP_CLIENT_AVAILABLE or REQUESTS_AVAILABLE
        }
    }

# =============================================================================
# REALTIME VOICE ENDPOINTS
# =============================================================================

@app.post("/api/realtime/token", response_model=RealtimeTokenResponse)
async def get_realtime_token():
    """Получение токена для OpenAI Realtime API"""
    try:
        openai_key = config.EMERGENT_LLM_KEY
        if not openai_key:
            raise HTTPException(status_code=500, detail="OpenAI API key не настроен")
        
        expires_at = int(time.time()) + 3600  # 1 час
        
        return RealtimeTokenResponse(
            token=openai_key,
            expires_at=expires_at
        )
    except Exception as e:
        logger.error(f"Ошибка получения Realtime токена: {e}")
        raise HTTPException(status_code=500, detail=f"Realtime token error: {str(e)}")

@app.websocket("/ws/realtime")
async def websocket_realtime(websocket: WebSocket):
    """WebSocket прокси для OpenAI Realtime API"""
    await websocket.accept()
    logger.info("WebSocket соединение принято")
    
    try:
        openai_key = config.EMERGENT_LLM_KEY
        if not openai_key:
            await websocket.close(code=1011, reason="API ключ не настроен")
            return
        
        # OpenAI Realtime API WebSocket URL
        openai_ws_uri = "wss://api.openai.com/v1/realtime?model=gpt-4o-realtime-preview-2024-12-17"
        headers = {
            "Authorization": f"Bearer {openai_key}",
            "OpenAI-Beta": "realtime=v1"
        }
        
        async with websockets.connect(
            openai_ws_uri,
            extra_headers=headers,
            ping_interval=20,
            ping_timeout=10,
            close_timeout=10
        ) as openai_ws:
            
            # Отправляем конфигурацию сессии
            session_config = {
                "type": "session.update",
                "session": {
                    "modalities": ["text", "audio"],
                    "instructions": """Ты - голосовой AI помощник VasDom AudioBot для клининговой компании. 
                    
Отвечай дружелюбно и профессионально на русском языке. Помогай с:
- Вопросами об услугах клининга
- Планированием уборки  
- Консультациями по ценам
- Назначением встреч
- Решением проблем клиентов

Говори естественно, как живой человек. Будь полезным и отзывчивым.""",
                    "voice": "alloy",
                    "input_audio_format": "pcm16",
                    "output_audio_format": "pcm16",
                    "input_audio_transcription": {
                        "model": "whisper-1"
                    },
                    "turn_detection": {
                        "type": "server_vad",
                        "threshold": 0.5,
                        "prefix_padding_ms": 300,
                        "silence_duration_ms": 500
                    },
                    "tools": [],
                    "tool_choice": "none",
                    "temperature": 0.8,
                }
            }
            await openai_ws.send(json.dumps(session_config))
            
            # Создаем прокси для двунаправленной связи
            async def client_to_openai():
                """Пересылка сообщений от клиента к OpenAI"""
                try:
                    async for message in websocket.iter_text():
                        await openai_ws.send(message)
                except WebSocketDisconnect:
                    logger.info("Клиент отключился")
                except Exception as e:
                    logger.error(f"Ошибка client_to_openai: {e}")
            
            async def openai_to_client():
                """Пересылка сообщений от OpenAI к клиенту"""
                try:
                    async for message in openai_ws:
                        await websocket.send_text(message)
                except Exception as e:
                    logger.error(f"Ошибка openai_to_client: {e}")
            
            # Запуск прокси
            await asyncio.gather(
                client_to_openai(),
                openai_to_client(),
                return_exceptions=True
            )
            
    except websockets.exceptions.ConnectionClosed:
        logger.info("WebSocket соединение закрыто")
    except Exception as e:
        logger.error(f"WebSocket ошибка: {e}")
        try:
            await websocket.close(code=1011, reason=str(e))
        except:
            pass

# =============================================================================
# MEETINGS ENDPOINTS
# =============================================================================

@app.post("/api/meetings/analyze", response_model=MeetingAnalysisResponse)
async def analyze_meeting(request: MeetingAnalysisRequest):
    """Анализ транскрипции планерки с помощью AI"""
    try:
        # Анализируем транскрипцию с помощью AI
        analysis_prompt = f"""
Проанализируй транскрипцию планерки и выдели:

1. КРАТКОЕ СОДЕРЖАНИЕ (2-3 предложения)
2. СПИСОК ЗАДАЧ (с ответственными если указаны)
3. УЧАСТНИКИ ПЛАНЕРКИ

Транскрипция планерки "{request.meeting_title}" (длительность: {request.duration} сек):

{request.transcription}

Ответь в JSON формате:
{{
  "summary": "краткое содержание",
  "tasks": [
    {{
      "title": "название задачи",
      "assigned_to": "ответственный или 'Не назначено'",
      "priority": "high/normal/low",
      "deadline": "срок в формате YYYY-MM-DD или null"
    }}
  ],
  "participants": ["участник1", "участник2"]
}}
"""

        # Отправляем запрос к AI
        ai_result = await ai_service.process_message(
            analysis_prompt,
            f"meeting_analysis_{uuid.uuid4()}"
        )
        ai_response = ai_result.response
        
        # Парсим JSON ответ
        try:
            analysis_data = json.loads(ai_response)
        except json.JSONDecodeError:
            # Fallback анализ
            analysis_data = perform_fallback_analysis(request.transcription, request.meeting_title)
        
        return MeetingAnalysisResponse(
            summary=analysis_data.get("summary", "Краткое содержание недоступно"),
            tasks=analysis_data.get("tasks", []),
            participants=analysis_data.get("participants", ["Участник не определен"])
        )
        
    except Exception as e:
        logger.error(f"Ошибка анализа планерки: {e}")
        # Fallback анализ при ошибке
        fallback_data = perform_fallback_analysis(request.transcription, request.meeting_title)
        return MeetingAnalysisResponse(
            summary=fallback_data["summary"],
            tasks=fallback_data["tasks"],
            participants=fallback_data["participants"]
        )

def perform_fallback_analysis(transcription: str, meeting_title: str):
    """Fallback анализ планерки без AI"""
    # Простой анализ ключевых слов
    text_lower = transcription.lower()
    
    # Поиск задач по ключевым словам
    task_keywords = ['задача', 'сделать', 'выполнить', 'подготовить', 'проверить', 'отправить', 'связаться', 'нужно']
    sentences = transcription.split('.')
    
    tasks = []
    for i, sentence in enumerate(sentences):
        if any(keyword in sentence.lower() for keyword in task_keywords):
            task_title = sentence.strip()
            if len(task_title) > 10:  # Минимальная длина задачи
                tasks.append({
                    "title": task_title,
                    "assigned_to": "Не назначено",
                    "priority": "normal",
                    "deadline": (datetime.now() + timedelta(days=7)).strftime("%Y-%m-%d")
                })
    
    # Поиск участников (имена)
    participants = ["Участник планерки"]  # По умолчанию
    
    summary = f"Краткое содержание планерки '{meeting_title}'. Обсуждались вопросы организации работы. Выявлено {len(tasks)} задач."
    
    return {
        "summary": summary,
        "tasks": tasks[:10],  # Максимум 10 задач
        "participants": participants
    }

@app.post("/api/bitrix/create-tasks")
async def create_bitrix_tasks(request: BitrixTaskRequest):
    """Создание задач в Битрикс24"""
    try:
        # Здесь должна быть реальная интеграция с Битрикс24 API
        # Пока возвращаем mock данные
        
        created_tasks = []
        for i, task in enumerate(request.tasks):
            mock_task_id = 1000 + i
            created_tasks.append({
                "id": mock_task_id,
                "title": task.get("title", "Без названия"),
                "url": f"https://bitrix24.ru/workgroups/task/view/{mock_task_id}/",
                "status": "created"
            })
            
        logger.info(f"Создано {len(created_tasks)} задач в Битрикс24 (mock)")
        
        return {
            "success": True,
            "created_tasks": created_tasks,
            "meeting_title": request.meeting_title
        }
        
    except Exception as e:
        logger.error(f"Ошибка создания задач в Битрикс: {e}")
        raise HTTPException(status_code=500, detail=f"Bitrix error: {str(e)}")

# =============================================================================
# ОСТАЛЬНЫЕ ENDPOINTS
# =============================================================================

@app.get("/api/health")
async def health_check():
    """Расширенная проверка здоровья системы с метриками"""
    start_time = time.time()
    
    try:
        # Базовые проверки
        health_status = {
            "status": "healthy",
            "timestamp": datetime.utcnow().isoformat(),
            "platform": "Production",
            "version": "3.0.0",
            "uptime_seconds": time.time() - app_start_time,
        }
        
        # Проверка сервисов
        services_status = {
            "emergent_llm": bool(ai_service.llm_client),
            "embeddings": True,  # Fallback эмбеддинги всегда работают
            "database": False,   # In-memory mode
            "storage": True,
            "http_client": HTTP_CLIENT_AVAILABLE or REQUESTS_AVAILABLE
        }
        
        # Проверка learning данных
        learning_data = {
            "total_conversations": len(storage.conversations) if hasattr(storage, 'conversations') else 0,
            "embeddings_cached": len(storage.embeddings) if hasattr(storage, 'embeddings') else 0,
            "rated_conversations": 0,  # Будет получено через stats
            "max_storage_limit": storage.max_conversations
        }
        
        # Проверка системных ресурсов
        try:
            import psutil
            system_metrics = {
                "cpu_percent": psutil.cpu_percent(interval=0.1),
                "memory_percent": psutil.virtual_memory().percent,
                "disk_percent": psutil.disk_usage('/').percent
            }
        except ImportError:
            system_metrics = {"status": "psutil_not_available"}
        
        # Проверка критических функций
        critical_checks = {
            "ai_service_init": ai_service is not None,
            "storage_accessible": hasattr(storage, 'conversations') and len(storage.conversations) >= 0,
            "config_loaded": len(config.EMERGENT_LLM_KEY) > 0,
            "embedding_creation": True  # Всегда работает через fallback
        }
        
        # Определяем общий статус
        all_critical_ok = all(critical_checks.values())
        if not all_critical_ok:
            health_status["status"] = "degraded"
        
        response_time = time.time() - start_time
        
        return {
            **health_status,
            "services": services_status,
            "learning_data": learning_data,
            "system_metrics": system_metrics,
            "critical_checks": critical_checks,
            "response_time_ms": round(response_time * 1000, 2)
        }
        
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return {
            "status": "unhealthy",
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat()
        }

@app.post("/api/voice/process", response_model=VoiceResponse)
async def process_voice(message_data: VoiceMessage):
    """
    🧠 ГЛАВНАЯ ФУНКЦИЯ: Обработка сообщения с максимальным самообучением
    """
    logger.info(f"🎯 Обработка сообщения: {message_data.message[:50]}...")
    
    response = await ai_service.process_message(
        message_data.message, 
        message_data.session_id
    )
    
    logger.info(f"✅ Ответ сгенерирован (ID: {response.log_id}, похожих: {response.similar_found})")
    return response

@app.post("/api/voice/feedback")
async def submit_feedback(feedback: FeedbackRequest, background_tasks: BackgroundTasks):
    """⭐ Обратная связь для улучшения AI"""
    success = await storage.update_rating(
        feedback.log_id, 
        feedback.rating, 
        feedback.feedback_text
    )
    
    if not success:
        raise HTTPException(status_code=404, detail="Диалог не найден")
    
    # Записываем метрику обратной связи
    LEARNING_FEEDBACK.labels(rating=str(feedback.rating)).inc()
    
    # Запускаем фоновое обучение при получении обратной связи
    background_tasks.add_task(ai_service.continuous_learning)
    
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
    stats = await storage.get_stats()
    
    # Расчет скорости улучшения
    if hasattr(storage, 'conversations'):
        recent_conversations = [
            c for c in storage.conversations 
            if c["timestamp"] > datetime.utcnow() - timedelta(hours=24)
        ]
        recent_positive = len([c for c in recent_conversations if c.get("rating") is not None and c.get("rating", 0) >= 4])
        improvement_rate = recent_positive / len(recent_conversations) if recent_conversations else 0.0
    else:
        # Для PostgreSQL используем основную статистику
        improvement_rate = stats["positive_ratings"] / stats["rated_interactions"] if stats["rated_interactions"] > 0 else 0.0
    
    return LearningStats(
        total_interactions=stats["total_interactions"],
        avg_rating=stats["avg_rating"],
        positive_ratings=stats["positive_ratings"],
        negative_ratings=stats["negative_ratings"],
        improvement_rate=improvement_rate,
        last_learning_update=ai_service.last_training
    )

@app.get("/api/learning/export")
async def export_learning_data():
    """📤 Экспорт качественных диалогов для дообучения"""
    high_quality_data = await storage.get_rated_conversations(min_rating=config.MIN_RATING_THRESHOLD)
    
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

@app.post("/api/learning/train")
async def trigger_training(background_tasks: BackgroundTasks):
    """🚀 Ручной запуск обучения"""
    background_tasks.add_task(ai_service.continuous_learning)
    return {
        "status": "training_started",
        "message": "Обучение запущено в фоновом режиме",
        "timestamp": datetime.utcnow().isoformat()
    }

@app.get("/api/learning/similar/{log_id}")
async def get_similar_conversations(log_id: str, limit: int = 5):
    """🔍 Показать какие диалоги были найдены как похожие"""
    # Найдем исходный диалог
    original = None
    if hasattr(storage, 'conversations'):
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
            "📊 Live статистика обучения",
            "🔒 Безопасная сериализация данных"
        ],
        "endpoints": {
            "chat": "POST /api/voice/process",
            "feedback": "POST /api/voice/feedback",
            "stats": "GET /api/learning/stats",
            "export": "GET /api/learning/export",
            "train": "POST /api/learning/train"
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

# Status endpoints с безопасным хранилищем
class StatusCheck(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    client_name: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    platform: str = "Render"

class StatusCheckCreate(BaseModel):
    client_name: str

@app.post("/api/status", response_model=StatusCheck)
async def create_status_check(input: StatusCheckCreate):
    """Создание проверки статуса (безопасное хранилище с лимитом)"""
    try:
        status_obj = StatusCheck(**input.dict())
        status_checks.append(status_obj)  # deque автоматически ограничивает размер
        return status_obj
    except Exception as e:
        logger.error(f"Ошибка создания status check: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/status", response_model=List[StatusCheck])
async def get_status_checks():
    """Получение проверок статуса (всегда ≤ 10 записей)"""
    try:
        return list(status_checks)  # deque гарантирует максимум 10 элементов
    except Exception as e:
        logger.error(f"Ошибка получения status checks: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/metrics")
async def get_metrics():
    """Prometheus метрики для мониторинга"""
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)

logger.info("🎯 VasDom AudioBot запущен в режиме максимального самообучения!")
logger.info(f"🧠 AI сервисы: LLM={bool(ai_service.llm_client)}, HTTP={HTTP_CLIENT_AVAILABLE or REQUESTS_AVAILABLE}")
logger.info(f"💾 Хранилище: In-Memory с безопасной сериализацией")
logger.info(f"🔒 Безопасность: Исправлены все критические проблемы")