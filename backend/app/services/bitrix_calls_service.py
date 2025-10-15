"""
Сервис для работы со звонками в Bitrix24
"""
import httpx
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import os

logger = logging.getLogger(__name__)

class BitrixCallsService:
    def __init__(self):
        self.webhook_url = os.getenv("BITRIX24_WEBHOOK_URL", "").rstrip('/') + '/'
        self.timeout = httpx.Timeout(30.0)
    
    async def get_recent_calls(self, limit: int = 50) -> List[Dict[str, Any]]:
        """
        Получить последние звонки из Bitrix24
        """
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                # Получаем список звонков через voximplant.statistic.get
                response = await client.post(
                    f"{self.webhook_url}voximplant.statistic.get",
                    json={
                        "FILTER": {
                            ">=CALL_START_DATE": (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d")
                        },
                        "SORT": "CALL_START_DATE",
                        "ORDER": "DESC"
                    }
                )
                
                if response.status_code != 200:
                    logger.error(f"Failed to get calls from Bitrix24: {response.status_code}")
                    return []
                
                data = response.json()
                
                if not data.get("result"):
                    logger.warning("No calls found in Bitrix24")
                    return []
                
                calls = data["result"]
                logger.info(f"✅ Retrieved {len(calls)} calls from Bitrix24")
                
                return calls[:limit]
                
        except Exception as e:
            logger.error(f"Error getting calls from Bitrix24: {e}")
            return []
    
    async def get_call_details(self, call_id: str) -> Optional[Dict[str, Any]]:
        """
        Получить детали конкретного звонка
        """
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    f"{self.webhook_url}voximplant.statistic.get",
                    json={
                        "FILTER": {
                            "CALL_ID": call_id
                        }
                    }
                )
                
                if response.status_code != 200:
                    return None
                
                data = response.json()
                
                if data.get("result") and len(data["result"]) > 0:
                    return data["result"][0]
                
                return None
                
        except Exception as e:
            logger.error(f"Error getting call details: {e}")
            return None
    
    async def get_call_recording(self, call_id: str) -> Optional[str]:
        """
        Получить ссылку на запись звонка
        """
        try:
            call_details = await self.get_call_details(call_id)
            
            if not call_details:
                return None
            
            # В Bitrix24 запись звонка хранится в поле RECORD_FILE_ID
            record_file_id = call_details.get("RECORD_FILE_ID")
            
            if not record_file_id:
                logger.warning(f"No recording found for call {call_id}")
                return None
            
            # Получаем ссылку на файл через disk.file.get
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    f"{self.webhook_url}disk.file.get",
                    json={
                        "id": record_file_id
                    }
                )
                
                if response.status_code != 200:
                    return None
                
                file_data = response.json()
                
                if file_data.get("result"):
                    download_url = file_data["result"].get("DOWNLOAD_URL")
                    
                    # Добавляем базовый URL если нужно
                    if download_url and not download_url.startswith("http"):
                        portal_url = self.webhook_url.split("/rest/")[0]
                        download_url = f"{portal_url}{download_url}"
                    
                    return download_url
                
                return None
                
        except Exception as e:
            logger.error(f"Error getting call recording: {e}")
            return None
    
    async def search_calls_by_phone(self, phone: str) -> List[Dict[str, Any]]:
        """
        Поиск звонков по номеру телефона
        """
        try:
            # Очищаем номер от лишних символов
            clean_phone = phone.replace("+", "").replace("-", "").replace(" ", "").replace("(", "").replace(")", "")
            
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    f"{self.webhook_url}voximplant.statistic.get",
                    json={
                        "FILTER": {
                            "PHONE_NUMBER": clean_phone
                        },
                        "SORT": "CALL_START_DATE",
                        "ORDER": "DESC"
                    }
                )
                
                if response.status_code != 200:
                    return []
                
                data = response.json()
                
                return data.get("result", [])
                
        except Exception as e:
            logger.error(f"Error searching calls by phone: {e}")
            return []
    
    def format_call_info(self, call: Dict[str, Any]) -> Dict[str, Any]:
        """
        Форматировать информацию о звонке в удобный вид
        """
        return {
            "call_id": call.get("CALL_ID", ""),
            "portal_call_id": call.get("PORTAL_CALL_ID", ""),
            "phone_number": call.get("PHONE_NUMBER", ""),
            "direction": "in" if call.get("CALL_TYPE") == "1" else "out",
            "duration": call.get("CALL_DURATION", 0),
            "status": self._get_call_status(call.get("CALL_STATUS")),
            "start_date": call.get("CALL_START_DATE", ""),
            "portal_user_id": call.get("PORTAL_USER_ID", ""),
            "has_record": bool(call.get("RECORD_FILE_ID")),
            "record_file_id": call.get("RECORD_FILE_ID"),
            "cost": call.get("COST", 0),
            "cost_currency": call.get("COST_CURRENCY", "RUB")
        }
    
    def _get_call_status(self, status_code: str) -> str:
        """
        Преобразовать код статуса в читаемый текст
        """
        status_map = {
            "200": "answered",  # Отвечен
            "304": "missed",    # Пропущен
            "603": "declined",  # Отклонен
            "486": "busy",      # Занято
            "487": "cancelled", # Отменен
            "404": "not_found"  # Не найден
        }
        
        return status_map.get(str(status_code), "unknown")
