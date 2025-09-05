import os
import asyncio
import aiohttp
import json
from typing import Dict, List, Optional, Any
from datetime import datetime
from dotenv import load_dotenv
import logging

# Load environment variables
load_dotenv()

logger = logging.getLogger(__name__)

class Bitrix24Service:
    """Service for Bitrix24 API integration"""
    
    def __init__(self):
        self.webhook_url = os.getenv("BITRIX24_WEBHOOK_URL")
        if not self.webhook_url:
            raise ValueError("BITRIX24_WEBHOOK_URL not found in environment variables")
        
        # Ensure webhook URL ends with /
        if not self.webhook_url.endswith('/'):
            self.webhook_url += '/'
        
        self.session = None
        
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
        session = await self._get_session()
        
        try:
            async with session.post(url, json=params) as response:
                if response.status == 200:
                    result = await response.json()
                    return result
                else:
                    error_text = await response.text()
                    logger.error(f"Bitrix24 API error {response.status}: {error_text}")
                    return {"error": f"HTTP {response.status}: {error_text}"}
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
                                  "DATE_CREATE", "DATE_MODIFY", "OPPORTUNITY", "CURRENCY_ID"]
            
            result = await self.call_method("crm.deal.list", params)
            return result.get("result", [])
        except Exception as e:
            logger.error(f"Error getting deals: {e}")
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
                address = contact.get("ADDRESS", "").lower()
                if "калуга" in address:
                    kaluga_count += 1
                elif "кемерово" in address:
                    kemerovo_count += 1
            
            for company in companies:
                address = company.get("ADDRESS", "").lower() 
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

# Global service instance
bitrix24_service = None

async def get_bitrix24_service():
    """Get or create Bitrix24 service instance"""
    global bitrix24_service
    if bitrix24_service is None:
        bitrix24_service = Bitrix24Service()
    return bitrix24_service