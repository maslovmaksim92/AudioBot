from fastapi import FastAPI, APIRouter, HTTPException, Query, Request
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
from uuid import uuid4

# DB / Vector (kept minimal)
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker

# LLM / Files (some imports kept for other modules)
from openai import AsyncOpenAI  # noqa: F401

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# Scrub invalid PGSSLMODE
allowed_pgssl = {'disable','allow','prefer','require','verify-ca','verify-full'}
pgssl = os.environ.get('PGSSLMODE')
if pgssl and pgssl.strip().lower() not in allowed_pgssl:
    os.environ['PGSSLMODE'] = 'require'

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("server")

app = FastAPI(title="VasDom AudioBot API", version="1.1.0")
api_router = APIRouter(prefix="/api")

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=os.environ.get('CORS_ORIGINS', '*').split(','),
    allow_methods=["*"],
    allow_headers=["*"],
)

# aiohttp cleanup to avoid 'Unclosed client session'
try:
    import aiohttp
    _http_session: Optional[aiohttp.ClientSession] = None
except Exception:
    aiohttp = None
    _http_session = None

@app.on_event('shutdown')
async def _shutdown_cleanup():
    try:
        global _livekit_client, _http_session
        if _livekit_client:
            await _livekit_client.aclose()
        if _http_session:
            await _http_session.close()
            _http_session = None
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

# ====== LiveKit SIP Outbound calling (Novofon) & Realtime session ======
try:
    from livekit import api as lk_api
    from livekit.plugins import openai as lk_openai
    from livekit import agents as lk_agents
    LIVEKIT_AVAILABLE = True
except Exception:
    LIVEKIT_AVAILABLE = False

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

async def _openai_realtime_create(voice: str, instructions: str, temperature: float = 0.6, max_tokens: int = 1024) -> RealtimeSessionResponse:
    api_key = os.environ.get('OPENAI_API_KEY')
    if not api_key:
        raise HTTPException(status_code=500, detail='OPENAI_API_KEY not configured')
    payload = {
        'model': 'gpt-4o-realtime-preview',
        'voice': voice or 'marin',
        'instructions': instructions or '',
        'temperature': temperature,
        'max_response_output_tokens': max_tokens,
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
            return RealtimeSessionResponse(
                client_secret=data['client_secret']['value'],
                model=data['model'],
                voice=data.get('voice', voice or 'marin'),
                instructions=data.get('instructions', instructions or ''),
                expires_at=data['client_secret']['expires_at'],
                session_id=data['id']
            )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f'Realtime session create error: {e}')
        raise HTTPException(status_code=500, detail='Failed to create realtime session')

@api_router.post('/realtime/sessions', response_model=RealtimeSessionResponse)
async def create_realtime_session(req: RealtimeSessionRequest):
    return await _openai_realtime_create(req.voice or 'marin', req.instructions or '', req.temperature or 0.6, req.max_response_output_tokens or 1024)

# ====== AI Invite (room link) ======
MoscowTZ = timezone(timedelta(hours=3))
_ai_invites: Dict[str, Dict[str, Any]] = {}

class InviteCreateRequest(BaseModel):
    start_at: Optional[str] = Field(default=None, description='ISO datetime в московском времени, напр. 2025-09-25T16:55:00')
    ttl_minutes: int = Field(default=30, ge=5, le=180)
    employee_id: Optional[str] = None
    context: Optional[str] = Field(default='Напоминание по задачам')
    voice: Optional[str] = Field(default='marin')

class InviteCreateResponse(BaseModel):
    token: str
    start_at: str
    expires_at: str
    voice: str
    context: str

class InviteResolveResponse(RealtimeSessionResponse):
    token: str
    start_at: str
    expires_at: str
    context: str

@api_router.post('/ai-invite/create', response_model=InviteCreateResponse)
async def ai_invite_create(req: InviteCreateRequest):
    # compute start time (default: now)
    try:
        if req.start_at:
            start_dt = datetime.fromisoformat(req.start_at)
            if start_dt.tzinfo is None:
                start_dt = start_dt.replace(tzinfo=MoscowTZ)
            else:
                start_dt = start_dt.astimezone(MoscowTZ)
        else:
            start_dt = datetime.now(MoscowTZ) + timedelta(minutes=1)
    except Exception:
        raise HTTPException(status_code=400, detail='start_at must be ISO datetime')
    exp_dt = start_dt + timedelta(minutes=req.ttl_minutes)
    token = uuid4().hex
    _ai_invites[token] = {
        'token': token,
        'start_at': start_dt.isoformat(),
        'expires_at': exp_dt.isoformat(),
        'employee_id': req.employee_id,
        'context': req.context or '',
        'voice': (req.voice or 'marin'),
        'used': False
    }
    logger.info(f"[INVITE] created token={token} start_at={_ai_invites[token]['start_at']} expires_at={_ai_invites[token]['expires_at']} emp={req.employee_id}")
    return InviteCreateResponse(token=token, start_at=_ai_invites[token]['start_at'], expires_at=_ai_invites[token]['expires_at'], voice=_ai_invites[token]['voice'], context=_ai_invites[token]['context'])

class InviteStatus(BaseModel):
    token: str
    status: str
    starts_in_sec: int
    start_at: str
    expires_at: str
    context: str

@api_router.get('/ai-invite/{token}/status', response_model=InviteStatus)
async def ai_invite_status(token: str):
    inv = _ai_invites.get(token)
    if not inv:
        raise HTTPException(status_code=404, detail='Invite not found')
    now = datetime.now(MoscowTZ)
    start_dt = datetime.fromisoformat(inv['start_at'])
    exp_dt = datetime.fromisoformat(inv['expires_at'])
    if now < start_dt:
        status = 'not_started'
        delta = int((start_dt - now).total_seconds())
    elif now > exp_dt:
        status = 'expired'
        delta = -1
    else:
        status = 'available'
        delta = 0
    return InviteStatus(token=token, status=status, starts_in_sec=delta, start_at=inv['start_at'], expires_at=inv['expires_at'], context=inv['context'])

@api_router.post('/ai-invite/{token}/resolve', response_model=InviteResolveResponse)
async def ai_invite_resolve(token: str):
    inv = _ai_invites.get(token)
    if not inv:
        raise HTTPException(status_code=404, detail='Invite not found')
    if inv.get('used'):
        raise HTTPException(status_code=410, detail='Invite already used')
    now = datetime.now(MoscowTZ)
    start_dt = datetime.fromisoformat(inv['start_at'])
    exp_dt = datetime.fromisoformat(inv['expires_at'])
    if now < start_dt - timedelta(minutes=2):
        raise HTTPException(status_code=425, detail='Invite not started yet')
    if now > exp_dt:
        raise HTTPException(status_code=410, detail='Invite expired')
    # Prepare instructions for this invite
    instr = f"Вы — ассистент VasDom. Сейчас {now.astimezone(MoscowTZ).strftime('%H:%M')}. Проводите короткий разговор-отчёт по задачам сотрудника. {inv.get('context','')}"
    sess = await _openai_realtime_create(inv.get('voice') or 'marin', instr)
    inv['used'] = True
    logger.info(f"[INVITE] resolved token={token} session={sess.session_id}")
    return InviteResolveResponse(token=token, start_at=inv['start_at'], expires_at=inv['expires_at'], context=inv['context'], **sess.dict())

# ===== Health =====
@api_router.get('/health')
async def health():
    return {'ok': True, 'ts': int(datetime.now(timezone.utc).timestamp())}

app.include_router(api_router)
# ====== Outbound Voice via LiveKit SIP Gateway ======
_livekit_client: Optional[lk_api.LiveKitAPI] = None if LIVEKIT_AVAILABLE else None
_call_store: Dict[str, Dict[str, Any]] = {}


def _normalize_phone(num: str) -> str:
    if not num:
        return ''
    s = ''.join(ch for ch in str(num) if ch.isdigit() or ch == '+')
    # allow short codes like 8888
    if s.startswith('+'):
        return s
    # if short extension keep as-is
    if len(s) <= 6:
        return s
    # Russia-specific quick normalize: leading 8 -> +7
    if s.startswith('8') and len(s) == 11:
        return '+7' + s[1:]
    if not s.startswith('+'):
        return '+' + s
    return s

async def _get_livekit_client() -> lk_api.LiveKitAPI:
    if not LIVEKIT_AVAILABLE:
        raise HTTPException(status_code=500, detail='LiveKit SDK not available')
    global _livekit_client
    if _livekit_client is None:
        host = os.environ.get('LIVEKIT_URL') or os.environ.get('LIVEKIT_HOST') or os.environ.get('LIVEKIT_WS_URL')
        api_key = os.environ.get('LIVEKIT_API_KEY')
        api_secret = os.environ.get('LIVEKIT_API_SECRET')
        if not host or not api_key or not api_secret:
            raise HTTPException(status_code=500, detail='LIVEKIT_URL/API_KEY/API_SECRET not configured')
        # Normalize ws(s) -> http(s) for LiveKit server API base
        if host.startswith('wss://'):
            host = 'https://' + host[len('wss://'):]
        elif host.startswith('ws://'):
            host = 'http://' + host[len('ws://'):]
        _livekit_client = lk_api.LiveKitAPI(host, api_key, api_secret)
    return _livekit_client

class StartCallRequest(BaseModel):
    phone_number: str
    trunk_id: Optional[str] = None
    from_number: Optional[str] = None
    wait_for_answer: Optional[bool] = False

class StartCallResponse(BaseModel):
    call_id: str
    status: str

class CallStatusResponse(BaseModel):
    call_id: str
    status: str
    details: Optional[Dict[str, Any]] = None

@api_router.post('/voice/call/start', response_model=StartCallResponse)
async def voice_call_start(req: StartCallRequest):
    lk = await _get_livekit_client()
    call_id = uuid4().hex
    to = _normalize_phone(req.phone_number)
    if not to:
        raise HTTPException(status_code=400, detail='phone_number is empty')
    trunk_id = req.trunk_id or os.environ.get('LIVEKIT_SIP_TRUNK_ID')
    if not trunk_id:
        raise HTTPException(status_code=500, detail='LIVEKIT_SIP_TRUNK_ID not configured')
    from_number = _normalize_phone(req.from_number or os.environ.get('DEFAULT_CALLER_ID') or os.environ.get('LIVEKIT_DEFAULT_FROM') or '')
    if not from_number:
        # not fatal; LiveKit may use trunk default
        from_number = None

    _call_store[call_id] = {
        'call_id': call_id,
        'status': 'initiating',
        'to': to,
        'from': from_number,
        'ts': int(datetime.now(timezone.utc).timestamp())
    }

    try:
        # Create SIP participant (outbound call)
        req_payload = lk_api.sip.CreateSIPParticipantRequest(
            sip_trunk_id=trunk_id,
            sip_call_to=to,
            sip_number=from_number or '',
            participant_name=f'Outbound {to}',
            wait_until_answered=bool(req.wait_for_answer),
        )
        result = await lk.sip.create_sip_participant(req_payload)
        _call_store[call_id]['status'] = 'ringing' if not req.wait_for_answer else 'connected'
        _call_store[call_id]['participant_identity'] = getattr(result, 'identity', None)
        # some attrs may include SIP Call-ID
        try:
            _call_store[call_id]['sip_attrs'] = dict(getattr(result, 'attributes', {}) or {})
        except Exception:
            pass
        logger.info(f"[CALL] started call_id={call_id} to={to} trunk={trunk_id} participant={getattr(result, 'identity', None)}")
        return StartCallResponse(call_id=call_id, status=_call_store[call_id]['status'])
    except lk_api.TwirpError as e:
        logger.error(f"[CALL] LiveKit error: {e}")
        _call_store[call_id]['status'] = 'failed'
        _call_store[call_id]['error'] = {'code': getattr(e, 'code', ''), 'message': str(e)}
        raise HTTPException(status_code=502, detail=f'LiveKit error: {e}')
    except Exception as e:
        logger.exception("[CALL] unexpected error")
        _call_store[call_id]['status'] = 'failed'
        _call_store[call_id]['error'] = {'message': str(e)}
        raise HTTPException(status_code=500, detail='Failed to start call')

@api_router.get('/voice/call/{call_id}/status', response_model=CallStatusResponse)
async def voice_call_status(call_id: str):
    info = _call_store.get(call_id)
    if not info:
        raise HTTPException(status_code=404, detail='call not found')
    return CallStatusResponse(call_id=call_id, status=info.get('status','unknown'), details={k:v for k,v in info.items() if k not in ('status','call_id')})

logger.info('Main API router mounted')
@api_router.get('/voice/debug/check')
async def voice_debug_check():
    host = os.environ.get('LIVEKIT_URL') or os.environ.get('LIVEKIT_HOST') or os.environ.get('LIVEKIT_WS_URL')
    api_key_set = bool(os.environ.get('LIVEKIT_API_KEY'))
    api_secret_set = bool(os.environ.get('LIVEKIT_API_SECRET'))
    trunk_id = os.environ.get('LIVEKIT_SIP_TRUNK_ID')
    caller = os.environ.get('DEFAULT_CALLER_ID') or os.environ.get('LIVEKIT_DEFAULT_FROM')
    norm_host = host
    if norm_host:
      if norm_host.startswith('wss://'):
          norm_host = 'https://' + norm_host[len('wss://'):]
      elif norm_host.startswith('ws://'):
          norm_host = 'http://' + norm_host[len('ws://'):]
    return {
        'livekit_host_raw': host,
        'livekit_host_api': norm_host,
        'api_key_set': api_key_set,
        'api_secret_set': api_secret_set,
        'trunk_id_set': bool(trunk_id),
        'trunk_id': trunk_id[:4] + '****' if trunk_id else None,
        'default_caller': caller,
        'routes': ['/api/voice/call/start', '/api/voice/call/{call_id}/status']
    }
