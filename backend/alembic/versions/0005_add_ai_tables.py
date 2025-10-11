"""add ai chat and tasks tables

Revision ID: 0005
Revises: 0004
Create Date: 2025-10-10 18:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID


# revision identifiers, used by Alembic.
revision = '0005'
down_revision = '0004_add_position_to_users'
branch_labels = None
depends_on = None


def upgrade():
    # Создаем таблицу chat_history
    op.create_table(
        'chat_history',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('user_id', sa.String(), nullable=False),
        sa.Column('role', sa.String(20), nullable=False),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('telegram_message_id', sa.String(), nullable=True),
        sa.Column('message_metadata', sa.Text(), nullable=True),
        sa.Column('synced_to_telegram', sa.Boolean(), default=False),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE')
    )
    op.create_index('ix_chat_history_user_id', 'chat_history', ['user_id'])
    
    # Создаем таблицу ai_tasks
    op.create_table(
        'ai_tasks',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('created_by', sa.String(), nullable=False),
        sa.Column('assigned_to', sa.String(), nullable=True),
        sa.Column('task_type', sa.String(50), nullable=False),
        sa.Column('status', sa.String(50), default='pending'),
        sa.Column('title', sa.String(255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('scheduled_at', sa.DateTime(), nullable=True),
        sa.Column('completed_at', sa.DateTime(), nullable=True),
        sa.Column('related_data', sa.Text(), nullable=True),
        sa.Column('result', sa.Text(), nullable=True),
        sa.Column('is_recurring', sa.Boolean(), default=False),
        sa.Column('notify_telegram', sa.Boolean(), default=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.func.now(), onupdate=sa.func.now()),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['created_by'], ['users.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['assigned_to'], ['users.id'], ondelete='SET NULL')
    )
    op.create_index('ix_ai_tasks_created_by', 'ai_tasks', ['created_by'])
    

def downgrade():
    op.drop_index('ix_ai_tasks_created_by', 'ai_tasks')
    op.drop_table('ai_tasks')
    op.drop_index('ix_chat_history_user_id', 'chat_history')
    op.drop_table('chat_history')
