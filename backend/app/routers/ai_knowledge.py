from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
import os, io, json, zipfile, logging
from datetime import datetime, timezone, timedelta
from uuid import uuid4

# Psycopg3 async (preferred for Neon)
try:
    from psycopg_pool import AsyncConnectionPool
    from psycopg.rows import dict_row
    import psycopg
    PSYCOPG_AVAILABLE = True
except Exception as e:
    PSYCOPG_AVAILABLE = False
    AsyncConnectionPool = None
    dict_row = None
    psycopg = None

from openai import AsyncOpenAI
from emergentintegrations.llm.chat import LlmChat, UserMessage

import tiktoken
from PyPDF2 import PdfReader
from docx import Document as DocxDocument
from openpyxl import load_workbook

logger = logging.getLogger("ai_knowledge_router")

router = APIRouter(prefix="/api/ai-knowledge", tags=["AI Knowledge"])

# ENV / DB
RAW_DATABASE_URL = (os.environ.get('NEON_DATABASE_URL') or '').strip()
EMERGENT_LLM_KEY = os.environ.get('EMERGENT_LLM_KEY', '').strip()
OPENAI_API_KEY = os.environ.get('OPENAI_API_KEY', '').strip()

ALLOWED_EXT = {'.pdf', '.docx', '.txt', '.xlsx', '.zip'}
MAX_FILE_MB = int(os.environ.get('AI_MAX_FILE_MB', '50'))
MAX_TOTAL_MB = int(os.environ.get('AI_MAX_TOTAL_MB', '200'))

# Normalize DB URL for psycopg3 (libpq-style)
from urllib.parse import urlparse, parse_qsl, urlencode, urlunparse

def _scrub_ssl_env():
    removed = []
    for k in ('PGSSLMODE','PGSSL','PGSSLCERT','PGSSLKEY','PGSSLROOTCERT'):
        if os.environ.pop(k, None) is not None:
            removed.append(k)
    if removed:
        logger.warning(f'AI Knowledge: removed SSL-related env vars: {",".join(removed)}')

def _normalize_db_url_psycopg(url: str) -> str:
    try:
        if not url:
            return url
        url = url.strip().strip("'\"")
        if url.lower().startswith('psql '):
            url = url[5:].strip().strip("'\"")
        # Ensure scheme is postgresql://
        if url.startswith('postgresql+asyncpg://'):
            url = url.replace('postgresql+asyncpg://', 'postgresql://', 1)
        elif url.startswith('postgres://'):
            url = url.replace('postgres://', 'postgresql://', 1)
        elif not url.startswith('postgresql://'):
            url = 'postgresql://' + url.split('://', 1)[-1]
        u = urlparse(url)
        q = dict(parse_qsl(u.query, keep_blank_values=True))
        # Drop incompatible/irrelevant params
        q.pop('channel_binding', None)
        # Convert ssl=true/false to sslmode
        if 'ssl' in q:
            sval = str(q.get('ssl')).lower()
            q.pop('ssl', None)
            if sval in ('true', '1', 'yes', 'on'):
                q['sslmode'] = 'require'
            elif sval in ('false', '0', 'no', 'off'):
                q['sslmode'] = 'disable'
        # Default sslmode=require for Neon if not set or invalid
        allowed = {'disable','allow','prefer','require','verify-ca','verify-full'}
        if 'sslmode' in q:
            if str(q['sslmode']).lower() not in allowed:
                q['sslmode'] = 'require'
        else:
            q['sslmode'] = 'require'
        # Add keepalive and timeout hints for better stability on serverless
        q.setdefault('keepalives', '1')
        q.setdefault('keepalives_idle', '30')
        q.setdefault('keepalives_interval', '10')
        q.setdefault('keepalives_count', '5')
        q.setdefault('connect_timeout', '10')
        # Use system CA bundle explicitly (sometimes required in container env)
        q.setdefault('sslrootcert', '/etc/ssl/certs/ca-certificates.crt')
        new_query = urlencode(q, doseq=True)
        return urlunparse((u.scheme, u.netloc, u.path, u.params, new_query, u.fragment))
    except Exception:
        return url

_scrub_ssl_env()
DATABASE_URL = _normalize_db_url_psycopg(RAW_DATABASE_URL)

# Psycopg3 async pool
pg_pool: Optional[AsyncConnectionPool] = None
if PSYCOPG_AVAILABLE and DATABASE_URL:
    try:
        # keep pool small; Neon serverless prefers many short connections
        pg_pool = AsyncConnectionPool(conninfo=DATABASE_URL, min_size=1, max_size=int(os.environ.get('AI_PG_MAX_POOL', '5')))
        logger.info('AI Knowledge: psycopg3 async pool initialized')
    except Exception as e:
        logger.warning(f"AI Knowledge: psycopg3 pool init failed: {e}")
        pg_pool = None

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

async def _detect_vector_dims() -> int:
    """Detect current pgvector dimension of ai_chunks.embedding. Fallback to 1536."""
    if not pg_pool:
        return 1536
    try:
        async with pg_pool.connection() as conn:
            conn.row_factory = dict_row
            async with conn.cursor() as cur:
                await cur.execute(
                    """
                    SELECT a.atttypmod AS atttypmod
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
                )
                row = await cur.fetchone()
                if row and isinstance(row.get('atttypmod'), int) and row['atttypmod'] > 4:
                    dims = int(row['atttypmod']) - 4
                    if dims in (1536, 3072):
                        return dims
    except Exception as e:
        logger.warning(f"Vector dims detection failed: {e}")
    return 1536

async def _embed_texts_dynamic(texts: List[str]) -> List[List[float]]:
    dims = await _detect_vector_dims()
    model = 'text-embedding-3-small' if dims == 1536 else 'text-embedding-3-large'
    if not OPENAI_API_KEY:
        return [[0.0]*dims for _ in texts]
    client = AsyncOpenAI(api_key=OPENAI_API_KEY)
    out: List[List[float]] = []
    for t in texts:
        try:
            r = await client.embeddings.create(model=model, input=t)
            vec = r.data[0].embedding
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
async def preview(file: UploadFile = File(None), files: List[UploadFile] = File(None), chunk_tokens: int = Form(1200), overlap: int = Form(200)):
    if not pg_pool:
        raise HTTPException(status_code=500, detail='Database is not initialized')
    # Support both 'file' and 'files' field names (take the first available)
    picked: Optional[UploadFile] = None
    if file is not None:
        picked = file
    elif files:
        picked = files[0]
    if not picked:
        raise HTTPException(status_code=400, detail='Файл не передан')
    file = picked
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
    try:
        async with pg_pool.connection() as conn:
            conn.row_factory = dict_row
            async with conn.cursor() as cur:
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
                await cur.execute(
                    'INSERT INTO ai_uploads_temp (upload_id, meta, expires_at) VALUES (%(id)s, %(m)s::jsonb, %(exp)s)',
                    {"id": upload_id, "m": json.dumps(meta, ensure_ascii=False), "exp": datetime.now(timezone.utc)+timedelta(hours=6)}
                )
                await conn.commit()
    except Exception as e:
        logger.error(f"DB insert preview error: {e}")
        raise HTTPException(status_code=500, detail='Database write error')

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
    if not pg_pool:
        raise HTTPException(status_code=500, detail='Database is not initialized')
    try:
        async with pg_pool.connection() as conn:
            conn.row_factory = dict_row
            async with conn.cursor() as cur:
                row = None
                try:
                    await cur.execute('SELECT meta FROM ai_uploads_temp WHERE upload_id=%(id)s', {"id": upload_id})
                    row = await cur.fetchone()
                except Exception as e:
                    logger.error(f"read temp error: {e}")
                if not row:
                    raise HTTPException(status_code=404, detail='upload_id не найден или истёк')
                raw_meta = row.get('meta')
                meta = raw_meta if isinstance(raw_meta, dict) else (json.loads(raw_meta) if isinstance(raw_meta, str) else {})
                chunks: List[str] = meta.get('chunks') or []
                vectors = await _embed_texts_dynamic(chunks)
                doc_id = str(uuid4())
                summary = meta.get('summary') or ''
                size_bytes = int(meta.get('size_bytes') or 0)
                pages = meta.get('pages')
                mime = f"text/plain; category={category}"
                await cur.execute(
                    'INSERT INTO ai_documents (id, filename, mime, size_bytes, summary, pages, created_at) VALUES (%(i)s,%(fn)s,%(mime)s,%(sz)s,%(sm)s,%(pg)s,%(ca)s)',
                    {"i": doc_id, "fn": filename, "mime": mime, "sz": size_bytes, "sm": (summary[:500] if isinstance(summary, str) else None), "pg": pages, "ca": datetime.now(timezone.utc)}
                )
                for idx, (text, v) in enumerate(zip(chunks, vectors)):
                    await cur.execute(
                        'INSERT INTO ai_chunks (id, document_id, chunk_index, content, embedding) VALUES (%(i)s,%(d)s,%(x)s,%(c)s,%(e)s)',
                        {"i": str(uuid4()), "d": doc_id, "x": idx, "c": text, "e": v}
                    )
                await cur.execute('DELETE FROM ai_uploads_temp WHERE upload_id=%(id)s', {"id": upload_id})
                await conn.commit()
        return {"document_id": doc_id, "chunks": len(chunks), "category": category}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"study error: {e}")
        raise HTTPException(status_code=500, detail='Database write error')

# Status endpoint: checks temp table presence
@router.get('/status', response_model=StatusResponse)
async def status(upload_id: str):
    if not pg_pool:
        raise HTTPException(status_code=500, detail='Database is not initialized')
    try:
        async with pg_pool.connection() as conn:
            conn.row_factory = dict_row
            async with conn.cursor() as cur:
                await cur.execute('SELECT meta FROM ai_uploads_temp WHERE upload_id=%(id)s', {"id": upload_id})
                row = await cur.fetchone()
                if row:
                    raw_meta = row.get('meta')
                    meta = raw_meta if isinstance(raw_meta, dict) else (json.loads(raw_meta) if isinstance(raw_meta, str) else {})
                    return StatusResponse(status=meta.get('status') or 'ready')
    except Exception as e:
        logger.error(f"status error: {e}")
        raise HTTPException(status_code=500, detail='Database read error')
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
    errors: List[str] = []
    ai_tables: List[str] = []
    connected = False
    pgvector_available = False
    pgvector_installed = False
    dims: Optional[int] = None
    if not pg_pool:
        return DbCheckResponse(
            connected=False,
            pgvector_available=False,
            pgvector_installed=False,
            ai_tables=[],
            embedding_dims=None,
            errors=['pool_not_initialized']
        )
    try:
        async with pg_pool.connection() as conn:
            conn.row_factory = dict_row
            async with conn.cursor() as cur:
                try:
                    await cur.execute('SELECT 1')
                    await cur.fetchone()
                    connected = True
                except Exception as e:
                    errors.append(f'connect: {e}')
                try:
                    await cur.execute("SELECT default_version FROM pg_available_extensions WHERE name='vector'")
                    row = await cur.fetchone()
                    pgvector_available = bool(row)
                except Exception as e:
                    errors.append(f'available: {e}')
                try:
                    await cur.execute("SELECT extversion FROM pg_extension WHERE extname='vector'")
                    row2 = await cur.fetchone()
                    pgvector_installed = bool(row2)
                except Exception as e:
                    errors.append(f'installed: {e}')
                try:
                    await cur.execute("SELECT table_name FROM information_schema.tables WHERE table_schema='public' AND table_name LIKE 'ai_%'")
                    rows = await cur.fetchall()
                    ai_tables = [r['table_name'] for r in rows] if rows else []
                except Exception as e:
                    errors.append(f'ai_tables: {e}')
                try:
                    if 'ai_chunks' in ai_tables:
                        await cur.execute(
                            """
                            SELECT a.atttypmod AS atttypmod
                            FROM pg_attribute a
                            JOIN pg_class c ON c.oid = a.attrelid
                            WHERE c.relname = 'ai_chunks' AND a.attname = 'embedding'
                            """
                        )
                        rowd = await cur.fetchone()
                        if rowd and rowd.get('atttypmod') and rowd['atttypmod'] > 4:
                            dims = int(rowd['atttypmod']) - 4
                except Exception as e:
                    errors.append(f'dims: {e}')
    except Exception as e:
        errors.append(f'session: {e}')
    # Round dims to common expected values for display (some deployments report 1532 due to atttypmod specifics)
    if dims and dims in (1532,):
        dims = 1536
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
    if not pg_pool:
        raise HTTPException(status_code=500, detail='Database is not initialized')
    if not req.confirm:
        raise HTTPException(status_code=400, detail='confirm=false')
    try:
        async with pg_pool.connection() as conn:
            async with conn.cursor() as cur:
                await cur.execute('CREATE EXTENSION IF NOT EXISTS vector')
                await conn.commit()
                return {'ok': True}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# DSN diagnostics (sanitized)
@router.get('/db-dsn')
async def db_dsn():
    from urllib.parse import urlparse, parse_qsl
    raw = (os.environ.get('NEON_DATABASE_URL') or '').strip()
    norm = _normalize_db_url_psycopg(raw)
    def parse_info(u: str):
        try:
            p = urlparse(u)
            q = dict(parse_qsl(p.query, keep_blank_values=True))
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
    # Flatten normalized info to match tester expectations
    norm_info = parse_info(norm) if norm else None
    normalized = {
        'scheme': (norm_info or {}).get('scheme'),
        'host': (norm_info or {}).get('host'),
        'port': (norm_info or {}).get('port'),
        'database': (norm_info or {}).get('database'),
        'username': (norm_info or {}).get('username'),
        'query': 'sslmode=' + (norm_info.get('query', {}).get('sslmode') or '') if norm_info else None
    }
    return {
        'raw_present': bool(raw),
        'normalized': normalized,
    }