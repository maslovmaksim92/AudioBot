from alembic import op
import sqlalchemy as sa
from pgvector.sqlalchemy import Vector
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '0001_init_pgvector_ai_knowledge'
down_revision = None
branch_labels = None
depends_on = None

def upgrade():
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")
    op.create_table(
        'ai_documents',
        sa.Column('id', sa.String(), primary_key=True),
        sa.Column('filename', sa.String(), nullable=False),
        sa.Column('mime', sa.String()),
        sa.Column('size_bytes', sa.Integer()),
        sa.Column('summary', sa.Text()),
        sa.Column('pages', sa.Integer()),
        sa.Column('created_at', sa.DateTime(timezone=True))
    )
    op.create_table(
        'ai_chunks',
        sa.Column('id', sa.String(), primary_key=True),
        sa.Column('document_id', sa.String(), sa.ForeignKey('ai_documents.id', ondelete='CASCADE'), nullable=False),
        sa.Column('chunk_index', sa.Integer(), nullable=False),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('embedding', Vector(1536))
    )
    op.create_index('ix_ai_chunks_document_id', 'ai_chunks', ['document_id'])
    # On Neon free, IVFFLAT doesn't allow dims>2000; 1536 is fine. Use smaller lists to be safe.
    op.execute("CREATE INDEX IF NOT EXISTS ix_ai_chunks_embedding ON ai_chunks USING ivfflat (embedding vector_cosine_ops) WITH (lists=50)")
    op.create_table(
        'ai_uploads_temp',
        sa.Column('upload_id', sa.String(), primary_key=True),
        sa.Column('meta', postgresql.JSONB, nullable=False),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=False)
    )

def downgrade():
    op.drop_table('ai_uploads_temp')
    op.drop_index('ix_ai_chunks_document_id', table_name='ai_chunks')
    op.drop_table('ai_chunks')
    op.drop_table('ai_documents')