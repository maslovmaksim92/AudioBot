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
from emergentintegrations.llm.chat import LlmChat, UserMessage
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

# ====== OpenAI Realtime: Ephemeral session endpoint (omitted here) ======
# ... existing endpoint here ...

# ===== Bitrix Tasks (no Mongo) =====
from backend.app_main import bitrix, _build_cleaning_dates, _compute_periodicity

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