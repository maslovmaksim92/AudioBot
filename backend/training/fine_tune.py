"""
Модуль дообучения AI модели на основе данных пользователей
Использует transformers для fine-tuning локальных моделей
"""
import os
import json
import torch
import logging
from datetime import datetime
from typing import Dict, List, Optional
from pathlib import Path
import argparse

try:
    from transformers import (
        AutoTokenizer, AutoModelForCausalLM, 
        TrainingArguments, Trainer, DataCollatorForLanguageModeling
    )
    from datasets import Dataset
    TRANSFORMERS_AVAILABLE = True
except ImportError:
    TRANSFORMERS_AVAILABLE = False
    logging.warning("transformers не установлен. Дообучение недоступно.")

from app.config.settings import get_settings
from app.config.database import SessionLocal
from app.models.database import TrainingDatasetDB, ModelMetricsDB
from sqlalchemy import select

logger = logging.getLogger(__name__)
settings = get_settings()

class ModelFineTuner:
    """Класс для дообучения языковых моделей"""
    
    def __init__(self, base_model_name: str = "microsoft/DialoGPT-medium"):
        self.base_model_name = base_model_name
        self.output_dir = settings.LOCAL_MODEL_PATH
        self.training_data_dir = "training/data"
        
        # Создаем необходимые директории
        Path(self.output_dir).mkdir(parents=True, exist_ok=True)
        Path(self.training_data_dir).mkdir(parents=True, exist_ok=True)
        
        self.tokenizer = None
        self.model = None
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        
        logger.info(f"Инициализация fine-tuner для {base_model_name} на {self.device}")
    
    def load_base_model(self) -> bool:
        """Загрузка базовой модели и токенизатора"""
        if not TRANSFORMERS_AVAILABLE:
            logger.error("transformers не доступен")
            return False
        
        try:
            logger.info(f"Загрузка базовой модели: {self.base_model_name}")
            
            self.tokenizer = AutoTokenizer.from_pretrained(self.base_model_name)
            self.model = AutoModelForCausalLM.from_pretrained(self.base_model_name)
            
            # Настройка токенизатора
            if self.tokenizer.pad_token is None:
                self.tokenizer.pad_token = self.tokenizer.eos_token
            
            # Перемещение модели на устройство
            self.model.to(self.device)
            
            logger.info("✅ Базовая модель загружена успешно")
            return True
            
        except Exception as e:
            logger.error(f"❌ Ошибка загрузки базовой модели: {str(e)}")
            return False
    
    def prepare_dataset(self, jsonl_file_path: str) -> Optional[Dataset]:
        """
        Подготовка датасета из JSONL файла
        
        Args:
            jsonl_file_path: Путь к JSONL файлу с данными
            
        Returns:
            Dataset для обучения или None при ошибке
        """
        try:
            if not os.path.exists(jsonl_file_path):
                logger.error(f"Файл не найден: {jsonl_file_path}")
                return None
            
            # Загрузка данных
            training_data = []
            with open(jsonl_file_path, 'r', encoding='utf-8') as f:
                for line in f:
                    try:
                        data = json.loads(line.strip())
                        messages = data.get("messages", [])
                        
                        if len(messages) >= 2:
                            user_msg = messages[0]["content"] 
                            assistant_msg = messages[1]["content"]
                            
                            # Формируем текст для обучения
                            conversation = f"Пользователь: {user_msg}\nПомощник: {assistant_msg}"
                            training_data.append(conversation)
                            
                    except json.JSONDecodeError as e:
                        logger.warning(f"Ошибка парсинга JSON: {str(e)}")
                        continue
            
            logger.info(f"Загружено {len(training_data)} диалогов для обучения")
            
            if len(training_data) == 0:
                logger.error("Нет данных для обучения")
                return None
            
            # Токенизация данных
            def tokenize_function(examples):
                return self.tokenizer(
                    examples["text"],
                    truncation=True,
                    padding=True,
                    max_length=512
                )
            
            # Создание Dataset
            dataset = Dataset.from_dict({"text": training_data})
            tokenized_dataset = dataset.map(tokenize_function, batched=True)
            
            logger.info(f"✅ Датасет подготовлен: {len(tokenized_dataset)} образцов")
            return tokenized_dataset
            
        except Exception as e:
            logger.error(f"❌ Ошибка подготовки датасета: {str(e)}")
            return None
    
    def fine_tune_model(
        self,
        dataset: Dataset,
        num_epochs: int = 3,
        batch_size: int = 4,
        learning_rate: float = 5e-5,
        save_steps: int = 500
    ) -> Dict:
        """
        Дообучение модели
        
        Args:
            dataset: Подготовленный датасет
            num_epochs: Количество эпох
            batch_size: Размер батча
            learning_rate: Скорость обучения
            save_steps: Частота сохранения чекпоинтов
            
        Returns:
            Результаты обучения
        """
        try:
            logger.info("🚀 Начало дообучения модели")
            
            # Настройки обучения
            training_args = TrainingArguments(
                output_dir=self.output_dir,
                overwrite_output_dir=True,
                num_train_epochs=num_epochs,
                per_device_train_batch_size=batch_size,
                per_device_eval_batch_size=batch_size,
                warmup_steps=100,
                learning_rate=learning_rate,
                logging_steps=50,
                save_steps=save_steps,
                evaluation_strategy="no",  # Пока без валидации
                remove_unused_columns=False,
                dataloader_num_workers=0,  # Для стабильности
                report_to=[],  # Отключаем логирование в wandb
            )
            
            # Data collator
            data_collator = DataCollatorForLanguageModeling(
                tokenizer=self.tokenizer,
                mlm=False,  # Causal LM
                pad_to_multiple_of=8
            )
            
            # Trainer
            trainer = Trainer(
                model=self.model,
                args=training_args,
                train_dataset=dataset,
                data_collator=data_collator,
                tokenizer=self.tokenizer,
            )
            
            # Обучение
            start_time = datetime.now()
            train_result = trainer.train()
            end_time = datetime.now()
            
            # Сохранение модели
            trainer.save_model()
            self.tokenizer.save_pretrained(self.output_dir)
            
            training_duration = (end_time - start_time).total_seconds()
            
            result = {
                "success": True,
                "training_loss": train_result.training_loss,
                "num_epochs": num_epochs,
                "training_duration_seconds": training_duration,
                "model_path": self.output_dir,
                "timestamp": end_time.isoformat()
            }
            
            logger.info(f"✅ Обучение завершено успешно за {training_duration:.1f} сек")
            logger.info(f"📁 Модель сохранена в: {self.output_dir}")
            
            return result
            
        except Exception as e:
            logger.error(f"❌ Ошибка дообучения: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
    
    async def update_training_dataset_status(
        self,
        dataset_id: int,
        status: str,
        training_logs: Optional[str] = None,
        model_weights_path: Optional[str] = None
    ):
        """Обновление статуса датасета в БД"""
        try:
            async with SessionLocal() as db:
                dataset = await db.query(TrainingDatasetDB).filter(
                    TrainingDatasetDB.id == dataset_id
                ).first()
                
                if dataset:
                    dataset.status = status
                    dataset.training_logs = training_logs
                    
                    if status == "training":
                        dataset.training_started_at = datetime.utcnow()
                    elif status == "completed":
                        dataset.training_completed_at = datetime.utcnow()
                        dataset.model_weights_path = model_weights_path
                    
                    await db.commit()
                    logger.info(f"Статус датасета {dataset_id} обновлен на {status}")
                    
        except Exception as e:
            logger.error(f"Ошибка обновления статуса датасета: {str(e)}")

async def fine_tune_from_export(
    jsonl_file_path: str,
    base_model: str = "microsoft/DialoGPT-medium",
    num_epochs: int = 3,
    batch_size: int = 4,
    learning_rate: float = 5e-5
) -> Dict:
    """
    Главная функция дообучения модели
    
    Args:
        jsonl_file_path: Путь к файлу с данными
        base_model: Базовая модель для дообучения
        num_epochs: Количество эпох
        batch_size: Размер батча
        learning_rate: Скорость обучения
        
    Returns:
        Результаты обучения
    """
    if not TRANSFORMERS_AVAILABLE:
        return {
            "success": False,
            "error": "transformers не установлен"
        }
    
    fine_tuner = ModelFineTuner(base_model_name=base_model)
    
    # Загрузка базовой модели
    if not fine_tuner.load_base_model():
        return {
            "success": False,
            "error": "Ошибка загрузки базовой модели"
        }
    
    # Подготовка датасета
    dataset = fine_tuner.prepare_dataset(jsonl_file_path)
    if dataset is None:
        return {
            "success": False,
            "error": "Ошибка подготовки датасета"
        }
    
    # Дообучение
    result = fine_tuner.fine_tune_model(
        dataset=dataset,
        num_epochs=num_epochs,
        batch_size=batch_size,
        learning_rate=learning_rate
    )
    
    return result

if __name__ == "__main__":
    import asyncio
    
    parser = argparse.ArgumentParser(description="Дообучение AI модели VasDom AudioBot")
    parser.add_argument("--data", type=str, required=True, help="Путь к JSONL файлу с данными")
    parser.add_argument("--model", type=str, default="microsoft/DialoGPT-medium", help="Базовая модель")
    parser.add_argument("--epochs", type=int, default=3, help="Количество эпох")
    parser.add_argument("--batch-size", type=int, default=4, help="Размер батча")
    parser.add_argument("--learning-rate", type=float, default=5e-5, help="Скорость обучения")
    
    args = parser.parse_args()
    
    async def main():
        print("🚀 Запуск дообучения модели VasDom AudioBot")
        print(f"📊 Данные: {args.data}")
        print(f"🤖 Базовая модель: {args.model}")
        print(f"📈 Эпохи: {args.epochs}, Батч: {args.batch_size}, LR: {args.learning_rate}")
        
        result = await fine_tune_from_export(
            jsonl_file_path=args.data,
            base_model=args.model,
            num_epochs=args.epochs,
            batch_size=args.batch_size,
            learning_rate=args.learning_rate
        )
        
        if result["success"]:
            print("✅ Дообучение завершено успешно!")
            print(f"📁 Модель сохранена в: {result['model_path']}")
            print(f"📊 Loss: {result.get('training_loss', 'N/A')}")
        else:
            print(f"❌ Ошибка дообучения: {result['error']}")
    
    asyncio.run(main())