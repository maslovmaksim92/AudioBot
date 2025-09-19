from fastapi import APIRouter, UploadFile, File, Form, HTTPException, Depends
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
import os, io, json, zipfile, logging
from datetime import datetime, timezone, timedelta
from uuid import uuid4

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy import text as sa_text

from openai import AsyncOpenAI
from emergentintegrations.llm.chat import LlmChat, UserMessage

import tiktoken
from PyPDF2 import PdfReader
from docx import Document as DocxDocument
from openpyxl import load_workbook

logger = logging.getLogger("ai_knowledge_router")

router = APIRouter(prefix="/api/ai-knowledge", tags=["AI Knowledge"])

# ENV / DB
RAW_DATABASE_URL = (os.environ.get('DATABASE_URL_OVERRIDE') or os.environ.get('NEON_DATABASE_URL') or os.environ.get('DATABASE_URL') or '').strip()
EMERGENT_LLM_KEY = os.environ.get('EMERGENT_LLM_KEY', '').strip()
OPENAI_API_KEY = os.environ.get('OPENAI_API_KEY', '').strip()

ALLOWED_EXT = {'.pdf', '.docx', '.txt', '.xlsx', '.zip'}
MAX_FILE_MB = int(os.environ.get('AI_MAX_FILE_MB', '50'))
MAX_TOTAL_MB = int(os.environ.get('AI_MAX_TOTAL_MB', '200'))

engine = None
AsyncSessionLocal = None

# Normalize DB URL locally to avoid asyncpg/sslmode issues
from urllib.parse import urlparse, parse_qsl, urlencode, urlunparse

def _normalize_db_url(url: str) -> str:
    try:
        if not url:
            return url
        url = url.strip().strip("'\"")
        if url.lower().startswith('psql '):
            url = url[5:].strip().strip("'\"")
        # Remove any leading garbage before scheme
        for marker in ('postgresql+asyncpg://', 'postgresql://', 'postgres://'):
            idx = url.find(marker)
            if idx > 0:
                url = url[idx:]
                break
        # ensure async driver
        if url.startswith('postgres://'):
            url = url.replace('postgres://', 'postgresql+asyncpg://', 1)
        elif url.startswith('postgresql://') and not url.startswith('postgresql+asyncpg://'):
            url = url.replace('postgresql://', 'postgresql+asyncpg://', 1)
        elif not url.startswith('postgresql+asyncpg://'):
            url = 'postgresql+asyncpg://' + url.split('://',1)[-1]
        u = urlparse(url)
        q = dict(parse_qsl(u.query, keep_blank_values=True))
        # remove/convert params
        q.pop('channel_binding', None)
        if 'sslmode' in q:
            q.pop('sslmode', None)
        if q.get('ssl') is None:
            q['ssl'] = 'true'
        new_query = urlencode(q, doseq=True)
        return urlunparse((u.scheme, u.netloc, u.path, u.params, new_query, u.fragment))
    except Exception:
        return url

DATABASE_URL = _normalize_db_url(RAW_DATABASE_URL)

from urllib.parse import urlparse, urlunparse, quote

def _build_clean_async_url(url: str) -> str:
    try:
        p = urlparse(url)
        scheme = 'postgresql+asyncpg'
        username = p.username or ''
        password = p.password or ''
        host = p.hostname or ''
        port = f":{p.port}" if p.port else ''
        auth = ''
        if username:
            u = quote(username, safe='')
            if password:
                pw = quote(password, safe='')
                auth = f"{u}:{pw}@"
            else:
                auth = f"{u}@"
        netloc = f"{auth}{host}{port}"
        path = p.path or ''
        return urlunparse((scheme, netloc, path, '', '', ''))
    except Exception:
        return url

# initialize local engine/session (separate from server.py to avoid circular imports)
if DATABASE_URL:
    try:
        clean_url = _build_clean_async_url(DATABASE_URL)
        engine = create_async_engine(clean_url, echo=False, pool_pre_ping=True, future=True, connect_args={"ssl": True})
        AsyncSessionLocal = async_sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)
    except Exception as e:
        logger.warning(f"DB init in ai_knowledge.py failed: {e}")

# Helpers
async def _split_into_chunks(text: str, target_tokens: int = 1200, overlap: int = 200) -> List[str]:
    enc = tiktoken.get_encoding('cl100k_base')
    toks = enc.encode(text)
    chunks: List[str] = []
    i = 0
    while i < len(toks):
        window = toks[i:i+target_tokens]
        chunks.append(enc.decode(window))
        i += max(1, target_tokens - overlap)
    return chunks

async def _summarize(text: str, max_chars: int = 2000) -> str:
    if not EMERGENT_LLM_KEY:
        return (text or '')[:max_chars]
    try:
        chat = LlmChat(api_key=EMERGENT_LLM_KEY, session_id=f"ai_preview_{datetime.now().strftime('%Y%m%d_%H%M%S')}", system_message="Ты помощник. Кратко опиши содержимое документа на русском, до 2000 символов, выдели ключевые темы, без выдумок.").with_model('openai','gpt-5-mini')
        prompt = f"Сделай краткое описание (до {max_chars} символов).\n\nТекст:\n{text[:8000]}\n\nОписание:"
        resp = await chat.send_message(UserMessage(text=prompt))
        s = (resp or '')
        if len(s) > max_chars:
            s = s[:max_chars-1] + '…'
        return s
    except Exception as e:
        logger.warning(f"LLM preview error: {e}")
        return (text or '')[:max_chars]

async def _detect_vector_dims(db: AsyncSession) -> int:
    """Detect current pgvector dimension of ai_chunks.embedding. Fallback to 1536."""
    try:
        # Read atttypmod from pg_attribute; vector dims stored as (atttypmod - 4)
        sql = """
        SELECT a.atttypmod
        FROM pg_attribute a
        JOIN pg_class c ON c.oid = a.attrelid
        JOIN pg_namespace n ON n.oid = c.relnamespace
        WHERE n.nspname = current_schema()
          AND c.relname = 'ai_chunks'
          AND a.attname = 'embedding'
          AND a.attnum > 0
          AND NOT a.attisdropped
        LIMIT 1
        """
        row = (await db.execute(sa_text(sql))).first()
        if row and isinstance(row[0], int) and row[0] > 4:
            dims = int(row[0]) - 4
            if dims in (1536, 3072):
                return dims
    except Exception as e:
        logger.warning(f"Vector dims detection failed: {e}")
    return 1536

async def _embed_texts_dynamic(texts: List[str], db: AsyncSession) -> List[List[float]]:
    dims = await _detect_vector_dims(db)
    model = 'text-embedding-3-small' if dims == 1536 else 'text-embedding-3-large'
    if not OPENAI_API_KEY:
        return [[0.0]*dims for _ in texts]
    client = AsyncOpenAI(api_key=OPENAI_API_KEY)
    out: List[List[float]] = []
    for t in texts:
        try:
            r = await client.embeddings.create(model=model, input=t)
            vec = r.data[0].embedding
            # if model returns unexpected dims, pad/trim to match column
            if len(vec) != dims:
                if len(vec) > dims:
                    vec = vec[:dims]
                else:
                    vec = vec + [0.0]*(dims - len(vec))
            out.append(vec)
        except Exception as e:
            logger.error(f"Embedding error: {e}")
            out.append([0.0]*dims)
    return out

# Models
class StatusResponse(BaseModel):
    status: str
    detail: Optional[str] = None

# Preview endpoint (one file per request recommended)
@router.post('/preview')
async def preview(file: UploadFile = File(...), chunk_tokens: int = Form(1200), overlap: int = Form(200)):
    if AsyncSessionLocal is None:
        raise HTTPException(status_code=500, detail='Database is not initialized')
    if not file:
        raise HTTPException(status_code=400, detail='Файл не передан')
    ext = os.path.splitext(file.filename or '')[1].lower()
    if ext not in ALLOWED_EXT:
        raise HTTPException(status_code=400, detail=f'Недопустимый формат: {ext}')

    raw = await file.read()
    size_mb = len(raw) / (1024*1024)
    if size_mb > MAX_FILE_MB:
        raise HTTPException(status_code=413, detail='Файл превышает 50MB')

    # Extract text
    text = ''
    pages = None
    try:
        if ext == '.txt':
            text = raw.decode('utf-8', errors='ignore')
        elif ext == '.pdf':
            reader = PdfReader(io.BytesIO(raw))
            pages = len(reader.pages)
            parts = []
            for p in reader.pages:
                try:
                    parts.append(p.extract_text() or '')
                except Exception:
                    continue
            text = '\n'.join(parts)
        elif ext == '.docx':
            doc = DocxDocument(io.BytesIO(raw))
            text = '\n'.join(p.text for p in doc.paragraphs)
        elif ext == '.xlsx':
            wb = load_workbook(io.BytesIO(raw), read_only=True, data_only=True)
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
            # For preview: read supported inner files and concat
            txt = []
            try:
                zf = zipfile.ZipFile(io.BytesIO(raw))
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
                        try:
                            if sub_ext == '.txt':
                                txt.append(sub_raw.decode('utf-8', errors='ignore'))
                            elif sub_ext == '.pdf':
                                sreader = PdfReader(io.BytesIO(sub_raw))
                                sparts = []
                                for sp in sreader.pages:
                                    try:
                                        sparts.append(sp.extract_text() or '')
                                    except Exception:
                                        continue
                                txt.append('\n'.join(sparts))
                            elif sub_ext == '.docx':
                                sdoc = DocxDocument(io.BytesIO(sub_raw))
                                txt.append('\n'.join(p.text for p in sdoc.paragraphs))
                            elif sub_ext == '.xlsx':
                                swb = load_workbook(io.BytesIO(sub_raw), read_only=True, data_only=True)
                                sparts = []
                                for ws in swb.worksheets:
                                    for row in ws.iter_rows(values_only=True):
                                        line = ' '.join([str(c) for c in row if c is not None])
                                        if line:
                                            sparts.append(line)
                                txt.append('\n'.join(sparts))
                        except Exception:
                            continue
            except Exception:
                pass
            text = '\n\n'.join(txt)
    except Exception:
        text = ''

    chunks = await _split_into_chunks(text or '', target_tokens=int(chunk_tokens), overlap=int(overlap))
    desc = await _summarize(text or '', max_chars=2000)

    upload_id = str(uuid4())
    async with AsyncSessionLocal() as s:
        meta = {
            'filename': file.filename,
            'summary': desc,
            'chunks': chunks,
            'chunks_count': len(chunks),
            'size_bytes': len(raw),
            'pages': pages,
            'chunk_tokens': int(chunk_tokens),
            'overlap': int(overlap),
            'status': 'ready'
        }
        await s.execute(sa_text('INSERT INTO ai_uploads_temp (upload_id, meta, expires_at) VALUES (:id, :m::jsonb, :exp)'),
                        {"id": upload_id, "m": json.dumps(meta, ensure_ascii=False), "exp": datetime.now(timezone.utc)+timedelta(hours=6)})
        await s.commit()

    return {
        'upload_id': upload_id,
        'preview': desc,
        'chunks': len(chunks),
        'stats': {
            'total_size_bytes': len(raw),
            'total_pages': pages or 0,
            'file_stats': [{'name': file.filename, 'ext': ext, 'size_bytes': len(raw), 'pages': pages, 'text_chars': len(text or '')}]
        }
    }

# Study endpoint: persist to pgvector with category
@router.post('/study')
async def study(upload_id: str = Form(...), filename: str = Form('document.txt'), category: str = Form('Клининг')):
    if AsyncSessionLocal is None:
        raise HTTPException(status_code=500, detail='Database is not initialized')
    async with AsyncSessionLocal() as db:
        row = (await db.execute(sa_text('SELECT meta FROM ai_uploads_temp WHERE upload_id=:id'), {"id": upload_id})).first()
        if not row:
            raise HTTPException(status_code=404, detail='upload_id не найден или истёк')
        raw_meta = row[0]
        meta = json.loads(raw_meta) if isinstance(raw_meta, str) else raw_meta
        chunks: List[str] = meta.get('chunks') or []
        vectors = await _embed_texts_dynamic(chunks, db)
        doc_id = str(uuid4())
        summary = meta.get('summary') or ''
        size_bytes = int(meta.get('size_bytes') or 0)
        pages = meta.get('pages')
        # Save document (store category in mime field suffix for simplicity)
        mime = f"text/plain; category={category}"
        await db.execute(sa_text('INSERT INTO ai_documents (id, filename, mime, size_bytes, summary, pages, created_at) VALUES (:i,:fn,:mime,:sz,:sm,:pg,:ca)'),
                         {"i": doc_id, "fn": filename, "mime": mime, "sz": size_bytes, "sm": summary[:500], "pg": pages, "ca": datetime.now(timezone.utc)})
        for idx, (text, v) in enumerate(zip(chunks, vectors)):
            await db.execute(sa_text('INSERT INTO ai_chunks (id, document_id, chunk_index, content, embedding) VALUES (:i,:d,:x,:c,:e)'),
                             {"i": str(uuid4()), "d": doc_id, "x": idx, "c": text, "e": v})
        # Update status and remove temp
        await db.execute(sa_text("DELETE FROM ai_uploads_temp WHERE upload_id=:id"), {"id": upload_id})
        await db.commit()
    return {"document_id": doc_id, "chunks": len(chunks), "category": category}

# Status endpoint: checks temp table presence
@router.get('/status', response_model=StatusResponse)
async def status(upload_id: str):
    if AsyncSessionLocal is None:
        raise HTTPException(status_code=500, detail='Database is not initialized')
    async with AsyncSessionLocal() as db:
        row = (await db.execute(sa_text('SELECT meta FROM ai_uploads_temp WHERE upload_id=:id'), {"id": upload_id})).first()
        if row:
            raw_meta = row[0]
            meta = json.loads(raw_meta) if isinstance(raw_meta, str) else raw_meta
            return StatusResponse(status=meta.get('status') or 'ready')
    return StatusResponse(status='done')

# ===== Utilities for DB diagnostics =====
class DbCheckResponse(BaseModel):
    connected: bool
    pgvector_available: bool
    pgvector_installed: bool
    ai_tables: List[str]
    embedding_dims: Optional[int] = None
    errors: List[str] = []

@router.get('/db-check', response_model=DbCheckResponse)
async def db_check():
    if AsyncSessionLocal is None:
        raise HTTPException(status_code=500, detail='Database is not initialized')
    errors: List[str] = []
    ai_tables: List[str] = []
    connected = False
    pgvector_available = False
    pgvector_installed = False
    dims: Optional[int] = None
    try:
        async with AsyncSessionLocal() as db:
            # Connection check
            try:
                await db.execute(sa_text('SELECT 1'))
                connected = True
            except Exception as e:
                errors.append(f'connect: {e}')
            # Available extensions
            try:
                row = (await db.execute(sa_text("SELECT default_version FROM pg_available_extensions WHERE name='vector'"))).first()
                pgvector_available = bool(row)
            except Exception as e:
                errors.append(f'available: {e}')
            # Installed extension
            try:
                row2 = (await db.execute(sa_text("SELECT extversion FROM pg_extension WHERE extname='vector'"))).first()
                pgvector_installed = bool(row2)
            except Exception as e:
                errors.append(f'installed: {e}')
            # AI tables
            try:
                rows = (await db.execute(sa_text("SELECT table_name FROM information_schema.tables WHERE table_schema='public' AND table_name LIKE 'ai_%'"))).all()
                ai_tables = [r[0] for r in rows] if rows else []
            except Exception as e:
                errors.append(f'ai_tables: {e}')
            # Embedding dims
            try:
                if 'ai_chunks' in ai_tables:
                    dims = await _detect_vector_dims(db)
            except Exception as e:
                errors.append(f'dims: {e}')
    except Exception as e:
        errors.append(f'session: {e}')
    return DbCheckResponse(
        connected=connected,
        pgvector_available=pgvector_available,
        pgvector_installed=pgvector_installed,
        ai_tables=ai_tables,
        embedding_dims=dims,
        errors=errors
    )

class DbInstallRequest(BaseModel):
    confirm: bool = False

@router.post('/db-install-vector')
async def db_install_vector(req: DbInstallRequest):
    if AsyncSessionLocal is None:
        raise HTTPException(status_code=500, detail='Database is not initialized')
    if not req.confirm:
        raise HTTPException(status_code=400, detail='confirm=false')
    async with AsyncSessionLocal() as db:
        try:
            await db.execute(sa_text('CREATE EXTENSION IF NOT EXISTS vector'))
            await db.commit()
            return {'ok': True}
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

# DSN diagnostics (sanitized)
@router.get('/db-dsn')
async def db_dsn():
    from urllib.parse import urlparse, parse_qsl
    raw = (os.environ.get('DATABASE_URL_OVERRIDE') or os.environ.get('NEON_DATABASE_URL') or os.environ.get('DATABASE_URL') or '').strip()
    norm = _normalize_db_url(raw)
    env_sslmode = os.environ.get('PGSSLMODE')
    def parse_info(u: str):
        try:
            p = urlparse(u)
            q = dict(parse_qsl(p.query, keep_blank_values=True))
            # mask user and password
            username = (p.username or '')
            if username:
                if len(username) > 3:
                    username_mask = username[:2] + '***'
                else:
                    username_mask = '***'
            else:
                username_mask = ''
            host = p.hostname or ''
            port = p.port
            dbname = (p.path or '').lstrip('/')
            return {
                'scheme': p.scheme,
                'host': host,
                'port': port,
                'database': dbname,
                'username': username_mask,
                'query': q
            }
        except Exception:
            return {'error': 'parse_failed'}
    return {
        'raw_present': bool(raw),
        'raw_contains_sslmode': ('sslmode=' in raw.lower()),
        'raw': parse_info(raw) if raw else None,
        'normalized_contains_sslmode': ('sslmode=' in norm.lower()),
        'normalized': parse_info(norm) if norm else None,
        'env_sslmode': env_sslmode
    }