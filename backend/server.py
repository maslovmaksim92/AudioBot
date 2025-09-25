from fastapi import FastAPI, APIRouter, HTTPException, Query, Request
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

app = FastAPI(title="VasDom AudioBot API", version="1.0.0")
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

# ====== LiveKit SIP Outbound calling (Novofon) ======
try:
    from livekit import api as lk_api
    from livekit.plugins import openai as lk_openai
    from livekit import agents as lk_agents
    LIVEKIT_AVAILABLE = True
except Exception:
    LIVEKIT_AVAILABLE = False

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
    global _livekit_trunk_id
    if _livekit_trunk_id:
        return _livekit_trunk_id

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
    try:
        resp = await client.sip.list_sip_outbound_trunk(lk_api.ListSIPOutboundTrunkRequest())
        trunks = getattr(resp, 'trunks', None) or getattr(resp, 'items', None) or []
        for t in trunks:
            if getattr(t, 'name', '') == name:
                tid = getattr(t, 'trunk_id', None) or getattr(t, 'id', None)
                if tid:
                    _livekit_trunk_id = tid
                    logger.info(f'Found existing SIP trunk "{name}": {tid}')
                    return _livekit_trunk_id
    except Exception as e:
        logger.warning(f'List trunks failed: {e}')

    try:
        trunk = lk_api.SIPOutboundTrunkInfo(
            name=name,
            address=(os.environ.get('NOVOFON_SIP_DOMAIN') or 'sip.novofon.ru'),
            numbers=[os.environ.get('NOVOFON_CALLER_ID') or ''],
            auth_username=os.environ.get('NOVOFON_SIP_USERNAME') or '',
            auth_password=os.environ.get('NOVOFON_SIP_PASSWORD') or '',
        )
        created = await client.sip.create_sip_outbound_trunk(lk_api.CreateSIPOutboundTrunkRequest(trunk=trunk))
        tid = getattr(created, 'trunk_id', None) or getattr(created, 'id', None)
        if not tid and hasattr(created, 'trunk'):
            tid = getattr(created.trunk, 'trunk_id', None) or getattr(created.trunk, 'id', None)
        if tid:
            _livekit_trunk_id = tid
            logger.info(f'LiveKit outbound trunk created: {tid}')
            return _livekit_trunk_id
    except Exception as e:
        logger.error(f'Create outbound trunk failed: {e}')
    return None

async def _start_openai_agent(call_id: str, room_name: str, voice: str, instructions: Optional[str]):
    if not LIVEKIT_AVAILABLE:
        return
    room = None
    session = None
    try:
        # Build token
        token = lk_api.AccessToken(api_key=os.environ.get('LIVEKIT_API_KEY'), api_secret=os.environ.get('LIVEKIT_API_SECRET'))
        token = token.with_identity(f'ai_agent_{call_id}').with_name('AI Assistant')
        grants = lk_api.VideoGrants(room_join=True, room=room_name)
        token = token.with_grants(grants)
        jwt = token.to_jwt()

        # Connect to room
        from livekit import rtc as lk_rtc
        ws_url = os.environ.get('LIVEKIT_WS_URL')
        if not ws_url:
            raise RuntimeError('LIVEKIT_WS_URL is not set')
        room = lk_rtc.Room()
        room.on('participant_connected', lambda p: logger.info(f'[CALL {call_id}] participant connected: id={getattr(p,"identity",None)} name={getattr(p,"name",None)}'))
        room.on('participant_disconnected', lambda p: logger.info(f'[CALL {call_id}] participant disconnected: id={getattr(p,"identity",None)} name={getattr(p,"name",None)}'))
        await room.connect(ws_url, jwt)

        # TTS config
        try:
            allowed = {'alloy','verse','coral','sage','ash','ballad','echo','fable','onyx','nova','shimmer'}
            tts_voice = (voice or os.environ.get('OPENAI_TTS_VOICE') or 'alloy').strip()
            if tts_voice not in allowed:
                logger.info(f"[CALL {call_id}] requested voice '{tts_voice}' not in TTS set, falling back to 'alloy'")
                tts_voice = 'alloy'
            tts_model = os.environ.get('OPENAI_TTS_MODEL', 'gpt-4o-mini-tts')
            tts_cfg = lk_openai.TTS(model=tts_model, voice=tts_voice)
            logger.info(f"[CALL {call_id}] TTS configured: model={tts_model}, voice={tts_voice}")
        except Exception as e:
            logger.warning(f"[CALL {call_id}] TTS configure failed: {e}")
            tts_cfg = None

        # Realtime model and session
        model = lk_openai.realtime.RealtimeModel(voice=voice or 'marin', modalities=['audio','text'])
        session = lk_agents.voice.AgentSession(llm=model, tts=tts_cfg) if tts_cfg else lk_agents.voice.AgentSession(llm=model)
        instr_text = instructions or 'Вы — голосовой ассистент VasDom. Общайтесь кратко, вежливо и по делу. Отвечайте по-русски.'
        try:
            agent = lk_agents.voice.Agent(instructions=instr_text)
        except TypeError:
            agent = lk_agents.voice.Agent()
        try:
            from livekit.agents.voice import room_io as lk_room_io
            room_in_opts = lk_room_io.RoomInputOptions(close_on_disconnect=False)
            await session.start(agent=agent, room=room, room_input_options=room_in_opts)
        except Exception:
            await session.start(agent=agent, room=room)
        _call_states[call_id]['agent'] = 'started'

        # Main loop
        import time
        start_ts = time.time()
        had_pstn = False
        greeted = False
        max_alive_sec = int(os.environ.get('AI_CALL_MAX_SECONDS', '900'))
        while time.time() - start_ts < max_alive_sec:
            try:
                rp = list(room.remote_participants.values()) if hasattr(room, 'remote_participants') else []
                logger.info(f'[CALL {call_id}] participants={len(rp)}')
                if rp:
                    if _call_states.get(call_id, {}).get('status') != 'active':
                        _call_states[call_id]['status'] = 'active'
                        logger.info(f'[CALL {call_id}] PSTN joined, set status=active')
                    had_pstn = True
                    if not greeted:
                        try:
                            await session.say('Здравствуйте, это VasDom. Слышно ли меня?')
                            greeted = True
                        except Exception as se:
                            logger.warning(f'[CALL {call_id}] greeting failed: {se}')
                else:
                    if had_pstn:
                        logger.info(f'[CALL {call_id}] PSTN left, finishing session')
                        break
                await asyncio.sleep(1)
            except Exception as loop_e:
                logger.warning(f'[CALL {call_id}] loop warn: {loop_e}')
                await asyncio.sleep(1)
        _call_states[call_id]['status'] = 'ended'
    except Exception as e:
        logger.error(f'AI agent start failed: {e}')
        _call_states[call_id]['agent_error'] = str(e)
    finally:
        try:
            if session:
                await session.aclose()
        except Exception:
            pass
        try:
            if room:
                await room.disconnect()
        except Exception:
            pass

@api_router.post('/voice/call/start', response_model=VoiceCallStartResponse)
async def voice_call_start(req: VoiceCallStartRequest):
    client = await _get_livekit_client()
    if not client:
        raise HTTPException(status_code=500, detail='LiveKit not configured')
    trunk_id = await _ensure_outbound_trunk()
    if not trunk_id:
        raise HTTPException(status_code=500, detail='SIP trunk not available')
    phone = (req.phone_number or os.environ.get('DEFAULT_CALLEE_NUMBER') or '').strip()
    if not phone:
        raise HTTPException(status_code=400, detail='phone_number required')
    call_id = str(uuid4())
    room_name = f'call-{call_id}'
    logger.info(f'[CALL {call_id}] start → room={room_name} to={phone} trunk={trunk_id}')

    # Create room
    try:
        await client.room.create_room(lk_api.CreateRoomRequest(name=room_name))
        logger.info(f'[CALL {call_id}] room created')
    except Exception as e:
        logger.warning(f'[CALL {call_id}] create room warning: {e}')

    # Create SIP participant (outbound call)
    try:
        logger.info(f"[CALL {call_id}] creating SIP participant → trunk={trunk_id}, to={phone}, room={room_name}")
        req_obj = lk_api.CreateSIPParticipantRequest(
            sip_trunk_id=trunk_id,
            sip_call_to=phone,
            room_name=room_name,
            participant_identity=f"pstn-{phone.replace('+','').replace(' ','').replace('-','')}",
            participant_name=req.caller_id or "PSTN",
        )
        part = await client.sip.create_sip_participant(req_obj)
        try:
            part_dict = {
                'sip_participant_id': getattr(part, 'sip_participant_id', None),
                'status': getattr(part, 'status', None),
                'sip_call_id': getattr(part, 'sip_call_id', None),
                'name': getattr(part, 'name', None),
            }
        except Exception:
            part_dict = {'repr': str(part)}
        sip_pid = part_dict.get('sip_participant_id')
        logger.info(f"[CALL {call_id}] SIP participant created: {sip_pid} details={part_dict}")
        _call_states[call_id] = {
            'status': 'ringing', 'room': room_name, 'sip_participant_id': sip_pid,
            'to': phone, 'created_at': datetime.now(timezone.utc).isoformat()
        }
        # Start AI agent in background
        asyncio.create_task(_start_openai_agent(call_id, room_name, req.voice or 'marin', req.instructions))
        return VoiceCallStartResponse(call_id=call_id, room_name=room_name, status='ringing', sip_participant_id=sip_pid)
    except lk_api.TwirpError as e:
        logger.error(f'[CALL {call_id}] LiveKit SIP error: {e}')
        raise HTTPException(status_code=502, detail=f'LiveKit SIP error: {e}')
    except Exception as e:
        logger.error(f'[CALL {call_id}] Create SIP participant failed: {e}')
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

# LiveKit Webhook (diagnostics)
@api_router.post('/voice/webhooks/livekit')
async def livekit_webhook(request: Request):
    try:
        payload = await request.json()
    except Exception:
        body = await request.body()
        payload = {'raw': body.decode('utf-8', errors='ignore')}
    headers = {k: v for k, v in request.headers.items()}
    logger.info(f"[LIVEKIT WEBHOOK] headers={headers} payload={payload}")
    return {'ok': True}

# ===== Realtime sessions (unchanged) =====
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

# ===== Bitrix Tasks (subset) =====
class BitrixService:
    def __init__(self):
        self.webhook_url = os.environ.get('BITRIX24_WEBHOOK_URL', '').rstrip('/')

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

    async def user_phone(self, user_id: int) -> Optional[str]:
        try:
            if not user_id:
                return None
            resp = await self._call('user.get', { 'ID': int(user_id) })
            if not resp.get('ok'):
                return None
            u = resp.get('result') or {}
            for key in ('PERSONAL_MOBILE', 'WORK_PHONE', 'PERSONAL_PHONE'):
                v = (u or {}).get(key)
                if isinstance(v, str) and v.strip():
                    return v.strip()
            return None
        except Exception:
            return None

bitrix = BitrixService()

class TaskCallAIRequest(BaseModel):
    task_id: Optional[int] = None
    title: Optional[str] = None
    description: Optional[str] = None
    responsible_id: Optional[int] = None
    phone_number: Optional[str] = None
    voice: Optional[str] = 'marin'

class TaskCallAIResponse(VoiceCallStartResponse):
    used_phone: str
    instructions: Optional[str] = None

def _normalize_phone(phone: str) -> str:
    if not phone:
        return phone
    p = ''.join(ch for ch in phone if ch.isdigit() or ch == '+')
    if p and p[0] == '8' and len(p) == 11:
        p = '+7' + p[1:]
    if p and p[0] != '+':
        p = '+' + p
    return p

@api_router.post('/tasks/call-ai', response_model=TaskCallAIResponse)
async def tasks_call_ai(req: TaskCallAIRequest):
    phone = (req.phone_number or '').strip()
    if not phone and req.responsible_id:
        phone = await bitrix.user_phone(int(req.responsible_id)) or ''
    phone = _normalize_phone(phone)
    if not phone:
        raise HTTPException(status_code=400, detail='Phone number not found for this task/responsible user')

    base_instr = (
        'Вы — голосовой ассистент VasDom. Общайтесь кратко, вежливо и по делу. '
        'Звонок сотруднику по задаче: уточните статус выполнения, сроки и следующие шаги; зафиксируйте договорённости.'
    )
    task_bits = []
    if req.title:
        task_bits.append(f"Задача: {req.title}")
    if req.description:
        task_bits.append(f"Описание: {req.description}")
    instr = base_instr + ('\n' + '\n'.join(task_bits) if task_bits else '')

    logger.info(f"[TASK CALL] task_id={req.task_id} to={phone} resp_id={req.responsible_id} voice={req.voice}")
    vc_req = VoiceCallStartRequest(phone_number=phone, caller_id=None, instructions=instr, voice=req.voice or 'marin')
    vc_resp = await voice_call_start(vc_req)
    logger.info(f"[TASK CALL] started call_id={vc_resp.call_id} room={vc_resp.room_name} status={vc_resp.status}")
    return TaskCallAIResponse(call_id=vc_resp.call_id, room_name=vc_resp.room_name, status=vc_resp.status, sip_participant_id=vc_resp.sip_participant_id, used_phone=phone, instructions=instr)

# ===== Utility: burst calls to 8888 for IP confirmation =====
class CallBurstRequest(BaseModel):
    phone_number: Optional[str] = Field(default='8888')
    count: int = Field(default=4, ge=1, le=10)
    interval_sec: int = Field(default=12, ge=5, le=60)
    voice: Optional[str] = Field(default='marin')

@api_router.post('/voice/call/burst')
async def voice_call_burst(req: CallBurstRequest):
    call_ids: List[str] = []
    for i in range(req.count):
        try:
            start_req = VoiceCallStartRequest(phone_number=req.phone_number or '8888', voice=req.voice)
            resp = await voice_call_start(start_req)
            call_ids.append(resp.call_id)
            logger.info(f"[BURST] started {i+1}/{req.count} call_id={resp.call_id} room={resp.room_name}")
        except Exception as e:
            logger.error(f"[BURST] start error idx={i}: {e}")
        await asyncio.sleep(req.interval_sec)
    return {'ok': True, 'calls': call_ids}

# Health endpoints
@api_router.get('/health')
async def health():
    return {'ok': True, 'ts': int(datetime.now(timezone.utc).timestamp())}

@api_router.get('/ready')
async def ready():
    return {'ready': True}

# Mount router
app.include_router(api_router)
logger.info('Main API router mounted')

# Try mount AI Knowledge router if present
try:
    from app.routers import ai_knowledge as _ai_kb_mod  # noqa: E402
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