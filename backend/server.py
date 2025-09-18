from fastapi import FastAPI, APIRouter, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
import os
import logging
import httpx
import asyncio
from datetime import datetime, timezone
from pathlib import Path
import json

# Load environment variables
ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(title="VasDom AudioBot API", description="Интеллектуальная система управления клининговой компанией", version="1.0.0")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=os.environ.get('CORS_ORIGINS', '*').split(','),
    allow_methods=["*"],
    allow_headers=["*"],
)

# API Router with /api prefix
api_router = APIRouter(prefix="/api")

# ============================================================================
# MODELS & SCHEMAS (from working branch)
# ============================================================================
class HouseResponse(BaseModel):
    id: int
    title: str
    address: str
    brigade: Optional[str] = ""
    management_company: Optional[str] = ""
    status: Optional[str] = ""
    apartments: int = 0
    entrances: int = 0
    floors: int = 0
    cleaning_dates: Dict = Field(default_factory=dict)
    periodicity: Optional[str] = "индивидуальная"
    bitrix_url: Optional[str] = ""

class HousesResponse(BaseModel):
    houses: List[HouseResponse]
    total: int
    page: int
    limit: int
    pages: int

class FiltersResponse(BaseModel):
    brigades: List[str] = Field(default_factory=list)
    management_companies: List[str] = Field(default_factory=list)
    statuses: List[str] = Field(default_factory=list)

# ============================================================================
# BITRIX24 SERVICE (as in Bitrix1 branch)
# ============================================================================
class BitrixService:
    def __init__(self):
        self.webhook_url = os.environ.get('BITRIX24_WEBHOOK_URL', '')
        self.base_url = self.webhook_url.rstrip('/') if self.webhook_url else ""
        self._user_cache: Dict[str, Dict[str, Any]] = {}
        self._user_cache_ttl_seconds = int(os.environ.get('BITRIX_USER_CACHE_TTL', '600'))
        self._enum_cache: Dict[str, Dict[str, Any]] = {}
        self._enum_cache_ttl_seconds = int(os.environ.get('BITRIX_ENUM_CACHE_TTL', '3600'))
        self._deals_cache: Dict[str, Dict[str, Any]] = {}
        self._deals_cache_ttl_seconds = int(os.environ.get('DEALS_CACHE_TTL', '120'))

    async def _make_request(self, method: str, params: Dict = None) -> Dict:
        if not self.base_url:
            logger.warning("Bitrix24 webhook URL not configured")
            return {"ok": False, "result": None}
        url = f"{self.base_url}/{method}"
        retries = 2
        last_error = None
        for attempt in range(retries + 1):
            try:
                async with httpx.AsyncClient(timeout=30.0) as client:
                    response = await client.post(url, json=params or {})
                    response.raise_for_status()
                    data = response.json()
                    return {"ok": True, "result": data.get("result"), "next": data.get("next"), "total": data.get("total")}
            except Exception as e:
                last_error = e
                logger.error(f"Bitrix24 request error (attempt {attempt+1}/{retries+1}): {e}")
                await asyncio.sleep(0.3 * (attempt + 1))
        return {"ok": False, "result": None, "error": str(last_error) if last_error else "unknown"}

    async def get_company_details(self, company_id: str) -> Dict:
        try:
            if not company_id:
                return {}
            if not hasattr(self, "_company_cache"):
                self._company_cache = {}
                self._company_cache_ttl_seconds = int(os.environ.get('BITRIX_COMPANY_CACHE_TTL', '1800'))
            now_ts = int(datetime.now(timezone.utc).timestamp())
            ce = self._company_cache.get(str(company_id))
            if ce and now_ts - ce.get("ts", 0) < self._company_cache_ttl_seconds:
                return ce.get("data", {})
            response = await self._make_request("crm.company.get", {"id": company_id})
            if not response.get("ok"):
                logger.warning(f"crm.company.get failed for ID {company_id}: {response.get('error')}")
                return {}
            company_data = response.get("result") or {}
            if isinstance(company_data, list):
                company_data = company_data[0] if company_data else {}
            self._company_cache[str(company_id)] = {"data": company_data, "ts": now_ts}
            return company_data
        except Exception as e:
            logger.error(f"Error getting company details: {e}")
            return {}

    async def get_user_details(self, user_id: str) -> Dict:
        try:
            if not user_id:
                return {}
            cache_entry = self._user_cache.get(str(user_id))
            now_ts = int(datetime.now(timezone.utc).timestamp())
            if cache_entry and now_ts - cache_entry.get("ts", 0) < self._user_cache_ttl_seconds:
                return cache_entry.get("data", {})
            response = await self._make_request("user.get", {"ID": user_id})
            if not response.get("ok"):
                logger.warning(f"user.get failed for ID {user_id}: {response.get('error')}")
                return {}
            user_list = response.get("result") or []
            user = user_list[0] if isinstance(user_list, list) and user_list else {}
            if user:
                self._user_cache[str(user_id)] = {"data": user, "ts": now_ts}
            return user
        except Exception as e:
            logger.error(f"Error getting user details: {e}")
            return {}

    async def get_contact_details(self, contact_id: str) -> Dict:
        try:
            if not contact_id:
                return {}
            response = await self._make_request("crm.contact.get", {"id": contact_id})
            if not response.get("ok"):
                logger.warning(f"crm.contact.get failed for ID {contact_id}: {response.get('error')}")
                return {}
            return response.get("result") or {}
        except Exception as e:
            logger.error(f"Error getting contact details: {e}")
            return {}

    async def get_field_enum_map(self, field_name: str) -> Dict[str, str]:
        try:
            if not field_name:
                return {}
            cache_entry = self._enum_cache.get(field_name)
            now_ts = int(datetime.now(timezone.utc).timestamp())
            if cache_entry and now_ts - cache_entry.get("ts", 0) < self._enum_cache_ttl_seconds:
                return cache_entry.get("data", {})
            response = await self._make_request("crm.deal.userfield.list", {"filter": {"FIELD_NAME": field_name}})
            if not response.get("ok"):
                logger.warning(f"crm.deal.userfield.list failed for {field_name}: {response.get('error')}")
                return {}
            fields = response.get("result") or []
            mapping: Dict[str, str] = {}
            if isinstance(fields, list) and fields:
                field = fields[0]
                for item in field.get("LIST", []) or []:
                    id_str = str(item.get("ID")); value = item.get("VALUE")
                    if id_str and value: mapping[id_str] = value
            self._enum_cache[field_name] = {"data": mapping, "ts": now_ts}
            return mapping
        except Exception as e:
            logger.error(f"Error getting enum map for {field_name}: {e}")
            return {}

    async def get_total_deals_count(self) -> int:
        try:
            limit = 100; start = 0; total = 0
            while True:
                response = await self._make_request("crm.deal.list", {"select": ["ID"], "filter": {"CATEGORY_ID": "34"}, "order": {"ID": "DESC"}, "start": start, "limit": limit})
                if not response.get("ok"):
                    logger.warning(f"crm.deal.list call failed in total counter: {response.get('error')}")
                    break
                if response.get("total") is not None:
                    total = int(response.get("total") or 0); break
                batch = response.get("result", []) or []
                total += len(batch)
                next_start = response.get("next")
                if next_start is None: break
                start = next_start
            return total if total > 0 else 490
        except Exception as e:
            logger.error(f"Error getting total deals count: {e}")
            return 490

    async def _enrich_deal_data(self, deal: Dict) -> Dict:
        if deal.get("COMPANY_ID"):
            try:
                company_data = await self.get_company_details(deal["COMPANY_ID"])
                deal["COMPANY_TITLE_ENRICHED"] = company_data.get("TITLE", "")
            except Exception:
                deal["COMPANY_TITLE_ENRICHED"] = ""
        else:
            deal["COMPANY_TITLE_ENRICHED"] = ""

        if deal.get("ASSIGNED_BY_ID"):
            try:
                user = await self.get_user_details(deal["ASSIGNED_BY_ID"])
                name = (user.get("NAME", "").strip()); last_name = (user.get("LAST_NAME", "").strip())
                if name and last_name: brigade_name = f"{name} {last_name}"
                elif name: brigade_name = name
                elif last_name: brigade_name = last_name
                else: brigade_name = deal.get("ASSIGNED_BY_NAME", "") or f"Бригада {deal['ASSIGNED_BY_ID']}"
                deal["BRIGADE_NAME_ENRICHED"] = brigade_name
            except Exception:
                deal["BRIGADE_NAME_ENRICHED"] = deal.get("ASSIGNED_BY_NAME", "") or f"Бригада {deal.get('ASSIGNED_BY_ID','')}"
        else:
            deal["BRIGADE_NAME_ENRICHED"] = ""

        async def process_cleaning_type(type_code, field_name: str):
            if not type_code: return ""
            enum_map = await self.get_field_enum_map(field_name)
            key = str(type_code[0]) if isinstance(type_code, list) and type_code else (str(type_code) if type_code else None)
            if key and enum_map.get(key): return enum_map[key]
            return f"Тип уборки {key}" if key else ""

        def process_dates(date_field):
            if isinstance(date_field, list):
                return [str(date).split('T')[0] for date in date_field if date]
            elif isinstance(date_field, str):
                return [date_field.split('T')[0]]
            return []

        cleaning_dates = {}
        # Сентябрь 2025
        if deal.get("UF_CRM_1741592774017") or deal.get("UF_CRM_1741592855565"):
            cleaning_dates["september_1"] = {"dates": process_dates(deal.get("UF_CRM_1741592774017")), "type": await process_cleaning_type(deal.get("UF_CRM_1741592855565"), "UF_CRM_1741592855565")}
        if deal.get("UF_CRM_1741592892232") or deal.get("UF_CRM_1741592945060"):
            cleaning_dates["september_2"] = {"dates": process_dates(deal.get("UF_CRM_1741592892232")), "type": await process_cleaning_type(deal.get("UF_CRM_1741592945060"), "UF_CRM_1741592945060")}
        # Октябрь 2025
        if deal.get("UF_CRM_1741593004888") or deal.get("UF_CRM_1741593047994"):
            cleaning_dates["october_1"] = {"dates": process_dates(deal.get("UF_CRM_1741593004888")), "type": await process_cleaning_type(deal.get("UF_CRM_1741593047994"), "UF_CRM_1741593047994")}
        if deal.get("UF_CRM_1741593067418") or deal.get("UF_CRM_1741593115407"):
            cleaning_dates["october_2"] = {"dates": process_dates(deal.get("UF_CRM_1741593067418")), "type": await process_cleaning_type(deal.get("UF_CRM_1741593115407"), "UF_CRM_1741593115407")}
        # Ноябрь 2025
        if deal.get("UF_CRM_1741593156926") or deal.get("UF_CRM_1741593210242"):
            cleaning_dates["november_1"] = {"dates": process_dates(deal.get("UF_CRM_1741593156926")), "type": await process_cleaning_type(deal.get("UF_CRM_1741593210242"), "UF_CRM_1741593210242")}
        if deal.get("UF_CRM_1741593231558") or deal.get("UF_CRM_1741593285121"):
            cleaning_dates["november_2"] = {"dates": process_dates(deal.get("UF_CRM_1741593231558")), "type": await process_cleaning_type(deal.get("UF_CRM_1741593285121"), "UF_CRM_1741593285121")}
        # Декабрь 2025
        if deal.get("UF_CRM_1741593340713") or deal.get("UF_CRM_1741593387667"):
            cleaning_dates["december_1"] = {"dates": process_dates(deal.get("UF_CRM_1741593340713")), "type": await process_cleaning_type(deal.get("UF_CRM_1741593387667"), "UF_CRM_1741593387667")}
        if deal.get("UF_CRM_1741593408621") or deal.get("UF_CRM_1741593452062"):
            cleaning_dates["december_2"] = {"dates": process_dates(deal.get("UF_CRM_1741593408621")), "type": await process_cleaning_type(deal.get("UF_CRM_1741593452062"), "UF_CRM_1741593452062")}

        deal["cleaning_dates"] = cleaning_dates
        return deal

    async def get_deals_optimized(self, brigade: Optional[str] = None, status: Optional[str] = None, management_company: Optional[str] = None, week: Optional[str] = None, limit: int = 100, offset: int = 0) -> List[Dict]:
        params = {
            "select": [
                "ID", "TITLE", "STAGE_ID", "COMPANY_ID", "COMPANY_TITLE",
                "ASSIGNED_BY_ID", "ASSIGNED_BY_NAME", "CATEGORY_ID", "CONTACT_ID",
                "UF_CRM_1669561599956",
                "UF_CRM_1669704529022","UF_CRM_1669705507390","UF_CRM_1669704631166","UF_CRM_1669706387893",
                "UF_CRM_1741592774017","UF_CRM_1741592855565",
                "UF_CRM_1741592892232","UF_CRM_1741592945060",
                "UF_CRM_1741593004888","UF_CRM_1741593047994",
                "UF_CRM_1741593067418","UF_CRM_1741593115407",
                "UF_CRM_1741593156926","UF_CRM_1741593210242",
                "UF_CRM_1741593231558","UF_CRM_1741593285121",
                "UF_CRM_1741593340713","UF_CRM_1741593387667",
                "UF_CRM_1741593408621","UF_CRM_1741593452062"
            ],
            "order": {"ID": "DESC"},
            "start": offset,
            "limit": min(limit, 1000)
        }
        filter_params = {"CATEGORY_ID": "34"}
        if brigade: filter_params["ASSIGNED_BY_NAME"] = f"%{brigade}%"
        if status: filter_params["STAGE_ID"] = status
        if management_company: filter_params["COMPANY_TITLE"] = f"%{management_company}%"
        params["filter"] = filter_params

        cache_key = json.dumps({"brigade": brigade, "status": status, "management_company": management_company, "week": week, "limit": limit, "offset": offset}, ensure_ascii=False)
        now_ts = int(datetime.now(timezone.utc).timestamp())
        entry = self._deals_cache.get(cache_key)
        if entry and now_ts - entry.get("ts", 0) < self._deals_cache_ttl_seconds:
            return entry.get("data", [])

        response = await self._make_request("crm.deal.list", params)
        if not response.get("ok"):
            logger.warning(f"crm.deal.list call failed: {response.get('error')}")
            return []
        deals = response.get("result", []) or []
        enriched_deals = await asyncio.gather(*(self._enrich_deal_data(d) for d in deals[:limit]))
        self._deals_cache[cache_key] = {"data": enriched_deals, "ts": now_ts}
        return enriched_deals

bitrix_service = BitrixService()

# ============================================================================
# CLEANING ROUTES
# ============================================================================
@api_router.get("/cleaning/houses", response_model=HousesResponse)
async def get_houses(
    brigade: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    management_company: Optional[str] = Query(None),
    week: Optional[str] = Query(None),
    cleaning_date: Optional[str] = Query(None),
    date_from: Optional[str] = Query(None),
    date_to: Optional[str] = Query(None),
    limit: int = Query(50),
    offset: int = Query(0),
    page: int = Query(1)
):
    try:
        calculated_offset = (page - 1) * limit if page > 1 else offset
        fetch_limit = 1000 if cleaning_date else min(limit, 1000)
        deals = await bitrix_service.get_deals_optimized(brigade=brigade, status=status, management_company=management_company, week=week, limit=fetch_limit, offset=calculated_offset)

        if cleaning_date or (date_from and date_to):
            def matches_date(cleaning_dates: Dict) -> bool:
                for m in cleaning_dates.values():
                    dates = m.get("dates", []) if isinstance(m, dict) else []
                    for dt in dates:
                        if cleaning_date and dt == cleaning_date:
                            return True
                        if date_from and date_to and (date_from <= dt <= date_to):
                            return True
                return False
            filtered = [d for d in deals if matches_date(d.get("cleaning_dates", {}))]
            total_count = len(filtered)
            start_idx = (page - 1) * limit
            end_idx = start_idx + limit
            deals = filtered[start_idx:end_idx]
        else:
            total_count = await bitrix_service.get_total_deals_count()

        base_url = bitrix_service.base_url.replace('/rest','') if bitrix_service.base_url else ''
        houses: List[HouseResponse] = []
        for deal in deals:
            apartments = int(deal.get("UF_CRM_1669704529022") or 0)
            entrances = int(deal.get("UF_CRM_1669705507390") or 0)
            floors = int(deal.get("UF_CRM_1669704631166") or 0)
            address = deal.get("UF_CRM_1669561599956") or deal.get("TITLE", "")
            brigade_name = deal.get("BRIGADE_NAME_ENRICHED") or deal.get("ASSIGNED_BY_NAME") or "Бригада не назначена"
            management_company = deal.get("COMPANY_TITLE_ENRICHED") or deal.get("COMPANY_TITLE") or ""
            cleaning_dates = deal.get("cleaning_dates", {})

            def get_periodicity_label(cd: Dict) -> str:
                wash_dates = sweep_dates = full_wash_dates = first_floor_wash_dates = 0
                for key in ["september_1", "september_2"]:
                    block = cd.get(key) or {}
                    t = str(block.get("type") or "").lower()
                    dates = block.get("dates") or []
                    if not isinstance(dates, list):
                        dates = []
                    has_wash = ("влажная уборка" in t) or ("мытье" in t)
                    has_sweep = ("подмет" in t)
                    is_full = ("всех этаж" in t)
                    is_first_floor = ("1 этажа" in t) or ("1 этаж" in t) or ("первые этаж" in t)
                    if has_wash:
                        wash_dates += len(dates)
                    if has_sweep:
                        sweep_dates += len(dates)
                    if has_wash and is_full:
                        full_wash_dates += len(dates)
                    if has_wash and is_first_floor:
                        first_floor_wash_dates += len(dates)
                if wash_dates == 2 and sweep_dates == 0:
                    return "2 раза"
                if full_wash_dates >= 1 and first_floor_wash_dates >= 1 and wash_dates == (full_wash_dates + first_floor_wash_dates) and sweep_dates == 0:
                    return "2 раза + первые этажи"
                if wash_dates == 2 and sweep_dates == 2:
                    return "Мытье 2 раза + подметание 2 раза"
                if wash_dates >= 4:
                    return "4 раза"
                return "индивидуальная"

            periodicity = get_periodicity_label(cleaning_dates)
            houses.append(HouseResponse(
                id=int(deal.get("ID", 0)),
                title=deal.get("TITLE", "Без названия"),
                address=address,
                brigade=brigade_name,
                management_company=management_company,
                status=deal.get("STAGE_ID") or "",
                apartments=apartments,
                entrances=entrances,
                floors=floors,
                cleaning_dates=cleaning_dates,
                periodicity=periodicity,
                bitrix_url=f"{base_url}/crm/deal/details/{deal.get('ID')}/" if base_url else ""
            ))

        return HousesResponse(houses=houses, total=total_count, page=page, limit=limit, pages=(total_count + limit - 1) // limit)
    except Exception as e:
        logger.error(f"Error retrieving houses: {e}")
        raise HTTPException(status_code=500, detail=f"Ошибка получения домов: {str(e)}")

@api_router.get("/cleaning/filters", response_model=FiltersResponse)
async def get_filters():
    try:
        response = await bitrix_service._make_request("crm.deal.list", {"select": ["ASSIGNED_BY_NAME", "COMPANY_TITLE", "STAGE_ID"], "filter": {"CATEGORY_ID": "34"}, "order": {"ID": "DESC"}})
        if not response.get("ok"):
            logger.warning(f"crm.deal.list call failed: {response.get('error')}")
            return FiltersResponse()
        deals = response.get("result", []) or []
        brigades = sorted({d.get("ASSIGNED_BY_NAME") for d in deals if d.get("ASSIGNED_BY_NAME")})
        companies = sorted({d.get("COMPANY_TITLE") for d in deals if d.get("COMPANY_TITLE")})
        statuses = sorted({d.get("STAGE_ID") for d in deals if d.get("STAGE_ID")})
        return FiltersResponse(brigades=brigades, management_companies=companies, statuses=statuses)
    except Exception as e:
        logger.error(f"Error retrieving filters: {e}")
        raise HTTPException(status_code=500, detail=f"Ошибка получения фильтров: {str(e)}")

@api_router.get("/cleaning/house/{house_id}/details")
async def get_house_details(house_id: int):
    try:
        # Get deal details with enrichment
        params = {
            "select": [
                "ID", "TITLE", "COMPANY_ID", "COMPANY_TITLE", "CONTACT_ID",
                "ASSIGNED_BY_NAME", "ASSIGNED_BY_ID", "STAGE_ID", 
                "UF_CRM_1669561599956",  # Address
                "UF_CRM_1669704529022",  # Apartments
                "UF_CRM_1669705507390",  # Entrances
                "UF_CRM_1669704631166"   # Floors
            ],
            "filter": {"ID": house_id, "CATEGORY_ID": "34"}
        }
        
        response = await bitrix_service._make_request("crm.deal.get", {"id": house_id})
        if not response.get("ok"):
            logger.warning(f"crm.deal.get failed for ID {house_id}: {response.get('error')}")
            raise HTTPException(status_code=404, detail="Дом не найден")
        
        deal = response.get("result") or {}
        if isinstance(deal, list) and deal:
            deal = deal[0]
        if not deal:
            raise HTTPException(status_code=404, detail="Дом не найден")
        
        # Enrich deal data
        enriched_deal = await bitrix_service._enrich_deal_data(deal)
        
        # Get company details
        company_details = {}
        if deal.get("COMPANY_ID"):
            company_details = await bitrix_service.get_company_details(deal["COMPANY_ID"])
        
        # Get contact details
        contact_details = {}
        cid = deal.get("CONTACT_ID")
        if cid:
            if isinstance(cid, list) and cid:
                cid = cid[0]
            contact_details = await bitrix_service.get_contact_details(cid)
        
        base_url = bitrix_service.base_url.replace('/rest','') if bitrix_service.base_url else ''
        brigade_name = enriched_deal.get("BRIGADE_NAME_ENRICHED") or deal.get("ASSIGNED_BY_NAME") or "Бригада не назначена"
        
        return {
            "house": {
                "id": int(deal.get("ID", 0)),
                "title": deal.get("TITLE", ""),
                "address": deal.get("UF_CRM_1669561599956", ""),
                "apartments": int(deal.get("UF_CRM_1669704529022") or 0),
                "entrances": int(deal.get("UF_CRM_1669705507390") or 0),
                "floors": int(deal.get("UF_CRM_1669704631166") or 0),
                "brigade": brigade_name,
                "status": deal.get("STAGE_ID", ""),
                "bitrix_url": f"{base_url}/crm/deal/details/{deal.get('ID')}/" if base_url else ""
            },
            "management_company": {
                "id": company_details.get("ID", ""),
                "title": company_details.get("TITLE", deal.get("COMPANY_TITLE", "")),
                "phone": (company_details.get("PHONE", [{}])[0].get("VALUE", "") if company_details.get("PHONE") else ""),
                "email": (company_details.get("EMAIL", [{}])[0].get("VALUE", "") if company_details.get("EMAIL") else ""),
                "address": company_details.get("ADDRESS", "")
            },
            "senior_resident": {
                "name": contact_details.get("NAME", "") + " " + contact_details.get("LAST_NAME", ""),
                "phone": (contact_details.get("PHONE", [{}])[0].get("VALUE", "") if contact_details.get("PHONE") else ""),
                "email": (contact_details.get("EMAIL", [{}])[0].get("VALUE", "") if contact_details.get("EMAIL") else "")
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving house details for ID {house_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Ошибка получения деталей дома: {str(e)}")

# Root
@api_router.get("/")
async def root():
    return {"message": "VasDom AudioBot API", "version": "1.0.0"}

# Mount routers
app.include_router(api_router)

# Import and mount AI Training router (isolated)
try:
    from .ai_training import router as ai_training_router  # backend is a package
    app.include_router(ai_training_router)
except Exception:
    # If relative import fails in some environments, try absolute import
    try:
        from ai_training import router as ai_training_router  # type: ignore
        app.include_router(ai_training_router)
    except Exception as e:
        logger.warning(f"AI Training router not mounted: {e}")