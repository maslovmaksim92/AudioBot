"""
API роутер для управления сотрудниками
CRUD операции для сотрудников
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from typing import List, Optional
from pydantic import BaseModel, EmailStr, Field
import uuid
import logging

from backend.app.config.database import get_db
from backend.app.models.user import User, PositionEnum

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/employees", tags=["Employees"])

# Pydantic модели для API

class EmployeeCreate(BaseModel):
    """Модель для создания сотрудника"""
    email: EmailStr
    full_name: str = Field(..., min_length=1, max_length=255)
    phone: Optional[str] = Field(None, max_length=20)
    position: Optional[PositionEnum] = None
    brigade_number: Optional[str] = Field(None, max_length=10)
    password: str = Field(..., min_length=6)

class EmployeeUpdate(BaseModel):
    """Модель для обновления сотрудника"""
    full_name: Optional[str] = Field(None, min_length=1, max_length=255)
    phone: Optional[str] = Field(None, max_length=20)
    position: Optional[PositionEnum] = None
    brigade_number: Optional[str] = Field(None, max_length=10)
    is_active: Optional[bool] = None

class EmployeeResponse(BaseModel):
    """Модель ответа с данными сотрудника"""
    id: str
    email: str
    full_name: str
    phone: Optional[str]
    position: Optional[str]
    position_display: Optional[str]
    brigade_number: Optional[str]
    is_active: bool
    created_at: str
    
    class Config:
        from_attributes = True

# Helper функции

def get_position_display(position: Optional[PositionEnum]) -> Optional[str]:
    """Получить человекочитаемое название должности"""
    if not position:
        return None
    
    position_map = {
        PositionEnum.CLEANING_OPERATOR: "Оператор уборки",
        PositionEnum.BRIGADE_LEADER: "Бригадир",
        PositionEnum.DRIVER: "Водитель"
    }
    return position_map.get(position, position.value)

def hash_password(password: str) -> str:
    """Хеширование пароля (упрощенная версия)"""
    # В реальном приложении использовать bcrypt или passlib
    import hashlib
    return hashlib.sha256(password.encode()).hexdigest()

# API Endpoints

@router.get("", response_model=List[EmployeeResponse])
async def get_employees(
    skip: int = 0,
    limit: int = 100,
    position: Optional[str] = None,
    is_active: Optional[bool] = None,
    search: Optional[str] = None,
    db: AsyncSession = Depends(get_db)
):
    """
    Получить список всех сотрудников
    
    - **skip**: количество записей для пропуска (пагинация)
    - **limit**: максимальное количество записей
    - **position**: фильтр по должности
    - **is_active**: фильтр по активности
    - **search**: поиск по ФИО или email
    """
    try:
        query = select(User)
        
        # Применяем фильтры
        if position:
            try:
                position_enum = PositionEnum(position)
                query = query.where(User.position == position_enum)
            except ValueError:
                pass  # Игнорируем неверную должность
        
        if is_active is not None:
            query = query.where(User.is_active == is_active)
        
        if search:
            search_pattern = f"%{search}%"
            query = query.where(
                (User.full_name.ilike(search_pattern)) |
                (User.email.ilike(search_pattern))
            )
        
        # Сортировка и пагинация
        query = query.order_by(User.created_at.desc()).offset(skip).limit(limit)
        
        result = await db.execute(query)
        employees = result.scalars().all()
        
        # Формируем ответ
        response = []
        for emp in employees:
            response.append(EmployeeResponse(
                id=emp.id,
                email=emp.email,
                full_name=emp.full_name,
                phone=emp.phone,
                position=emp.position.value if emp.position else None,
                position_display=get_position_display(emp.position),
                brigade_number=emp.brigade_number,
                is_active=emp.is_active,
                created_at=emp.created_at.isoformat() if emp.created_at else ""
            ))
        
        return response
        
    except Exception as e:
        logger.error(f"Error getting employees: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ошибка при получении списка сотрудников: {str(e)}"
        )

@router.get("/positions/list")
async def get_positions():
    """Получить список всех доступных должностей"""
    return [
        {"value": PositionEnum.CLEANING_OPERATOR.value, "label": "Оператор уборки"},
        {"value": PositionEnum.BRIGADE_LEADER.value, "label": "Бригадир"},
        {"value": PositionEnum.DRIVER.value, "label": "Водитель"}
    ]

@router.get("/{employee_id}", response_model=EmployeeResponse)
async def get_employee(employee_id: str, db: AsyncSession = Depends(get_db)):
    """Получить данные конкретного сотрудника"""
    try:
        result = await db.execute(select(User).where(User.id == employee_id))
        employee = result.scalar_one_or_none()
        
        if not employee:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Сотрудник не найден"
            )
        
        return EmployeeResponse(
            id=employee.id,
            email=employee.email,
            full_name=employee.full_name,
            phone=employee.phone,
            position=employee.position.value if employee.position else None,
            position_display=get_position_display(employee.position),
            brigade_number=employee.brigade_number,
            is_active=employee.is_active,
            created_at=employee.created_at.isoformat() if employee.created_at else ""
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting employee {employee_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ошибка при получении данных сотрудника: {str(e)}"
        )

@router.post("", response_model=EmployeeResponse, status_code=status.HTTP_201_CREATED)
async def create_employee(employee_data: EmployeeCreate, db: AsyncSession = Depends(get_db)):
    """Создать нового сотрудника"""
    try:
        # Проверяем, существует ли пользователь с таким email
        result = await db.execute(select(User).where(User.email == employee_data.email))
        existing_user = result.scalar_one_or_none()
        
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Пользователь с таким email уже существует"
            )
        
        # Создаем нового сотрудника
        new_employee = User(
            id=str(uuid.uuid4()),
            email=employee_data.email,
            full_name=employee_data.full_name,
            phone=employee_data.phone,
            position=employee_data.position,
            brigade_number=employee_data.brigade_number,
            password_hash=hash_password(employee_data.password),
            is_active=True
        )
        
        db.add(new_employee)
        await db.commit()
        await db.refresh(new_employee)
        
        logger.info(f"Created new employee: {new_employee.email}")
        
        return EmployeeResponse(
            id=new_employee.id,
            email=new_employee.email,
            full_name=new_employee.full_name,
            phone=new_employee.phone,
            position=new_employee.position.value if new_employee.position else None,
            position_display=get_position_display(new_employee.position),
            brigade_number=new_employee.brigade_number,
            is_active=new_employee.is_active,
            created_at=new_employee.created_at.isoformat() if new_employee.created_at else ""
        )
        
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        logger.error(f"Error creating employee: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ошибка при создании сотрудника: {str(e)}"
        )

@router.put("/{employee_id}", response_model=EmployeeResponse)
async def update_employee(
    employee_id: str,
    employee_data: EmployeeUpdate,
    db: AsyncSession = Depends(get_db)
):
    """Обновить данные сотрудника"""
    try:
        # Получаем сотрудника
        result = await db.execute(select(User).where(User.id == employee_id))
        employee = result.scalar_one_or_none()
        
        if not employee:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Сотрудник не найден"
            )
        
        # Обновляем поля
        if employee_data.full_name is not None:
            employee.full_name = employee_data.full_name
        if employee_data.phone is not None:
            employee.phone = employee_data.phone
        if employee_data.position is not None:
            employee.position = employee_data.position
        if employee_data.brigade_number is not None:
            employee.brigade_number = employee_data.brigade_number
        if employee_data.is_active is not None:
            employee.is_active = employee_data.is_active
        
        await db.commit()
        await db.refresh(employee)
        
        logger.info(f"Updated employee: {employee.email}")
        
        return EmployeeResponse(
            id=employee.id,
            email=employee.email,
            full_name=employee.full_name,
            phone=employee.phone,
            position=employee.position.value if employee.position else None,
            position_display=get_position_display(employee.position),
            brigade_number=employee.brigade_number,
            is_active=employee.is_active,
            created_at=employee.created_at.isoformat() if employee.created_at else ""
        )
        
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        logger.error(f"Error updating employee {employee_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ошибка при обновлении данных сотрудника: {str(e)}"
        )

@router.delete("/{employee_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_employee(employee_id: str, db: AsyncSession = Depends(get_db)):
    """Удалить сотрудника"""
    try:
        # Получаем сотрудника
        result = await db.execute(select(User).where(User.id == employee_id))
        employee = result.scalar_one_or_none()
        
        if not employee:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Сотрудник не найден"
            )
        
        # Удаляем сотрудника
        await db.delete(employee)
        await db.commit()
        
        logger.info(f"Deleted employee: {employee.email}")
        
        return None
        
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        logger.error(f"Error deleting employee {employee_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ошибка при удалении сотрудника: {str(e)}"
        )