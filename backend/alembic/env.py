from __future__ import with_statement
from logging.config import fileConfig
import os
from sqlalchemy import engine_from_config, pool
from alembic import context

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

# Interpret the config file for Python logging.
# This line sets up loggers basically.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# get DATABASE_URL from env (Render)
db_url = os.environ.get("DATABASE_URL_OVERRIDE") or os.environ.get("NEON_DATABASE_URL") or os.environ.get("DATABASE_URL") or ""
if db_url:
    # normalize URL for sync engine: ensure postgresql:// and sslmode=require
    from urllib.parse import urlparse, parse_qsl, urlencode, urlunparse
    try:
        raw = db_url.strip().strip("'\"")
        if raw.startswith('postgresql+asyncpg://'):
            raw = raw.replace('postgresql+asyncpg://', 'postgresql://', 1)
        if raw.startswith('postgres://'):
            raw = raw.replace('postgres://', 'postgresql://', 1)
        u = urlparse(raw)
        q = dict(parse_qsl(u.query, keep_blank_values=True))
        # convert ssl=true to sslmode=require; drop channel_binding
        if 'ssl' in q:
            if str(q.get('ssl')).lower() in ('true','1','yes'):
                q.pop('ssl', None)
                q['sslmode'] = 'require'
            else:
                q.pop('ssl', None)
        q.pop('channel_binding', None)
        # validate sslmode
        if 'sslmode' in q:
            allowed = {'disable','allow','prefer','require','verify-ca','verify-full'}
            if q['sslmode'] not in allowed:
                q['sslmode'] = 'require'
        new_query = urlencode(q, doseq=True)
        normalized = urlunparse((u.scheme, u.netloc, u.path, u.params, new_query, u.fragment))
        config.set_main_option("sqlalchemy.url", normalized)
    except Exception:
        config.set_main_option("sqlalchemy.url", raw)

# add your model's MetaData object here for 'autogenerate' support
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.config.database import Base
from app.models import User, Role, House, Task, Log  # Import all models
from app.models.chat_history import ChatHistory
from app.models.ai_task import AITask

target_metadata = Base.metadata
from sqlalchemy import MetaData
from sqlalchemy.dialects import postgresql
from sqlalchemy import Table, Column, String, Integer, Text, DateTime, ForeignKey
from pgvector.sqlalchemy import Vector

metadata = MetaData()

aidoc = Table(
    'ai_documents', metadata,
    Column('id', String, primary_key=True),
    Column('filename', String, nullable=False),
    Column('mime', String),
    Column('size_bytes', Integer),
    Column('summary', Text),
    Column('pages', Integer),
    Column('created_at', DateTime(timezone=True))
)

aichunk = Table(
    'ai_chunks', metadata,
    Column('id', String, primary_key=True),
    Column('document_id', String, ForeignKey('ai_documents.id', ondelete='CASCADE'), nullable=False, index=True),
    Column('chunk_index', Integer, nullable=False),
    Column('content', Text, nullable=False),
    Column('embedding', Vector(3072))
)

aiupload = Table(
    'ai_uploads_temp', metadata,
    Column('upload_id', String, primary_key=True),
    Column('meta', postgresql.JSONB, nullable=False),
    Column('expires_at', DateTime(timezone=True), nullable=False)
)

def run_migrations_offline():
    url = config.get_main_option("sqlalchemy.url")
    context.configure(url=url, target_metadata=metadata, literal_binds=True, dialect_opts={"paramstyle": "named"})

    with context.begin_transaction():
        context.execute("CREATE EXTENSION IF NOT EXISTS vector")
        context.run_migrations()


def run_migrations_online():
    connectable = engine_from_config(
        config.get_section(config.config_ini_section),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=metadata)

        with context.begin_transaction():
            context.execute("CREATE EXTENSION IF NOT EXISTS vector")
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()