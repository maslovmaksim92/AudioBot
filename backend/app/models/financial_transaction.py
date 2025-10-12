from pydantic import BaseModel, Field
from typing import Optional, Literal
from datetime import datetime
from uuid import uuid4

# Pydantic модели для API

class TransactionBase(BaseModel):
    """Базовая модель транзакции"""
    date: datetime
    amount: float
    category: str
    type: Literal["income", "expense"]
    description: Optional[str] = None
    payment_method: Optional[str] = None
    counterparty: Optional[str] = None  # Контрагент (от кого/кому)
    project: Optional[str] = None
    tags: Optional[list[str]] = []

class TransactionCreate(TransactionBase):
    """Модель для создания транзакции"""
    pass

class TransactionUpdate(BaseModel):
    """Модель для обновления транзакции"""
    date: Optional[datetime] = None
    amount: Optional[float] = None
    category: Optional[str] = None
    type: Optional[Literal["income", "expense"]] = None
    description: Optional[str] = None
    payment_method: Optional[str] = None
    counterparty: Optional[str] = None
    project: Optional[str] = None
    tags: Optional[list[str]] = None

class TransactionResponse(TransactionBase):
    """Модель для ответа с транзакцией"""
    id: str
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True

# Категории по умолчанию
DEFAULT_INCOME_CATEGORIES = [
    "Оплата услуг",
    "Продажа товаров",
    "Аренда",
    "Инвестиции",
    "Прочие доходы"
]

DEFAULT_EXPENSE_CATEGORIES = [
    "Зарплата",
    "Материалы",
    "Аренда",
    "Коммунальные услуги",
    "Транспорт",
    "Реклама и маркетинг",
    "Налоги",
    "Страхование",
    "Оборудование",
    "Прочие расходы"
]

# SQL для создания таблицы (для PostgreSQL)
CREATE_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS financial_transactions (
    id VARCHAR(36) PRIMARY KEY,
    date TIMESTAMP WITH TIME ZONE NOT NULL,
    amount DECIMAL(15, 2) NOT NULL,
    category VARCHAR(100) NOT NULL,
    type VARCHAR(10) NOT NULL CHECK (type IN ('income', 'expense')),
    description TEXT,
    payment_method VARCHAR(50),
    counterparty VARCHAR(200),
    project VARCHAR(100),
    tags TEXT[],
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE
);

CREATE INDEX IF NOT EXISTS idx_transactions_date ON financial_transactions(date);
CREATE INDEX IF NOT EXISTS idx_transactions_type ON financial_transactions(type);
CREATE INDEX IF NOT EXISTS idx_transactions_category ON financial_transactions(category);
"""
