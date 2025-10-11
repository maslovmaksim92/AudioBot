"""add position field to users

Revision ID: 0004
Revises: 0003
Create Date: 2025-10-10 12:00:00

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '0004'
down_revision = '0003'
branch_labels = None
depends_on = None


def upgrade():
    # Создаем ENUM тип для должностей
    op.execute("""
        CREATE TYPE positionenum AS ENUM ('cleaning_operator', 'brigade_leader', 'driver');
    """)
    
    # Добавляем колонку position в таблицу users
    op.add_column('users', sa.Column('position', sa.Enum('cleaning_operator', 'brigade_leader', 'driver', name='positionenum'), nullable=True))


def downgrade():
    # Удаляем колонку position
    op.drop_column('users', 'position')
    
    # Удаляем ENUM тип
    op.execute('DROP TYPE positionenum;')
