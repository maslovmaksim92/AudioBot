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
import sys

# Fix PYTHONPATH for Render deployment
# Добавляем корневую директорию проекта в sys.path для правильных импортов
PROJECT_ROOT = Path(__file__).parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

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

# DB - используем модульную конфигурацию из app/config/database.py
# Старая инициализация БД закомментирована - теперь используем app.config.database
try:
    # Попытка импорта для Render (uvicorn backend.server:app из корня)
    from backend.app.config.database import get_db, init_db, engine, AsyncSessionLocal
    logger.info('✅ Using modular database configuration from backend.app.config.database')
except ImportError:
    try:
        # Попытка импорта для локальной разработки (uvicorn server:app из backend/)
        from app.config.database import get_db, init_db, engine, AsyncSessionLocal
        logger.info('✅ Using modular database configuration from app.config.database')
    except ImportError as e:
        logger.warning(f'⚠️ Could not import modular database config: {e}')
    # Fallback к старой конфигурации (для совместимости)
    from urllib.parse import urlparse, parse_qsl, urlencode, urlunparse
    import ssl
    
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
            # Убираем sslmode из URL
            parsed = urlparse(url)
            q = dict(parse_qsl(parsed.query, keep_blank_values=True))
            q.pop('sslmode', None)
            q.pop('sslrequire', None)
            new_query = urlencode(q)
            url = urlunparse((parsed.scheme, parsed.netloc, parsed.path, parsed.params, new_query, parsed.fragment))
        except Exception:
            return url
        return url

    DATABASE_URL = _normalize_db_url(os.environ.get('NEON_DATABASE_URL') or os.environ.get('DATABASE_URL') or '')
    engine = None
    async_session = None

    if DATABASE_URL:
        ssl_context = ssl.create_default_context()
        ssl_context.check_hostname = False
        ssl_context.verify_mode = ssl.CERT_NONE
        connect_args = {'ssl': ssl_context}
        engine = create_async_engine(DATABASE_URL, future=True, echo=False, connect_args=connect_args)
        async_session = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)

    async def get_db() -> AsyncSession:
        if not async_session:
            raise HTTPException(status_code=500, detail='Database is not initialized')
        async with async_session() as session:
            yield session
    
    async def init_db():
        """Fallback init_db"""
        pass

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
        'model': 'gpt-realtime',
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

# ====== Outbound Voice via LiveKit SIP Gateway ======
_livekit_client: Optional[Any] = None
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

async def _get_livekit_client() -> Any:
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
    from_number = _normalize_phone(
        req.from_number or 
        os.environ.get('NOVOFON_CALLER_ID') or 
        os.environ.get('DEFAULT_CALLER_ID') or 
        os.environ.get('LIVEKIT_DEFAULT_FROM') or 
        ''
    )
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
    
    # Include AI agent status if it's an AI call
    details = {k:v for k,v in info.items() if k not in ('status','call_id')}
    if info.get('ai_enabled'):
        details['ai_agent_status'] = info.get('ai_agent_status', 'unknown')
        if 'ai_agent_error' in info:
            details['ai_agent_error'] = info['ai_agent_error']
    
    return CallStatusResponse(call_id=call_id, status=info.get('status','unknown'), details=details)

logger.info('Main API router mounted')
# ====== AI-Powered Outbound Calls ======
class AICallRequest(BaseModel):
    phone_number: str
    prompt_id: Optional[str] = Field(default='pmpt_68b199151b248193a68a8c70861adf550e6f2509209ed3a5')
    voice: Optional[str] = Field(default='marin')
    greeting: Optional[str] = Field(default='Здравствуйте! Это VasDom AudioBot.')
    trunk_id: Optional[str] = None
    from_number: Optional[str] = None

class AICallResponse(BaseModel):
    call_id: str
    room_name: str
    status: str

_ai_call_workers: Dict[str, Any] = {}

# In-memory call logs for observability (non-persistent)
_ai_call_logs: Dict[str, List[Dict[str, Any]] ] = {}

def _add_call_log(call_id: str, level: str, message: str):
    try:
        if call_id not in _ai_call_logs:
            _ai_call_logs[call_id] = []
        _ai_call_logs[call_id].append({
            'ts': int(datetime.now(timezone.utc).timestamp()),
            'level': level,
            'message': message[:2000]
        })
        # cap at last 500 entries per call to bound memory
        if len(_ai_call_logs[call_id]) > 500:
            _ai_call_logs[call_id] = _ai_call_logs[call_id][-500:]
    except Exception:
        pass


async def _run_ai_agent_worker(room_name: str, call_id: str, prompt_id: str, voice: str, greeting: str):
    """Background task to run AI agent with direct OpenAI Realtime API"""
    if not LIVEKIT_AVAILABLE:
        logger.error(f"[AI-CALL {call_id}] LiveKit SDK not available")
        return

    import websockets
    import base64
    import audioop
    import time


    try:
        import livekit.rtc as rtc
        REvent = getattr(rtc, "RoomEvent", None)

        logger.info(f"[AI-CALL {call_id}] Starting Direct OpenAI Realtime agent for room={room_name}, prompt={prompt_id}")

        # Get credentials
        host = os.environ.get('LIVEKIT_URL') or os.environ.get('LIVEKIT_HOST') or os.environ.get('LIVEKIT_WS_URL')
        api_key = os.environ.get('LIVEKIT_API_KEY')
        api_secret = os.environ.get('LIVEKIT_API_SECRET')
        openai_key = os.environ.get('OPENAI_API_KEY')

        if not all([host, api_key, api_secret, openai_key]):
            logger.error(f"[AI-CALL {call_id}] Missing credentials")
            _call_store[call_id]['ai_agent_status'] = 'failed'
            _call_store[call_id]['ai_agent_error'] = 'Missing credentials'
            return

        # Normalize host for WebSocket
        ws_url = host
        if ws_url.startswith('https://'):
            ws_url = 'wss://' + ws_url[len('https://'):]
        elif ws_url.startswith('http://'):
            ws_url = 'ws://' + ws_url[len('http://'):]
        elif not ws_url.startswith('ws'):
            ws_url = 'wss://' + ws_url

        logger.info(f"[AI-CALL {call_id}] Connecting to LiveKit: {ws_url}")

        # Generate access token for AI agent
        from livekit import api as lk_api_token
        token = lk_api_token.AccessToken(api_key, api_secret)
        token.identity = f'ai_agent_{call_id}'
        token.name = 'AI Assistant'
        token.with_grants(lk_api_token.VideoGrants(
            room_join=True,
            room=room_name,
            can_publish=True,
            can_subscribe=True,
            can_publish_data=True
        ))
        agent_token = token.to_jwt()

        # Create and connect Room
        room = rtc.Room()
        await room.connect(ws_url, agent_token)
        logger.info(f"[AI-CALL {call_id}] Agent connected to LiveKit room")
        _add_call_log(call_id, 'info', 'Agent connected to LiveKit room')

        # Create local audio track for AI speech (24k mono to match OpenAI Realtime PCM16 output)
        source_sr = 24000
        source_ch = 1
        logger.info(f"[AI-CALL {call_id}] Creating AI AudioSource: sr={source_sr}, ch={source_ch}")
        source = rtc.AudioSource(sample_rate=source_sr, num_channels=source_ch)
        track = rtc.LocalAudioTrack.create_audio_track("ai_voice", source)
        options = rtc.TrackPublishOptions()
        options.source = rtc.TrackSource.SOURCE_MICROPHONE
        await room.local_participant.publish_track(track, options)
        logger.info(f"[AI-CALL {call_id}] Published local audio track (target sr={source_sr}, ch={source_ch})")

        # Smoother playback chunking and text accumulator
        AI_FRAME_BYTES = int(0.02 * 24000 * 2)  # 20ms @ 24k, 960 bytes
        ai_out_buf = bytearray()
        ai_backlog_limit = AI_FRAME_BYTES * 50  # ~1 sec max backlog
        response_text_acc: list[str] = []
        last_cancel_ts = 0.0

        # Audio forwarding state
        pstn_track = None
        is_running = True

        # Helpers for diagnostics
        def _safe_attr(obj, name, default=None):
            try:
                return getattr(obj, name)
            except Exception:
                return default

        def _describe_pub(pub):
            return {
                'sid': _safe_attr(pub, 'sid'),
                'track_sid': _safe_attr(pub, 'track_sid'),
                'kind': str(_safe_attr(pub, 'kind')),
                'track_kind': str(_safe_attr(pub, 'track_kind')),
                'source': str(_safe_attr(pub, 'source')),
                'subscribed': _safe_attr(pub, 'subscribed'),
                'is_subscribed': _safe_attr(pub, 'is_subscribed'),
                'muted': _safe_attr(pub, 'muted'),
                'disabled': _safe_attr(pub, 'disabled'),
                'track_name': _safe_attr(pub, 'track_name'),
                'stream_state': _safe_attr(pub, 'stream_state')
            }

        # Helper to normalize publications collection (dict or list)
        def _pub_values(participant: rtc.RemoteParticipant):
            try:
                pubs = getattr(participant, 'track_publications', {}) or {}
                if isinstance(pubs, dict):
                    return list(pubs.values())
                return list(pubs)
            except Exception:
                return []

        # Event handlers to reliably subscribe to PSTN audio
        def _is_audio_pub(pub) -> bool:
            try:
                k = _safe_attr(pub, 'kind')
                if k is None:
                    return False
                # Support enum, int, or string representations
                if hasattr(rtc.TrackKind, 'KIND_AUDIO') and k == rtc.TrackKind.KIND_AUDIO:
                    return True
                if isinstance(k, int) and k == 1:
                    return True
                if str(k).lower() in ('1', 'audio', 'trackkind.kind_audio', 'kindaudio'):
                    return True
            except Exception:
                return False
            return False

        def on_track_subscribed(track_obj: rtc.Track, publication: rtc.TrackPublication, participant: rtc.RemoteParticipant):
            nonlocal pstn_track
            try:
                info = _describe_pub(publication)
                logger.info(f"[AI-CALL {call_id}] Track subscribed: track_kind={getattr(track_obj,'kind',None)} pub={info} participant={participant.identity}")
                if _is_audio_pub(publication):
                    # Ensure subscription
                    asyncio.create_task(_force_subscribe(publication, participant, reason="track_subscribed"))
                    # Treat first remote audio as PSTN if not our AI participant
                    if (participant.identity or '') != f'ai_agent_{call_id}' and pstn_track is None:
                        pstn_track = track_obj
                        logger.info(f"[AI-CALL {call_id}] Remote audio captured as PSTN from participant={participant.identity}")
            except Exception as e:
                logger.error(f"[AI-CALL {call_id}] on_track_subscribed error: {e}")

        async def _force_subscribe(pub: rtc.RemoteTrackPublication, participant: rtc.RemoteParticipant, reason: str = "event"):
            nonlocal pstn_track
            try:
                info = _describe_pub(pub)
                logger.info(f"[AI-CALL {call_id}] [subscribe:{reason}] pub={info} participant={participant.identity}")
                # Try multiple ways to ensure subscription
                if hasattr(pub, 'set_subscribed'):
                    pub.set_subscribed(True)
                if hasattr(pub, 'subscribed') and not pub.subscribed and hasattr(pub, 'set_subscribed'):
                    pub.set_subscribed(True)
                if hasattr(pub, 'is_subscribed') and not pub.is_subscribed and hasattr(pub, 'set_subscribed'):
                    pub.set_subscribed(True)
                # If track object is available after subscription, capture it
                trk = getattr(pub, 'track', None)
                if trk and pstn_track is None and _is_audio_pub(pub) and (getattr(participant, 'identity', '') != f'ai_agent_{call_id}'):
                    pstn_track = trk
                    logger.info(f"[AI-CALL {call_id}] Captured PSTN track from publication.track after subscribe")
            except Exception as e:
                logger.error(f"[AI-CALL {call_id}] force_subscribe error: {e}")

        def on_track_published(publication: rtc.RemoteTrackPublication, participant: rtc.RemoteParticipant):
            try:
                info = _describe_pub(publication)
                logger.info(f"[AI-CALL {call_id}] Track published: pub={info} by={participant.identity}")
                if _is_audio_pub(publication):
                    asyncio.create_task(_force_subscribe(publication, participant, reason="track_published"))
                else:
                    logger.info(f"[AI-CALL {call_id}] Ignoring non-audio publication")
            except Exception as e:
                logger.error(f"[AI-CALL {call_id}] Error handling track_published: {e}")

        def on_track_subscription_failed(track_sid: str, participant: rtc.RemoteParticipant):
            logger.error(f"[AI-CALL {call_id}] Track subscription failed for sid={track_sid} participant={participant.identity}")

        def on_participant_connected(participant: rtc.RemoteParticipant):
            try:
                pubs = _pub_values(participant)
                logger.info(f"[AI-CALL {call_id}] Participant connected: id={participant.identity}, pubs={len(pubs)}")
                for pub in pubs:
                    info = _describe_pub(pub)
                    logger.info(f"[AI-CALL {call_id}] Participant pub on connect: pub={info}")
                    asyncio.create_task(_force_subscribe(pub, participant, reason="participant_connected"))
            except Exception as e:
                logger.error(f"[AI-CALL {call_id}] Error on participant_connected: {e}")

        def on_participant_disconnected(participant: rtc.RemoteParticipant):
            logger.warning(f"[AI-CALL {call_id}] Participant disconnected: {participant.identity}")
            if 'pstn' in (participant.identity or ''):
                logger.error(f"[AI-CALL {call_id}] PSTN participant disconnected - call may not have been answered!")
                _call_store[call_id]['status'] = 'failed'
                _call_store[call_id]['error'] = {'message': 'Call not answered or disconnected'}

        # Fallback to enable auto_subscribe if API available
        try:
            if hasattr(room, 'set_auto_subscribe'):
                room.set_auto_subscribe(True)
                logger.info(f"[AI-CALL {call_id}] Enabled auto_subscribe via API")
        # Register event listeners using constants when available
        except Exception:
            pass

        try:
            if REvent:
                room.on(REvent.ParticipantConnected, on_participant_connected)
                room.on(REvent.TrackPublished, on_track_published)
                room.on(REvent.TrackSubscribed, on_track_subscribed)
                room.on(REvent.TrackSubscriptionFailed, on_track_subscription_failed)
                room.on(REvent.ParticipantDisconnected, on_participant_disconnected)
                logger.info(f"[AI-CALL {call_id}] Event listeners registered via RoomEvent")
        except Exception as e:
            logger.warning(f"[AI-CALL {call_id}] RoomEvent constants not available: {e}")
            logger.warning(f"[AI-CALL {call_id}] auto_subscribe setup not available: {e}")

        # Register listeners
        room.on("participant_connected", on_participant_connected)
        room.on("track_published", on_track_published)
        room.on("track_subscribed", on_track_subscribed)
        room.on("track_subscription_failed", on_track_subscription_failed)
        room.on("participant_disconnected", on_participant_disconnected)

        # Ensure we subscribe to any already-connected PSTN participant
        try:
            remotes = getattr(room, 'remote_participants', {}) or {}
            participants = list(remotes.values()) if isinstance(remotes, dict) else list(remotes)
            logger.info(f"[AI-CALL {call_id}] Existing remote participants: {len(participants)}")
            for p in participants:
                pubs = _pub_values(p)
                logger.info(f"[AI-CALL {call_id}] Existing participant={getattr(p, 'identity', '')}, pubs={len(pubs)}")
                for pub in pubs:
                    logger.info(f"[AI-CALL {call_id}] Existing pub kind={getattr(pub, 'kind', None)} sid={getattr(pub, 'sid', None)} subscribed={getattr(pub,'subscribed',None)}")
        except Exception as e:
            logger.error(f"[AI-CALL {call_id}] Error while enumerating existing participants: {e}")

        async def _periodic_subscribe_retry():
            attempts = 0
            while is_running and attempts < 30 and pstn_track is None:
                await asyncio.sleep(1.0)
                attempts += 1
                try:
                    remotes = getattr(room, 'remote_participants', {}) or {}
                    participants = list(remotes.values()) if isinstance(remotes, dict) else list(remotes)
                    for p in participants:
                        pubs = _pub_values(p)
                        for pub in pubs:
                            await _force_subscribe(pub, p, reason=f"retry#{attempts}")
                except Exception as e:
                    logger.error(f"[AI-CALL {call_id}] periodic subscribe retry error: {e}")

        # Wait briefly for PSTN to join
        await asyncio.sleep(2.0)

        # Connect to OpenAI Realtime API
        logger.info(f"[AI-CALL {call_id}] Connecting to OpenAI Realtime API...")
        openai_ws_url = "wss://api.openai.com/v1/realtime?model=gpt-realtime"
        # Build headers for different websockets versions
        header_tuples = [("Authorization", f"Bearer {openai_key}"), ("OpenAI-Beta", "realtime=v1")]
        openai_ws = None
        try:
            # Most versions support extra_headers with list of tuples
            openai_ws = await websockets.connect(openai_ws_url, extra_headers=header_tuples)
            logger.info(f"[AI-CALL {call_id}] Connected to OpenAI Realtime API via extra_headers")
        except TypeError as e:
            if 'extra_headers' in str(e):
                logger.warning(f"[AI-CALL {call_id}] websockets.connect extra_headers unsupported, retrying with additional_headers")
                openai_ws = await websockets.connect(openai_ws_url, additional_headers=header_tuples)
                logger.info(f"[AI-CALL {call_id}] Connected to OpenAI Realtime API via additional_headers")
            else:
                raise

        # Configure session with prompt ID
        session_config = {
            "type": "session.update",
            "session": {
                "modalities": ["text", "audio"],
                "voice": voice or "marin",
                "temperature": 0.9,  # Более естественные ответы
                "turn_detection": {
                    "type": "server_vad",
                    "threshold": 0.5,  # Более чувствительная детекция
                    "prefix_padding_ms": 300,  # Больше контекста перед речью
                    "silence_duration_ms": 500  # Больше паузы перед ответом (естественнее)
                },
                "prompt": {"id": prompt_id},
                "input_audio_format": "pcm16",
                "output_audio_format": "pcm16",
                "input_audio_transcription": {"model": "whisper-1", "language": "ru"},
                "tool_choice": "auto",
                "instructions": "Ты — живой человек, ассистент VasDom, собираешь отчеты от сотрудников по телефону. Говори естественно, коротко, как в обычном разговоре. Иногда используй 'хм', 'ага', 'понятно'. Задавай короткие уточняющие вопросы. Не говори что ты AI.",
                "max_response_output_tokens": 300  # Короче, естественнее
            }
        }
        await openai_ws.send(json.dumps(session_config))
        logger.info(f"[AI-CALL {call_id}] Sent session config with prompt ID: {prompt_id}")

        # Start periodic subscribe retry in background
        retry_task = asyncio.create_task(_periodic_subscribe_retry())

        # Watchdog for OpenAI audio after greeting
        got_openai_audio = False
        async def _openai_greeting_watchdog():
            try:
                # wait a short period; if no audio chunks received, re-trigger greeting
                await asyncio.sleep(2.0)
                if not got_openai_audio:
                    logger.info(f"[AI-CALL {call_id}] No OpenAI audio yet, re-triggering greeting")
                    try:
                        await openai_ws.send(json.dumps({
                            "type": "response.create",
                            "response": {
                                "modalities": ["text", "audio"],
                                "instructions": f"Скажи естественно: {greeting}",
                                "temperature": 0.9
                            }
                        }))
                    except Exception as e:
                        logger.error(f"[AI-CALL {call_id}] Failed to re-trigger greeting: {e}")
            except Exception:
                pass

        # TTS synthesis with OpenAI gpt-4o-mini-tts (marin)
        async def _synth_and_play_tts(text: str):
            nonlocal ai_talking
            if not text:
                return
            try:
                import io
                import wave
                ai_talking = True
                # Call OpenAI TTS
                try:
                    async with httpx.AsyncClient(timeout=60) as cli:
                        resp = await cli.post(
                            'https://api.openai.com/v1/audio/speech',
                            headers={
                                'Authorization': f'Bearer {openai_key}',
                                'Content-Type': 'application/json'
                            },
                            json={
                                'model': 'gpt-4o-mini-tts',
                                'voice': (voice or 'marin'),
                                'input': text,
                                'format': 'wav'
                            }
                        )
                        if resp.status_code != 200:
                            logger.error(f"[AI-CALL {call_id}] TTS error: {resp.status_code} {resp.text}")
                            return
                        wav_bytes = resp.content
                except Exception as e:
                    logger.error(f"[AI-CALL {call_id}] TTS request failed: {e}")
                    return

                # Decode WAV -> PCM16 mono 16k
                try:
                    bio = io.BytesIO(wav_bytes)
                    w = wave.open(bio, 'rb')
                    sr = w.getframerate()
                    ch = w.getnchannels()
                    sampw = w.getsampwidth()
                    nframes = w.getnframes()
                    pcm = w.readframes(nframes)
                    w.close()
                    # ensure 16-bit
                    if sampw != 2:
                        try:
                            pcm = audioop.lin2lin(pcm, sampw, 2)
                        except Exception as e:
                            logger.error(f"[AI-CALL {call_id}] TTS lin2lin failed: {e}")
                            return
                    # to mono
                    if ch and ch > 1:
                        try:
                            pcm = audioop.tomono(pcm, 2, 0.5, 0.5)
                            ch = 1
                        except Exception as e:
                            logger.error(f"[AI-CALL {call_id}] TTS tomono failed: {e}")
                            return
                    # resample to 16k if needed
                    if sr != 16000:
                        try:
                            pcm, _ = audioop.ratecv(pcm, 2, ch or 1, sr, 16000, None)
                            sr = 16000
                        except Exception as e:
                            logger.error(f"[AI-CALL {call_id}] TTS ratecv failed: {e}")
                            return
                    # Stream into LiveKit source in ~20ms frames
                    frame_bytes = int(0.02 * 16000 * 2)  # 640 bytes
                    # playback chunking defined at worker scope

                    total = 0
                    for i in range(0, len(pcm), frame_bytes):
                        chunk = pcm[i:i+frame_bytes]
                        if not chunk:
                            continue
                        try:
                            frame = rtc.AudioFrame(
                                data=chunk,
                                sample_rate=16000,
                                num_channels=1,
                                samples_per_channel=len(chunk)//2
                            )
                            await source.capture_frame(frame)
                            total += len(chunk)
                        except Exception as e:
                            logger.error(f"[AI-CALL {call_id}] TTS capture_frame error: {e}")
                            break
                    logger.info(f"[AI-CALL {call_id}] TTS played: bytes={total}, text_len={len(text)}")
                except Exception as e:
                    logger.error(f"[AI-CALL {call_id}] TTS decode/play failed: {e}")
            finally:
                ai_talking = False

        # Handle OpenAI responses -> push audio to LiveKit
        ai_talking = False

        async def handle_openai_messages():
            nonlocal is_running, got_openai_audio, ai_talking
            openai_audio_bytes = 0
            openai_audio_frames = 0
            try:
                async for message in openai_ws:
                    event = json.loads(message)
                    etype = event.get('type')
                    if etype == 'session.created':
                        logger.info(f"[AI-CALL {call_id}] OpenAI session created")
                    elif etype == 'response.text.delta':
                        # Накопим текст для логов наблюдаемости
                        try:
                            txt = event.get('delta') or ''
                            if txt:
                                response_text_acc.append(txt)
                        except Exception:
                            pass
                    elif etype == 'response.output_text.delta':
                        # альтернативное имя события у некоторых версий
                        try:
                            txt = event.get('delta') or ''
                            if txt:
                                response_text_acc.append(txt)
                        except Exception:
                            pass

                    elif etype == 'session.updated':
                        logger.info(f"[AI-CALL {call_id}] OpenAI session updated with prompt")
                    elif etype == 'response.audio.delta':
                        # NATIVE OpenAI audio - напрямую в LiveKit с выравниванием по 20мс
                        delta_b64 = event.get('delta', '')
                        if delta_b64:
                            got_openai_audio = True
                            ai_talking = True
                            try:
                                pcm = base64.b64decode(delta_b64)
                                openai_audio_bytes += len(pcm)

                                # буферизуем и порежем на ровные 20мс фреймы
                                ai_out_buf.extend(pcm)
                                # ограничение очереди ~1с чтобы не накапливать задержку
                                if len(ai_out_buf) > ai_backlog_limit:
                                    drop = len(ai_out_buf) - ai_backlog_limit
                                    del ai_out_buf[:drop]
                                    logger.debug(f"[AI-CALL {call_id}] Dropped backlog bytes={drop}")

                                while len(ai_out_buf) >= AI_FRAME_BYTES:
                                    chunk = ai_out_buf[:AI_FRAME_BYTES]
                                    del ai_out_buf[:AI_FRAME_BYTES]
                                    samples = len(chunk)//2
                                    frame = rtc.AudioFrame(
                                        data=bytes(chunk),
                                        sample_rate=24000,
                                        num_channels=1,
                                        samples_per_channel=samples
                                    )
                                    logger.debug(f"[AI-CALL {call_id}] OpenAI delta frame: bytes={len(chunk)}, samples={samples}, sr=24000, ch=1")
                                    await source.capture_frame(frame)
                                    openai_audio_frames += 1
                                # barge-in inside OpenAI loop not needed
                            except Exception as e:
                                logger.error(f"[AI-CALL {call_id}] Audio delta error: {e}")
                    elif etype == 'response.done':
                        ai_talking = False
                        # логируем краткий текст ответа
                        if response_text_acc:
                            _add_call_log(call_id, 'ai_text', ''.join(response_text_acc)[:1000])
                            response_text_acc.clear()
                        logger.info(f"[AI-CALL {call_id}] OpenAI response.done (audio_bytes={openai_audio_bytes}, frames={openai_audio_frames})")
                        openai_audio_bytes = 0
                        openai_audio_frames = 0
                    elif etype == 'error':
                        logger.error(f"[AI-CALL {call_id}] OpenAI error: {event.get('error')}")
            except Exception as e:
                logger.error(f"[AI-CALL {call_id}] OpenAI message handler error: {e}")
            finally:
                is_running = False

        # Forward PSTN audio to OpenAI - ПРОСТАЯ отправка без manual VAD
        async def forward_pstn_to_openai():
            nonlocal is_running
            # wait until we get a track
            t0 = time.time()
            while is_running and not pstn_track:
                await asyncio.sleep(0.1)
                if time.time() - t0 > 15:
                    logger.warning(f"[AI-CALL {call_id}] Timeout waiting for PSTN audio track (15s)")
                    break
            if not pstn_track:
                logger.warning(f"[AI-CALL {call_id}] No PSTN track found")
                return
            try:
                audio_stream = rtc.AudioStream(pstn_track)
                logger.info(f"[AI-CALL {call_id}] Forwarding PSTN audio to OpenAI (Server VAD mode)")
                frame_count = 0
                bytes_sent = 0
                last_log = time.time()
                first_frame_logged = False
                mismatch_logged = False

                async for evt in audio_stream:
                    # Unwrap AudioFrameEvent -> AudioFrame when needed
                    frame_obj = getattr(evt, 'frame', evt)
                    sr = getattr(frame_obj, 'sample_rate', 48000)
                    ch = getattr(frame_obj, 'num_channels', 1)
                    data = getattr(frame_obj, 'data', None)
                    if data is None:
                        # Try alternate properties just in case
                        data = getattr(frame_obj, 'pcm', None) or getattr(frame_obj, 'buffer', None)
                        if data is not None and not isinstance(data, (bytes, bytearray)):
                            try:
                                data = bytes(data)
                            except Exception:
                                data = None
                    if not first_frame_logged:
                        size = len(data) if isinstance(data, (bytes, bytearray)) else 0
                        logger.info(f"[AI-CALL {call_id}] PSTN AudioStream first frame received: sr={sr} ch={ch} size={size}")
                        first_frame_logged = True
                    # log mismatches once
                    if (sr != 24000 or ch != 1) and not mismatch_logged:
                        logger.warning(f"[AI-CALL {call_id}] PSTN frame mismatch detected: incoming sr={sr}, ch={ch}; will convert to sr=24000, ch=1")
                        mismatch_logged = True
                    if not is_running:
                        break
                    if not data:
                        continue
                    
                    # Basic audio processing - convert to 24kHz mono PCM16 for OpenAI
                    # to mono if needed
                    if ch and ch > 1:
                        try:
                            data = audioop.tomono(data, 2, 0.5, 0.5)
                            ch = 1
                        except Exception as e:
                            logger.error(f"[AI-CALL {call_id}] tomono failed: {e}")
                    
                    # resample to 24k if needed (OpenAI Realtime prefers 24kHz)
                    if sr and sr != 24000:
                        try:
                            before = len(data)
                            data, _ = audioop.ratecv(data, 2, ch or 1, sr, 24000, None)
                            sr = 24000
                            logger.debug(f"[AI-CALL {call_id}] PSTN resampled to 24k: bytes {before}->{len(data)}")
                        except Exception as e:
                            logger.error(f"[AI-CALL {call_id}] ratecv failed (sr={sr}): {e}")
                    
                    # Send directly to OpenAI - let server VAD handle everything
                    audio_b64 = base64.b64encode(data).decode('utf-8')
                    await openai_ws.send(json.dumps({"type": "input_audio_buffer.append", "audio": audio_b64}))
                    frame_count += 1
                    bytes_sent += len(data)

                    # Simple periodic logging
                    if time.time() - last_log > 5.0:
                        logger.info(f"[AI-CALL {call_id}] PSTN->OpenAI: frames={frame_count}, bytes_sent={bytes_sent}, sr={sr}, ch={ch}")
                        _add_call_log(call_id, 'metric', f'PSTN->OpenAI frames={frame_count} bytes={bytes_sent} sr={sr} ch={ch}')
                        last_log = time.time()

            except Exception as e:
                logger.error(f"[AI-CALL {call_id}] PSTN audio forwarding error: {e}")

        # Start both handlers
        openai_task = asyncio.create_task(handle_openai_messages())
        pstn_task = asyncio.create_task(forward_pstn_to_openai())

        # Initial greeting
        await asyncio.sleep(1.0)
        logger.info(f"[AI-CALL {call_id}] Sending initial greeting via OpenAI")
        await openai_ws.send(json.dumps({
            "type": "response.create",
            "response": {
                "modalities": ["text", "audio"],
                "instructions": f"Скажи естественно: {greeting}",
                "temperature": 0.9
            }
        }))

        # Start watchdog for greeting audio
        watchdog_task = asyncio.create_task(_openai_greeting_watchdog())

        _call_store[call_id]['ai_agent_status'] = 'active'
        logger.info(f"[AI-CALL {call_id}] Direct OpenAI AI agent is now active")

        # Store worker info
        _ai_call_workers[call_id] = {
            'room': room,
            'openai_ws': openai_ws,
            'track': track,
            'source': source,
            'tasks': [openai_task, pstn_task, watchdog_task]
        }

        # Wait for tasks
        await asyncio.gather(openai_task, pstn_task, watchdog_task, return_exceptions=True)

    except Exception as e:
        logger.exception(f"[AI-CALL {call_id}] Direct OpenAI agent error: {e}")
        if call_id in _call_store:
            _call_store[call_id]['ai_agent_status'] = 'failed'
            _call_store[call_id]['ai_agent_error'] = str(e)
        try:
            await retry_task
        except Exception:
            pass


@api_router.post('/voice/ai-call', response_model=AICallResponse)
async def voice_ai_call(req: AICallRequest):
    """Create an AI-powered outbound call with Direct OpenAI Realtime API and prompt ID"""
    lk = await _get_livekit_client()
    call_id = uuid4().hex
    to = _normalize_phone(req.phone_number)
    
    if not to:
        raise HTTPException(status_code=400, detail='phone_number is empty')
    
    # Validate OpenAI API key
    openai_key = os.environ.get('OPENAI_API_KEY')
    if not openai_key:
        raise HTTPException(status_code=500, detail='OPENAI_API_KEY not configured')
    
    trunk_id = req.trunk_id or os.environ.get('LIVEKIT_SIP_TRUNK_ID')
    if not trunk_id:
        raise HTTPException(status_code=500, detail='LIVEKIT_SIP_TRUNK_ID not configured')
    
    from_number = _normalize_phone(
        req.from_number or 
        os.environ.get('NOVOFON_CALLER_ID') or 
        os.environ.get('DEFAULT_CALLER_ID') or 
        os.environ.get('LIVEKIT_DEFAULT_FROM') or 
        ''
    )
    if not from_number:
        from_number = None
    
    # Create room name
    room_name = f'ai_call_{call_id}'
    
    _call_store[call_id] = {
        'call_id': call_id,
        'room_name': room_name,
        'status': 'initiating',
        'to': to,
        'from': from_number,
        'ts': int(datetime.now(timezone.utc).timestamp()),
        'ai_enabled': True,
        'prompt_id': req.prompt_id,
        'voice': req.voice,
        'greeting': req.greeting,
        'ai_agent_status': 'starting'
    }
    
    try:
        logger.info(f"[AI-CALL {call_id}] Creating SIP participant for {to} (from: {from_number}, trunk: {trunk_id})")
        
        # Create SIP participant (outbound call)
        result = await lk.sip.create_sip_participant(
            lk_api.CreateSIPParticipantRequest(
                sip_trunk_id=trunk_id,
                sip_call_to=to,
                room_name=room_name,
                sip_number=from_number or '',
                participant_identity=f'pstn_{call_id}',
                participant_name=f'Outbound {to}',
            )
        )
        
        _call_store[call_id]['status'] = 'ringing'
        _call_store[call_id]['sip_participant_identity'] = getattr(result, 'identity', None)
        _call_store[call_id]['sip_participant_id'] = getattr(result, 'participant_id', None)
        
        logger.info(f"[AI-CALL {call_id}] SIP participant created: identity={getattr(result, 'identity', None)}, id={getattr(result, 'participant_id', None)}")
        
        logger.info(f"[AI-CALL {call_id}] SIP participant created, starting AI agent...")
        
        # Start AI agent in background
        asyncio.create_task(_run_ai_agent_worker(
            room_name=room_name,
            call_id=call_id,
            prompt_id=req.prompt_id or 'pmpt_68b199151b248193a68a8c70861adf550e6f2509209ed3a5',
            voice=req.voice or 'marin',
            greeting=req.greeting or 'Здравствуйте! Это VasDom AudioBot.'
        ))
        
        logger.info(f"[AI-CALL {call_id}] AI call initiated successfully")
        
        return AICallResponse(
            call_id=call_id,
            room_name=room_name,
            status='ringing'
        )
        
    except lk_api.TwirpError as e:
        logger.error(f"[AI-CALL {call_id}] LiveKit SIP error: {e}")
        _call_store[call_id]['status'] = 'failed'
        _call_store[call_id]['error'] = {'code': getattr(e, 'code', ''), 'message': str(e)}
        raise HTTPException(status_code=502, detail=f'LiveKit SIP error: {e}')
    except Exception as e:
        logger.exception(f"[AI-CALL {call_id}] Unexpected error")
        _call_store[call_id]['status'] = 'failed'
        _call_store[call_id]['error'] = {'message': str(e)}
        raise HTTPException(status_code=500, detail=f'Failed to start AI call: {str(e)}')

@api_router.get('/voice/debug/check')
async def voice_debug_check():
    host = os.environ.get('LIVEKIT_URL') or os.environ.get('LIVEKIT_HOST') or os.environ.get('LIVEKIT_WS_URL')
    api_key_set = bool(os.environ.get('LIVEKIT_API_KEY'))
    api_secret_set = bool(os.environ.get('LIVEKIT_API_SECRET'))
    openai_key_set = bool(os.environ.get('OPENAI_API_KEY'))
    trunk_id = os.environ.get('LIVEKIT_SIP_TRUNK_ID')
    caller = os.environ.get('NOVOFON_CALLER_ID') or os.environ.get('DEFAULT_CALLER_ID') or os.environ.get('LIVEKIT_DEFAULT_FROM')
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
        'openai_key_set': openai_key_set,
        'trunk_id_set': bool(trunk_id),
        'trunk_id': trunk_id[:4] + '****' if trunk_id else None,
        'default_caller': caller,
        'routes': ['/api/voice/call/start', '/api/voice/ai-call', '/api/voice/call/{call_id}/status']
    }

@api_router.post('/voice/webhooks/livekit')
async def livekit_webhook(request: Request):
    """Handle LiveKit webhooks (room events, participant events, etc.)"""
    try:
        body = await request.json()
        event_type = body.get('event')
        logger.info(f"[WEBHOOK] LiveKit event: {event_type}")
        # Log the webhook for debugging but don't process it for now
        # In production, you might want to verify the webhook signature
        return {'ok': True}
    except Exception as e:
        logger.error(f"[WEBHOOK] Error processing webhook: {e}")
        return {'ok': False, 'error': str(e)}

@api_router.get('/voice/ai-call/{call_id}/logs')
async def voice_ai_call_logs(call_id: str):
    try:
        logs = _ai_call_logs.get(call_id) or []
        return {'call_id': call_id, 'logs': logs}
    except Exception as e:
        return {'call_id': call_id, 'logs': [], 'error': str(e)}


# Mount API router with all voice endpoints
app.include_router(api_router)
logger.info('API router mounted with all voice endpoints')

# Import and mount new modular routers
try:
    # Попытка импорта для Render (uvicorn backend.server:app из корня)
    from backend.app.routers import health, auth, houses, cleaning, telegram, dashboard, logs, ai_knowledge, tasks, meetings, notifications, employees, ai_agent, ai_chat, finances, finance_transactions, finance_articles, revenue, debts, inventory, agents, telegram_webhook, agent_dashboard, render_logs, plannerka, realtime_transcription, telegram_auth, call_summary, bitrix_calls, bitrix_webhook, test_agent, debug_users
    from backend.app.routers import brain as brain_router

    from backend.app.routers import ai_assistant_api as ai_assistant_api_router

    logger.info('✅ Routers imported via backend.app.routers')
except Exception as e1:
    logger.warning(f'⚠️ First import attempt failed (backend.app.routers): {e1}')
    try:
        from app.routers import brain as brain_router

        from app.routers import ai_assistant_api as ai_assistant_api_router

        # Попытка импорта для локальной разработки (uvicorn server:app из backend/)
        from app.routers import health, auth, houses, cleaning, telegram, dashboard, logs, ai_knowledge, tasks, meetings, notifications, employees, ai_agent, ai_chat, finances, finance_transactions, finance_articles, revenue, agents, telegram_webhook, agent_dashboard, render_logs, plannerka, realtime_transcription, telegram_auth, call_summary, bitrix_calls, bitrix_webhook, test_agent, debug_users
        logger.info('✅ Routers imported via app.routers')
    except Exception as e2:
        logger.error(f'⚠️ Could not mount new routers: {e2}')
        import traceback
        logger.error(f'Traceback: {traceback.format_exc()}')
        health = auth = houses = cleaning = telegram = dashboard = logs = ai_knowledge = tasks = meetings = notifications = employees = ai_agent = ai_chat = finances = finance_transactions = finance_articles = revenue = agents = telegram_webhook = agent_dashboard = render_logs = plannerka = realtime_transcription = None

if health:
    try:
        app.include_router(health.router, prefix="/api")
        app.include_router(auth.router, prefix="/api")
        app.include_router(houses.router, prefix="/api")
        app.include_router(cleaning.router, prefix="/api")
        app.include_router(telegram.router, prefix="/api")
        app.include_router(dashboard.router, prefix="/api")
        app.include_router(logs.router, prefix="/api")
        app.include_router(ai_knowledge.router, prefix="/api")
        app.include_router(tasks.router, prefix="/api")
        app.include_router(meetings.router, prefix="/api")
        app.include_router(notifications.router, prefix="/api")
        app.include_router(employees.router, prefix="/api")
        app.include_router(ai_agent.router, prefix="/api")
        app.include_router(ai_chat.router, prefix="/api")
        app.include_router(finances.router, prefix="/api")
        app.include_router(finance_transactions.router, prefix="/api/finances")
        app.include_router(finance_articles.router, prefix="/api/finances")
        app.include_router(revenue.router, prefix="/api/finances")
        app.include_router(brain_router.router, prefix="/api")

        app.include_router(ai_assistant_api_router.router, prefix="/api")

        app.include_router(agents.router, prefix="/api")
        app.include_router(telegram_webhook.router, prefix="/api")
        app.include_router(agent_dashboard.router, prefix="/api")
        app.include_router(render_logs.router, prefix="/api")
        app.include_router(plannerka.router, prefix="/api")
        app.include_router(realtime_transcription.router, prefix="/api")
        app.include_router(telegram_auth.router, prefix="/api")
        app.include_router(call_summary.router, prefix="/api")
        app.include_router(bitrix_calls.router, prefix="/api")
        app.include_router(bitrix_webhook.router, prefix="/api")
        app.include_router(test_agent.router, prefix="/api")
        app.include_router(debug_users.router, prefix="/api")
        logger.info('✅ New modular routers mounted: health, auth, houses, cleaning, telegram, dashboard, logs, ai_knowledge, tasks, meetings, notifications, employees, ai_agent, ai_chat, finances, finance_transactions, finance_articles, revenue, agents, telegram_webhook, agent_dashboard, render_logs, plannerka, realtime_transcription, telegram_auth, call_summary, bitrix_calls, bitrix_webhook, test_agent, debug_users')
    except Exception as e:
        logger.warning(f'⚠️ Could not mount new routers: {e}')
        import traceback
        logger.error(traceback.format_exc())
else:
    logger.error('❌ Routers could not be imported - API endpoints will not be available!')

# NOTE: Voice endpoints are already in api_router (this file), no need for separate voice.py

# Import and start task scheduler
@app.on_event("startup")
async def startup_event():
    """Инициализация при старте приложения"""
    logger.info("🚀 Starting VasDom AudioBot...")
    
    # Инициализация базы данных
    try:
        await init_db()
        logger.info("✅ Database initialized successfully")
        
        # Запуск миграций
        try:
            from backend.app.migrations.run_migrations import run_migrations
            from backend.app.config.database import get_db_pool
            
            db_pool = await get_db_pool()
            if db_pool:
                await run_migrations(db_pool)
                logger.info("✅ Database migrations completed")
        except Exception as migration_error:
            logger.warning(f"⚠️ Migrations skipped: {migration_error}")
            
    except Exception as e:
        logger.error(f"❌ Database initialization failed: {e}")
        logger.warning("⚠️ Please check DATABASE_URL environment variable on Render")
        logger.warning("⚠️ App will continue without database. Some features may not work.")
    
    # Запуск планировщика задач
    try:
        # Попытка импорта для Render
        from backend.app.tasks.scheduler import task_scheduler
        task_scheduler.start()
        logger.info('✅ Task scheduler started')
        
        # Инициализируем планировщик агентов
        try:
            from backend.app.services.agent_scheduler import init_agent_scheduler
            # Передаём реальный APScheduler, а не обёртку
            agent_sched = init_agent_scheduler(task_scheduler.scheduler)
            logger.info('✅ Agent scheduler initialized')
        except Exception as e:
            logger.warning(f'⚠️ Could not initialize agent scheduler: {e}')
            
    except ImportError:
        try:
            # Попытка импорта для локальной разработки
            from app.tasks.scheduler import task_scheduler
            task_scheduler.start()
            logger.info('✅ Task scheduler started')
            
            # Инициализируем планировщик агентов
            try:
                from app.services.agent_scheduler import init_agent_scheduler
                # Передаём реальный APScheduler, а не обёртку
                agent_sched = init_agent_scheduler(task_scheduler.scheduler)
                logger.info('✅ Agent scheduler initialized')
            except Exception as e:
                logger.warning(f'⚠️ Could not initialize agent scheduler: {e}')
                
        except Exception as e:
            logger.warning(f'⚠️ Could not start task scheduler: {e}')

@app.on_event("shutdown")
async def shutdown_event():
    """Очистка при остановке приложения"""
    logger.info("🛑 Stopping VasDom AudioBot...")
    
    # Остановка планировщика
    try:
        # Попытка импорта для Render
        from backend.app.tasks.scheduler import task_scheduler
        task_scheduler.stop()
        logger.info('✅ Task scheduler stopped')
    except ImportError:
        try:
            # Попытка импорта для локальной разработки
            from app.tasks.scheduler import task_scheduler
            task_scheduler.stop()
            logger.info('✅ Task scheduler stopped')
        except Exception as e:
            logger.warning(f'⚠️ Could not stop task scheduler: {e}')
    except Exception as e:
        logger.warning(f'⚠️ Could not stop task scheduler: {e}')