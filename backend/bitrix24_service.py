import os
import aiohttp
import httpx
from typing import Dict, List, Optional
from datetime import datetime
from dotenv import load_dotenv
import logging

# Load environment variables
load_dotenv()

logger = logging.getLogger(__name__)

class Bitrix24Service:
    """Service for Bitrix24 API integration"""
    
    def __init__(self):
        # Получаем данные приложения
        self.portal_url = os.getenv("BITRIX24_PORTAL_URL", "https://vas-dom.bitrix24.ru")
        self.client_id = os.getenv("BITRIX24_CLIENT_ID")
        self.client_secret = os.getenv("BITRIX24_CLIENT_SECRET")
        
        # ПРИОРИТЕТ: используем прямой WEBHOOK_URL если есть
        self.webhook_url = os.getenv("BITRIX24_WEBHOOK_URL")
        
        if self.webhook_url:
            logger.info(f"✅ Using direct Bitrix24 webhook: {self.webhook_url}")
        elif self.client_id:
            # Fallback на формирование URL из CLIENT_ID
            self.webhook_url = f"{self.portal_url}/rest/1/{self.client_id}/"
            logger.info(f"⚠️ Using Bitrix24 app integration: {self.client_id}")
        else:
            raise ValueError("BITRIX24_WEBHOOK_URL or BITRIX24_CLIENT_ID must be provided")
        
        # Ensure webhook URL ends with /
        if not self.webhook_url.endswith('/'):
            self.webhook_url += '/'
        
        self.session = None
        logger.info(f"🔗 Bitrix24 service initialized with URL: {self.webhook_url}")
        
    async def _get_session(self):
        """Get or create aiohttp session"""
        if self.session is None:
            self.session = aiohttp.ClientSession()
        return self.session
    
    async def close(self):
        """Close aiohttp session"""
        if self.session:
            await self.session.close()

    async def call_method(self, method: str, params: Dict = None) -> Dict:
        """Make API call to Bitrix24"""
        if params is None:
            params = {}
        
        url = f"{self.webhook_url}{method}"
        logger.info(f"🔗 Calling Bitrix24: {method} at {url}")
        
        try:
            # Используем httpx напрямую для более надежного подключения
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(url, json=params if params else None)
                
                if response.status_code == 200:
                    result = response.json()
                    # Bitrix24 возвращает структуру {result: ..., time: ...}
                    if "result" in result:
                        logger.info(f"✅ Bitrix24 API success: {method} - {len(result.get('result', []))} items")
                        return result
                    elif "error" in result:
                        logger.error(f"❌ Bitrix24 API error: {result['error']}")
                        return result
                    else:
                        return result
                else:
                    error_text = response.text
                    logger.error(f"Bitrix24 API error {response.status_code}: {error_text}")
                    return {"error": f"HTTP {response.status_code}: {error_text}"}
        except Exception as e:
            logger.error(f"Bitrix24 API call failed: {e}")
            return {"error": str(e)}

    async def test_connection(self) -> Dict:
        """Test Bitrix24 connection"""
        try:
            result = await self.call_method("user.current")
            if "result" in result:
                return {
                    "status": "success",
                    "user": result["result"],
                    "message": "Bitrix24 connection successful"
                }
            else:
                return {
                    "status": "error",
                    "message": "Invalid response from Bitrix24",
                    "details": result
                }
        except Exception as e:
            return {
                "status": "error", 
                "message": f"Connection test failed: {e}"
            }

    async def get_deal_categories(self) -> List[Dict]:
        """Get all deal pipelines/categories"""
        try:
            result = await self.call_method("crm.dealcategory.list")
            return result.get("result", [])
        except Exception as e:
            logger.error(f"Error getting deal categories: {e}")
            return []

    async def find_cleaning_pipeline(self) -> Optional[Dict]:
        """Find the 'уборка подъездов' pipeline"""
        try:
            categories = await self.get_deal_categories()
            
            for category in categories:
                name = category.get("NAME", "").lower()
                if "уборка" in name or "подъезд" in name or "клининг" in name:
                    logger.info(f"Found cleaning pipeline: {category.get('NAME')}")
                    return category
            
            # If no specific pipeline found, return default
            if categories:
                logger.info("No specific cleaning pipeline found, using default")
                return categories[0]
            
            return None
        except Exception as e:
            logger.error(f"Error finding cleaning pipeline: {e}")
            return None

    async def get_deals(self, filter_params: Dict = None, select: List = None) -> List[Dict]:
        """Get deals with optional filtering"""
        try:
            params = {}
            if filter_params:
                params["filter"] = filter_params
            if select:
                params["select"] = select
            else:
                params["select"] = ["ID", "TITLE", "STAGE_ID", "CONTACT_ID", "ASSIGNED_BY_ID", 
                                  "DATE_CREATE", "DATE_MODIFY", "OPPORTUNITY", "CURRENCY_ID", "COMPANY_ID"]
            
            result = await self.call_method("crm.deal.list", params)
            deals = result.get("result", [])
            logger.info(f"📋 Retrieved {len(deals)} deals from Bitrix24")
            if len(deals) == 0:
                logger.warning(f"⚠️ No deals found. Full result: {result}")
            return deals
        except Exception as e:
            logger.error(f"Error getting deals: {e}")
            return []

    async def get_cleaning_houses_deals(self) -> List[Dict]:
        """Get all houses from 'Уборка подъездов' funnel (remove 'в работе' filter to show all)"""
        try:
            # Get all deals from cleaning funnel without status filter
            params = {
                'select': ['ID', 'TITLE', 'STAGE_ID', 'OPPORTUNITY', 'CURRENCY_ID', 'DATE_CREATE', 'DATE_MODIFY', 'CONTACT_ID', 'COMPANY_ID'],
                'filter': {
                    'CATEGORY_ID': '0'  # Main funnel, adjust if cleaning funnel has different ID
                }
            }
            
            response = await self.call_method('crm.deal.list', params)
            deals = response.get('result', [])
            
            # Filter for cleaning deals by title or other criteria
            cleaning_deals = []
            for deal in deals:
                title = deal.get('TITLE', '').lower()
                if any(keyword in title for keyword in ['подъезд', 'уборка', 'дом', 'калуга']):
                    cleaning_deals.append(deal)
            
            logger.info(f"Found {len(cleaning_deals)} cleaning house deals")
            return cleaning_deals
            
        except Exception as e:
            logger.error(f"Error getting cleaning houses: {e}")
            return []

    async def get_contacts(self, filter_params: Dict = None) -> List[Dict]:
        """Get contacts with optional filtering"""
        try:
            params = {}
            if filter_params:
                params["filter"] = filter_params
            
            params["select"] = ["ID", "NAME", "LAST_NAME", "PHONE", "EMAIL", "ADDRESS"]
            
            result = await self.call_method("crm.contact.list", params)
            return result.get("result", [])
        except Exception as e:
            logger.error(f"Error getting contacts: {e}")
            return []

    async def get_companies(self, filter_params: Dict = None) -> List[Dict]:
        """Get companies (properties/buildings)"""
        try:
            params = {}
            if filter_params:
                params["filter"] = filter_params
            
            params["select"] = ["ID", "TITLE", "ADDRESS", "PHONE", "EMAIL", "ASSIGNED_BY_ID"]
            
            result = await self.call_method("crm.company.list", params)
            return result.get("result", [])
        except Exception as e:
            logger.error(f"Error getting companies: {e}")
            return []

    async def create_deal(self, deal_data: Dict) -> Optional[int]:
        """Create new deal"""
        try:
            params = {"fields": deal_data}
            result = await self.call_method("crm.deal.add", params)
            
            if "result" in result:
                return int(result["result"])
            else:
                logger.error(f"Error creating deal: {result}")
                return None
        except Exception as e:
            logger.error(f"Error creating deal: {e}")
            return None

    async def update_deal(self, deal_id: int, update_data: Dict) -> bool:
        """Update existing deal"""
        try:
            params = {
                "id": deal_id,
                "fields": update_data
            }
            result = await self.call_method("crm.deal.update", params)
            return "result" in result and result["result"]
        except Exception as e:
            logger.error(f"Error updating deal {deal_id}: {e}")
            return False

    async def get_deal_fields(self) -> Dict:
        """Get available deal fields"""
        try:
            result = await self.call_method("crm.deal.fields")
            return result.get("result", {})
        except Exception as e:
            logger.error(f"Error getting deal fields: {e}")
            return {}

    async def get_cleaning_statistics(self) -> Dict:
        """Get cleaning business statistics"""
        try:
            # Get all deals
            deals = await self.get_deals()
            
            # Get all contacts (properties)
            contacts = await self.get_contacts()
            
            # Get all companies (buildings)
            companies = await self.get_companies()
            
            # Parse addresses to get city distribution
            kaluga_count = 0
            kemerovo_count = 0
            
            for contact in contacts:
                address = contact.get("ADDRESS") or ""
                address = address.lower() if address else ""
                if "калуга" in address:
                    kaluga_count += 1
                elif "кемерово" in address:
                    kemerovo_count += 1
            
            for company in companies:
                address = company.get("ADDRESS") or ""
                address = address.lower() if address else ""
                if "калуга" in address:
                    kaluga_count += 1
                elif "кемерово" in address:
                    kemerovo_count += 1
            
            return {
                "total_deals": len(deals),
                "total_contacts": len(contacts),
                "total_companies": len(companies),
                "kaluga_properties": kaluga_count,
                "kemerovo_properties": kemerovo_count,
                "last_updated": datetime.utcnow().isoformat()
            }
        except Exception as e:
            logger.error(f"Error getting cleaning statistics: {e}")
            return {
                "total_deals": 0,
                "total_contacts": 0, 
                "total_companies": 0,
                "kaluga_properties": 0,
                "kemerovo_properties": 0,
                "error": str(e)
            }

    async def create_test_deal(self, title: str, opportunity: int = 50000) -> Dict:
        """Create a test deal"""
        try:
            params = {
                'fields': {
                    'TITLE': title,
                    'OPPORTUNITY': opportunity,
                    'CURRENCY_ID': 'RUB',
                    'STAGE_ID': 'NEW'
                }
            }
            
            response = await self.call_method('crm.deal.add', params)
            return response
        except Exception as e:
            logger.error(f"Error creating test deal: {e}")
            return {'error': str(e)}

    async def create_task(self, title: str, description: str = "", responsible_id: int = 1, deadline: str = None) -> Dict:
        """Create task in Bitrix24"""
        try:
            fields = {
                'TITLE': title,
                'DESCRIPTION': description,
                'RESPONSIBLE_ID': responsible_id,
                'CREATED_BY': 1,  # System user
                'STATUS': '2',  # In progress
                'PRIORITY': '1'  # Normal priority
            }
            
            if deadline:
                fields['DEADLINE'] = deadline
            
            params = {'fields': fields}
            response = await self.call_method('tasks.task.add', params)
            
            if response.get('result'):
                logger.info(f"Task created successfully: {title}")
                return {
                    'success': True,
                    'task_id': response['result']['task']['id'],
                    'title': title
                }
            else:
                return {'success': False, 'error': 'Failed to create task'}
                
        except Exception as e:
            logger.error(f"Error creating task: {e}")
            return {'success': False, 'error': str(e)}

    async def get_tasks(self, filter_params: Dict = None) -> List[Dict]:
        """Get tasks from Bitrix24"""
        try:
            params = {
                'select': ['ID', 'TITLE', 'DESCRIPTION', 'STATUS', 'RESPONSIBLE_ID', 'CREATED_BY', 'CREATED_DATE', 'DEADLINE'],
                'filter': filter_params or {}
            }
            
            response = await self.call_method('tasks.task.list', params)
            return response.get('result', {}).get('tasks', [])
        except Exception as e:
            logger.error(f"Error getting tasks: {e}")
            return []

    async def update_task_status(self, task_id: int, status: str = '5') -> Dict:
        """Update task status (5 = completed)"""
        try:
            params = {
                'taskId': task_id,
                'fields': {'STATUS': status}
            }
            
            await self.call_method('tasks.task.update', params)
            return {'success': True, 'task_id': task_id, 'status': status}
        except Exception as e:
            logger.error(f"Error updating task: {e}")
            return {'success': False, 'error': str(e)}

    async def add_task_comment(self, task_id: int, comment: str) -> Dict:
        """Add comment to task"""
        try:
            params = {
                'taskId': task_id,
                'fields': {'POST_MESSAGE': comment}
            }
            
            response = await self.call_method('tasks.task.comment.add', params)
            return {'success': True, 'comment_id': response.get('result')}
        except Exception as e:
            logger.error(f"Error adding comment: {e}")
            return {'success': False, 'error': str(e)}

# Global service instance
bitrix24_service = None

async def get_bitrix24_service():
    """Get or create Bitrix24 service instance"""
    global bitrix24_service
    if bitrix24_service is None:
        bitrix24_service = Bitrix24Service()
    return bitrix24_service