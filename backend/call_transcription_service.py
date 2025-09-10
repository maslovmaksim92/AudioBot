"""
Сервис транскрибации звонков из CRM для самообучения AI
Интеграция с различными телефонными системами включая "задарма новофон"
"""
import os
import logging
import json
import asyncio
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Any
import uuid

# Настройка логирования
logger = logging.getLogger(__name__)

class CallTranscriptionService:
    """Сервис для транскрибации звонков из различных CRM систем"""
    
    def __init__(self):
        self.supported_systems = {
            "bitrix24": {
                "name": "Bitrix24 CRM",
                "webhook_url": os.getenv("BITRIX24_WEBHOOK_URL", ""),
                "phone_field": "PHONE",
                "call_field": "UF_CRM_CALL_RECORD"
            },
            "novofon": {
                "name": "Задарма Новофон",
                "api_key": os.getenv("NOVOFON_API_KEY", ""),
                "api_url": "https://api.novofon.com/v1",
                "webhook_secret": os.getenv("NOVOFON_WEBHOOK_SECRET", "")
            },
            "mango": {
                "name": "Mango Office",
                "api_key": os.getenv("MANGO_API_KEY", ""),
                "api_secret": os.getenv("MANGO_API_SECRET", "")
            },
            "zadarma": {
                "name": "Zadarma",
                "user_key": os.getenv("ZADARMA_USER_KEY", ""),
                "secret_key": os.getenv("ZADARMA_SECRET_KEY", "")
            }
        }
        
        # Конфигурация транскрибации
        self.transcription_config = {
            "min_call_duration": 30,  # Минимальная длительность звонка в секундах
            "language": "ru-RU",      # Язык распознавания
            "auto_learning": True,    # Автоматическое добавление в систему обучения
            "quality_threshold": 0.7,  # Минимальный порог качества транскрибации
        }
        
        logger.info("🎙️ Call Transcription Service инициализирован")
        self._log_supported_systems()
    
    def _log_supported_systems(self):
        """Логирование поддерживаемых систем"""
        logger.info("📞 Поддерживаемые телефонные системы:")
        for system_id, config in self.supported_systems.items():
            status = "✅ Настроено" if self._is_system_configured(system_id) else "⚠️ Требует настройки"
            logger.info(f"   {config['name']}: {status}")
    
    def _is_system_configured(self, system_id: str) -> bool:
        """Проверка настройки системы"""
        config = self.supported_systems.get(system_id, {})
        
        if system_id == "bitrix24":
            return bool(config.get("webhook_url"))
        elif system_id == "novofon":
            return bool(config.get("api_key"))
        elif system_id == "mango":
            return bool(config.get("api_key")) and bool(config.get("api_secret"))
        elif system_id == "zadarma":
            return bool(config.get("user_key")) and bool(config.get("secret_key"))
        
        return False
    
    async def transcribe_audio_file(self, audio_file_path: str, system: str = "auto") -> Dict[str, Any]:
        """
        Транскрибация аудиофайла звонка
        
        Args:
            audio_file_path: Путь к аудиофайлу или URL
            system: Система откуда получен звонок
            
        Returns:
            Результат транскрибации с метаданными
        """
        try:
            logger.info(f"🎧 Начало транскрибации: {audio_file_path}")
            
            # В реальной системе здесь был бы вызов к сервису транскрибации
            # Например: OpenAI Whisper, Google Speech-to-Text, Yandex SpeechKit
            
            # Симуляция транскрибации (в продакшене заменить на реальный API)
            transcription_result = await self._simulate_transcription(audio_file_path, system)
            
            # Обработка и валидация результата
            processed_result = self._process_transcription_result(transcription_result)
            
            logger.info(f"✅ Транскрибация завершена: {len(processed_result.get('text', ''))} символов")
            
            return processed_result
            
        except Exception as e:
            logger.error(f"❌ Ошибка транскрибации {audio_file_path}: {e}")
            return {
                "success": False,
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }
    
    async def _simulate_transcription(self, audio_file_path: str, system: str) -> Dict:
        """Симуляция транскрибации для демонстрации (заменить на реальный API)"""
        
        # Симулированные диалоги клининговой компании
        sample_conversations = [
            {
                "duration": 120,
                "speakers": [
                    {"speaker": "operator", "text": "Добрый день! VasDom, клининговая компания. Меня зовут Анна, чем могу помочь?"},
                    {"speaker": "client", "text": "Здравствуйте! Хотел узнать про уборку подъезда в нашем доме на улице Ленина 15."},
                    {"speaker": "operator", "text": "Конечно! Мы обслуживаем этот район. Сколько подъездов в вашем доме?"},
                    {"speaker": "client", "text": "Два подъезда, по 5 этажей каждый. Как часто вы убираете?"},
                    {"speaker": "operator", "text": "Мы предлагаем уборку 2 раза в неделю - влажную уборку и сухую. Стоимость зависит от площади."},
                    {"speaker": "client", "text": "А можете прислать коммерческое предложение на почту?"},
                    {"speaker": "operator", "text": "Обязательно! Оставьте ваш email, и я вышлю расчет в течение часа."}
                ]
            },
            {
                "duration": 85,
                "speakers": [
                    {"speaker": "operator", "text": "VasDom, добрый день! Как дела с уборкой?"},
                    {"speaker": "client", "text": "Здравствуйте! У нас проблема - клининг делают плохо, остается грязь на лестницах."},
                    {"speaker": "operator", "text": "Извините за неудобства! Это дом на какой улице? Я сразу свяжусь с бригадой."},
                    {"speaker": "client", "text": "Калужская область, дом 23. Уже неделю как такая ситуация."},
                    {"speaker": "operator", "text": "Понял вас. Отправлю старшего бригадира завтра утром для проверки качества. Перезвоню вам."}
                ]
            },
            {
                "duration": 180,
                "speakers": [
                    {"speaker": "operator", "text": "Клининговая компания VasDom, слушаю вас."},
                    {"speaker": "client", "text": "Добрый день! Нужно узнать расценки на уборку большого подъезда."},
                    {"speaker": "operator", "text": "Хорошо! Сколько этажей и квартир в подъезде?"},
                    {"speaker": "client", "text": "9 этажей, 54 квартиры. Площадь подъезда примерно 200 квадратных метров."},
                    {"speaker": "operator", "text": "Понятно. Для такого объема рекомендуем генеральную уборку раз в неделю плюс поддерживающую 2 раза в неделю."},
                    {"speaker": "client", "text": "А сколько это будет стоить в месяц?"},
                    {"speaker": "operator", "text": "Для подъезда такой площади выйдет примерно 15-18 тысяч рублей в месяц. Могу выслать точный расчет?"}
                ]
            }
        ]
        
        # Выбираем случайный диалог
        import random
        conversation = random.choice(sample_conversations)
        
        # Формируем результат транскрибации
        full_text = ""
        dialogue_pairs = []
        current_pair = {"client": "", "operator": ""}
        
        for turn in conversation["speakers"]:
            full_text += f"{turn['speaker'].title()}: {turn['text']}\n"
            
            if turn["speaker"] == "client":
                current_pair["client"] = turn["text"]
            elif turn["speaker"] == "operator":
                current_pair["operator"] = turn["text"]
                if current_pair["client"]:  # Если есть вопрос клиента
                    dialogue_pairs.append(current_pair.copy())
                    current_pair = {"client": "", "operator": ""}
        
        return {
            "success": True,
            "text": full_text.strip(),
            "duration": conversation["duration"],
            "speakers_detected": 2,
            "dialogue_pairs": dialogue_pairs,
            "confidence": 0.95,
            "language": "ru-RU",
            "system": system,
            "audio_file": audio_file_path
        }
    
    def _process_transcription_result(self, raw_result: Dict) -> Dict[str, Any]:
        """Обработка результата транскрибации"""
        if not raw_result.get("success"):
            return raw_result
        
        processed = {
            "success": True,
            "transcription_id": str(uuid.uuid4()),
            "timestamp": datetime.utcnow().isoformat(),
            "text": raw_result.get("text", ""),
            "duration_seconds": raw_result.get("duration", 0),
            "confidence_score": raw_result.get("confidence", 0.0),
            "language": raw_result.get("language", "ru-RU"),
            "speakers_count": raw_result.get("speakers_detected", 0),
            "dialogue_pairs": raw_result.get("dialogue_pairs", []),
            "metadata": {
                "system": raw_result.get("system", "unknown"),
                "audio_file": raw_result.get("audio_file", ""),
                "processing_time": datetime.utcnow().isoformat()
            }
        }
        
        # Оценка качества транскрибации
        processed["quality_assessment"] = self._assess_transcription_quality(processed)
        
        return processed
    
    def _assess_transcription_quality(self, transcription: Dict) -> Dict[str, Any]:
        """Оценка качества транскрибации"""
        
        text = transcription.get("text", "")
        confidence = transcription.get("confidence_score", 0.0)
        duration = transcription.get("duration_seconds", 0)
        
        # Метрики качества
        word_count = len(text.split())
        words_per_minute = (word_count / duration * 60) if duration > 0 else 0
        
        # Определение качества
        quality_score = 0.0
        
        # Факторы качества
        if confidence > 0.9:
            quality_score += 0.4
        elif confidence > 0.7:
            quality_score += 0.3
        elif confidence > 0.5:
            quality_score += 0.2
        
        if 100 <= words_per_minute <= 200:  # Нормальная скорость речи
            quality_score += 0.2
        elif 80 <= words_per_minute <= 250:
            quality_score += 0.1
        
        if word_count >= 50:  # Достаточно слов для анализа
            quality_score += 0.2
        elif word_count >= 20:
            quality_score += 0.1
        
        if len(transcription.get("dialogue_pairs", [])) >= 2:  # Есть диалог
            quality_score += 0.2
        elif len(transcription.get("dialogue_pairs", [])) >= 1:
            quality_score += 0.1
        
        quality_level = "high" if quality_score >= 0.7 else "medium" if quality_score >= 0.4 else "low"
        suitable_for_learning = quality_score >= self.transcription_config["quality_threshold"]
        
        return {
            "quality_score": quality_score,
            "quality_level": quality_level,
            "suitable_for_learning": suitable_for_learning,
            "metrics": {
                "word_count": word_count,
                "words_per_minute": words_per_minute,
                "confidence": confidence,
                "dialogue_pairs_count": len(transcription.get("dialogue_pairs", []))
            }
        }
    
    async def process_crm_calls(self, system: str, date_range: Optional[Dict] = None) -> Dict[str, Any]:
        """
        Обработка звонков из CRM системы
        
        Args:
            system: ID системы (bitrix24, novofon, mango, zadarma)
            date_range: Диапазон дат для обработки
            
        Returns:
            Результат обработки звонков
        """
        try:
            if system not in self.supported_systems:
                raise ValueError(f"Неподдерживаемая система: {system}")
            
            if not self._is_system_configured(system):
                raise ValueError(f"Система {system} не настроена")
            
            logger.info(f"📞 Начало обработки звонков из {self.supported_systems[system]['name']}")
            
            # Получаем список звонков
            calls = await self._fetch_calls_from_system(system, date_range)
            
            processed_calls = []
            learning_data = []
            
            for call in calls:
                # Транскрибируем каждый звонок
                transcription = await self.transcribe_audio_file(call["audio_url"], system)
                
                if transcription.get("success") and transcription.get("quality_assessment", {}).get("suitable_for_learning"):
                    processed_calls.append(transcription)
                    
                    # Подготавливаем данные для обучения
                    for pair in transcription.get("dialogue_pairs", []):
                        if pair.get("client") and pair.get("operator"):
                            learning_data.append({
                                "user_message": pair["client"],
                                "ai_response": pair["operator"],
                                "source": "call_transcription",
                                "system": system,
                                "transcription_id": transcription.get("transcription_id"),
                                "quality_score": transcription.get("quality_assessment", {}).get("quality_score", 0.0)
                            })
            
            result = {
                "success": True,
                "system": system,
                "processed_calls": len(processed_calls),
                "learning_data_extracted": len(learning_data),
                "total_calls_found": len(calls),
                "transcriptions": processed_calls,
                "learning_data": learning_data,
                "timestamp": datetime.utcnow().isoformat()
            }
            
            logger.info(f"✅ Обработано {len(processed_calls)} звонков, извлечено {len(learning_data)} диалогов для обучения")
            
            return result
            
        except Exception as e:
            logger.error(f"❌ Ошибка обработки звонков из {system}: {e}")
            return {
                "success": False,
                "system": system,
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }
    
    async def _fetch_calls_from_system(self, system: str, date_range: Optional[Dict] = None) -> List[Dict]:
        """Получение списка звонков из CRM системы"""
        
        # Временные данные для демонстрации
        # В реальной системе здесь были бы API вызовы к соответствующим сервисам
        
        sample_calls = [
            {
                "call_id": "call_2025_001",
                "phone_number": "+7(123)456-78-90",
                "duration": 120,
                "date": "2025-01-09T10:30:00",
                "audio_url": "https://example.com/call_001.wav",
                "direction": "incoming"
            },
            {
                "call_id": "call_2025_002", 
                "phone_number": "+7(987)654-32-10",
                "duration": 85,
                "date": "2025-01-09T11:15:00",
                "audio_url": "https://example.com/call_002.wav",
                "direction": "incoming"
            },
            {
                "call_id": "call_2025_003",
                "phone_number": "+7(555)123-45-67",
                "duration": 180,
                "date": "2025-01-09T14:22:00", 
                "audio_url": "https://example.com/call_003.wav",
                "direction": "incoming"
            }
        ]
        
        # Фильтрация по длительности
        filtered_calls = [
            call for call in sample_calls 
            if call["duration"] >= self.transcription_config["min_call_duration"]
        ]
        
        logger.info(f"📋 Найдено {len(filtered_calls)} звонков для обработки")
        
        return filtered_calls
    
    def get_system_status(self) -> Dict[str, Any]:
        """Получение статуса всех телефонных систем"""
        status = {
            "service": "Call Transcription Service",
            "version": "1.0.0",
            "supported_systems": {},
            "configuration": self.transcription_config,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        for system_id, config in self.supported_systems.items():
            status["supported_systems"][system_id] = {
                "name": config["name"],
                "configured": self._is_system_configured(system_id),
                "ready_for_transcription": self._is_system_configured(system_id)
            }
        
        return status

# Глобальный экземпляр сервиса
call_transcription_service = CallTranscriptionService()