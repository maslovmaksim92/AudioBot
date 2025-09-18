from alembic import op

# revision identifiers, used by Alembic.
revision = '0003_change_embedding_dim_1536'
down_revision = '0002_reindex_ai_chunks_embedding'
branch_labels = None
depends_on = None

def upgrade():
    # Recreate IVFFLAT index for new dimensions
    op.execute("DROP INDEX IF EXISTS ix_ai_chunks_embedding")
    # Change vector dimension to 1536 for text-embedding-3-small
    op.execute("ALTER TABLE ai_chunks ALTER COLUMN embedding TYPE vector(1536)")
    op.execute("CREATE INDEX ix_ai_chunks_embedding ON ai_chunks USING ivfflat (embedding vector_cosine_ops) WITH (lists=200)")


def downgrade():
    op.execute("DROP INDEX IF EXISTS ix_ai_chunks_embedding")
    op.execute("ALTER TABLE ai_chunks ALTER COLUMN embedding TYPE vector(3072)")
    op.execute("CREATE INDEX ix_ai_chunks_embedding ON ai_chunks USING ivfflat (embedding vector_cosine_ops) WITH (lists=200)")