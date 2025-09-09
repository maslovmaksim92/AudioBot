from sqlalchemy import Column, Integer, String, Text, DateTime, Float, LargeBinary, ForeignKey, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid

Base = declarative_base()

class VoiceLogDB(Base):
    """Логи AI взаимодействий для самообучения"""
    __tablename__ = "voice_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(String, default=lambda: str(uuid.uuid4()))
    user_message = Column(Text, nullable=False)
    ai_response = Column(Text, nullable=False)
    
    # Новые поля для самообучения
    rating = Column(Integer, nullable=True)  # 1-5 звезд от пользователя
    feedback_text = Column(Text, nullable=True)  # Опциональный комментарий
    
    # Метаданные
    model_used = Column(String, default="gpt-4-mini")  # Какая модель использовалась
    response_time = Column(Float, nullable=True)  # Время генерации ответа
    token_count = Column(Integer, nullable=True)  # Количество токенов
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Связь с эмбеддингами
    embeddings = relationship("VoiceEmbeddingDB", back_populates="voice_log", cascade="all, delete-orphan")

class VoiceEmbeddingDB(Base):
    """Векторные представления для поиска похожих вопросов"""
    __tablename__ = "voice_embeddings"
    
    id = Column(Integer, primary_key=True, index=True)
    log_id = Column(Integer, ForeignKey("voice_logs.id"), nullable=False)
    
    # Векторное представление (сериализованный numpy array)
    vector = Column(LargeBinary, nullable=False)
    embedding_model = Column(String, default="sentence-transformers/paraphrase-multilingual-MiniLM-L6-v2")
    
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Связь с логом
    voice_log = relationship("VoiceLogDB", back_populates="embeddings")

class ModelMetricsDB(Base):
    """Метрики качества моделей для автоматической переоценки"""
    __tablename__ = "model_metrics"
    
    id = Column(Integer, primary_key=True, index=True)
    model_version = Column(String, nullable=False)  # gpt-4-mini, local-llama-v1, etc.
    
    # Основные метрики
    avg_rating = Column(Float, nullable=True)  # Средняя оценка пользователей
    total_interactions = Column(Integer, default=0)  # Общее количество взаимодействий
    positive_ratings = Column(Integer, default=0)  # Количество положительных оценок (4-5 звезд)
    negative_ratings = Column(Integer, default=0)  # Количество отрицательных оценок (1-2 звезды)
    
    # Дополнительные метрики
    accuracy_score = Column(Float, nullable=True)  # Точность на тестовом наборе
    response_quality = Column(Float, nullable=True)  # Качество ответов (экспертная оценка)
    user_satisfaction = Column(Float, nullable=True)  # Удовлетворенность пользователей
    
    # Временные метки
    evaluation_period_start = Column(DateTime, nullable=False)
    evaluation_period_end = Column(DateTime, nullable=False)
    evaluated_at = Column(DateTime, default=datetime.utcnow)
    
    # Флаги
    is_current_model = Column(Boolean, default=False)  # Активная модель
    requires_retraining = Column(Boolean, default=False)  # Нужно ли переобучение

class TrainingDatasetDB(Base):
    """Наборы данных для обучения моделей"""
    __tablename__ = "training_datasets"
    
    id = Column(Integer, primary_key=True, index=True)
    dataset_name = Column(String, nullable=False)
    version = Column(String, nullable=False)
    
    # Статистика датасета
    total_samples = Column(Integer, default=0)
    min_rating_threshold = Column(Integer, default=4)  # Минимальный рейтинг для включения
    
    # Пути к файлам
    jsonl_path = Column(String, nullable=True)  # Путь к JSONL файлу
    model_weights_path = Column(String, nullable=True)  # Путь к весам модели
    
    # Метаданные
    created_at = Column(DateTime, default=datetime.utcnow)
    training_started_at = Column(DateTime, nullable=True)
    training_completed_at = Column(DateTime, nullable=True)
    
    # Статус
    status = Column(String, default="created")  # created, training, completed, failed
    training_logs = Column(Text, nullable=True)  # Логи обучения

# Обратная совместимость с MongoDB структурой
class StatusCheckDB(Base):
    """Проверки статуса (мигрировано из MongoDB)"""
    __tablename__ = "status_checks"
    
    id = Column(Integer, primary_key=True, index=True)
    client_name = Column(String, nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow)