import aiohttp
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime
import os

logger = logging.getLogger(__name__)

class Bitrix24Service:
    """Сервис интеграции с Bitrix24 CRM"""
    
    def __init__(self):
        self.webhook_url = os.getenv("BITRIX24_WEBHOOK_URL")
        if not self.webhook_url:
            raise ValueError("BITRIX24_WEBHOOK_URL environment variable is required")
        
        # Убираем trailing slash если есть
        self.webhook_url = self.webhook_url.rstrip('/')
        
    async def _make_request(self, method: str, params: Dict = None) -> Dict[str, Any]:
        """Базовый метод для запросов к Bitrix24"""
        try:
            url = f"{self.webhook_url}/{method}"
            
            async with aiohttp.ClientSession() as session:
                async with session.post(url, json=params or {}, timeout=30) as response:
                    if response.status == 200:
                        data = await response.json()
                        return data
                    else:
                        error_text = await response.text()
                        logger.error(f"Bitrix24 API error {response.status}: {error_text}")
                        return {"error": f"HTTP {response.status}: {error_text}"}
                        
        except Exception as e:
            logger.error(f"Error making Bitrix24 request: {str(e)}")
            return {"error": str(e)}
    
    async def get_deals(self, limit: int = 50, filter_params: Dict = None) -> List[Dict[str, Any]]:
        """Получает сделки из CRM"""
        params = {
            "SELECT": [
                "ID", "TITLE", "STAGE_ID", "OPPORTUNITY", "CURRENCY_ID",
                "CONTACT_ID", "COMPANY_ID", "DATE_CREATE", "DATE_MODIFY",
                "ASSIGNED_BY_ID", "UF_CRM_*"  # Пользовательские поля
            ],
            "start": 0,
            "limit": limit
        }
        
        if filter_params:
            params["FILTER"] = filter_params
            
        result = await self._make_request("crm.deal.list", params)
        
        if "error" in result:
            return []
            
        deals = result.get("result", [])
        return deals
    
    async def get_cleaning_houses(self) -> List[Dict[str, Any]]:
        """Получает дома для уборки подъездов"""
        # Ищем сделки с определенным типом или категорией
        filter_params = {
            "CATEGORY_ID": "0",  # Базовая воронка
            "STAGE_ID": ["NEW", "PREPARATION", "PREPAYMENT_INVOICE", "EXECUTING", "FINAL_INVOICE"]  # Активные стадии
        }
        
        deals = await self.get_deals(limit=500, filter_params=filter_params)
        
        # Преобразуем в формат домов
        houses = []
        for deal in deals:
            house = {
                "id": deal.get("ID"),
                "title": deal.get("TITLE", ""),
                "address": deal.get("TITLE", ""),  # В title обычно адрес
                "stage": deal.get("STAGE_ID"),
                "value": float(deal.get("OPPORTUNITY", 0)),
                "currency": deal.get("CURRENCY_ID", "RUB"),
                "contact_id": deal.get("CONTACT_ID"),
                "assigned_user": deal.get("ASSIGNED_BY_ID"),
                "created": deal.get("DATE_CREATE"),
                "modified": deal.get("DATE_MODIFY"),
                "status": "active" if deal.get("STAGE_ID") not in ["WON", "LOST"] else "completed"
            }
            
            # Получаем дополнительные поля если есть
            for field, value in deal.items():
                if field.startswith("UF_CRM_"):
                    house[field] = value
            
            houses.append(house)
        
        return houses
    
    async def get_contacts(self, contact_ids: List[str] = None) -> List[Dict[str, Any]]:
        """Получает контакты"""
        params = {
            "SELECT": [
                "ID", "NAME", "LAST_NAME", "SECOND_NAME", "COMPANY_TITLE",
                "PHONE", "EMAIL", "ADDRESS", "DATE_CREATE"
            ]
        }
        
        if contact_ids:
            params["FILTER"] = {"ID": contact_ids}
            
        result = await self._make_request("crm.contact.list", params)
        return result.get("result", [])
    
    async def create_deal(self, deal_data: Dict[str, Any]) -> Dict[str, Any]:
        """Создает новую сделку"""
        params = {
            "fields": deal_data
        }
        
        result = await self._make_request("crm.deal.add", params)
        return result
    
    async def update_deal(self, deal_id: str, deal_data: Dict[str, Any]) -> Dict[str, Any]:
        """Обновляет сделку"""
        params = {
            "id": deal_id,
            "fields": deal_data
        }
        
        result = await self._make_request("crm.deal.update", params)
        return result
    
    async def create_task(self, task_data: Dict[str, Any]) -> Dict[str, Any]:
        """Создает задачу в Bitrix24"""
        params = {
            "fields": {
                "TITLE": task_data.get("title", ""),
                "DESCRIPTION": task_data.get("description", ""),
                "RESPONSIBLE_ID": task_data.get("responsible_id"),
                "DEADLINE": task_data.get("deadline"),
                "GROUP_ID": task_data.get("group_id"),
                "UF_CRM_TASK": task_data.get("crm_ids", [])  # Связь с CRM
            }
        }
        
        result = await self._make_request("tasks.task.add", params)
        return result
    
    async def get_users(self) -> List[Dict[str, Any]]:
        """Получает пользователей Bitrix24"""
        params = {
            "SELECT": ["ID", "NAME", "LAST_NAME", "EMAIL", "WORK_PHONE", "PERSONAL_MOBILE"]
        }
        
        result = await self._make_request("user.get", params)
        return result.get("result", [])
    
    async def sync_employees_with_bitrix(self, db) -> Dict[str, Any]:
        """Синхронизирует сотрудников с Bitrix24"""
        try:
            bitrix_users = await self.get_users()
            synced_count = 0
            
            for user in bitrix_users:
                # Ищем сотрудника в нашей БД
                existing = await db.employees.find_one({"bitrix24_id": user["ID"]})
                
                employee_data = {
                    "full_name": f"{user.get('NAME', '')} {user.get('LAST_NAME', '')}".strip(),
                    "phone": user.get("WORK_PHONE") or user.get("PERSONAL_MOBILE", ""),
                    "bitrix24_id": user["ID"],
                    "updated_at": datetime.utcnow()
                }
                
                if existing:
                    # Обновляем существующего
                    await db.employees.update_one(
                        {"bitrix24_id": user["ID"]},
                        {"$set": employee_data}
                    )
                else:
                    # Создаем нового
                    employee_data.update({
                        "id": f"emp_{user['ID']}",
                        "role": "client_manager",  # По умолчанию
                        "department": "Администрация",
                        "active": True,
                        "performance_score": 5.0,
                        "created_at": datetime.utcnow(),
                        "notes": []
                    })
                    await db.employees.insert_one(employee_data)
                
                synced_count += 1
            
            return {"status": "success", "synced": synced_count}
            
        except Exception as e:
            logger.error(f"Error syncing employees with Bitrix24: {str(e)}")
            return {"status": "error", "error": str(e)}
    
    async def sync_projects_with_deals(self, db) -> Dict[str, Any]:
        """Синхронизирует проекты с сделками Bitrix24"""
        try:
            deals = await self.get_deals(limit=100)
            synced_count = 0
            
            for deal in deals:
                # Ищем проект в нашей БД
                existing = await db.projects.find_one({"bitrix24_deal_id": deal["ID"]})
                
                project_data = {
                    "name": deal.get("TITLE", ""),
                    "type": "cleaning",  # Определяем тип по категории или другим полям
                    "status": self._map_deal_stage_to_project_status(deal.get("STAGE_ID")),
                    "budget": float(deal.get("OPPORTUNITY", 0)),
                    "bitrix24_deal_id": deal["ID"],
                    "updated_at": datetime.utcnow()
                }
                
                if existing:
                    await db.projects.update_one(
                        {"bitrix24_deal_id": deal["ID"]},
                        {"$set": project_data}
                    )
                else:
                    project_data.update({
                        "id": f"proj_{deal['ID']}",
                        "description": f"Проект из сделки Bitrix24 #{deal['ID']}",
                        "client_id": deal.get("CONTACT_ID", "unknown"),
                        "manager_id": deal.get("ASSIGNED_BY_ID", "unknown"),
                        "team_members": [],
                        "progress": 0.0,
                        "actual_cost": 0.0,
                        "created_at": datetime.utcnow()
                    })
                    await db.projects.insert_one(project_data)
                
                synced_count += 1
            
            return {"status": "success", "synced": synced_count}
            
        except Exception as e:
            logger.error(f"Error syncing projects with Bitrix24: {str(e)}")
            return {"status": "error", "error": str(e)}
    
    def _map_deal_stage_to_project_status(self, stage_id: str) -> str:
        """Маппинг стадий сделки на статус проекта"""
        stage_mapping = {
            "NEW": "planning",
            "PREPARATION": "planning", 
            "PREPAYMENT_INVOICE": "active",
            "EXECUTING": "active",
            "FINAL_INVOICE": "active",
            "WON": "completed",
            "LOST": "cancelled"
        }
        
        return stage_mapping.get(stage_id, "planning")
    
    async def test_connection(self) -> Dict[str, Any]:
        """Тестирует подключение к Bitrix24"""
        try:
            result = await self._make_request("app.info")
            
            if "error" in result:
                return {"status": "error", "message": result["error"]}
            
            return {
                "status": "success",
                "bitrix_info": result.get("result", {}),
                "webhook_url": self.webhook_url
            }
            
        except Exception as e:
            return {"status": "error", "message": str(e)}