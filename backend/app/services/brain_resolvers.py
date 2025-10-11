"""
Brain resolvers - implementation with Bitrix24 and DB integration
"""
from __future__ import annotations

from typing import Any, Dict, Optional
from datetime import datetime, timedelta
from sqlalchemy import text as sql_text
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.services.brain_intents import extract_address, extract_month
from backend.app.services.brain_store import BrainStore

# Singleton BrainStore instance
_brain_store = BrainStore()


def _success(answer: str, data: Optional[Dict[str, Any]] = None, rule: Optional[str] = None, sources: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Helper to create success response"""
    result = {
        "success": True,
        "answer": answer
    }
    if data:
        result["data"] = data
    if rule:
        result["rule"] = rule
    if sources:
        result["sources"] = sources
    return result


def _fail(error: str) -> Dict[str, Any]:
    """Helper to create failure response"""
    return {
        "success": False,
        "error": error
    }


def format_cleaning_for_month(cleaning_dates: Any, month: str) -> str:
    """Форматировать даты уборок для месяца"""
    if not cleaning_dates:
        return "Данные отсутствуют"
    
    periods = cleaning_dates.get_for_month(month)
    if not periods:
        return f"Нет данных по уборкам на {month}"
    
    lines = []
    for period_name, period_data in periods:
        if not isinstance(period_data, dict):
            continue
        dates = period_data.get('dates') or []
        cleaning_type = period_data.get('type') or 'Не указан'
        for dt in dates:
            lines.append(f"{dt} — {cleaning_type}")
    
    return "\n".join(lines) if lines else "Нет дат"


async def resolve_elder_contact(text: str, ent: Optional[Dict[str, Any]] = None) -> Optional[Dict[str, Any]]:
    """Resolve elder contact queries"""
    if not text:
        return None
    
    tl = text.lower()
    if not any(k in tl for k in ["контакт", "старш", "телефон", "почта", "email"]):
        return None
    
    # Извлекаем адрес
    address = (ent or {}).get('address') or extract_address(text)
    if not address:
        return _fail("no_address")
    
    try:
        # Получаем контакты старшего
        result = await _brain_store.get_elder_contact_by_address(address, return_debug=True)
        if isinstance(result, tuple):
            elder, meta = result
        else:
            elder = result
            meta = {}
        
        if not elder or elder.is_empty():
            return _fail("elder_not_found")
        
        # Получаем дом для адреса и ссылки Bitrix
        houses_result = await _brain_store.get_houses_by_address(address, limit=1, return_debug=True)
        if isinstance(houses_result, tuple):
            houses, houses_meta = houses_result
        else:
            houses = houses_result
            houses_meta = {}
        
        bitrix_url = houses[0].bitrix_url if houses else None
        house_title = houses[0].title if houses else address
        
        # Форматируем ответ
        lines = [f"🏠 Адрес: {house_title}", f"Старший: {elder.name or 'Не указан'}"]
        if elder.phones:
            lines.append(f"Телефон(ы): {', '.join(elder.phones)}")
        if elder.emails:
            lines.append(f"Email: {', '.join(elder.emails)}")
        if bitrix_url:
            lines.append(f"Ссылка в Bitrix: {bitrix_url}")
        
        answer = "\n".join(lines)
        
        sources = {
            "addr": address,
            "elder": meta,
            "houses": houses_meta
        }
        
        return _success(answer, rule="elder_contact", sources=sources)
    
    except Exception as e:
        return _fail(f"error: {str(e)}")


async def resolve_cleaning_month(text: str, ent: Optional[Dict[str, Any]] = None) -> Optional[Dict[str, Any]]:
    """Resolve cleaning schedule queries"""
    if not text:
        return None
    
    tl = text.lower()
    if not any(k in tl for k in ["уборк", "когда", "дат", "график", "расписан"]):
        return None
    
    # Извлекаем адрес и месяц
    address = (ent or {}).get('address') or extract_address(text)
    month = (ent or {}).get('month') or extract_month(text)
    
    if not address:
        return _fail("no_address")
    
    if not month:
        return _fail("no_month")
    
    try:
        # Получаем даты уборок
        result = await _brain_store.get_cleaning_for_month_by_address(address, month, return_debug=True)
        if isinstance(result, tuple):
            cleaning_dates, meta = result
        else:
            cleaning_dates = result
            meta = {}
        
        if not cleaning_dates:
            return _fail("cleaning_not_found")
        
        # Форматируем даты
        formatted = format_cleaning_for_month(cleaning_dates, month)
        
        # Получаем название дома
        houses_result = await _brain_store.get_houses_by_address(address, limit=1, return_debug=True)
        if isinstance(houses_result, tuple):
            houses, houses_meta = houses_result
        else:
            houses = houses_result
            houses_meta = {}
        
        house_title = houses[0].title if houses else address
        
        month_names = {
            'october': 'Октябрь',
            'november': 'Ноябрь',
            'december': 'Декабрь'
        }
        month_name = month_names.get(month, month)
        
        answer = f"🏠 Адрес: {house_title}\n📅 {month_name}:\n{formatted}"
        
        sources = {
            "addr": address,
            "month": month,
            "cleaning": meta.get('houses', {})
        }
        
        return _success(answer, rule="cleaning_month", sources=sources)
    
    except Exception as e:
        return _fail(f"error: {str(e)}")


async def resolve_brigade_by_address(text: str, ent: Optional[Dict[str, Any]] = None) -> Optional[Dict[str, Any]]:
    """Resolve brigade queries by address"""
    if not text:
        return None
    
    tl = text.lower()
    if not any(k in tl for k in ["бригад", "кто убирает"]):
        return None
    
    # Извлекаем адрес
    address = (ent or {}).get('address') or extract_address(text)
    if not address:
        return _fail("no_address")
    
    try:
        # Получаем дома по адресу
        result = await _brain_store.get_houses_by_address(address, limit=1, return_debug=True)
        if isinstance(result, tuple):
            houses, meta = result
        else:
            houses = result
            meta = {}
        
        if not houses:
            return _fail("house_not_found")
        
        house = houses[0]
        brigade_name = house.brigade_name or 'Не назначена'
        
        answer = f"🏠 Адрес: {house.title}\n👷 Бригада: {brigade_name}"
        
        sources = {
            "addr": address,
            "houses": meta
        }
        
        return _success(answer, rule="brigade", sources=sources)
    
    except Exception as e:
        return _fail(f"error: {str(e)}")


async def resolve_finance_basic(text: str, db: AsyncSession, ent: Optional[Dict[str, Any]] = None) -> Optional[Dict[str, Any]]:
    """Resolve basic finance queries"""
    if not text:
        return None
    
    tl = text.lower()
    if not any(k in tl for k in ["финанс", "деньги", "баланс", "прибыль"]):
        return None
    
    try:
        # Получаем базовую финансовую статистику
        result = await _brain_store.get_finance_aggregate(db, return_debug=True)
        if isinstance(result, tuple):
            data, meta = result
        else:
            data = result
            meta = {}
        
        income = data.get('income', 0.0)
        expense = data.get('expense', 0.0)
        profit = income - expense
        transactions = data.get('transactions', 0)
        
        answer = (
            f"💰 Финансы:\n"
            f"Доходы: {income:,.2f} ₽\n"
            f"Расходы: {expense:,.2f} ₽\n"
            f"Прибыль: {profit:,.2f} ₽\n"
            f"Транзакций: {transactions}"
        )
        
        sources = {
            "finance": meta
        }
        
        return _success(answer, data=data, rule="finance_basic", sources=sources)
    
    except Exception as e:
        return _fail(f"error: {str(e)}")


async def resolve_structural_totals(text: str, db: AsyncSession, ent: Optional[Dict[str, Any]] = None) -> Optional[Dict[str, Any]]:
    """Resolve structural totals queries"""
    if not text:
        return None
    
    tl = text.lower()
    if not any(k in tl for k in ["квартир", "этаж", "подъезд", "сколько домов", "всего"]):
        return None
    
    try:
        # Извлекаем адрес (если есть - статистика по одному дому, иначе - по всем)
        address = (ent or {}).get('address') or extract_address(text)
        
        if address:
            # Статистика по конкретному дому
            result = await _brain_store.get_houses_by_address(address, limit=1, return_debug=True)
            if isinstance(result, tuple):
                houses, meta = result
            else:
                houses = result
                meta = {}
            
            if not houses:
                return _fail("house_not_found")
            
            house = houses[0]
            answer = (
                f"🏠 Адрес: {house.title}\n"
                f"📊 Структура:\n"
                f"Квартир: информация недоступна\n"
                f"Этажей: информация недоступна\n"
                f"Подъездов: информация недоступна"
            )
            sources = {"addr": address, "houses": meta}
        else:
            # Статистика по всем домам из БД
            q = sql_text(
                """
                SELECT 
                    COUNT(*) as total_houses,
                    SUM(apartments_count) as total_apartments,
                    SUM(floors_count) as total_floors,
                    SUM(entrances_count) as total_entrances
                FROM houses
                """
            )
            res = await db.execute(q)
            row = res.first()
            
            total_houses = int(row[0] or 0) if row else 0
            total_apartments = int(row[1] or 0) if row else 0
            total_floors = int(row[2] or 0) if row else 0
            total_entrances = int(row[3] or 0) if row else 0
            
            answer = (
                f"📊 Общая статистика:\n"
                f"Домов: {total_houses}\n"
                f"Квартир: {total_apartments}\n"
                f"Этажей: {total_floors}\n"
                f"Подъездов: {total_entrances}"
            )
            sources = {"db": "houses"}
        
        return _success(answer, rule="structural_totals", sources=sources)
    
    except Exception as e:
        return _fail(f"error: {str(e)}")


async def resolve_finance_breakdown(text: str, db: AsyncSession, ent: Optional[Dict[str, Any]] = None) -> Optional[Dict[str, Any]]:
    """Resolve finance breakdown queries"""
    if not text:
        return None
    
    tl = text.lower()
    if not any(k in tl for k in ["разбивк", "категори", "по категор"]):
        return None
    
    try:
        # Получаем разбивку по категориям
        q = sql_text(
            """
            SELECT 
                category,
                SUM(CASE WHEN type = 'income' THEN amount ELSE 0 END) as income,
                SUM(CASE WHEN type = 'expense' THEN amount ELSE 0 END) as expense,
                COUNT(*) as count
            FROM financial_transactions
            GROUP BY category
            ORDER BY expense DESC, income DESC
            LIMIT 10
            """
        )
        res = await db.execute(q)
        rows = res.fetchall()
        
        if not rows:
            return _fail("no_transactions")
        
        lines = ["💰 Разбивка по категориям:"]
        for row in rows:
            cat = row[0] or 'Без категории'
            inc = float(row[1] or 0.0)
            exp = float(row[2] or 0.0)
            cnt = int(row[3] or 0)
            
            if exp > 0:
                lines.append(f"📉 {cat}: {exp:,.2f} ₽ расход ({cnt} тр.)")
            elif inc > 0:
                lines.append(f"📈 {cat}: {inc:,.2f} ₽ доход ({cnt} тр.)")
        
        answer = "\n".join(lines)
        
        sources = {"db": "financial_transactions"}
        
        return _success(answer, rule="finance_breakdown", sources=sources)
    
    except Exception as e:
        return _fail(f"error: {str(e)}")


async def resolve_finance_mom(text: str, db: AsyncSession, ent: Optional[Dict[str, Any]] = None) -> Optional[Dict[str, Any]]:
    """Resolve month-over-month finance queries"""
    if not text:
        return None
    
    tl = text.lower()
    if not any(k in tl for k in ["м/м", "месяц к месяц", "динамик"]):
        return None
    
    try:
        # Получаем данные за последние 2 месяца
        q = text(
            """
            WITH 
            recent AS (
                SELECT 
                    SUM(CASE WHEN type='income' THEN amount ELSE 0 END) AS inc,
                    SUM(CASE WHEN type='expense' THEN amount ELSE 0 END) AS exp
                FROM financial_transactions
                WHERE date >= (CURRENT_DATE - INTERVAL '30 days')
            ),
            previous AS (
                SELECT 
                    SUM(CASE WHEN type='income' THEN amount ELSE 0 END) AS inc,
                    SUM(CASE WHEN type='expense' THEN amount ELSE 0 END) AS exp
                FROM financial_transactions
                WHERE date < (CURRENT_DATE - INTERVAL '30 days')
                  AND date >= (CURRENT_DATE - INTERVAL '60 days')
            )
            SELECT r.inc, r.exp, p.inc, p.exp FROM recent r CROSS JOIN previous p
            """
        )
        res = await db.execute(q)
        row = res.first()
        
        if not row:
            return _fail("no_transactions")
        
        inc_now = float(row[0] or 0.0)
        exp_now = float(row[1] or 0.0)
        inc_prev = float(row[2] or 0.0)
        exp_prev = float(row[3] or 0.0)
        
        inc_change = ((inc_now - inc_prev) / inc_prev * 100) if inc_prev > 0 else 0.0
        exp_change = ((exp_now - exp_prev) / exp_prev * 100) if exp_prev > 0 else 0.0
        
        profit_now = inc_now - exp_now
        profit_prev = inc_prev - exp_prev
        profit_change = ((profit_now - profit_prev) / profit_prev * 100) if profit_prev != 0 else 0.0
        
        answer = (
            f"📊 Месяц к месяцу (М/М):\n"
            f"Доходы: {inc_now:,.2f} ₽ ({inc_change:+.1f}%)\n"
            f"Расходы: {exp_now:,.2f} ₽ ({exp_change:+.1f}%)\n"
            f"Прибыль: {profit_now:,.2f} ₽ ({profit_change:+.1f}%)"
        )
        
        sources = {"db": "financial_transactions"}
        
        return _success(answer, rule="finance_mom", sources=sources)
    
    except Exception as e:
        return _fail(f"error: {str(e)}")