"""
Модуль экспорта данных для обучения AI модели
Выгружает пары user_message/ai_response и фильтрует по положительным оценкам
"""
import json
import os
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from sqlalchemy.orm import Session
from sqlalchemy import and_, func
import logging

from app.config.database import SessionLocal
from app.models.database import VoiceLogDB, TrainingDatasetDB
from app.config.settings import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

class TrainingDataExporter:
    """Экспортер данных для обучения модели"""
    
    def __init__(self, min_rating: int = None):
        self.min_rating = min_rating or settings.MIN_RATING_THRESHOLD
        self.export_dir = "training/data"
        os.makedirs(self.export_dir, exist_ok=True)
    
    async def export_training_data(
        self,
        days_back: int = 30,
        max_samples: int = 10000,
        output_filename: Optional[str] = None
    ) -> Dict:
        """
        Экспорт данных для обучения в формате JSONL
        
        Args:
            days_back: Количество дней назад для выборки
            max_samples: Максимальное количество образцов
            output_filename: Имя выходного файла
            
        Returns:
            Dict с информацией об экспорте
        """
        try:
            async with SessionLocal() as db:
                # Определяем период выборки
                cutoff_date = datetime.utcnow() - timedelta(days=days_back)
                
                # Запрос на выборку данных с фильтрацией по рейтингу
                query = db.query(VoiceLogDB).filter(
                    and_(
                        VoiceLogDB.created_at >= cutoff_date,
                        VoiceLogDB.rating >= self.min_rating,
                        VoiceLogDB.user_message.isnot(None),
                        VoiceLogDB.ai_response.isnot(None)
                    )
                ).order_by(VoiceLogDB.created_at.desc()).limit(max_samples)
                
                logs = await query.all()
                
                # Подсчет общего количества записей (без фильтрации по рейтингу)
                total_query = db.query(func.count(VoiceLogDB.id)).filter(
                    VoiceLogDB.created_at >= cutoff_date
                )
                total_count = await total_query.scalar()
                
                # Генерация имени файла
                if not output_filename:
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    output_filename = f"training_data_{timestamp}.jsonl"
                
                output_path = os.path.join(self.export_dir, output_filename)
                
                # Экспорт в JSONL формат
                exported_count = 0
                with open(output_path, 'w', encoding='utf-8') as f:
                    for log in logs:
                        training_sample = {
                            "messages": [
                                {"role": "user", "content": log.user_message},
                                {"role": "assistant", "content": log.ai_response}
                            ],
                            "metadata": {
                                "log_id": log.id,
                                "rating": log.rating,
                                "session_id": log.session_id,
                                "created_at": log.created_at.isoformat(),
                                "model_used": log.model_used
                            }
                        }
                        f.write(json.dumps(training_sample, ensure_ascii=False) + '\n')
                        exported_count += 1
                
                # Сохраняем информацию о датасете в БД
                dataset = TrainingDatasetDB(
                    dataset_name=f"training_export_{datetime.now().strftime('%Y%m%d')}",
                    version="1.0",
                    total_samples=exported_count,
                    min_rating_threshold=self.min_rating,
                    jsonl_path=output_path,
                    status="completed"
                )
                db.add(dataset)
                await db.commit()
                
                export_info = {
                    "success": True,
                    "total_samples": total_count,
                    "filtered_samples": exported_count,
                    "min_rating_threshold": self.min_rating,
                    "export_path": output_path,
                    "dataset_id": dataset.id,
                    "created_at": datetime.utcnow().isoformat(),
                    "period_days": days_back
                }
                
                logger.info(f"Экспорт завершен: {exported_count} образцов из {total_count} записей")
                return export_info
                
        except Exception as e:
            logger.error(f"Ошибка экспорта данных: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "total_samples": 0,
                "filtered_samples": 0
            }
    
    async def validate_export_data(self, file_path: str) -> Dict:
        """
        Валидация экспортированных данных
        """
        try:
            if not os.path.exists(file_path):
                return {"valid": False, "error": "Файл не найден"}
            
            line_count = 0
            valid_samples = 0
            errors = []
            
            with open(file_path, 'r', encoding='utf-8') as f:
                for line_num, line in enumerate(f, 1):
                    line_count += 1
                    try:
                        data = json.loads(line.strip())
                        
                        # Проверяем обязательные поля
                        if "messages" not in data:
                            errors.append(f"Строка {line_num}: отсутствует поле 'messages'")
                            continue
                        
                        messages = data["messages"]
                        if len(messages) != 2:
                            errors.append(f"Строка {line_num}: должно быть ровно 2 сообщения")
                            continue
                        
                        if messages[0]["role"] != "user" or messages[1]["role"] != "assistant":
                            errors.append(f"Строка {line_num}: неверные роли сообщений")
                            continue
                        
                        valid_samples += 1
                        
                    except json.JSONDecodeError as e:
                        errors.append(f"Строка {line_num}: ошибка JSON - {str(e)}")
            
            return {
                "valid": len(errors) == 0,
                "total_lines": line_count,
                "valid_samples": valid_samples,
                "errors": errors[:10],  # Только первые 10 ошибок
                "error_count": len(errors)
            }
            
        except Exception as e:
            return {"valid": False, "error": f"Ошибка валидации: {str(e)}"}

# Функция для CLI использования
async def export_logs_cli(min_rating: int = 4, days_back: int = 30, max_samples: int = 10000):
    """CLI функция для экспорта логов"""
    exporter = TrainingDataExporter(min_rating=min_rating)
    result = await exporter.export_training_data(
        days_back=days_back,
        max_samples=max_samples
    )
    
    if result["success"]:
        print(f"✅ Экспорт успешен!")
        print(f"📊 Экспортировано: {result['filtered_samples']} из {result['total_samples']} записей")
        print(f"📁 Файл: {result['export_path']}")
        print(f"⭐ Минимальный рейтинг: {result['min_rating_threshold']}")
    else:
        print(f"❌ Ошибка экспорта: {result['error']}")
    
    return result

if __name__ == "__main__":
    import asyncio
    import argparse
    
    parser = argparse.ArgumentParser(description="Экспорт данных для обучения AI модели")
    parser.add_argument("--min-rating", type=int, default=4, help="Минимальный рейтинг (1-5)")
    parser.add_argument("--days-back", type=int, default=30, help="Количество дней назад")
    parser.add_argument("--max-samples", type=int, default=10000, help="Максимальное количество образцов")
    
    args = parser.parse_args()
    
    asyncio.run(export_logs_cli(
        min_rating=args.min_rating,
        days_back=args.days_back,
        max_samples=args.max_samples
    ))