"""
Cron задачи для автоматической оценки и переобучения модели
Запускается периодически для мониторинга качества AI
"""
import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, Optional
from sqlalchemy import func, and_, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.config.database import SessionLocal
from app.config.settings import get_settings
from app.models.database import VoiceLogDB, ModelMetricsDB, TrainingDatasetDB
from training.export_logs import TrainingDataExporter
from training.fine_tune import fine_tune_from_export

logger = logging.getLogger(__name__)
settings = get_settings()

class ModelEvaluator:
    """Класс для автоматической оценки и управления переобучением"""
    
    def __init__(self):
        self.evaluation_period_days = settings.EVALUATION_SCHEDULE_DAYS
        self.retraining_threshold = settings.RETRAINING_THRESHOLD
        self.min_interactions_for_evaluation = 100
    
    async def evaluate_current_model(self) -> Dict:
        """
        Оценка текущей модели по пользовательским рейтингам
        
        Returns:
            Словарь с метриками качества
        """
        try:
            logger.info("🔍 Начало оценки текущей модели")
            
            # Определяем период для оценки
            end_date = datetime.utcnow()
            start_date = end_date - timedelta(days=self.evaluation_period_days)
            
            async with SessionLocal() as db:
                # Базовые метрики за период
                period_logs = db.query(VoiceLogDB).filter(
                    and_(
                        VoiceLogDB.created_at >= start_date,
                        VoiceLogDB.created_at <= end_date
                    )
                )
                
                total_interactions = await period_logs.count()
                
                # Взаимодействия с рейтингами
                rated_logs = period_logs.filter(VoiceLogDB.rating.isnot(None))
                rated_count = await rated_logs.count()
                
                if rated_count < self.min_interactions_for_evaluation:
                    logger.warning(f"Недостаточно оценок для анализа: {rated_count} < {self.min_interactions_for_evaluation}")
                    return {
                        "success": False,
                        "reason": "insufficient_data",
                        "rated_interactions": rated_count,
                        "min_required": self.min_interactions_for_evaluation
                    }
                
                # Средний рейтинг
                avg_rating_result = await db.query(
                    func.avg(VoiceLogDB.rating)
                ).filter(
                    and_(
                        VoiceLogDB.created_at >= start_date,
                        VoiceLogDB.created_at <= end_date,
                        VoiceLogDB.rating.isnot(None)
                    )
                ).scalar()
                
                avg_rating = float(avg_rating_result) if avg_rating_result else 0.0
                
                # Положительные и отрицательные оценки
                positive_ratings = await db.query(func.count(VoiceLogDB.id)).filter(
                    and_(
                        VoiceLogDB.created_at >= start_date,
                        VoiceLogDB.created_at <= end_date,
                        VoiceLogDB.rating >= 4
                    )
                ).scalar()
                
                negative_ratings = await db.query(func.count(VoiceLogDB.id)).filter(
                    and_(
                        VoiceLogDB.created_at >= start_date,
                        VoiceLogDB.created_at <= end_date,
                        VoiceLogDB.rating <= 2
                    )
                ).scalar()
                
                # Расчет дополнительных метрик
                user_satisfaction = positive_ratings / rated_count if rated_count > 0 else 0.0
                
                # Определяем текущую модель
                current_model_query = await db.query(VoiceLogDB.model_used).filter(
                    VoiceLogDB.created_at >= start_date
                ).distinct().all()
                
                current_models = [result[0] for result in current_model_query]
                primary_model = current_models[0] if current_models else "unknown"
                
                # Формируем результат оценки
                evaluation_result = {
                    "success": True,
                    "model_version": primary_model,
                    "evaluation_period": {
                        "start": start_date.isoformat(),
                        "end": end_date.isoformat(),
                        "days": self.evaluation_period_days
                    },
                    "metrics": {
                        "avg_rating": avg_rating,
                        "total_interactions": total_interactions,
                        "rated_interactions": rated_count,
                        "positive_ratings": positive_ratings,
                        "negative_ratings": negative_ratings,
                        "user_satisfaction": user_satisfaction,
                        "rating_coverage": rated_count / total_interactions if total_interactions > 0 else 0.0
                    },
                    "quality_assessment": {
                        "overall_quality": self._assess_quality(avg_rating, user_satisfaction),
                        "requires_retraining": avg_rating < self.retraining_threshold,
                        "threshold_used": self.retraining_threshold
                    },
                    "evaluated_at": datetime.utcnow().isoformat()
                }
                
                # Сохранение метрик в БД
                await self._save_evaluation_metrics(db, evaluation_result)
                
                logger.info(f"✅ Оценка завершена. Средний рейтинг: {avg_rating:.2f}")
                
                return evaluation_result
                
        except Exception as e:
            logger.error(f"❌ Ошибка оценки модели: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "evaluated_at": datetime.utcnow().isoformat()
            }
    
    def _assess_quality(self, avg_rating: float, user_satisfaction: float) -> str:
        """Оценка общего качества модели"""
        if avg_rating >= 4.0 and user_satisfaction >= 0.7:
            return "excellent"
        elif avg_rating >= 3.5 and user_satisfaction >= 0.6:
            return "good"
        elif avg_rating >= 3.0 and user_satisfaction >= 0.5:
            return "acceptable"
        elif avg_rating >= 2.5:
            return "poor"
        else:
            return "very_poor"
    
    async def _save_evaluation_metrics(self, db, evaluation_result: Dict):
        """Сохранение метрик оценки в базу данных"""
        try:
            metrics = evaluation_result["metrics"]
            quality = evaluation_result["quality_assessment"]
            
            # Деактивируем предыдущие метрики
            await db.query(ModelMetricsDB).filter(
                ModelMetricsDB.is_current_model == True
            ).update({"is_current_model": False})
            
            # Создаем новую запись метрик
            new_metrics = ModelMetricsDB(
                model_version=evaluation_result["model_version"],
                avg_rating=metrics["avg_rating"],
                total_interactions=metrics["total_interactions"],
                positive_ratings=metrics["positive_ratings"],
                negative_ratings=metrics["negative_ratings"],
                user_satisfaction=metrics["user_satisfaction"],
                evaluation_period_start=datetime.fromisoformat(evaluation_result["evaluation_period"]["start"]),
                evaluation_period_end=datetime.fromisoformat(evaluation_result["evaluation_period"]["end"]),
                is_current_model=True,
                requires_retraining=quality["requires_retraining"]
            )
            
            db.add(new_metrics)
            await db.commit()
            
            logger.info(f"Метрики сохранены для модели {evaluation_result['model_version']}")
            
        except Exception as e:
            logger.error(f"Ошибка сохранения метрик: {str(e)}")
    
    async def check_and_trigger_retraining(self) -> Dict:
        """
        Проверка необходимости переобучения и автоматический запуск
        
        Returns:
            Результат проверки и возможного переобучения
        """
        try:
            logger.info("🔄 Проверка необходимости переобучения")
            
            # Получаем последнюю оценку
            evaluation_result = await self.evaluate_current_model()
            
            if not evaluation_result["success"]:
                return {
                    "action": "evaluation_failed",
                    "reason": evaluation_result.get("reason", "unknown"),
                    "details": evaluation_result
                }
            
            # Проверяем, нужно ли переобучение
            quality_assessment = evaluation_result["quality_assessment"]
            
            if not quality_assessment["requires_retraining"]:
                logger.info(f"✅ Переобучение не требуется. Рейтинг: {evaluation_result['metrics']['avg_rating']:.2f}")
                return {
                    "action": "no_retraining_needed",
                    "current_rating": evaluation_result["metrics"]["avg_rating"],
                    "threshold": quality_assessment["threshold_used"],
                    "evaluation": evaluation_result
                }
            
            logger.warning(f"⚠️ Требуется переобучение! Рейтинг: {evaluation_result['metrics']['avg_rating']:.2f} < {quality_assessment['threshold_used']}")
            
            # Экспорт данных для переобучения
            exporter = TrainingDataExporter(min_rating=settings.MIN_RATING_THRESHOLD)
            export_result = await exporter.export_training_data(
                days_back=30,  # Последние 30 дней
                max_samples=5000  # Максимум 5000 образцов
            )
            
            if not export_result["success"]:
                return {
                    "action": "export_failed",
                    "error": export_result["error"],
                    "evaluation": evaluation_result
                }
            
            # Запуск переобучения
            if export_result["filtered_samples"] >= 50:  # Минимум 50 качественных образцов
                logger.info(f"🚀 Запуск автоматического переобучения с {export_result['filtered_samples']} образцами")
                
                retraining_result = await fine_tune_from_export(
                    jsonl_file_path=export_result["export_path"],
                    num_epochs=2,  # Меньше эпох для автоматического переобучения
                    batch_size=4,
                    learning_rate=3e-5
                )
                
                return {
                    "action": "retraining_completed" if retraining_result["success"] else "retraining_failed",
                    "export": export_result,
                    "retraining": retraining_result,
                    "evaluation": evaluation_result
                }
            else:
                logger.warning(f"❌ Недостаточно качественных данных для переобучения: {export_result['filtered_samples']} < 50")
                return {
                    "action": "insufficient_training_data",
                    "available_samples": export_result["filtered_samples"],
                    "min_required": 50,
                    "export": export_result,
                    "evaluation": evaluation_result
                }
                
        except Exception as e:
            logger.error(f"❌ Ошибка проверки переобучения: {str(e)}")
            return {
                "action": "error",
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }

# Главные функции для cron задач
async def evaluate_model():
    """Cron задача для оценки модели"""
    logger.info("📊 Запуск cron задачи оценки модели")
    
    evaluator = ModelEvaluator()
    result = await evaluator.evaluate_current_model()
    
    if result["success"]:
        logger.info(f"✅ Оценка модели завершена. Средний рейтинг: {result['metrics']['avg_rating']:.2f}")
    else:
        logger.error(f"❌ Ошибка оценки модели: {result.get('error', 'unknown')}")
    
    return result

async def check_retraining():
    """Cron задача для проверки и запуска переобучения"""
    logger.info("🔄 Запуск cron задачи проверки переобучения")
    
    evaluator = ModelEvaluator()
    result = await evaluator.check_and_trigger_retraining()
    
    logger.info(f"📋 Результат проверки переобучения: {result['action']}")
    
    return result

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 2:
        print("Использование: python cron_tasks.py [evaluate_model|check_retraining]")
        sys.exit(1)
    
    task = sys.argv[1]
    
    if task == "evaluate_model":
        result = asyncio.run(evaluate_model())
        print(f"Результат оценки: {result}")
    elif task == "check_retraining":
        result = asyncio.run(check_retraining())
        print(f"Результат проверки переобучения: {result}")
    else:
        print(f"Неизвестная задача: {task}")
        sys.exit(1)