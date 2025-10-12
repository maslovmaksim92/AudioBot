"""
Модели пользователей и ролей - RBAC система
"""
from sqlalchemy import Column, String, Boolean, DateTime, ForeignKey, Table, Enum as SQLEnum
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
import enum

from backend.app.config.database import Base

class RoleEnum(str, enum.Enum):
    """Роли пользователей в системе"""
    DIRECTOR = "director"  # Директор - полный доступ
    GENERAL_DIRECTOR = "general_director"  # Генеральный директор - полный доступ
    ACCOUNTANT = "accountant"  # Бухгалтер - полный доступ
    HR_DIRECTOR = "hr_director"  # HR директор - полный, кроме бухгалтерии
    HR_MANAGER = "hr_manager"  # HR менеджер - полный доступ
    CLEANING_HEAD = "cleaning_head"  # Начальник отдела клининга - полный доступ
    MANAGER = "manager"  # Менеджер - полный доступ
    ESTIMATOR = "estimator"  # Сметчик - полный доступ
    OFFICE_MANAGER = "office_manager"  # Офис-менеджер
    BRIGADE = "brigade"  # Бригада - только свои дома
    PRESENTATION = "presentation"  # Презентация - только просмотр

class PositionEnum(str, enum.Enum):
    """Должности сотрудников"""
    CLEANING_OPERATOR = "cleaning_operator"  # Оператор уборки
    BRIGADE_LEADER = "brigade_leader"  # Бригадир
    DRIVER = "driver"  # Водитель

# Таблица связи пользователей и ролей (many-to-many)
user_roles = Table(
    'user_roles',
    Base.metadata,
    Column('user_id', String, ForeignKey('users.id', ondelete='CASCADE'), primary_key=True),
    Column('role_name', SQLEnum(RoleEnum), ForeignKey('roles.name', ondelete='CASCADE'), primary_key=True)
)

class User(Base):
    """Модель пользователя"""
    __tablename__ = 'users'
    
    id = Column(String, primary_key=True)  # UUID
    email = Column(String, unique=True, index=True, nullable=False)
    full_name = Column(String, nullable=False)
    phone = Column(String, nullable=True)
    password_hash = Column(String, nullable=False)
    
    # Роли (many-to-many через таблицу user_roles)
    roles = relationship(
        'Role',
        secondary=user_roles,
        back_populates='users',
        lazy='selectin'
    )
    
    # Доп. поля
    position = Column(SQLEnum(PositionEnum), nullable=True)  # Должность сотрудника
    brigade_number = Column(String, nullable=True)  # Номер бригады (1-7) для роли BRIGADE
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=lambda: datetime.utcnow())
    updated_at = Column(DateTime, default=lambda: datetime.utcnow(), onupdate=lambda: datetime.utcnow())
    
    def __repr__(self):
        return f"<User(id={self.id}, email={self.email}, full_name={self.full_name})>"
    
    def has_role(self, role: RoleEnum) -> bool:
        """Проверка наличия роли у пользователя"""
        return any(r.name == role for r in self.roles)
    
    def has_full_access(self) -> bool:
        """Проверка полного доступа (все кроме бригады и презентации)"""
        full_access_roles = {
            RoleEnum.DIRECTOR,
            RoleEnum.GENERAL_DIRECTOR,
            RoleEnum.ACCOUNTANT,
            RoleEnum.HR_DIRECTOR,
            RoleEnum.HR_MANAGER,
            RoleEnum.CLEANING_HEAD,
            RoleEnum.MANAGER,
            RoleEnum.ESTIMATOR,
            RoleEnum.OFFICE_MANAGER
        }
        return any(r.name in full_access_roles for r in self.roles)

class Role(Base):
    """Модель роли"""
    __tablename__ = 'roles'
    
    name = Column(SQLEnum(RoleEnum), primary_key=True)
    description = Column(String, nullable=True)
    
    # Связь с пользователями
    users = relationship(
        'User',
        secondary=user_roles,
        back_populates='roles',
        lazy='selectin'
    )
    
    def __repr__(self):
        return f"<Role(name={self.name})>"