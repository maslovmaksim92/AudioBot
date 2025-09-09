from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
import uuid

# Базовые схемы для самообучения
class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=2000, description="Сообщение пользователя")
    session_id: Optional[str] = Field(default_factory=lambda: str(uuid.uuid4()), description="ID сессии")

class ChatResponse(BaseModel):
    response: str = Field(..., description="Ответ AI")
    log_id: int = Field(..., description="ID лога для обратной связи")
    session_id: str = Field(..., description="ID сессии")
    model_used: str = Field(default="gpt-4-mini", description="Используемая модель")
    response_time: Optional[float] = Field(None, description="Время генерации ответа в секундах")

class FeedbackRequest(BaseModel):
    log_id: int = Field(..., description="ID лога взаимодействия")
    rating: int = Field(..., ge=1, le=5, description="Оценка от 1 до 5 звезд")
    feedback_text: Optional[str] = Field(None, max_length=1000, description="Опциональный комментарий")

class FeedbackResponse(BaseModel):
    success: bool = Field(..., description="Успешность операции")
    message: str = Field(..., description="Сообщение о результате")
    log_id: int = Field(..., description="ID обновленного лога")

# Схемы для статистики самообучения
class SelfLearningStatus(BaseModel):
    total_interactions: int = Field(..., description="Общее количество взаимодействий")
    avg_rating: Optional[float] = Field(None, description="Средняя оценка пользователей")
    positive_ratings_count: int = Field(default=0, description="Количество положительных оценок")
    negative_ratings_count: int = Field(default=0, description="Количество отрицательных оценок")
    
    # Информация о модели
    current_model: str = Field(default="gpt-4-mini", description="Текущая активная модель")
    last_evaluation: Optional[datetime] = Field(None, description="Время последней оценки")
    next_training_scheduled: Optional[datetime] = Field(None, description="Запланированное время следующего обучения")
    
    # Метрики качества
    current_metrics: Optional[dict] = Field(None, description="Текущие метрики качества")
    requires_retraining: bool = Field(default=False, description="Требуется ли переобучение")

class SimilarResponse(BaseModel):
    log_id: int = Field(..., description="ID похожего лога")
    user_message: str = Field(..., description="Похожий вопрос пользователя")
    ai_response: str = Field(..., description="Ответ AI на похожий вопрос")
    similarity_score: float = Field(..., ge=0, le=1, description="Коэффициент сходства")
    rating: Optional[int] = Field(None, description="Оценка пользователя")
    created_at: datetime = Field(..., description="Время создания")

class TrainingDataExport(BaseModel):
    total_samples: int = Field(..., description="Общее количество образцов")
    filtered_samples: int = Field(..., description="Образцы после фильтрации")
    min_rating_threshold: int = Field(..., description="Минимальный порог рейтинга")
    export_path: str = Field(..., description="Путь к экспортированному файлу")
    created_at: datetime = Field(..., description="Время создания экспорта")

class ModelMetrics(BaseModel):
    model_version: str = Field(..., description="Версия модели")
    avg_rating: Optional[float] = Field(None, description="Средняя оценка")
    total_interactions: int = Field(default=0, description="Общее количество взаимодействий")
    positive_ratings: int = Field(default=0, description="Положительные оценки")
    negative_ratings: int = Field(default=0, description="Отрицательные оценки")
    accuracy_score: Optional[float] = Field(None, description="Точность модели")
    user_satisfaction: Optional[float] = Field(None, description="Удовлетворенность пользователей")
    evaluation_period_start: datetime = Field(..., description="Начало периода оценки")
    evaluation_period_end: datetime = Field(..., description="Конец периода оценки")
    is_current_model: bool = Field(default=False, description="Активная модель")
    requires_retraining: bool = Field(default=False, description="Требуется переобучение")

# Обратная совместимость с существующими схемами
class StatusCheck(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    client_name: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)

class StatusCheckCreate(BaseModel):
    client_name: str