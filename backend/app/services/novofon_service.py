"""
Сервис для работы с Novofon API
Документация: https://novofon.github.io/data_api/
"""
import os
import logging
import httpx
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

NOVOFON_API_BASE_URL = "https://api.novofon.com/v1"


class NovofonService:
    """Сервис для работы с Novofon API"""
    
    def __init__(self):
        self.api_key = os.environ.get('NOVOFON_API_KEY', '')
        self.api_secret = os.environ.get('NOVOFON_API_SECRET', '')
        
        if not self.api_key or not self.api_secret:
            logger.warning("Novofon API credentials not configured")
    
    def _get_headers(self) -> Dict[str, str]:
        """Получить заголовки для запросов к Novofon API"""
        return {
            "Content-Type": "application/json",
            "Accept": "application/json"
        }
    
    def _get_auth_params(self) -> Dict[str, str]:
        """Получить параметры аутентификации"""
        return {
            "appid": self.api_key,
            "secret": self.api_secret
        }
    
    async def get_calls(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        limit: int = 100,
        offset: int = 0,
        is_recorded: bool = True
    ) -> List[Dict[str, Any]]:
        """
        Получить список звонков из Novofon
        
        Args:
            start_date: Начало периода (по умолчанию - последние 7 дней)
            end_date: Конец периода (по умолчанию - сейчас)
            limit: Количество записей
            offset: Смещение
            is_recorded: Только звонки с записями
        
        Returns:
            Список звонков
        """
        try:
            if not start_date:
                start_date = datetime.now() - timedelta(days=7)
            if not end_date:
                end_date = datetime.now()
            
            # Параметры запроса
            params = {
                **self._get_auth_params(),
                "start_date": start_date.strftime("%Y-%m-%d"),
                "end_date": end_date.strftime("%Y-%m-%d"),
                "limit": limit,
                "offset": offset
            }
            
            if is_recorded:
                params["is_recorded"] = "1"
            
            url = f"{NOVOFON_API_BASE_URL}/calls"
            
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(
                    url,
                    params=params,
                    headers=self._get_headers()
                )
                
                if response.status_code == 200:
                    data = response.json()
                    calls = data.get("data", []) if isinstance(data, dict) else data
                    logger.info(f"Получено {len(calls)} звонков из Novofon")
                    return calls
                else:
                    logger.error(f"Ошибка получения звонков из Novofon: {response.status_code}, {response.text}")
                    return []
                    
        except Exception as e:
            logger.error(f"Ошибка при запросе к Novofon API: {e}")
            return []
    
    async def get_call_recording_url(self, call_id: str) -> Optional[str]:
        """
        Получить URL записи звонка
        
        Args:
            call_id: ID звонка
        
        Returns:
            URL записи или None
        """
        try:
            params = {
                **self._get_auth_params(),
                "call_id": call_id
            }
            
            url = f"{NOVOFON_API_BASE_URL}/call/recording"
            
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(
                    url,
                    params=params,
                    headers=self._get_headers()
                )
                
                if response.status_code == 200:
                    data = response.json()
                    recording_url = data.get("recording_url") or data.get("url")
                    return recording_url
                else:
                    logger.error(f"Ошибка получения записи звонка {call_id}: {response.status_code}")
                    return None
                    
        except Exception as e:
            logger.error(f"Ошибка при получении записи звонка: {e}")
            return None
    
    async def download_recording(self, recording_url: str) -> Optional[bytes]:
        """
        Скачать аудиозапись звонка
        
        Args:
            recording_url: URL записи
        
        Returns:
            Аудиоданные или None
        """
        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.get(recording_url)
                
                if response.status_code == 200:
                    return response.content
                else:
                    logger.error(f"Ошибка скачивания записи: {response.status_code}")
                    return None
                    
        except Exception as e:
            logger.error(f"Ошибка при скачивании записи: {e}")
            return None


# Глобальный экземпляр сервиса
novofon_service = NovofonService()
