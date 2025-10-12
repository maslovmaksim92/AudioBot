"""init vasdom tables - users, roles, houses, tasks, logs

Revision ID: 0004_init_vasdom
Revises: 0003_change_embedding_dim_1536
Create Date: 2025-01-06
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers
revision = '0004_init_vasdom'
down_revision = '0003_change_embedding_dim_1536'
branch_labels = None
depends_on = None

def upgrade():
    # Создаем enum типы
    role_enum = postgresql.ENUM(
        'director', 'general_director', 'accountant', 'hr_director', 
        'hr_manager', 'cleaning_head', 'manager', 'estimator', 
        'brigade', 'presentation',
        name='roleenum'
    )
    role_enum.create(op.get_bind(), checkfirst=True)
    
    task_status_enum = postgresql.ENUM(
        'todo', 'in_progress', 'done', 'cancelled',
        name='taskstatus'
    )
    task_status_enum.create(op.get_bind(), checkfirst=True)
    
    task_priority_enum = postgresql.ENUM(
        'low', 'medium', 'high', 'urgent',
        name='taskpriority'
    )
    task_priority_enum.create(op.get_bind(), checkfirst=True)
    
    log_level_enum = postgresql.ENUM(
        'debug', 'info', 'warning', 'error', 'critical',
        name='loglevel'
    )
    log_level_enum.create(op.get_bind(), checkfirst=True)
    
    log_category_enum = postgresql.ENUM(
        'system', 'auth', 'cleaning', 'task', 'ai', 'integration', 'voice', 'user',
        name='logcategory'
    )
    log_category_enum.create(op.get_bind(), checkfirst=True)
    
    # Таблица roles
    op.create_table(
        'roles',
        sa.Column('name', role_enum, primary_key=True),
        sa.Column('description', sa.String(), nullable=True)
    )
    
    # Таблица users
    op.create_table(
        'users',
        sa.Column('id', sa.String(), primary_key=True),
        sa.Column('email', sa.String(), unique=True, nullable=False, index=True),
        sa.Column('full_name', sa.String(), nullable=False),
        sa.Column('phone', sa.String(), nullable=True),
        sa.Column('password_hash', sa.String(), nullable=False),
        sa.Column('brigade_number', sa.String(), nullable=True),
        sa.Column('is_active', sa.Boolean(), default=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False)
    )
    
    # Таблица связи user_roles
    op.create_table(
        'user_roles',
        sa.Column('user_id', sa.String(), sa.ForeignKey('users.id', ondelete='CASCADE'), primary_key=True),
        sa.Column('role', role_enum, primary_key=True)
    )
    
    # Таблица houses
    op.create_table(
        'houses',
        sa.Column('id', sa.String(), primary_key=True),
        sa.Column('bitrix_id', sa.String(), unique=True, nullable=True, index=True),
        sa.Column('address', sa.String(), nullable=False),
        sa.Column('apartments_count', sa.Integer(), nullable=True),
        sa.Column('entrances_count', sa.Integer(), nullable=True),
        sa.Column('floors_count', sa.Integer(), nullable=True),
        sa.Column('company_id', sa.String(), nullable=True),
        sa.Column('company_title', sa.String(), nullable=True),
        sa.Column('assigned_by_id', sa.String(), nullable=True),
        sa.Column('assigned_by_name', sa.String(), nullable=True),
        sa.Column('brigade_number', sa.String(), nullable=True),
        sa.Column('tariff', sa.String(), nullable=True),
        sa.Column('cleaning_schedule', postgresql.JSON(), nullable=True),
        sa.Column('complaints', postgresql.JSON(), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('elder_contact', sa.String(), nullable=True),
        sa.Column('act_signed', sa.DateTime(), nullable=True),
        sa.Column('last_cleaning', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.Column('synced_at', sa.DateTime(), nullable=True)
    )
    
    # Таблица tasks
    op.create_table(
        'tasks',
        sa.Column('id', sa.String(), primary_key=True),
        sa.Column('title', sa.String(), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('status', task_status_enum, nullable=False),
        sa.Column('priority', task_priority_enum, nullable=False),
        sa.Column('assigned_to_id', sa.String(), sa.ForeignKey('users.id'), nullable=True),
        sa.Column('created_by_id', sa.String(), sa.ForeignKey('users.id'), nullable=True),
        sa.Column('house_id', sa.String(), sa.ForeignKey('houses.id'), nullable=True),
        sa.Column('checklist', postgresql.JSON(), nullable=True),
        sa.Column('mindmap', postgresql.JSON(), nullable=True),
        sa.Column('due_date', sa.DateTime(), nullable=True),
        sa.Column('ai_proposed', sa.Boolean(), default=False),
        sa.Column('ai_reasoning', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.Column('completed_at', sa.DateTime(), nullable=True)
    )
    
    # Таблица logs
    op.create_table(
        'logs',
        sa.Column('id', sa.String(), primary_key=True),
        sa.Column('level', log_level_enum, nullable=False),
        sa.Column('category', log_category_enum, nullable=False),
        sa.Column('message', sa.Text(), nullable=False),
        sa.Column('user_id', sa.String(), nullable=True),
        sa.Column('user_email', sa.String(), nullable=True),
        sa.Column('extra_data', postgresql.JSON(), nullable=True),
        sa.Column('ip_address', sa.String(), nullable=True),
        sa.Column('user_agent', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, index=True)
    )

def downgrade():
    op.drop_table('logs')
    op.drop_table('tasks')
    op.drop_table('houses')
    op.drop_table('user_roles')
    op.drop_table('users')
    op.drop_table('roles')
    
    # Удаляем enum типы
    op.execute('DROP TYPE IF EXISTS logcategory CASCADE')
    op.execute('DROP TYPE IF EXISTS loglevel CASCADE')
    op.execute('DROP TYPE IF EXISTS taskpriority CASCADE')
    op.execute('DROP TYPE IF EXISTS taskstatus CASCADE')
    op.execute('DROP TYPE IF EXISTS roleenum CASCADE')
