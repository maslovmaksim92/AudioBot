"""
Модель домов (объектов уборки) - синхронизация с Bitrix24
"""
from sqlalchemy import Column, String, Integer, DateTime, JSON, Text
from datetime import datetime, timezone

from backend.app.config.database import Base

class House(Base):
    """Модель дома/объекта уборки"""
    __tablename__ = 'houses'
    
    id = Column(String, primary_key=True)  # UUID или ID из Bitrix24
    bitrix_id = Column(String, unique=True, index=True)  # ID в Bitrix24
    
    # Основная информация
    address = Column(String, nullable=False)  # Адрес
    apartments_count = Column(Integer, nullable=True)  # Количество квартир
    entrances_count = Column(Integer, nullable=True)  # Количество подъездов
    floors_count = Column(Integer, nullable=True)  # Количество этажей
    
    # Управляющая компания
    company_id = Column(String, nullable=True)  # ID УК в Bitrix24
    company_title = Column(String, nullable=True)  # Название УК
    
    # Ответственные
    assigned_by_id = Column(String, nullable=True)  # ID ответственного (бригады)
    assigned_by_name = Column(String, nullable=True)  # Имя ответственного
    brigade_number = Column(String, nullable=True)  # Номер бригады (1-7)
    
    # Тариф и периодичность
    tariff = Column(String, nullable=True)  # Тариф/периодичность уборки
    
    # Графики уборки (JSON с датами и типами)
    cleaning_schedule = Column(JSON, nullable=True)
    # Формат: {"september_2025": [{"date": "2025-09-05", "type": "standard"}, ...], ...}
    
    # Рекламации и комментарии
    complaints = Column(JSON, nullable=True)  # Список рекламаций
    # Формат: [{"date": "2025-09-10", "text": "...", "photo_url": "...", "author": "..."}, ...]
    
    notes = Column(Text, nullable=True)  # Дополнительные заметки
    
    # Контакты
    elder_contact = Column(String, nullable=True)  # Контакт старшего по дому
    
    # Статусы
    act_signed = Column(DateTime, nullable=True)  # Дата подписания акта
    last_cleaning = Column(DateTime, nullable=True)  # Дата последней уборки
    
    # Метаданные
    created_at = Column(DateTime, default=lambda: datetime.utcnow())
    updated_at = Column(DateTime, default=lambda: datetime.utcnow(), onupdate=lambda: datetime.utcnow())
    synced_at = Column(DateTime, nullable=True)  # Дата последней синхронизации с Bitrix24
    
    def __repr__(self):
        return f"<House(id={self.id}, address={self.address}, brigade={self.brigade_number})>"