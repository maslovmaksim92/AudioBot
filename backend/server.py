from fastapi import FastAPI, APIRouter, HTTPException, Query, Depends, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
import os
import logging
import httpx
import asyncio
from datetime import datetime, timezone, timedelta
from pathlib import Path
import json
import io
import zipfile

# DB / Vector
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import declarative_base
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey
from sqlalchemy import text as sa_text

# LLM / Files
# removed emergentintegrations usage to allow OpenAI 1.109.0 for LiveKit OpenAI Realtime
from openai import AsyncOpenAI
from PyPDF2 import PdfReader
from docx import Document as DocxDocument
from openpyxl import load_workbook
import tiktoken
from uuid import uuid4

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# Scrub invalid PGSSLMODE
allowed_pgssl = {'disable','allow','prefer','require','verify-ca','verify-full'}
pgssl = os.environ.get('PGSSLMODE')
if pgssl and pgssl.strip().lower() not in allowed_pgssl:
    os.environ['PGSSLMODE'] = 'require'

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("server")

app = FastAPI(title="VasDom AudioBot API", version="1.0.0")
api_router = APIRouter(prefix="/api")

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=os.environ.get('CORS_ORIGINS', '*').split(','),
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event('shutdown')
async def _shutdown_cleanup():
    try:
        global _livekit_client
        if _livekit_client:
            await _livekit_client.aclose()
    except Exception:
        pass

# DB
from urllib.parse import urlparse, parse_qsl, urlencode, urlunparse

def _normalize_db_url(url: str, for_async: bool = True) -> str:
    try:
        if not url:
            return url
        url = url.strip().strip("'\"")
        if url.lower().startswith('psql '):
            url = url[5:].strip().strip("'\"")
        for marker in ('postgresql+asyncpg://', 'postgresql://', 'postgres://'):
            idx = url.find(marker)
            if idx > 0:
                url = url[idx:]
                break
        if for_async:
            if url.startswith('postgres://'):
                url = url.replace('postgres://', 'postgresql+asyncpg://', 1)
            elif url.startswith('postgresql://') and not url.startswith('postgresql+asyncpg://'):
                url = url.replace('postgresql://', 'postgresql+asyncpg://', 1)
            elif not url.startswith('postgresql+asyncpg://'):
                url = 'postgresql+asyncpg://' + url.split('://',1)[-1]
        else:
            if url.startswith('postgres://'):
                url = url.replace('postgres://', 'postgresql://', 1)
        # remove sslmode, force ssl=true for asyncpg
        parsed = urlparse(url)
        q = dict(parse_qsl(parsed.query, keep_blank_values=True))
        if 'sslmode' in q:
            q.pop('sslmode', None)
        q['ssl'] = 'true'
        new_query = urlencode(q)
        url = urlunparse((parsed.scheme, parsed.netloc, parsed.path, parsed.params, new_query, parsed.fragment))
    except Exception:
        return url
    return url

DATABASE_URL = _normalize_db_url(os.environ.get('NEON_DATABASE_URL') or os.environ.get('DATABASE_URL') or '')
engine = None
async_session = None

if DATABASE_URL:
    connect_args = {'ssl': True}
    engine = create_async_engine(DATABASE_URL, future=True, echo=False, connect_args=connect_args)
    async_session = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)

async def get_db() -> AsyncSession:
    if not async_session:
        raise HTTPException(status_code=500, detail='Database is not initialized')
    async with async_session() as session:
        yield session

# ===== Meetings (Summarize + Send to Telegram) + STT (omitted here for brevity in this snippet) =====
# ... existing endpoints here ...

# ===== Meetings: Save to Knowledge Base & Recent (omitted here for brevity) =====
# ... existing endpoints here ...

# ====== OpenAI Realtime: Ephemeral session endpoint ======

# ====== LiveKit SIP Outbound calling (Novofon) ======
try:
    from livekit import api as lk_api
    from livekit import api as livekit_api
    from livekit import api
    from livekit import api as _lk_api
    from livekit import api as _api
    from livekit.plugins import openai as lk_openai
    from livekit import agents as lk_agents
    LIVEKIT_AVAILABLE = True
except Exception:
    LIVEKIT_AVAILABLE = False

from pydantic import BaseModel

class VoiceCallStartRequest(BaseModel):
    phone_number: str
    caller_id: Optional[str] = None
    instructions: Optional[str] = None
    voice: Optional[str] = 'marin'

class VoiceCallStartResponse(BaseModel):
    call_id: str
    room_name: str
    status: str
    sip_participant_id: Optional[str] = None

_livekit_client: Optional[lk_api.LiveKitAPI] = None
_livekit_trunk_id: Optional[str] = None
_call_states: Dict[str, Dict[str, Any]] = {}


def _livekit_http_url() -> Optional[str]:
    url = os.environ.get('LIVEKIT_WS_URL') or os.environ.get('LIVEKIT_URL') or ''
    if not url:
        return None
    url = url.strip()
    if url.startswith('wss://'):
        return 'https://' + url[len('wss://') :]
    if url.startswith('ws://'):
        return 'http://' + url[len('ws://') :]
    return url if url.startswith('http') else ('https://' + url)

async def _get_livekit_client() -> Optional[lk_api.LiveKitAPI]:
    global _livekit_client
    if not LIVEKIT_AVAILABLE:
        return None
    if _livekit_client is None:
        base = _livekit_http_url()
        key = os.environ.get('LIVEKIT_API_KEY')
        secret = os.environ.get('LIVEKIT_API_SECRET')
        if not (base and key and secret):
            return None
        _livekit_client = lk_api.LiveKitAPI(url=base, api_key=key, api_secret=secret)
    return _livekit_client

async def _ensure_outbound_trunk() -> Optional[str]:
    """Resolve or create outbound SIP trunk id.
    Priority:
    1) env LIVEKIT_SIP_TRUNK_ID / SIP_TRUNK_ID / LIVEKIT_TRUNK_ID
    2) list existing trunks by name LIVEKIT_SIP_TRUNK_NAME (default 'novofon-trunk')
    3) create trunk from NOVOFON_* env and re-list to get id
    """
    global _livekit_trunk_id
    if _livekit_trunk_id:
        return _livekit_trunk_id

    # 1) explicit env override
    for k in ('LIVEKIT_SIP_TRUNK_ID','SIP_TRUNK_ID','LIVEKIT_TRUNK_ID'):
        v = (os.environ.get(k) or '').strip()
        if v:
            _livekit_trunk_id = v
            logger.info(f'Using SIP trunk id from env {k}: {_livekit_trunk_id}')
            return _livekit_trunk_id

    client = await _get_livekit_client()
    if not client:
        return None

    name = os.environ.get('LIVEKIT_SIP_TRUNK_NAME', 'novofon-trunk')

    # Helper: extract list array from response
    async def _list_outbound_trunks():
        try:
            resp = await client.sip.list_sip_outbound_trunk(lk_api.ListSIPOutboundTrunkRequest())
            for attr in ('trunks','items','data','outbound_trunks'):
                if hasattr(resp, attr):
                    return getattr(resp, attr) or []
            # Fallback: try converting to dict-ish string
            try:
                return list(resp)  # if iterable
            except Exception:
                return []
        except Exception as e:
            logger.warning(f'LiveKit list outbound trunks failed: {e}')
            return []

    # 2) try find by name
    trunks = await _list_outbound_trunks()
    for t in trunks:
        try:
            tname = getattr(t, 'name', '')
            if tname == name:
                tid = getattr(t, 'trunk_id', None) or getattr(t, 'id', None)
                if tid:
                    _livekit_trunk_id = tid
                    logger.info(f'Found existing SIP trunk "{name}": {tid}')
                    return _livekit_trunk_id
        except Exception:
            continue

    # 3) Create trunk
    try:
        trunk = lk_api.SIPOutboundTrunkInfo(
            name=name,
            address=(os.environ.get('NOVOFON_SIP_DOMAIN') or 'sip.novofon.ru'),
            numbers=[os.environ.get('NOVOFON_CALLER_ID') or ''],
            auth_username=os.environ.get('NOVOFON_SIP_USERNAME') or '',
            auth_password=os.environ.get('NOVOFON_SIP_PASSWORD') or '',
        )
        req = lk_api.CreateSIPOutboundTrunkRequest(trunk=trunk)
        created = await client.sip.create_sip_outbound_trunk(req)
        # Try to read id from different shapes
        tid = None
        for attr in ('trunk_id','id'):
            tid = tid or getattr(created, attr, None)
        # Some versions return wrapper with .trunk
        if not tid and hasattr(created, 'trunk'):
            inner = getattr(created, 'trunk', None)
            for attr in ('trunk_id','id'):
                tid = tid or getattr(inner, attr, None)
        if tid:
            _livekit_trunk_id = tid
            logger.info(f'LiveKit outbound trunk created: {tid}')
            return _livekit_trunk_id
        # If id still unknown — re-list and find by name
        trunks2 = await _list_outbound_trunks()
        for t in trunks2:
            try:
                if getattr(t, 'name', '') == name:
                    tid = getattr(t, 'trunk_id', None) or getattr(t, 'id', None)
                    if tid:
                        _livekit_trunk_id = tid
                        logger.info(f'Found created SIP trunk by name: {tid}')
                        return _livekit_trunk_id
            except Exception:
                continue
        logger.error('Create outbound trunk succeeded but id not found in response/list')
        return None
    except Exception as e:
        logger.error(f'Create outbound trunk failed: {e}')
        return None

async def _start_openai_agent(call_id: str, room_name: str, voice: str, instructions: Optional[str]):
    if not LIVEKIT_AVAILABLE:
        return
    try:
        # Build LiveKit token for agent
        token = lk_api.AccessToken(api_key=os.environ.get('LIVEKIT_API_KEY'), api_secret=os.environ.get('LIVEKIT_API_SECRET'))
        token = token.with_identity(f'ai_agent_{call_id}').with_name('AI Assistant')
        grants = lk_api.VideoGrants(room_join=True, room=room_name)
        token = token.with_grants(grants)
        jwt = token.to_jwt()

        async def _entry(ctx: lk_agents.JobContext):
            await ctx.connect()
            # Configure OpenAI realtime model via plugin
            model = lk_openai.realtime.RealtimeModel(
                voice=voice or 'marin',
                instructions=instructions or 'Вы — ассистент VasDom, общайтесь вежливо и кратко.',
                modalities=['audio','text'],
                turn_detection=lk_openai.realtime.TurnDetection(type='server_vad', threshold=0.5, prefix_padding_ms=300, silence_duration_ms=600),
            )
            session = lk_agents.voice.AgentSession(llm=model)
            # Start agent in the room from job context
            await session.start(agent=lk_agents.voice.Agent(label='VasDom AI'), room=ctx.room)
            await session.drain()
            await session.aclose()

        # Create worker with options API
        opts = lk_agents.WorkerOptions(entrypoint_fnc=_entry)
        # Run worker in ROOM mode by passing room token & name via env options
        # Here we simulate job by connecting with token & room at runtime using AgentSession.start(room=...)
        worker = lk_agents.Worker(opts)
        asyncio.create_task(worker.run())
        _call_states[call_id]['agent'] = 'started'
    except Exception as e:
        logger.error(f'AI agent start failed: {e}')
        _call_states[call_id]['agent_error'] = str(e)

@api_router.post('/voice/call/start', response_model=VoiceCallStartResponse)
async def voice_call_start(req: VoiceCallStartRequest):
    client = await _get_livekit_client()
    if not client:
        raise HTTPException(status_code=500, detail='LiveKit not configured')
    trunk_id = await _ensure_outbound_trunk()
    if not trunk_id:
        raise HTTPException(status_code=500, detail='SIP trunk not available')
    call_id = str(uuid4())
    room_name = f'call-{call_id}'
    # Create room
    try:
        await client.room.create_room(lk_api.CreateRoomRequest(name=room_name))
    except Exception as e:
        logger.warning(f'Create room warning: {e}')
    # Create SIP participant (outbound call)
    try:
        part = await client.sip.create_sip_participant(lk_api.CreateSIPParticipantRequest(
            sip_trunk_id=trunk_id,
            sip_call_to=req.phone_number,
            room_name=room_name,
            participant_identity=f"pstn-{req.phone_number.replace('+','').replace(' ','').replace('-','')}",
            participant_name=req.caller_id or "PSTN",
        ))
        _call_states[call_id] = {'status': 'ringing', 'room': room_name, 'sip_participant_id': getattr(part, 'sip_participant_id', None)}
        # Start AI agent in background
        asyncio.create_task(_start_openai_agent(call_id, room_name, req.voice or 'marin', req.instructions))
        return VoiceCallStartResponse(call_id=call_id, room_name=room_name, status='ringing', sip_participant_id=getattr(part, 'sip_participant_id', None))
    except lk_api.TwirpError as e:
        logger.error(f'LiveKit SIP error: {e}')
        raise HTTPException(status_code=502, detail=f'LiveKit SIP error: {e}')
    except Exception as e:
        logger.error(f'Create SIP participant failed: {e}')
        raise HTTPException(status_code=500, detail='Failed to start call')

class VoiceCallStatus(BaseModel):
    call_id: str
    status: str
    room_name: str
    duration: Optional[int] = None
    sip_participant_id: Optional[str] = None

@api_router.get('/voice/call/{call_id}/status', response_model=VoiceCallStatus)
async def voice_call_status(call_id: str):
    st = _call_states.get(call_id)
    if not st:
        raise HTTPException(status_code=404, detail='Call not found')
    return VoiceCallStatus(call_id=call_id, status=st.get('status','unknown'), room_name=st.get('room',''), sip_participant_id=st.get('sip_participant_id'))

class RealtimeSessionRequest(BaseModel):
    voice: Optional[str] = Field(default='marin')
    instructions: Optional[str] = Field(default='Вы — голосовой ассистент VasDom. Отвечайте кратко и по делу. Если пользователь спрашивает про объект (адрес, периодичность, дату уборки), вызовите инструмент get_house_brief с параметром query.')
    temperature: Optional[float] = Field(default=0.6)
    max_response_output_tokens: Optional[int] = Field(default=1024)

class RealtimeSessionResponse(BaseModel):
    client_secret: str
    model: str
    voice: str
    instructions: str
    expires_at: int
    session_id: str

@api_router.post('/realtime/sessions', response_model=RealtimeSessionResponse)
async def create_realtime_session(req: RealtimeSessionRequest):
    api_key = os.environ.get('OPENAI_API_KEY')
    if not api_key:
        raise HTTPException(status_code=500, detail='OPENAI_API_KEY not configured')
    payload = {
        'model': 'gpt-4o-realtime-preview',
        'voice': req.voice or 'marin',
        'instructions': (req.instructions or ''),
        'temperature': req.temperature or 0.6,
        'max_response_output_tokens': req.max_response_output_tokens or 1024,
        'turn_detection': {
            'type': 'server_vad',
            'threshold': 0.5,
            'prefix_padding_ms': 300,
            'silence_duration_ms': 500,
            'create_response': True
        },
        'input_audio_format': 'pcm16',
        'output_audio_format': 'pcm16',
        'input_audio_transcription': { 'model': 'whisper-1' },
        'tools': [
            {
                'type': 'function',
                'name': 'get_house_brief',
                'description': 'Верни кратко: адрес, периодичность, ближайшая уборка по запросу пользователя (адрес/название).',
                'parameters': {
                    'type': 'object',
                    'properties': { 'query': { 'type': 'string', 'description': 'Адрес или часть адреса/названия' } },
                    'required': ['query']
                }
            }
        ],
        'tool_choice': 'auto'
    }
    try:
        async with httpx.AsyncClient(timeout=20) as cli:
            resp = await cli.post('https://api.openai.com/v1/realtime/sessions', json=payload, headers={
                'Authorization': f'Bearer {api_key}',
                'Content-Type': 'application/json'
            })
            if resp.status_code != 200:
                raise HTTPException(status_code=resp.status_code, detail=f'OpenAI error: {resp.text}')
            data = resp.json()
            return {
                'client_secret': data['client_secret']['value'],
                'model': data['model'],
                'voice': data.get('voice', req.voice or 'marin'),
                'instructions': data.get('instructions', req.instructions or ''),
                'expires_at': data['client_secret']['expires_at'],
                'session_id': data['id']
            }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f'Realtime session create error: {e}')
        raise HTTPException(status_code=500, detail='Failed to create realtime session')

# ===== Bitrix Tasks (no Mongo) =====
# Inline Bitrix service (removed app_main dependency)
class BitrixService:
    def __init__(self):
        self.webhook_url = os.environ.get('BITRIX24_WEBHOOK_URL', '').rstrip('/')
        self._deals_cache: Dict[str, Any] = {"ts": 0, "data": []}
        self._deals_full_cache: Dict[str, Any] = {"ts": 0, "data": []}
        self._deals_ttl = int(os.environ.get('DEALS_CACHE_TTL', '120'))
        self._uf_enums: Dict[str, Dict[str, str]] = {}
        self._uf_enums_ts: int = 0
        self._uf_enums_ttl = int(os.environ.get('BITRIX_UF_ENUMS_TTL', '900'))

    async def _call(self, method: str, params: Dict = None) -> Dict:
        if not self.webhook_url:
            return {"ok": False}
        url = f"{self.webhook_url}/{method}"
        try:
            async with httpx.AsyncClient(timeout=40.0) as client:
                r = await client.post(url, json=params or {})
                r.raise_for_status()
                data = r.json()
                return {"ok": True, "result": data.get("result"), "next": data.get("next"), "total": data.get("total")}
        except Exception as e:
            logger.error(f"Bitrix error: {e}")
            return {"ok": False}

    async def _list_all(self, method: str, params: Dict) -> List[Dict]:
        items: List[Dict] = []
        q = dict(params or {})
        next_start = None
        for _ in range(50):
            if next_start is not None:
                q['start'] = next_start
            resp = await self._call(method, q)
            if not resp.get('ok'):
                break
            part = resp.get('result') or []
            if isinstance(part, dict):
                part = [part]
            items.extend(part)
            next_start = resp.get('next')
            if next_start is None:
                break
        return items

    async def deals(self, limit=500) -> List[Dict]:
        now = int(datetime.now(timezone.utc).timestamp())
        if now - self._deals_cache["ts"] < self._deals_ttl and self._deals_cache["data"]:
            return self._deals_cache["data"]
        items = await self._list_all("crm.deal.list", {
            "select": ["ID","TITLE","UF_CRM_1669561599956","UF_CRM_1669704529022","UF_CRM_1669705507390","UF_CRM_1669704631166","ASSIGNED_BY_NAME","COMPANY_TITLE","STAGE_ID"],
            "filter": {"CATEGORY_ID":"34"},
            "order": {"ID":"DESC"},
            "limit": min(limit,1000)
        })
        if not items:
            return self._deals_cache["data"] or []
        self._deals_cache = {"ts": now, "data": items}
        return items

    async def deals_full(self) -> List[Dict]:
        now = int(datetime.now(timezone.utc).timestamp())
        if now - self._deals_full_cache["ts"] < self._deals_ttl and self._deals_full_cache["data"]:
            return self._deals_full_cache["data"]
        items = await self._list_all("crm.deal.list", {
            "select": [
                "ID","TITLE","STAGE_ID","COMPANY_ID","COMPANY_TITLE",
                "ASSIGNED_BY_ID","ASSIGNED_BY_NAME","CATEGORY_ID",
                "UF_CRM_1669561599956","UF_CRM_1669704529022","UF_CRM_1669705507390","UF_CRM_1669704631166",
                # cleaning schedule custom UF_* fields will be included as is
            ],
            "filter": {"CATEGORY_ID": "34"},
            "order": {"ID": "DESC"},
            "limit": 1000
        })
        if not items:
            return self._deals_full_cache["data"] or []
        self._deals_full_cache = {"ts": now, "data": items}
        return items

bitrix = BitrixService()

# Helpers to compute periodicity and next cleaning date from UF_* blocks
def _extract_dates_from_deal(deal: Dict[str, Any]) -> List[str]:
    dates: List[str] = []
    for k, v in (deal or {}).items():
        if not str(k).startswith('UF_CRM_'):
            continue
        try:
            if isinstance(v, str) and (v.strip().startswith('{') or v.strip().startswith('[')):
                obj = json.loads(v)
                if isinstance(obj, dict) and isinstance(obj.get('dates'), list):
                    for d in obj.get('dates'):
                        if isinstance(d, str):
                            dates.append(d)
                elif isinstance(obj, list):
                    for d in obj:
                        if isinstance(d, str):
                            dates.append(d)
            elif isinstance(v, dict) and isinstance(v.get('dates'), list):
                for d in v.get('dates'):
                    if isinstance(d, str): dates.append(d)
            elif isinstance(v, list):
                for d in v:
                    if isinstance(d, str): dates.append(d)
        except Exception:
            continue
    # keep unique and sort
    uniq = sorted(set(dates))
    return uniq

def _next_cleaning_date(deal: Dict[str, Any]) -> Optional[str]:
    today = datetime.now(timezone.utc).date()
    best: Optional[str] = None
    for d in _extract_dates_from_deal(deal):
        try:
            dt = datetime.fromisoformat(d).date()
            if dt >= today:
                if best is None or dt < datetime.fromisoformat(best).date():
                    best = d
        except Exception:
            continue
    return best

def _approximate_periodicity(deal: Dict[str, Any]) -> str:
    # naive heuristic from available dates
    dates = _extract_dates_from_deal(deal)
    if len(dates) >= 4:
        return "4 раза"
    if len(dates) >= 2:
        return "2 раза"
    return "индивидуальная"

class BitrixTaskCreate(BaseModel):
    title: str
    description: Optional[str] = ''
    responsible_id: Optional[int] = None
    deadline: Optional[str] = None  # ISO 'YYYY-MM-DDTHH:MM:SSZ' or 'YYYY-MM-DD HH:MM:SS'
    priority: Optional[int] = 2  # 0 low, 1 medium, 2 high

class BitrixTaskUpdate(BaseModel):
    id: int
    fields: Dict[str, Any]

class MeetingTaskItem(BaseModel):
    title: str
    owner: Optional[str] = None
    due: Optional[str] = None
    description: Optional[str] = ''

class MeetingTasksPayload(BaseModel):
    tasks: List[MeetingTaskItem]

async def _bitrix_user_search(name: str) -> Optional[int]:
    if not name:
        return None
    # Try user.search by name
    try:
        resp = await bitrix._call('user.search', { 'FILTER': { 'ACTIVE': 'true', 'FIND': name } })
        if resp.get('ok'):
            items = resp.get('result') or []
            if isinstance(items, dict): items = [items]
            if items:
                # pick exact match by NAME or LAST_NAME first
                for u in items:
                    full = f"{u.get('NAME','')} {u.get('LAST_NAME','')}".strip()
                    if full and name.lower() in full.lower():
                        return int(u.get('ID'))
                return int(items[0].get('ID'))
    except Exception:
        pass
    # fallback to default assignee
    try:
        da = os.environ.get('BITRIX_DEFAULT_ASSIGNEE_ID')
        return int(da) if da else None
    except Exception:
        return None

@api_router.post('/tasks/bitrix/create')
async def tasks_bitrix_create(req: BitrixTaskCreate):
    if not bitrix.webhook_url:
        raise HTTPException(status_code=500, detail='Bitrix webhook not configured')
    rid = req.responsible_id
    if not rid:
        rid = await _bitrix_user_search('')  # default
    fields = {
        'TITLE': req.title,
        'DESCRIPTION': req.description or '',
        'RESPONSIBLE_ID': rid,
        'PRIORITY': req.priority if req.priority is not None else 2,
    }
    if req.deadline:
        fields['DEADLINE'] = req.deadline
    resp = await bitrix._call('tasks.task.add', { 'fields': fields })
    if not resp.get('ok'):
        raise HTTPException(status_code=500, detail='Bitrix create task failed')
    return { 'ok': True, 'task_id': resp.get('result') }

@api_router.patch('/tasks/bitrix/update')
async def tasks_bitrix_update(req: BitrixTaskUpdate):
    if not bitrix.webhook_url:
        raise HTTPException(status_code=500, detail='Bitrix webhook not configured')
    resp = await bitrix._call('tasks.task.update', { 'taskId': int(req.id), 'fields': req.fields or {} })
    if not resp.get('ok'):
        raise HTTPException(status_code=500, detail='Bitrix update task failed')
    return { 'ok': True }

@api_router.get('/tasks/bitrix/list')
async def tasks_bitrix_list(date: Optional[str] = Query(None), responsible_id: Optional[int] = Query(None), status: Optional[str] = Query(None)):
    if not bitrix.webhook_url:
        raise HTTPException(status_code=500, detail='Bitrix webhook not configured')
    flt: Dict[str, Any] = {}
    if responsible_id:
        flt['RESPONSIBLE_ID'] = int(responsible_id)
    # Filter by deadline for a date
    if date:
        try:
            d = datetime.fromisoformat(date)
            start = d.replace(hour=0, minute=0, second=0, microsecond=0)
            end = d.replace(hour=23, minute=59, second=59, microsecond=0)
            flt['>=DEADLINE'] = start.strftime('%Y-%m-%dT%H:%M:%S')
            flt['<=DEADLINE'] = end.strftime('%Y-%m-%dT%H:%M:%S')
        except Exception:
            pass
    if status:
        flt['STATUS'] = status
    # Minimal select set
    params = {
        'filter': flt,
        'select': ['ID','TITLE','DESCRIPTION','RESPONSIBLE_ID','CREATED_BY','DEADLINE','STATUS','PRIORITY']
    }
    resp = await bitrix._call('tasks.task.list', params)
    if not resp.get('ok'):
        return { 'tasks': [] }
    items = resp.get('result') or []
    if isinstance(items, dict): items = [items]
    return { 'tasks': items }

@api_router.post('/tasks/from-meeting')
async def tasks_from_meeting(payload: MeetingTasksPayload):
    if not bitrix.webhook_url:
        raise HTTPException(status_code=500, detail='Bitrix webhook not configured')
    out = []
    for t in payload.tasks or []:
        rid = await _bitrix_user_search(t.owner or '')
        fields = {
            'TITLE': t.title,
            'DESCRIPTION': t.description or '',
            'RESPONSIBLE_ID': rid,
            'PRIORITY': 2
        }
        if t.due:
            fields['DEADLINE'] = t.due
        resp = await bitrix._call('tasks.task.add', { 'fields': fields })
        if resp.get('ok'):
            out.append({ 'title': t.title, 'task_id': resp.get('result'), 'responsible_id': rid })
    return { 'ok': True, 'created': out }

@api_router.get('/employees/office')
async def employees_office():
    if not bitrix.webhook_url:
        return { 'employees': [] }
    # Try to list active users
    try:
        resp = await bitrix._call('user.search', { 'FILTER': { 'ACTIVE': 'true' } })
        if not resp.get('ok'):
            return { 'employees': [] }
        items = resp.get('result') or []
        if isinstance(items, dict): items = [items]
        out = []
        for u in items:
            out.append({ 'id': int(u.get('ID')), 'name': f"{u.get('NAME','')} {u.get('LAST_NAME','')}".strip() or u.get('LOGIN') })
        return { 'employees': out }
    except Exception:
        return { 'employees': [] }

# Health endpoints for readiness
@api_router.get('/health')
async def health():
    return {'ok': True, 'ts': int(datetime.now(timezone.utc).timestamp())}

@api_router.get('/ready')
async def ready():
    return {'ready': True}

# Mount main API router
app.include_router(api_router)
logger.info('Main API router mounted')


# Mount AI Knowledge router for AI Chat endpoints
try:
    from app.routers import ai_knowledge as _ai_kb_mod
    _kb_router = getattr(_ai_kb_mod, 'router', None)
    if _kb_router:
        app.include_router(_kb_router)
        logger.info('AI Knowledge router mounted')
    else:
        logger.warning('AI Knowledge router not found in module app.routers.ai_knowledge')
except Exception as _e:
    logger.warning(f'AI Knowledge router not loaded: {_e}')

# Startup hook
async def init_db():
    if engine:
        async with engine.begin() as conn:
            await conn.run_sync(lambda conn: None)

@app.on_event("startup")
async def on_startup():
    await init_db()