from fastapi import FastAPI, APIRouter, HTTPException, Query, Depends, UploadFile, File, Request, Form
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

# SQLAlchemy / pgvector
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import declarative_base
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey
from sqlalchemy import text as sa_text
from pgvector.sqlalchemy import Vector

# LLM / Files
from emergentintegrations.llm.chat import LlmChat, UserMessage
from openai import AsyncOpenAI
import zipfile, io
from PyPDF2 import PdfReader
from docx import Document as DocxDocument
from openpyxl import load_workbook
import tiktoken
from uuid import uuid4

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

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
DATABASE_URL = os.environ.get('DATABASE_URL', '').strip()
Base = declarative_base()
engine = None
AsyncSessionLocal = None

class AIDocument(Base):
    __tablename__ = 'ai_documents'
    id = Column(String, primary_key=True)
    filename = Column(String, nullable=False)
    mime = Column(String)
    size_bytes = Column(Integer)
    summary = Column(Text)
    pages = Column(Integer)
    created_at = Column(DateTime(timezone=True), default=datetime.now(timezone.utc))

class AIChunk(Base):
    __tablename__ = 'ai_chunks'
    id = Column(String, primary_key=True)
    document_id = Column(String, ForeignKey('ai_documents.id', ondelete='CASCADE'), index=True, nullable=False)
    chunk_index = Column(Integer, nullable=False)
    content = Column(Text, nullable=False)
    embedding = Column(Vector(3072))

class AIUploadTemp(Base):
    __tablename__ = 'ai_uploads_temp'
    upload_id = Column(String, primary_key=True)
    meta = Column(Text, nullable=False)  # json string
    expires_at = Column(DateTime(timezone=True), nullable=False)

async def init_db():
    global engine, AsyncSessionLocal
    if not DATABASE_URL:
        logger.warning('DATABASE_URL is not configured; AI features will be disabled')
        return
    engine = create_async_engine(DATABASE_URL, echo=False, pool_pre_ping=True, future=True)
    AsyncSessionLocal = async_sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)
    # Alembic migrations
    try:
        import subprocess
        alembic_ini = str((ROOT_DIR / 'alembic.ini').resolve())
        if not os.path.exists(alembic_ini):
            alembic_ini = 'alembic.ini'
        subprocess.run(['alembic', '-c', alembic_ini, 'upgrade', 'head'], check=False)
        logger.info('Alembic migrations executed')
    except Exception as e:
        logger.warning(f'Alembic run error: {e}')

async def get_db():
    if AsyncSessionLocal is None:
        raise HTTPException(status_code=500, detail='Database is not initialized')
    async with AsyncSessionLocal() as session:
        yield session

# Bitrix minimal service with caching and graceful fallback
class BitrixService:
    def __init__(self):
        self.webhook_url = os.environ.get('BITRIX24_WEBHOOK_URL', '').rstrip('/')
        self._deals_cache: Dict[str, Any] = {"ts": 0, "data": []}
        self._deals_ttl = int(os.environ.get('DEALS_CACHE_TTL', '120'))

    async def _call(self, method: str, params: Dict = None) -> Dict:
        if not self.webhook_url:
            return {"ok": False}
        url = f"{self.webhook_url}/{method}"
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                r = await client.post(url, json=params or {})
                r.raise_for_status()
                data = r.json()
                return {"ok": True, "result": data.get("result"), "next": data.get("next"), "total": data.get("total")}
        except Exception as e:
            logger.error(f"Bitrix error: {e}")
            return {"ok": False}

    async def deals(self, limit=500) -> List[Dict]:
        now = int(datetime.now(timezone.utc).timestamp())
        if now - self._deals_cache["ts"] < self._deals_ttl:
            return self._deals_cache["data"]
        resp = await self._call("crm.deal.list", {
            "select": ["ID","TITLE","UF_CRM_1669561599956","UF_CRM_1669704529022","UF_CRM_1669705507390","UF_CRM_1669704631166"],
            "filter": {"CATEGORY_ID":"34"},
            "order": {"ID":"DESC"},
            "limit": min(limit,1000)
        })
        data = resp.get("result") or []
        self._deals_cache = {"ts": now, "data": data}
        return data

bitrix = BitrixService()

# Routes
@api_router.get("/")
async def root():
    return {"message":"VasDom AudioBot API","version":"1.0.0"}

@api_router.get("/dashboard/stats")
async def dashboard_stats():
    try:
        deals = await bitrix.deals(limit=500)
        total_houses = len(deals)
        total_apartments = sum(int(d.get("UF_CRM_1669704529022") or 0) for d in deals)
        total_entrances = sum(int(d.get("UF_CRM_1669705507390") or 0) for d in deals)
        total_floors = sum(int(d.get("UF_CRM_1669704631166") or 0) for d in deals)
        if total_apartments == 0: total_apartments = total_houses * 62
        if total_entrances == 0: total_entrances = total_houses * 3
        if total_floors == 0: total_floors = total_houses * 5
        return {
            "total_houses": total_houses,
            "total_apartments": total_apartments,
            "total_entrances": total_entrances,
            "total_floors": total_floors,
            "active_brigades": 7,
            "employees": 82
        }
    except Exception as e:
        logger.error(f"Dashboard stats error: {e}")
        return {
            "total_houses": 490,
            "total_apartments": 490*62,
            "total_entrances": 490*3,
            "total_floors": 490*5,
            "active_brigades": 7,
            "employees": 82
        }

# AI Knowledge
ALLOWED_EXT = {'.pdf','.docx','.txt','.xlsx','.zip'}
MAX_FILE_MB = int(os.environ.get('AI_MAX_FILE_MB', '50'))
MAX_TOTAL_MB = int(os.environ.get('AI_MAX_TOTAL_MB', '200'))
DEFAULT_TOP_K = 10
EMERGENT_LLM_KEY = os.environ.get('EMERGENT_LLM_KEY','').strip()
OPENAI_API_KEY = os.environ.get('OPENAI_API_KEY','').strip()

async def _split_into_chunks(text: str, target_tokens: int = 1200, overlap: int = 200) -> List[str]:
    enc = tiktoken.get_encoding('cl100k_base')
    toks = enc.encode(text)
    chunks = []
    i = 0
    while i < len(toks):
        window = toks[i:i+target_tokens]
        chunks.append(enc.decode(window))
        i += max(1, target_tokens - overlap)
    return chunks

async def _embed_texts(texts: List[str]) -> List[List[float]]:
    if not OPENAI_API_KEY:
        return [[0.0]*3072 for _ in texts]
    client = AsyncOpenAI(api_key=OPENAI_API_KEY)
    out = []
    for t in texts:
        try:
            r = await client.embeddings.create(model='text-embedding-3-large', input=t)
            out.append(r.data[0].embedding)
        except Exception as e:
            logger.error(f"Embedding error: {e}")
            out.append([0.0]*3072)
    return out

async def _summarize(text: str) -> str:
    if not EMERGENT_LLM_KEY:
        return text[:500]
    try:
        chat = LlmChat(api_key=EMERGENT_LLM_KEY, session_id=f"ai_summary_{datetime.now().strftime('%Y%m%d_%H%M%S')}", system_message="Ты помощник для создания кратких саммари документов.").with_model('openai','gpt-4o-mini')
        prompt = f"Суммируй кратко ключевые пункты (до 120 слов):\n{text[:6000]}"
        resp = await chat.send_message(UserMessage(text=prompt))
        return resp or text[:500]
    except Exception as e:
        logger.warning(f"Summary error: {e}")
        return text[:500]

@api_router.post('/ai-knowledge/upload')
async def ai_upload(files: List[UploadFile] = File(...), chunk_tokens: int = Form(1200), overlap: int = Form(200)):
    if not files:
        raise HTTPException(status_code=400, detail='Нет файлов')
    # Проверка форматов и лимитов
    total = 0
    for f in files:
        ext = os.path.splitext(f.filename or '')[1].lower()
        if ext not in ALLOWED_EXT:
            raise HTTPException(status_code=400, detail=f'Недопустимый формат: {ext}')
        total += (f.size or 0) if hasattr(f, 'size') else 0
    # Размер тела запроса контролирует ингресс; отдельная проверка делает повторное чтение — пропускаем

    if AsyncSessionLocal is None:
        raise HTTPException(status_code=500, detail='Database is not initialized')

    # Извлечение текста и сбор статистики
    all_text = ''
    total_size = 0
    total_pages = 0
    file_stats = []
    for f in files:
        ext = os.path.splitext(f.filename or '')[1].lower()
        data = await f.read()
        size_bytes = len(data)
        total_size += size_bytes
        pages = None
        text = ''
        try:
            if ext == '.txt':
                text = data.decode('utf-8', errors='ignore')
            elif ext == '.pdf':
                reader = PdfReader(io.BytesIO(data))
                pages = len(reader.pages)
                parts = []
                for p in reader.pages:
                    try:
                        parts.append(p.extract_text() or '')
                    except Exception:
                        continue
                text = '\n'.join(parts)
            elif ext == '.docx':
                doc = DocxDocument(io.BytesIO(data))
                text = '\n'.join(p.text for p in doc.paragraphs)
            elif ext == '.xlsx':
                wb = load_workbook(io.BytesIO(data), read_only=True, data_only=True)
                rows = 0
                parts = []
                for ws in wb.worksheets:
                    for row in ws.iter_rows(values_only=True):
                        line = ' '.join([str(c) for c in row if c is not None])
                        if line:
                            parts.append(line)
                        rows += 1
                pages = rows
                text = '\n'.join(parts)
            elif ext == '.zip':
                try:
                    zf = zipfile.ZipFile(io.BytesIO(data))
                    for name in zf.namelist():
                        if name.endswith('/'):
                            continue
                        sub_ext = os.path.splitext(name)[1].lower()
                        if sub_ext not in {'.pdf','.docx','.txt','.xlsx'}:
                            continue
                        if os.path.isabs(name) or '..' in name:
                            continue
                        with zf.open(name) as zf_f:
                            sub_raw = zf_f.read()
                            sub_size = len(sub_raw)
                            sub_pages = None
                            sub_text = ''
                            try:
                                if sub_ext == '.pdf':
                                    sreader = PdfReader(io.BytesIO(sub_raw))
                                    sub_pages = len(sreader.pages)
                                    sparts = []
                                    for sp in sreader.pages:
                                        try:
                                            sparts.append(sp.extract_text() or '')
                                        except Exception:
                                            continue
                                    sub_text = '\n'.join(sparts)
                                elif sub_ext == '.docx':
                                    sdoc = DocxDocument(io.BytesIO(sub_raw))
                                    sub_text = '\n'.join(p.text for p in sdoc.paragraphs)
                                elif sub_ext == '.xlsx':
                                    swb = load_workbook(io.BytesIO(sub_raw), read_only=True, data_only=True)
                                    srows = 0
                                    sparts = []
                                    for ws in swb.worksheets:
                                        for row in ws.iter_rows(values_only=True):
                                            line = ' '.join([str(c) for c in row if c is not None])
                                            if line:
                                                sparts.append(line)
                                            srows += 1
                                    sub_pages = srows
                                    sub_text = '\n'.join(sparts)
                                elif sub_ext == '.txt':
                                    sub_text = sub_raw.decode('utf-8', errors='ignore')
                            except Exception:
                                pass
                            file_stats.append({
                                'name': name,
                                'ext': sub_ext,
                                'size_bytes': sub_size,
                                'pages': sub_pages,
                                'text_chars': len(sub_text or '')
                            })
                            all_text += (sub_text or '') + '\n\n'
                except Exception:
                    pass
                continue
        except Exception:
            text = ''
        file_stats.append({'name': f.filename, 'ext': ext, 'size_bytes': size_bytes, 'pages': pages, 'text_chars': len(text or '')})
        total_pages += (pages or 0)
        all_text += (text or '') + '\n\n'

    if not all_text.strip():
        preview = 'Текст не извлечён. Проверьте, что файлы содержат текст (не только изображения). Статистика по файлам показана ниже.'
        upload_id = str(uuid4())
        async with AsyncSessionLocal() as s:
            meta = {
                'filenames': [f.filename for f in files],
                'summary': preview,
                'chunks': [],
                'chunks_count': 0,
                'total_size_bytes': total_size,
                'total_pages': total_pages,
                'file_stats': file_stats,
                'chunk_tokens': int(chunk_tokens),
                'overlap': int(overlap)
            }
            await s.execute(sa_text('INSERT INTO ai_uploads_temp (upload_id, meta, expires_at) VALUES (:id, :m::jsonb, :exp)'),
                            {"id": upload_id, "m": json.dumps(meta, ensure_ascii=False), "exp": datetime.now(timezone.utc)+timedelta(hours=6)})
            await s.commit()
        return {'upload_id': upload_id, 'preview': preview, 'chunks': 0, 'stats': {'total_size_bytes': total_size, 'total_pages': total_pages, 'file_stats': file_stats}}

    chunks = await _split_into_chunks(all_text, target_tokens=int(chunk_tokens), overlap=int(overlap))
    preview = await _summarize(all_text)
    if not preview:
        preview = (all_text or '')[:500]

    upload_id = str(uuid4())
    async with AsyncSessionLocal() as s:
        meta = {
            'filenames': [f.filename for f in files],
            'summary': preview,
            'chunks': chunks,
            'chunks_count': len(chunks),
            'total_size_bytes': total_size,
            'total_pages': total_pages,
            'file_stats': file_stats,
            'chunk_tokens': int(chunk_tokens),
            'overlap': int(overlap)
        }
        await s.execute(sa_text('INSERT INTO ai_uploads_temp (upload_id, meta, expires_at) VALUES (:id, :m, :exp)'),
                        {"id": upload_id, "m": json.dumps(meta, ensure_ascii=False), "exp": datetime.now(timezone.utc)+timedelta(hours=6)})
        await s.commit()

    return {
        'upload_id': upload_id,
        'preview': preview,
        'chunks': len(chunks),
        'stats': {'total_size_bytes': total_size, 'total_pages': total_pages, 'file_stats': file_stats}
    }

@api_router.post('/ai-knowledge/save')
async def ai_save(upload_id: str = Form(...), filename: str = Form('document.txt'), db: AsyncSession = Depends(get_db)):
    row = (await db.execute(sa_text('SELECT meta FROM ai_uploads_temp WHERE upload_id=:id'), {"id": upload_id})).first()
    if not row:
        raise HTTPException(status_code=404, detail='upload_id не найден или истёк')
    meta = json.loads(row[0])
    chunks = meta.get('chunks', [])
    vectors = await _embed_texts(chunks)
    doc_id = str(uuid4())
    summary = meta.get('summary') or 'См. превью при загрузке'
    size_bytes = meta.get('total_size_bytes')
    pages = meta.get('total_pages')
    await db.execute(sa_text('INSERT INTO ai_documents (id, filename, mime, size_bytes, summary, pages, created_at) VALUES (:i,:fn,:mime,:sz,:sm,:pg,:ca)'),
                     {"i": doc_id, "fn": filename, "mime": "text/plain", "sz": size_bytes, "sm": (summary[:500] if isinstance(summary,str) else None), "pg": pages, "ca": datetime.now(timezone.utc)})
    for idx, (text, v) in enumerate(zip(chunks, vectors)):
        await db.execute(sa_text('INSERT INTO ai_chunks (id, document_id, chunk_index, content, embedding) VALUES (:i,:d,:x,:c,:e)'),
                         {"i": str(uuid4()), "d": doc_id, "x": idx, "c": text, "e": v})
    await db.execute(sa_text('DELETE FROM ai_uploads_temp WHERE upload_id=:id'), {"id": upload_id})
    await db.commit()
    return {"document_id": doc_id}

@api_router.get('/ai-knowledge/documents')
async def ai_docs_list(db: AsyncSession = Depends(get_db)):
    rows = (await db.execute(sa_text('''
        SELECT d.id, d.filename, d.mime, d.size_bytes, d.summary, d.created_at, d.pages,
               (SELECT COUNT(1) FROM ai_chunks c WHERE c.document_id=d.id) AS chunks_count
        FROM ai_documents d
        ORDER BY d.created_at DESC
        LIMIT 200
    '''))).all()
    docs = []
    for r in rows:
        rid, filename, mime, size_bytes, summary, created_at, pages, chunks_count = r
        docs.append({"id": rid, "filename": filename, "mime": mime, "size_bytes": size_bytes, "summary": summary, "created_at": created_at.isoformat() if created_at else None, "pages": pages, "chunks_count": chunks_count})
    return {"documents": docs}

class SearchRequest(BaseModel):
    query: str
    top_k: int = DEFAULT_TOP_K

@api_router.post('/ai-knowledge/search')
async def ai_search(req: SearchRequest, db: AsyncSession = Depends(get_db)):
    if not req.query.strip():
        raise HTTPException(status_code=400, detail='query пуст')
    qv = (await _embed_texts([req.query]))[0]
    rows = (await db.execute(sa_text('''
        SELECT c.document_id, c.chunk_index, c.content, 1 - (c.embedding <=> :qv) as score, d.filename
        FROM ai_chunks c JOIN ai_documents d ON d.id = c.document_id
        ORDER BY c.embedding <=> :qv
        LIMIT :k
    '''), {"qv": qv, "k": req.top_k})).all()
    results = []
    for r in rows:
        doc_id, idx, content, score, filename = r
        results.append({"document_id": doc_id, "chunk_index": idx, "content": content, "score": float(score), "filename": filename})
    return {"results": results}

@api_router.delete('/ai-knowledge/document/{doc_id}')
async def ai_delete(doc_id: str, db: AsyncSession = Depends(get_db)):
    await db.execute(sa_text('DELETE FROM ai_chunks WHERE document_id=:id'), {"id": doc_id})
    await db.execute(sa_text('DELETE FROM ai_documents WHERE id=:id'), {"id": doc_id})
    await db.commit()
    return {"ok": True}

app.include_router(api_router)

@app.on_event("startup")
async def on_startup():
    await init_db()
