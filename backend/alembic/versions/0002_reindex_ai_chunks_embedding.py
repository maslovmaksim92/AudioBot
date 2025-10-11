from alembic import op

# revision identifiers, used by Alembic.
revision = '0002_reindex_ai_chunks_embedding'
down_revision = '0001_init_pgvector_ai_knowledge'
branch_labels = None
depends_on = None

def upgrade():
    # Recreate IVFFLAT index with lists=200 as per new tuning
    op.execute("DROP INDEX IF EXISTS ix_ai_chunks_embedding")
    op.execute("CREATE INDEX ix_ai_chunks_embedding ON ai_chunks USING ivfflat (embedding vector_cosine_ops) WITH (lists=200)")


def downgrade():
    # Rollback to lists=100 (previous default)
    op.execute("DROP INDEX IF EXISTS ix_ai_chunks_embedding")
    op.execute("CREATE INDEX ix_ai_chunks_embedding ON ai_chunks USING ivfflat (embedding vector_cosine_ops) WITH (lists=100)")