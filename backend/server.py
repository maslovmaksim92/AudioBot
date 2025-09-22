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

# pgvector typedef (declared in Alembic), not used in ORM here
# from pgvector.sqlalchemy import Vector
# Обновлено: под text-embedding-3-small используется размерность 1536 (см. Alembic 0003)

# LLM / Files
from emergentintegrations.llm.chat import LlmChat, UserMessage
from openai import AsyncOpenAI
from PyPDF2 import PdfReader
from docx import Document as DocxDocument
from openpyxl import load_workbook
import tiktoken
from uuid import uuid4

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# Scrub invalid PGSSLMODE values that break asyncpg
allowed_pgssl = {'disable','allow','prefer','require','verify-ca','verify-full'}
pgssl = os.environ.get('PGSSLMODE')
if pgssl and pgssl.strip().lower() not in allowed_pgssl:
    # set to require rather than invalid values like 'true'
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

# DB
from urllib.parse import urlparse, parse_qsl, urlencode, urlunparse

def _normalize_db_url(url: str, for_async: bool = True) -> str:
    try:
        if not url:
            return url
        url = url.strip().strip("'\"")
        if url.lower().startswith('psql '):
            # remove accidental 'psql ' prefix pasted from docs
            url = url[5:].strip().strip("'\"")
        # Remove any leading garbage before scheme
        for marker in ('postgresql+asyncpg://', 'postgresql://', 'postgres://'):
            idx = url.find(marker)
            if idx > 0:
                url = url[idx:]
                break
        # Ensure correct scheme explicitly
        if for_async:
            if url.startswith('postgres://'):
                url = url.replace('postgres://', 'postgresql+asyncpg://', 1)
            elif url.startswith('postgresql://') and not url.startswith('postgresql+asyncpg://'):
                url = url.replace('postgresql://', 'postgresql+asyncpg://', 1)
            elif not url.startswith('postgresql+asyncpg://'):
                # force scheme if broken
                url = 'postgresql+asyncpg://' + url.split('://',1)[-1]
        else:
            if url.startswith('postgres://'):
                url = url.replace('postgres://', 'postgresql://', 1)
        # Normalize query params: ensure asyncpg-friendly SSL
        parsed = urlparse(url)
        q = dict(parse_qsl(parsed.query, keep_blank_values=True))
        # Remove sslmode (asyncpg doesn't accept it as kwarg)
        if 'sslmode' in q:
            q.pop('sslmode', None)
        # Force SSL for Neon/Render
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
    # asyncpg ignores sslmode kwarg; it accepts ssl=True via connect args
    connect_args = {}
    connect_args['ssl'] = True
    engine = create_async_engine(DATABASE_URL, future=True, echo=False, connect_args=connect_args)
    async_session = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)

async def get_db() -> AsyncSession:
    if not async_session:
        raise HTTPException(status_code=500, detail='Database is not initialized')
    async with async_session() as session:
        yield session

# ===== Meetings (Summarize + Send to Telegram) =====
class MeetingSummarizeRequest(BaseModel):
    transcript: Optional[List[str]] = None
    text: Optional[str] = None
    locale: Optional[str] = 'ru'

@api_router.post('/meetings/summarize')
async def meetings_summarize(req: MeetingSummarizeRequest):
    raw = ''
    if req and req.text and req.text.strip():
        raw = req.text.strip()
    elif req and req.transcript:
        raw = '\n'.join([s for s in req.transcript if isinstance(s, str)])
    raw = (raw or '').strip()
    if not raw:
        return { 'summary': '' }
    EMERGENT_LLM_KEY = os.environ.get('EMERGENT_LLM_KEY')
    if not EMERGENT_LLM_KEY:
        # fallback: first 800 chars
        return { 'summary': raw[:800] }
    system = (
        'Ты помощник VasDom. Составь краткий протокол планёрки на русском языком: '
        '1) Итоги и ключевые решения. 2) Список задач (кто/что/срок). 3) Риски/блокеры. 4) Следующие шаги. '
        'Будь кратким и структурированным, используй маркированные списки. Не выдумывай.'
    )
    try:
        chat = LlmChat(api_key=EMERGENT_LLM_KEY, session_id=f'meeting_{datetime.now().strftime("%Y%m%d_%H%M%S")}', system_message=system).with_model('openai','gpt-4o-mini')
        prompt = f"Транскрипт встречи:\n{raw[:8000]}\n\nСформируй протокол:"
        resp = await chat.send_message(UserMessage(text=prompt))
        return { 'summary': resp or '' }
    except Exception as e:
        logger.warning(f'meeting summarize error: {e}')
        return { 'summary': raw[:800] }

# High-quality Speech-to-Text (OpenAI)
from tempfile import NamedTemporaryFile

@api_router.post('/meetings/stt')
async def meetings_stt(file: UploadFile = File(...), language: Optional[str] = 'ru', model: Optional[str] = 'gpt-4o-mini-transcribe'):
    if not file:
        raise HTTPException(status_code=400, detail='file is required')
    if not os.environ.get('OPENAI_API_KEY'):
        raise HTTPException(status_code=500, detail='OPENAI_API_KEY is not configured')
    # Validate content type (best-effort)
    allowed_types = {'audio/webm','audio/webm;codecs=opus','audio/ogg','audio/ogg;codecs=opus','audio/m4a','audio/mp4','audio/mpeg','audio/mp3','audio/wav'}
    ctype = (file.content_type or '').lower()
    if ctype and (ctype not in allowed_types):
        # allow anyway, STT might still handle
        logger.info(f"STT: non-standard content type {ctype}, proceeding")
    try:
        # Persist to temp file for OpenAI client
        with NamedTemporaryFile(delete=False, suffix=os.path.splitext(file.filename or '')[1] or '.webm') as tmp:
            raw = await file.read()
            tmp.write(raw)
            tmp_path = tmp.name
        client = AsyncOpenAI(api_key=os.environ.get('OPENAI_API_KEY'))
        params: Dict[str, Any] = {'model': model, 'file': open(tmp_path, 'rb')}
        if language and language != 'auto':
            params['language'] = language
        text = ''
        try:
            resp = await client.audio.transcriptions.create(**params)
            text = getattr(resp, 'text', None) or (resp.get('text') if isinstance(resp, dict) else '')
        except Exception as e1:
            logger.warning(f"STT primary model failed ({model}), trying fallback whisper-1: {e1}")
            try:
                params_fallback = dict(params)
                params_fallback['model'] = 'whisper-1'
                if language and language != 'auto':
                    params_fallback['language'] = language
                resp2 = await client.audio.transcriptions.create(**params_fallback)
                text = getattr(resp2, 'text', None) or (resp2.get('text') if isinstance(resp2, dict) else '')
            except Exception as e2:
                logger.error(f"STT fallback whisper-1 failed: {e2}")
                raise
        finally:
            try:
                params.get('file') and params['file'].close()
            except Exception:
                pass
            try:
                os.unlink(tmp_path)
            except Exception:
                pass
        return { 'ok': True, 'text': text or '' }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f'STT error: {e}')
        # Более информативный ответ, чтобы проще диагностировать
        raise HTTPException(status_code=500, detail=f'STT failed: {str(e)[:200]}')

# ===== Meetings: Send to Telegram =====
class MeetingSendRequest(BaseModel):
    text: str
    chat_id: Optional[str] = None
    doc_id: Optional[str] = None  # id документа в БЗ (для фидбека)
    with_feedback: Optional[bool] = False

TELEGRAM_BOT_TOKEN = os.environ.get('TELEGRAM_BOT_TOKEN')

async def _tg_send(method: str, payload: Dict[str, Any]):
    if not TELEGRAM_BOT_TOKEN:
        raise HTTPException(status_code=400, detail='telegram not configured')
    async with httpx.AsyncClient(timeout=20) as cli:
        resp = await cli.post(f'https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/{method}', json=payload)
        if resp.status_code != 200:
            logger.warning(f"telegram error {resp.status_code}: {resp.text}")

@api_router.post('/meetings/send')
async def meetings_send(req: MeetingSendRequest):
    if not req or not (req.text or '').strip():
        raise HTTPException(status_code=400, detail='text is required')
    chat_id = (req.chat_id or os.environ.get('TELEGRAM_TARGET_CHAT_ID') or '').strip()
    if not TELEGRAM_BOT_TOKEN or not chat_id:
        raise HTTPException(status_code=400, detail='telegram not configured')
    # Telegram limit: 4096 chars per message
    text = req.text.strip()
    chunks = []
    while text:
        chunks.append(text[:4000])
        text = text[4000:]
    for i, part in enumerate(chunks):
        payload = { 'chat_id': chat_id, 'text': part }
        if i == 0 and req.with_feedback and req.doc_id:
            payload['reply_markup'] = {
                'inline_keyboard': [[
                    { 'text': '👍', 'callback_data': f'mp:like:{req.doc_id}' },
                    { 'text': '👎', 'callback_data': f'mp:dislike:{req.doc_id}' }
                ]]
            }
        await _tg_send('sendMessage', payload)
    return { 'ok': True, 'parts': len(chunks) }

# ===== Meetings: Save to Knowledge Base & Recent =====
class MeetingTaskItem(BaseModel):
    title: str
    owner: Optional[str] = None
    due: Optional[str] = None
    status: Optional[str] = None

class MeetingProtocolForm(BaseModel):
    title: Optional[str] = None
    datetime: Optional[str] = None
    participants: Optional[str] = None
    goal: Optional[str] = None
    agenda: Optional[List[str]] = None
    decisions: Optional[str] = None
    tasks: Optional[List[MeetingTaskItem]] = None
    risks: Optional[str] = None
    next_steps: Optional[str] = None
    bitrix_link: Optional[str] = None

class SaveToKbRequest(BaseModel):
    protocol_text: Optional[str] = None
    form: Optional[MeetingProtocolForm] = None
    filename: Optional[str] = None

# remember proxy
_RemReq = None
_rag_remember = None
try:
    from app.routers.ai_knowledge import RememberRequest as _RemReq, remember as _rag_remember
except Exception:
    pass

def _compose_protocol_text(form: MeetingProtocolForm) -> str:
    parts: List[str] = []
    if form.title:
        parts.append(f"Заголовок: {form.title}")
    if form.datetime:
        parts.append(f"Дата/время: {form.datetime}")
    if form.participants:
        parts.append(f"Участники: {form.participants}")
    if form.goal:
        parts.append(f"Цель: {form.goal}")
    if form.agenda:
        parts.append("Повестка:")
        for i, item in enumerate(form.agenda, start=1):
            if item:
                parts.append(f"  {i}. {item}")
    if form.decisions:
        parts.append("Принятые решения:")
        parts.append(form.decisions)
    if form.tasks:
        parts.append("Поручения:")
        for t in form.tasks:
            line = f"- {t.title}"
            if t.owner:
                line += f" — ответственный: {t.owner}"
            if t.due:
                line += f", срок: {t.due}"
            if t.status:
                line += f", статус: {t.status}"
            parts.append(line)
    if form.risks:
        parts.append("Риски/блокеры:")
        parts.append(form.risks)
    if form.next_steps:
        parts.append("Следующие шаги:")
        parts.append(form.next_steps)
    if form.bitrix_link:
        parts.append(f"Ссылка Bitrix: {form.bitrix_link}")
    return "\n".join(parts)

@api_router.post('/meetings/save-to-kb')
async def meetings_save_to_kb(req: SaveToKbRequest):
    text = (req.protocol_text or '').strip()
    if not text and req.form:
        text = _compose_protocol_text(req.form)
    text = (text or '').strip()
    if not text:
        raise HTTPException(status_code=400, detail='protocol_text or form required')
    filename = (req.filename or (req.form and req.form.title) or f"meeting_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M')}.txt").strip()
    if _RemReq and _rag_remember:
        try:
            res = await _rag_remember(_RemReq(text=text, category='meetings', filename=filename))
            return { 'ok': True, 'document_id': res.get('document_id') }
        except Exception as e:
            logger.error(f'meetings_save_to_kb remember error: {e}')
            raise HTTPException(status_code=500, detail='Database write error')
    raise HTTPException(status_code=500, detail='Knowledge Base unavailable')

class RecentProtocolsResponse(BaseModel):
    protocols: List[Dict[str, Any]]

@api_router.get('/meetings/protocols/recent', response_model=RecentProtocolsResponse)
async def meetings_recent(limit: int = Query(50), db: AsyncSession = Depends(get_db)):
    sql_with_fb = '''
        SELECT d.id, d.filename, d.mime, d.size_bytes, d.summary, d.created_at, d.pages,
               (SELECT COUNT(1) FROM ai_chunks c WHERE c.document_id=d.id) AS chunks_count,
               (SELECT COUNT(1) FROM ai_feedback f WHERE f.message_id=d.id AND COALESCE(f.rating,0) > 0) AS likes,
               (SELECT COUNT(1) FROM ai_feedback f WHERE f.message_id=d.id AND COALESCE(f.rating,0) <= 0) AS dislikes
        FROM ai_documents d
        WHERE d.mime ILIKE '%category=meetings%'
        ORDER BY d.created_at DESC
        LIMIT :lim
    '''
    sql_no_fb = '''
        SELECT d.id, d.filename, d.mime, d.size_bytes, d.summary, d.created_at, d.pages,
               (SELECT COUNT(1) FROM ai_chunks c WHERE c.document_id=d.id) AS chunks_count
        FROM ai_documents d
        WHERE d.mime ILIKE '%category=meetings%'
        ORDER BY d.created_at DESC
        LIMIT :lim
    '''
    try:
        rows = (await db.execute(sa_text(sql_with_fb), { 'lim': int(limit) })).all()
        out: List[Dict[str, Any]] = []
        for r in rows:
            id_, filename, mime, size_bytes, summary, created_at, pages, chunks_count, likes, dislikes = r
            out.append({
                'id': id_, 'filename': filename, 'mime': mime, 'size_bytes': size_bytes,
                'summary': summary, 'created_at': created_at.isoformat() if created_at else None,
                'pages': pages, 'chunks_count': int(chunks_count or 0),
                'likes': int(likes or 0), 'dislikes': int(dislikes or 0)
            })
        return { 'protocols': out }
    except Exception as e:
        # Fallback when ai_feedback table not exists yet
        try:
            await db.rollback()
            rows = (await db.execute(sa_text(sql_no_fb), { 'lim': int(limit) })).all()
            out: List[Dict[str, Any]] = []
            for r in rows:
                id_, filename, mime, size_bytes, summary, created_at, pages, chunks_count = r
                out.append({
                    'id': id_, 'filename': filename, 'mime': mime, 'size_bytes': size_bytes,
                    'summary': summary, 'created_at': created_at.isoformat() if created_at else None,
                    'pages': pages, 'chunks_count': int(chunks_count or 0),
                    'likes': 0, 'dislikes': 0
                })
            return { 'protocols': out }
        except Exception as e2:
            logger.error(f'meetings_recent error: {e}; fallback failed: {e2}')
            return { 'protocols': [] }

# ====== OpenAI Realtime: Ephemeral session endpoint ======
class RealtimeSessionRequest(BaseModel):
    voice: Optional[str] = Field(default='marin')
    instructions: Optional[str] = Field(default='You are a helpful assistant.')
    temperature: Optional[float] = Field(default=0.8)
    max_response_output_tokens: Optional[int] = Field(default=4096)

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
        'instructions': (req.instructions or 'You are a helpful assistant.'),
        'temperature': req.temperature or 0.8,
        'max_response_output_tokens': req.max_response_output_tokens or 4096,
        'turn_detection': {
            'type': 'server_vad',
            'threshold': 0.5,
            'prefix_padding_ms': 300,
            'silence_duration_ms': 500,
            'create_response': True
        },
        'input_audio_format': 'pcm16',
        'output_audio_format': 'pcm16',
        'input_audio_transcription': { 'model': 'whisper-1' }
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

# Mount API router
app.include_router(api_router)

# Startup hook (db etc)
async def init_db():
    if engine:
        async with engine.begin() as conn:
            await conn.run_sync(lambda conn: None)

@app.on_event("startup")
async def on_startup():
    await init_db()