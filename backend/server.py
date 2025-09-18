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

# Load env
ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# Logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger('server')

# App
app = FastAPI(title='VasDom AudioBot API', version='1.0.0')
api_router = APIRouter(prefix='/api')

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=os.environ.get('CORS_ORIGINS', '*').split(','),
    allow_methods=['*'],
    allow_headers=['*'],
)

# ================= Models =================
class HouseResponse(BaseModel):
    id: int
    title: str
    address: str
    brigade: Optional[str] = ''
    management_company: Optional[str] = ''
    status: Optional[str] = ''
    apartments: int = 0
    entrances: int = 0
    floors: int = 0
    cleaning_dates: Dict = Field(default_factory=dict)
    periodicity: Optional[str] = 'индивидуальная'
    bitrix_url: Optional[str] = ''

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

# ================= Bitrix Service =================
class BitrixService:
    def __init__(self):
        self.webhook_url = os.environ.get('BITRIX24_WEBHOOK_URL', '')
        self.base_url = self.webhook_url.rstrip('/') if self.webhook_url else ''
        self._user_cache: Dict[str, Dict[str, Any]] = {}
        self._user_cache_ttl = int(os.environ.get('BITRIX_USER_CACHE_TTL', '600'))
        self._enum_cache: Dict[str, Dict[str, Any]] = {}
        self._enum_cache_ttl = int(os.environ.get('BITRIX_ENUM_CACHE_TTL', '3600'))
        self._deals_cache: Dict[str, Dict[str, Any]] = {}
        self._deals_cache_ttl = int(os.environ.get('DEALS_CACHE_TTL', '120'))

    async def _make_request(self, method: str, params: Dict = None) -> Dict:
        if not self.base_url:
            logger.warning('Bitrix24 webhook URL not configured')
            return {'ok': False}
        url = f'{self.base_url}/{method}'
        retries = 2
        last_error = None
        for attempt in range(retries + 1):
            try:
                async with httpx.AsyncClient(timeout=30.0) as client:
                    r = await client.post(url, json=params or {})
                    r.raise_for_status()
                    data = r.json()
                    return {'ok': True, 'result': data.get('result'), 'next': data.get('next'), 'total': data.get('total')}
            except Exception as e:
                last_error = e
                logger.error(f"Bitrix24 request error (attempt {attempt+1}/{retries+1}): {e}")
                await asyncio.sleep(0.3 * (attempt + 1))
        return {'ok': False, 'error': str(last_error) if last_error else 'unknown'}

    async def get_company_details(self, company_id: str) -> Dict:
        try:
            if not company_id:
                return {}
            if not hasattr(self, '_company_cache'):
                self._company_cache = {}
                self._company_cache_ttl = int(os.environ.get('BITRIX_COMPANY_CACHE_TTL', '1800'))
            now = int(datetime.now(timezone.utc).timestamp())
            ce = self._company_cache.get(str(company_id))
            if ce and now - ce.get('ts', 0) < self._company_cache_ttl:
                return ce.get('data', {})
            resp = await self._make_request('crm.company.get', {'id': company_id})
            if not resp.get('ok'):
                return {}
            data = resp.get('result') or {}
            if isinstance(data, list) and data:
                data = data[0]
            self._company_cache[str(company_id)] = {'data': data, 'ts': now}
            return data
        except Exception:
            return {}

    async def get_user_details(self, user_id: str) -> Dict:
        try:
            if not user_id:
                return {}
            now = int(datetime.now(timezone.utc).timestamp())
            ce = self._user_cache.get(str(user_id))
            if ce and now - ce.get('ts', 0) < self._user_cache_ttl:
                return ce.get('data', {})
            resp = await self._make_request('user.get', {'ID': user_id})
            if not resp.get('ok'):
                return {}
            arr = resp.get('result') or []
            user = arr[0] if isinstance(arr, list) and arr else {}
            if user:
                self._user_cache[str(user_id)] = {'data': user, 'ts': now}
            return user
        except Exception:
            return {}

    async def get_contact_details(self, contact_id: str) -> Dict:
        try:
            if not contact_id:
                return {}
            resp = await self._make_request('crm.contact.get', {'id': contact_id})
            if not resp.get('ok'):
                return {}
            return resp.get('result') or {}
        except Exception:
            return {}

    async def get_field_enum_map(self, field_name: str) -> Dict[str, str]:
        try:
            now = int(datetime.now(timezone.utc).timestamp())
            ce = self._enum_cache.get(field_name)
            if ce and now - ce.get('ts', 0) < self._enum_cache_ttl:
                return ce.get('data', {})
            resp = await self._make_request('crm.deal.userfield.list', {'filter': {'FIELD_NAME': field_name}})
            if not resp.get('ok'):
                return {}
            fields = resp.get('result') or []
            mapping: Dict[str, str] = {}
            if isinstance(fields, list) and fields:
                field = fields[0]
                for item in field.get('LIST', []) or []:
                    id_str = str(item.get('ID'))
                    value = item.get('VALUE')
                    if id_str and value:
                        mapping[id_str] = value
            self._enum_cache[field_name] = {'data': mapping, 'ts': now}
            return mapping
        except Exception:
            return {}

    async def get_total_deals_count(self) -> int:
        try:
            limit = 100; start = 0; total = 0
            while True:
                resp = await self._make_request('crm.deal.list', {'select': ['ID'], 'filter': {'CATEGORY_ID': '34'}, 'order': {'ID': 'DESC'}, 'start': start, 'limit': limit})
                if not resp.get('ok'):
                    break
                if resp.get('total') is not None:
                    total = int(resp.get('total') or 0)
                    break
                batch = resp.get('result') or []
                total += len(batch)
                next_start = resp.get('next')
                if next_start is None:
                    break
                start = next_start
            return total if total > 0 else 490
        except Exception:
            return 490

    async def _enrich_deal_data(self, deal: Dict) -> Dict:
        # Company
        company_title = deal.get('COMPANY_TITLE', '')
        if deal.get('COMPANY_ID'):
            c = await self.get_company_details(deal['COMPANY_ID'])
            company_title = c.get('TITLE', company_title)
        deal['COMPANY_TITLE_ENRICHED'] = company_title
        # Brigade
        brigade_name = deal.get('ASSIGNED_BY_NAME', '')
        if deal.get('ASSIGNED_BY_ID'):
            u = await self.get_user_details(deal['ASSIGNED_BY_ID'])
            if u:
                name = (u.get('NAME', '').strip())
                last = (u.get('LAST_NAME', '').strip())
                if name and last:
                    brigade_name = f'{name} {last}'
                elif name:
                    brigade_name = name
                elif last:
                    brigade_name = last
                else:
                    brigade_name = deal.get('ASSIGNED_BY_NAME', '') or f"Бригада {deal['ASSIGNED_BY_ID']}"
        deal['BRIGADE_NAME_ENRICHED'] = brigade_name or deal.get('ASSIGNED_BY_NAME', '')
        # Cleaning dates/types
        async def process_type(code, field_name):
            if not code:
                return ''
            mapping = await self.get_field_enum_map(field_name)
            key = str(code[0]) if isinstance(code, list) and code else (str(code) if code else None)
            return mapping.get(key, f'Тип уборки {key}' if key else '')
        def process_dates(val):
            if isinstance(val, list):
                return [str(x).split('T')[0] for x in val if x]
            if isinstance(val, str):
                return [val.split('T')[0]]
            return []
        cd: Dict[str, Any] = {}
        # September
        if deal.get('UF_CRM_1741592774017') or deal.get('UF_CRM_1741592855565'):
            cd['september_1'] = {'dates': process_dates(deal.get('UF_CRM_1741592774017')), 'type': await process_type(deal.get('UF_CRM_1741592855565'), 'UF_CRM_1741592855565')}
        if deal.get('UF_CRM_1741592892232') or deal.get('UF_CRM_1741592945060'):
            cd['september_2'] = {'dates': process_dates(deal.get('UF_CRM_1741592892232')), 'type': await process_type(deal.get('UF_CRM_1741592945060'), 'UF_CRM_1741592945060')}
        # October
        if deal.get('UF_CRM_1741593004888') or deal.get('UF_CRM_1741593047994'):
            cd['october_1'] = {'dates': process_dates(deal.get('UF_CRM_1741593004888')), 'type': await process_type(deal.get('UF_CRM_1741593047994'), 'UF_CRM_1741593047994')}
        if deal.get('UF_CRM_1741593067418') or deal.get('UF_CRM_1741593115407'):
            cd['october_2'] = {'dates': process_dates(deal.get('UF_CRM_1741593067418')), 'type': await process_type(deal.get('UF_CRM_1741593115407'), 'UF_CRM_1741593115407')}
        # November
        if deal.get('UF_CRM_1741593156926') or deal.get('UF_CRM_1741593210242'):
            cd['november_1'] = {'dates': process_dates(deal.get('UF_CRM_1741593156926')), 'type': await process_type(deal.get('UF_CRM_1741593210242'), 'UF_CRM_1741593210242')}
        if deal.get('UF_CRM_1741593231558') or deal.get('UF_CRM_1741593285121'):
            cd['november_2'] = {'dates': process_dates(deal.get('UF_CRM_1741593231558')), 'type': await process_type(deal.get('UF_CRM_1741593285121'), 'UF_CRM_1741593285121')}
        # December
        if deal.get('UF_CRM_1741593340713') or deal.get('UF_CRM_1741593387667'):
            cd['december_1'] = {'dates': process_dates(deal.get('UF_CRM_1741593340713')), 'type': await process_type(deal.get('UF_CRM_1741593387667'), 'UF_CRM_1741593387667')}
        if deal.get('UF_CRM_1741593408621') or deal.get('UF_CRM_1741593452062'):
            cd['december_2'] = {'dates': process_dates(deal.get('UF_CRM_1741593408621')), 'type': await process_type(deal.get('UF_CRM_1741593452062'), 'UF_CRM_1741593452062')}
        deal['cleaning_dates'] = cd
        return deal

    async def get_deals_optimized(self, brigade: Optional[str] = None, status: Optional[str] = None, management_company: Optional[str] = None, week: Optional[str] = None, limit: int = 100, offset: int = 0) -> List[Dict]:
        params = {
            'select': [
                'ID', 'TITLE', 'STAGE_ID', 'COMPANY_ID', 'COMPANY_TITLE',
                'ASSIGNED_BY_ID', 'ASSIGNED_BY_NAME', 'CATEGORY_ID', 'CONTACT_ID',
                'UF_CRM_1669561599956',
                'UF_CRM_1669704529022','UF_CRM_1669705507390','UF_CRM_1669704631166','UF_CRM_1669706387893',
                'UF_CRM_1741592774017','UF_CRM_1741592855565',
                'UF_CRM_1741592892232','UF_CRM_1741592945060',
                'UF_CRM_1741593004888','UF_CRM_1741593047994',
                'UF_CRM_1741593067418','UF_CRM_1741593115407',
                'UF_CRM_1741593156926','UF_CRM_1741593210242',
                'UF_CRM_1741593231558','UF_CRM_1741593285121',
                'UF_CRM_1741593340713','UF_CRM_1741593387667',
                'UF_CRM_1741593408621','UF_CRM_1741593452062'
            ],
            'order': {'ID': 'DESC'},
            'start': offset,
            'limit': min(limit, 1000)
        }
        f = {'CATEGORY_ID': '34'}
        if brigade:
            f['ASSIGNED_BY_NAME'] = f'%{brigade}%'
        if status:
            f['STAGE_ID'] = status
        if management_company:
            f['COMPANY_TITLE'] = f'%{management_company}%'
        params['filter'] = f
        key = json.dumps({'brigade': brigade, 'status': status, 'management_company': management_company, 'week': week, 'limit': limit, 'offset': offset}, ensure_ascii=False)
        now = int(datetime.now(timezone.utc).timestamp())
        ce = self._deals_cache.get(key)
        if ce and now - ce.get('ts', 0) < self._deals_cache_ttl:
            return ce.get('data', [])
        resp = await self._make_request('crm.deal.list', params)
        if not resp.get('ok'):
            logger.warning(f"crm.deal.list call failed: {resp.get('error')}")
            return []
        deals = resp.get('result', []) or []
        enriched = await asyncio.gather(*(self._enrich_deal_data(d) for d in deals[:limit]))
        self._deals_cache[key] = {'data': enriched, 'ts': now}
        return enriched

bitrix_service = BitrixService()

# ================= Routes =================
@api_router.get('/cleaning/houses', response_model=HousesResponse)
async def get_houses(
    brigade: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    management_company: Optional[str] = Query(None),
    week: Optional[str] = Query(None),
    cleaning_date: Optional[str] = Query(None),
    date_from: Optional[str] = Query(None),
    date_to: Optional[str] = Query(None),
    search: Optional[str] = Query(None),  # фильтр по адресу/названию
    limit: int = Query(50),
    offset: int = Query(0),
    page: int = Query(1)
):
    try:
        calc_offset = (page - 1) * limit if page > 1 else offset
        fetch_limit = 1000 if cleaning_date else min(limit, 1000)
        deals = await bitrix_service.get_deals_optimized(
            brigade=brigade,
            status=status,
            management_company=management_company,
            week=week,
            limit=fetch_limit,
            offset=calc_offset
        )
        # date filters
        if cleaning_date or (date_from and date_to):
            def date_match(d):
                cd = d.get('cleaning_dates', {})
                for m in cd.values():
                    dates = m.get('dates', []) if isinstance(m, dict) else []
                    for dt in dates:
                        if cleaning_date and dt == cleaning_date:
                            return True
                        if date_from and date_to and (date_from <= dt <= date_to):
                            return True
                return False
            deals = [d for d in deals if date_match(d)]
        # address search filter (in-memory contains)
        if search:
            s = search.lower().strip()
            def addr_match(d):
                addr = (d.get('UF_CRM_1669561599956') or d.get('TITLE') or '').lower()
                return s in addr
            deals = [d for d in deals if addr_match(d)]
        total_count = await bitrix_service.get_total_deals_count() if not (cleaning_date or date_from or date_to or search or brigade or status or management_company) else len(deals)
        # paginate
        start = (page - 1) * limit
        end = start + limit
        page_deals = deals[start:end] if (cleaning_date or date_from or date_to or search or brigade or status or management_company) else deals
        base_url = bitrix_service.base_url.replace('/rest','') if bitrix_service.base_url else ''
        houses: List[HouseResponse] = []
        for d in page_deals:
            apartments = int(d.get('UF_CRM_1669704529022') or 0)
            entrances = int(d.get('UF_CRM_1669705507390') or 0)
            floors = int(d.get('UF_CRM_1669704631166') or 0)
            address = d.get('UF_CRM_1669561599956') or d.get('TITLE') or ''
            brigade_name = d.get('BRIGADE_NAME_ENRICHED') or d.get('ASSIGNED_BY_NAME') or 'Бригада не назначена'
            management_title = d.get('COMPANY_TITLE_ENRICHED') or d.get('COMPANY_TITLE') or ''
            cd = d.get('cleaning_dates', {})
            # periodicity from september rules
            def periodicity(cd: Dict) -> str:
                wash = sweep = full = first = 0
                for key in ['september_1','september_2']:
                    b = cd.get(key) or {}
                    t = str(b.get('type') or '').lower()
                    dates = b.get('dates') or []
                    if not isinstance(dates, list):
                        dates = []
                    has_wash = ('влажная уборка' in t) or ('мытье' in t)
                    has_sweep = ('подмет' in t)
                    is_full = ('всех этаж' in t)
                    is_first = ('1 этажа' in t) or ('1 этаж' in t) or ('первые этаж' in t)
                    if has_wash: wash += len(dates)
                    if has_sweep: sweep += len(dates)
                    if has_wash and is_full: full += len(dates)
                    if has_wash and is_first: first += len(dates)
                if wash == 2 and sweep == 0: return '2 раза'
                if full >= 1 and first >= 1 and wash == (full + first) and sweep == 0: return '2 раза + первые этажи'
                if wash == 2 and sweep == 2: return 'Мытье 2 раза + подметание 2 раза'
                if wash >= 4: return '4 раза'
                return 'индивидуальная'
            houses.append(HouseResponse(
                id=int(d.get('ID', 0)),
                title=d.get('TITLE', 'Без названия'),
                address=address,
                brigade=brigade_name,
                management_company=management_title,
                status=d.get('STAGE_ID') or '',
                apartments=apartments,
                entrances=entrances,
                floors=floors,
                cleaning_dates=cd,
                periodicity=periodicity(cd),
                bitrix_url=f"{base_url}/crm/deal/details/{d.get('ID')}/" if base_url else ''
            ))
        pages = (total_count + limit - 1) // limit
        return HousesResponse(houses=houses, total=total_count, page=page, limit=limit, pages=pages)
    except Exception as e:
        logger.error(f'Error retrieving houses: {e}')
        raise HTTPException(status_code=500, detail=f'Ошибка получения домов: {str(e)}')

@api_router.get('/cleaning/filters', response_model=FiltersResponse)
async def get_filters():
    try:
        resp = await bitrix_service._make_request('crm.deal.list', {'select': ['ASSIGNED_BY_NAME','COMPANY_TITLE','STAGE_ID'], 'filter': {'CATEGORY_ID': '34'}, 'order': {'ID':'DESC'}})
        if not resp.get('ok'):
            return FiltersResponse()
        deals = resp.get('result', []) or []
        brigades = sorted({d.get('ASSIGNED_BY_NAME') for d in deals if d.get('ASSIGNED_BY_NAME')})
        companies = sorted({d.get('COMPANY_TITLE') for d in deals if d.get('COMPANY_TITLE')})
        statuses = sorted({d.get('STAGE_ID') for d in deals if d.get('STAGE_ID')})
        return FiltersResponse(brigades=brigades, management_companies=companies, statuses=statuses)
    except Exception as e:
        logger.error(f'Error retrieving filters: {e}')
        raise HTTPException(status_code=500, detail=f'Ошибка получения фильтров: {str(e)}')

@api_router.get('/cleaning/house/{house_id}/details')
async def get_house_details(house_id: int):
    try:
        resp = await bitrix_service._make_request('crm.deal.get', {'id': house_id})
        if not resp.get('ok'):
            raise HTTPException(status_code=404, detail='Дом не найден')
        deal = resp.get('result') or {}
        if isinstance(deal, list) and deal:
            deal = deal[0]
        if not deal:
            raise HTTPException(status_code=404, detail='Дом не найден')
        enriched = await bitrix_service._enrich_deal_data(deal)
        company = {}
        if deal.get('COMPANY_ID'):
            company = await bitrix_service.get_company_details(deal['COMPANY_ID'])
        contact = {}
        cid = deal.get('CONTACT_ID')
        if cid:
            if isinstance(cid, list) and cid:
                cid = cid[0]
            contact = await bitrix_service.get_contact_details(cid)
        base_url = bitrix_service.base_url.replace('/rest','') if bitrix_service.base_url else ''
        brigade_name = enriched.get('BRIGADE_NAME_ENRICHED') or deal.get('ASSIGNED_BY_NAME') or 'Бригада не назначена'
        return {
            'house': {
                'id': int(deal.get('ID', 0)),
                'title': deal.get('TITLE', ''),
                'address': deal.get('UF_CRM_1669561599956', ''),
                'apartments': int(deal.get('UF_CRM_1669704529022') or 0),
                'entrances': int(deal.get('UF_CRM_1669705507390') or 0),
                'floors': int(deal.get('UF_CRM_1669704631166') or 0),
                'brigade': brigade_name,
                'status': deal.get('STAGE_ID', ''),
                'bitrix_url': f"{base_url}/crm/deal/details/{deal.get('ID')}/" if base_url else ''
            },
            'management_company': {
                'id': company.get('ID', ''),
                'title': company.get('TITLE', deal.get('COMPANY_TITLE', '')),
                'phone': (company.get('PHONE', [{}])[0].get('VALUE', '') if company.get('PHONE') else ''),
                'email': (company.get('EMAIL', [{}])[0].get('VALUE', '') if company.get('EMAIL') else ''),
                'address': company.get('ADDRESS', '')
            },
            'senior_resident': {
                'name': f"{contact.get('NAME','')} {contact.get('LAST_NAME','')}",
                'phone': (contact.get('PHONE', [{}])[0].get('VALUE', '') if contact.get('PHONE') else ''),
                'email': (contact.get('EMAIL', [{}])[0].get('VALUE', '') if contact.get('EMAIL') else '')
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f'Error retrieving house details: {e}')
        raise HTTPException(status_code=500, detail=f'Ошибка получения деталей дома: {str(e)}')

@api_router.get('/')
async def root():
    return {'message': 'VasDom AudioBot API', 'version': '1.0.0'}

# Mount routers
app.include_router(api_router)

# Try mount AI training and Voice routers if present (no impact on CRM)
try:
    from .ai_training import router as ai_training_router  # type: ignore
    app.include_router(ai_training_router)
except Exception as e:
    try:
        from ai_training import router as ai_training_router  # type: ignore
        app.include_router(ai_training_router)
    except Exception:
        logger.info('AI Training router not mounted')

try:
    from .voice import router as voice_router  # type: ignore
    app.include_router(voice_router)
except Exception:
    try:
        from voice import router as voice_router  # type: ignore
        app.include_router(voice_router)
    except Exception:
        logger.info('Voice router not mounted')