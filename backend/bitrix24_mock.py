"""
Mock Bitrix24 Service для демонстрации системы
Возвращает тестовые данные, пока не настроена реальная интеграция
"""
import logging
from typing import Dict, List, Optional
from datetime import datetime

logger = logging.getLogger(__name__)

class MockBitrix24Service:
    """Mock сервис для демонстрации Bitrix24 интеграции"""
    
    def __init__(self):
        self.mock_data = {
            "deals": [
                {
                    "ID": "1",
                    "TITLE": "Уборка подъезда - ул. Ленина 15, Калуга",
                    "STAGE_ID": "NEW", 
                    "OPPORTUNITY": "15000",
                    "CURRENCY_ID": "RUB",
                    "DATE_CREATE": "2025-09-01T10:00:00",
                    "CONTACT_ID": "1"
                },
                {
                    "ID": "2", 
                    "TITLE": "Уборка подъездов - ЖК Березки, Кемерово",
                    "STAGE_ID": "WORK",
                    "OPPORTUNITY": "45000", 
                    "CURRENCY_ID": "RUB",
                    "DATE_CREATE": "2025-09-02T14:30:00",
                    "CONTACT_ID": "2"
                },
                {
                    "ID": "3",
                    "TITLE": "Строительство - Ремонт подъезда ул. Мира 22",
                    "STAGE_ID": "WORK",
                    "OPPORTUNITY": "120000",
                    "CURRENCY_ID": "RUB", 
                    "DATE_CREATE": "2025-08-28T09:15:00",
                    "CONTACT_ID": "3"
                }
            ],
            "contacts": [
                {
                    "ID": "1",
                    "NAME": "Управляющая компания Калуга-Сервис",
                    "PHONE": "+7 (4842) 123-456",
                    "EMAIL": "info@kaluga-service.ru",
                    "ADDRESS": "г. Калуга, ул. Ленина 15"
                },
                {
                    "ID": "2", 
                    "NAME": "ТСЖ Березки",
                    "PHONE": "+7 (3842) 654-321",
                    "EMAIL": "tszh@berezki-kem.ru", 
                    "ADDRESS": "г. Кемерово, ЖК Березки"
                }
            ],
            "companies": [
                {
                    "ID": "1",
                    "TITLE": "ООО Калуга-Сервис", 
                    "ADDRESS": "г. Калуга, ул. Ленина 15",
                    "PHONE": "+7 (4842) 123-456"
                },
                {
                    "ID": "2",
                    "TITLE": "ТСЖ Березки",
                    "ADDRESS": "г. Кемерово, ЖК Березки", 
                    "PHONE": "+7 (3842) 654-321"
                }
            ]
        }
        logger.info("✅ Mock Bitrix24 service initialized with demo data")
    
    async def test_connection(self) -> Dict:
        """Тест подключения - мок версия"""
        return {
            "status": "success",
            "message": "Mock Bitrix24 connection OK (demo data)",
            "user": {
                "ID": "1",
                "NAME": "Demo User",
                "EMAIL": "demo@vas-dom.ru"
            },
            "note": "Это демо-данные. Для реальной интеграции нужен webhook URL из Bitrix24"
        }
    
    async def get_deals(self) -> List[Dict]:
        """Получить сделки - мок версия"""
        logger.info("📋 Returning mock deals data")
        return self.mock_data["deals"]
    
    async def get_cleaning_houses_deals(self) -> List[Dict]:
        """Получить дома для уборки - мок версия"""
        cleaning_deals = [
            deal for deal in self.mock_data["deals"] 
            if "уборка" in deal["TITLE"].lower() or "подъезд" in deal["TITLE"].lower()
        ]
        logger.info(f"🏠 Returning {len(cleaning_deals)} cleaning houses")
        return cleaning_deals
    
    async def get_contacts(self) -> List[Dict]:
        """Получить контакты - мок версия"""
        return self.mock_data["contacts"]
    
    async def get_companies(self) -> List[Dict]:
        """Получить компании - мок версия"""
        return self.mock_data["companies"]
    
    async def get_cleaning_statistics(self) -> Dict:
        """Получить статистику - мок версия"""
        deals = self.mock_data["deals"]
        contacts = self.mock_data["contacts"]
        companies = self.mock_data["companies"]
        
        # Подсчитываем по городам
        kaluga_count = sum(1 for item in contacts + companies if "калуга" in item.get("ADDRESS", "").lower())
        kemerovo_count = sum(1 for item in contacts + companies if "кемерово" in item.get("ADDRESS", "").lower())
        
        return {
            "total_deals": len(deals),
            "total_contacts": len(contacts), 
            "total_companies": len(companies),
            "kaluga_properties": kaluga_count,
            "kemerovo_properties": kemerovo_count,
            "last_updated": datetime.utcnow().isoformat(),
            "note": "Демо-данные для тестирования"
        }
    
    async def create_task(self, title: str, description: str = "", responsible_id: int = 1, deadline: str = None) -> Dict:
        """Создать задачу - мок версия"""
        task_id = f"demo_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"
        
        logger.info(f"📝 Mock task created: {title}")
        
        return {
            'success': True,
            'task_id': task_id,
            'title': title,
            'note': 'Демо-задача создана (реальная интеграция требует настройки Bitrix24)'
        }
    
    async def close(self):
        """Закрыть соединение - мок версия"""
        pass

# Глобальный экземпляр мок-сервиса
mock_bitrix24_service = None

async def get_mock_bitrix24_service():
    """Получить экземпляр мок-сервиса"""
    global mock_bitrix24_service
    if mock_bitrix24_service is None:
        mock_bitrix24_service = MockBitrix24Service()
    return mock_bitrix24_service