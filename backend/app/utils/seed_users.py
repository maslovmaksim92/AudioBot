"""
Скрипт для создания начальных пользователей VasDom AudioBot (логины как есть)
"""
import asyncio
import uuid
from sqlalchemy import select

from backend.app.config.database import AsyncSessionLocal, init_db
from backend.app.models.user import User, Role, RoleEnum
from backend.app.utils.security import hash_password

# Данные пользователей (логины как есть, без доменов)
USERS_DATA = [
    {"full_name": "Маслов Максим Валерьевич", "phone": "+79200924550", "email": "m.masl@", "password": "V123456d", "roles": [RoleEnum.DIRECTOR]},
    {"full_name": "Маслова Валентина Михайловна", "phone": "+79208701769", "email": "v.masl@", "password": "V123456d", "roles": [RoleEnum.GENERAL_DIRECTOR]},
    {"full_name": "Колосов Дмитрий Сергеевич", "phone": "", "email": "d.kolos@", "password": "V123456d", "roles": [RoleEnum.ACCOUNTANT]},
    {"full_name": "Светлова Ольга Адендеевна", "phone": "", "email": "o.svetl@", "password": "V123456d", "roles": [RoleEnum.HR_DIRECTOR]},
    {"full_name": "Попов Никита Валерьевич", "phone": "", "email": "n.popov@", "password": "V123456d", "roles": [RoleEnum.HR_MANAGER]},
    {"full_name": "Наталья Викторовна", "phone": "", "email": "n@", "password": "V123456d", "roles": [RoleEnum.CLEANING_HEAD]},
    {"full_name": "Ильиных Алексей Владимирович", "phone": "", "email": "a.iln@", "password": "V123456d", "roles": [RoleEnum.MANAGER]},
    {"full_name": "Маслова Арина Алексеевна", "phone": "", "email": "a.masl@", "password": "V123456d", "roles": [RoleEnum.ESTIMATOR]},
    {"full_name": "Черкасов Ярослав Арутрович", "phone": "", "email": "y.chir@", "password": "V123456d", "roles": [RoleEnum.ESTIMATOR]},
    {"full_name": "Филиппов Сергей Сергеевич", "phone": "", "email": "s.fill@", "password": "V123456d", "roles": [RoleEnum.MANAGER]},
    {"full_name": "Аккаунт для презентации", "phone": "", "email": "test@", "password": "V123456d", "roles": [RoleEnum.PRESENTATION]},
    # Бригады 1-7
    {"full_name": "Бригада 1", "phone": "", "email": "brigada1@", "password": "V123456d", "roles": [RoleEnum.BRIGADE], "brigade_number": "1"},
    {"full_name": "Бригада 2", "phone": "", "email": "brigada2@", "password": "V123456d", "roles": [RoleEnum.BRIGADE], "brigade_number": "2"},
    {"full_name": "Бригада 3", "phone": "", "email": "brigada3@", "password": "V123456d", "roles": [RoleEnum.BRIGADE], "brigade_number": "3"},
    {"full_name": "Бригада 4", "phone": "", "email": "brigada4@", "password": "V123456d", "roles": [RoleEnum.BRIGADE], "brigade_number": "4"},
    {"full_name": "Бригада 5", "phone": "", "email": "brigada5@", "password": "V123456d", "roles": [RoleEnum.BRIGADE], "brigade_number": "5"},
    {"full_name": "Бригада 6", "phone": "", "email": "brigada6@", "password": "V123456d", "roles": [RoleEnum.BRIGADE], "brigade_number": "6"},
    {"full_name": "Бригада 7", "phone": "", "email": "brigada7@", "password": "V123456d", "roles": [RoleEnum.BRIGADE], "brigade_number": "7"},
]

async def create_roles(db):
    for role_enum in RoleEnum:
        result = await db.execute(select(Role).where(Role.name == role_enum))
        if not result.scalar_one_or_none():
            db.add(Role(name=role_enum, description=f"Роль: {role_enum.value}"))
    await db.commit()

async def create_users(db):
    for user_data in USERS_DATA:
        # пропускаем пустые логины
        if not user_data.get("email"):
            continue
        result = await db.execute(select(User).where(User.email == user_data["email"]))
        if result.scalar_one_or_none():
            continue
        user = User(
            id=str(uuid.uuid4()),
            email=user_data["email"],
            full_name=user_data["full_name"],
            phone=user_data.get("phone", ""),
            password_hash=hash_password(user_data["password"]),
            brigade_number=user_data.get("brigade_number"),
            is_active=True,
        )
        # привязываем роли
        for role_enum in user_data["roles"]:
            role_res = await db.execute(select(Role).where(Role.name == role_enum))
            role = role_res.scalar_one()
            user.roles.append(role)
        db.add(user)
    await db.commit()

async def seed_database():
    await init_db()
    async with AsyncSessionLocal() as db:
        await create_roles(db)
        await create_users(db)

if __name__ == "__main__":
    asyncio.run(seed_database())