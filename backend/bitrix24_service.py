import asyncio
import httpx
from typing import Dict, Any, List, Optional
from loguru import logger
import urllib.parse

class Bitrix24Service:
    """Bitrix24 CRM Integration Service"""
    
    def __init__(self, webhook_url: str):
        self.webhook_url = webhook_url.rstrip('/') if webhook_url else ""
        self.client = httpx.AsyncClient(timeout=30.0)
        
        if not webhook_url:
            logger.warning("⚠️ Bitrix24 webhook URL not provided")
        else:
            logger.info("✅ Bitrix24 service initialized")
    
    async def test_connection(self) -> Dict[str, Any]:
        """Test Bitrix24 connection"""
        if not self.webhook_url:
            return {"error": "Webhook URL not configured"}
        
        try:
            # Test with user.current method to get current user info
            url = f"{self.webhook_url}/user.current"
            
            response = await self.client.get(url)
            response.raise_for_status()
            
            data = response.json()
            
            if "result" in data:
                user = data["result"]
                return {
                    "status": "connected",
                    "user": {
                        "id": user.get("ID"),
                        "name": f"{user.get('NAME', '')} {user.get('LAST_NAME', '')}".strip(),
                        "email": user.get("EMAIL"),
                        "position": user.get("WORK_POSITION")
                    },
                    "portal": self.webhook_url.split('/rest/')[0] if '/rest/' in self.webhook_url else "unknown"
                }
            else:
                return {"error": "Invalid response format", "response": data}
                
        except httpx.HTTPError as e:
            logger.error(f"❌ Bitrix24 HTTP error: {e}")
            return {"error": f"HTTP error: {str(e)}"}
        except Exception as e:
            logger.error(f"❌ Bitrix24 connection error: {e}")
            return {"error": str(e)}
    
    async def get_deals(self, start: int = 0, limit: int = 50) -> List[Dict[str, Any]]:
        """Get deals from Bitrix24 with pagination"""
        if not self.webhook_url:
            return []
        
        try:
            url = f"{self.webhook_url}/crm.deal.list"
            
            params = {
                "start": start,
                "limit": limit,
                "order": {"DATE_CREATE": "DESC"},
                "select": ["ID", "TITLE", "STAGE_ID", "OPPORTUNITY", "CURRENCY_ID", "DATE_CREATE", "ASSIGNED_BY_ID", "CONTACT_ID", "COMPANY_ID"]
            }
            
            response = await self.client.post(url, json=params)
            response.raise_for_status()
            
            data = response.json()
            
            if "result" in data:
                deals = data["result"]
                
                # Enrich deals with additional info
                enriched_deals = []
                for deal in deals:
                    enriched_deal = {
                        "id": deal.get("ID"),
                        "title": deal.get("TITLE", "Без названия"),
                        "stage": deal.get("STAGE_ID"),
                        "amount": deal.get("OPPORTUNITY", "0"),
                        "currency": deal.get("CURRENCY_ID", "RUB"),
                        "created": deal.get("DATE_CREATE"),
                        "assigned_by": deal.get("ASSIGNED_BY_ID"),
                        "contact_id": deal.get("CONTACT_ID"),
                        "company_id": deal.get("COMPANY_ID")
                    }
                    enriched_deals.append(enriched_deal)
                
                logger.info(f"✅ Retrieved {len(enriched_deals)} deals from Bitrix24")
                return enriched_deals
            else:
                logger.warning(f"⚠️ Unexpected Bitrix24 response: {data}")
                return []
                
        except Exception as e:
            logger.error(f"❌ Error getting deals: {e}")
            return []
    
    async def get_cleaning_houses(self) -> List[Dict[str, Any]]:
        """Get addresses from 'Уборка подъездов' pipeline"""
        if not self.webhook_url:
            return []
        
        try:
            # First, get all deals
            deals = await self.get_deals(start=0, limit=100)
            
            # Filter for cleaning-related deals (you may need to adjust the filter logic)
            cleaning_deals = []
            for deal in deals:
                title = deal.get("title", "").lower()
                if any(keyword in title for keyword in ["уборка", "подъезд", "клининг", "чистка"]):
                    cleaning_deals.append(deal)
            
            # Extract address information (this would need to be customized based on your Bitrix24 setup)
            houses = []
            for deal in cleaning_deals:
                # Try to get contact info for address
                contact_id = deal.get("contact_id")
                if contact_id:
                    contact_info = await self.get_contact_info(contact_id)
                    address = contact_info.get("address", "Адрес не указан")
                else:
                    address = "Адрес не указан"
                
                houses.append({
                    "deal_id": deal.get("id"),
                    "title": deal.get("title"),
                    "address": address,
                    "amount": deal.get("amount"),
                    "status": deal.get("stage"),
                    "created": deal.get("created")
                })
            
            logger.info(f"✅ Found {len(houses)} cleaning houses")
            return houses
            
        except Exception as e:
            logger.error(f"❌ Error getting cleaning houses: {e}")
            return []
    
    async def get_contact_info(self, contact_id: str) -> Dict[str, Any]:
        """Get contact information by ID"""
        if not self.webhook_url or not contact_id:
            return {}
        
        try:
            url = f"{self.webhook_url}/crm.contact.get"
            params = {"id": contact_id}
            
            response = await self.client.post(url, json=params)
            response.raise_for_status()
            
            data = response.json()
            
            if "result" in data:
                contact = data["result"]
                return {
                    "id": contact.get("ID"),
                    "name": f"{contact.get('NAME', '')} {contact.get('LAST_NAME', '')}".strip(),
                    "phone": self.extract_phone(contact.get("PHONE", [])),
                    "email": self.extract_email(contact.get("EMAIL", [])),
                    "address": self.extract_address(contact.get("ADDRESS", []))
                }
            else:
                return {}
                
        except Exception as e:
            logger.error(f"❌ Error getting contact {contact_id}: {e}")
            return {}
    
    def extract_phone(self, phone_list: List) -> str:
        """Extract primary phone number"""
        if phone_list and isinstance(phone_list, list) and len(phone_list) > 0:
            return phone_list[0].get("VALUE", "")
        return ""
    
    def extract_email(self, email_list: List) -> str:
        """Extract primary email"""
        if email_list and isinstance(email_list, list) and len(email_list) > 0:
            return email_list[0].get("VALUE", "")
        return ""
    
    def extract_address(self, address_list: List) -> str:
        """Extract primary address"""
        if address_list and isinstance(address_list, list) and len(address_list) > 0:
            return address_list[0].get("VALUE", "")
        return ""
    
    async def create_lead(self, title: str, name: str = "", phone: str = "", message: str = "") -> Dict[str, Any]:
        """Create new lead in Bitrix24"""
        if not self.webhook_url:
            return {"error": "Webhook URL not configured"}
        
        try:
            url = f"{self.webhook_url}/crm.lead.add"
            
            fields = {
                "TITLE": title,
                "SOURCE_ID": "TELEGRAM",  # Custom source
                "STATUS_ID": "NEW",
                "COMMENTS": message
            }
            
            if name:
                fields["NAME"] = name
            
            if phone:
                fields["PHONE"] = [{"VALUE": phone, "VALUE_TYPE": "WORK"}]
            
            params = {"fields": fields}
            
            response = await self.client.post(url, json=params)
            response.raise_for_status()
            
            data = response.json()
            
            if "result" in data:
                lead_id = data["result"]
                logger.info(f"✅ Created lead {lead_id} in Bitrix24")
                return {"status": "created", "lead_id": lead_id}
            else:
                return {"error": "Failed to create lead", "response": data}
                
        except Exception as e:
            logger.error(f"❌ Error creating lead: {e}")
            return {"error": str(e)}
    
    async def add_timeline_entry(self, entity_type: str, entity_id: str, message: str) -> Dict[str, Any]:
        """Add timeline entry to CRM entity"""
        if not self.webhook_url:
            return {"error": "Webhook URL not configured"}
        
        try:
            url = f"{self.webhook_url}/crm.timeline.comment.add"
            
            params = {
                "fields": {
                    "ENTITY_ID": entity_id,
                    "ENTITY_TYPE": entity_type,  # "lead", "deal", "contact", etc.
                    "COMMENT": message
                }
            }
            
            response = await self.client.post(url, json=params)
            response.raise_for_status()
            
            data = response.json()
            
            if "result" in data:
                return {"status": "added", "comment_id": data["result"]}
            else:
                return {"error": "Failed to add timeline entry", "response": data}
                
        except Exception as e:
            logger.error(f"❌ Error adding timeline entry: {e}")
            return {"error": str(e)}
    
    async def search_entities(self, query: str, entity_type: str = "contact") -> List[Dict[str, Any]]:
        """Search for entities in Bitrix24"""
        if not self.webhook_url:
            return []
        
        try:
            url = f"{self.webhook_url}/crm.{entity_type}.list"
            
            params = {
                "filter": {
                    "%TITLE": query,
                    "%NAME": query,
                    "%PHONE": query
                },
                "select": ["ID", "TITLE", "NAME", "LAST_NAME", "PHONE"]
            }
            
            response = await self.client.post(url, json=params)
            response.raise_for_status()
            
            data = response.json()
            
            if "result" in data:
                return data["result"]
            else:
                return []
                
        except Exception as e:
            logger.error(f"❌ Error searching entities: {e}")
            return []
    
    async def get_pipeline_stages(self, category_id: int = 0) -> Dict[str, Any]:
        """Get pipeline stages"""
        if not self.webhook_url:
            return {}
        
        try:
            url = f"{self.webhook_url}/crm.status.list"
            params = {"filter": {"ENTITY_ID": "DEAL_STAGE"}}
            
            response = await self.client.post(url, json=params)
            response.raise_for_status()
            
            data = response.json()
            
            if "result" in data:
                stages = {}
                for stage in data["result"]:
                    stages[stage["STATUS_ID"]] = {
                        "name": stage["NAME"],
                        "sort": stage.get("SORT", 0)
                    }
                return stages
            else:
                return {}
                
        except Exception as e:
            logger.error(f"❌ Error getting pipeline stages: {e}")
            return {}
    
    async def __aenter__(self):
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.client.aclose()