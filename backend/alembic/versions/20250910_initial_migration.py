"""Initial migration with PostgreSQL support

Revision ID: initial_001
Revises: 
Create Date: 2025-09-10 01:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers
revision = 'initial_001'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create initial tables for VasDom AudioBot"""
    
    # Create voice_logs table
    op.create_table('voice_logs',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('session_id', sa.String(), nullable=True),
        sa.Column('user_message', sa.Text(), nullable=False),
        sa.Column('ai_response', sa.Text(), nullable=False),
        sa.Column('rating', sa.Integer(), nullable=True),
        sa.Column('feedback_text', sa.Text(), nullable=True),
        sa.Column('model_used', sa.String(), nullable=True),
        sa.Column('response_time', sa.Float(), nullable=True),
        sa.Column('token_count', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create voice_embeddings table
    op.create_table('voice_embeddings',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('log_id', sa.String(), nullable=False),
        sa.Column('vector', sa.LargeBinary(), nullable=False),
        sa.Column('embedding_model', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['log_id'], ['voice_logs.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create model_metrics table
    op.create_table('model_metrics',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('model_version', sa.String(), nullable=False),
        sa.Column('avg_rating', sa.Float(), nullable=True),
        sa.Column('total_interactions', sa.Integer(), nullable=True),
        sa.Column('positive_ratings', sa.Integer(), nullable=True),
        sa.Column('negative_ratings', sa.Integer(), nullable=True),
        sa.Column('user_satisfaction', sa.Float(), nullable=True),
        sa.Column('evaluation_period_start', sa.DateTime(), nullable=True),
        sa.Column('evaluation_period_end', sa.DateTime(), nullable=True),
        sa.Column('is_current_model', sa.Boolean(), nullable=True),
        sa.Column('requires_retraining', sa.Boolean(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create training_datasets table  
    op.create_table('training_datasets',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('min_rating_threshold', sa.Integer(), nullable=True),
        sa.Column('total_samples', sa.Integer(), nullable=True),
        sa.Column('filtered_samples', sa.Integer(), nullable=True),
        sa.Column('file_path', sa.String(), nullable=True),
        sa.Column('status', sa.String(), nullable=True),
        sa.Column('training_logs', sa.Text(), nullable=True),
        sa.Column('model_weights_path', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('training_started_at', sa.DateTime(), nullable=True),
        sa.Column('training_completed_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )


def downgrade() -> None:
    """Drop all tables"""
    op.drop_table('training_datasets')
    op.drop_table('model_metrics')
    op.drop_table('voice_embeddings')
    op.drop_table('voice_logs')