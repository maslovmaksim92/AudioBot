"""
Brain resolvers (Stage 3): fast, rule-based answers without LLM
- Elder contact by address
- Cleaning dates by month/address
- Brigade by address (basic)
- Finance aggregate (basic stub via BrainStore)
"""
from __future__ import annotations

from typing import Any, Dict, Optional
import logging

from backend.app.services.brain_store import brain_store
from backend.app.services.brain import (
    parse_address_candidate,
    detect_month_key,
    detect_period_index,
    format_cleaning_for_month,
    format_elder_contact,
    CleaningDates,
)

logger = logging.getLogger(__name__)


def _success(answer: str, data: Optional[Dict[str, Any]] = None, sources: Optional[Dict[str, Any]] = None, rule: str = "") -> Dict[str, Any]:
    return {"success": True, "answer": answer, "data": data or {}, "sources": sources or {}, "rule": rule}


def _fail(reason: str, rule: str = "") -> Dict[str, Any]:
    return {"success": False, "error": reason, "rule": rule}


async def resolve_elder_contact(text: str) -> Optional[Dict[str, Any]]:
    # detect intent
    tl = (text or "").lower()
    want_contacts = any(k in tl for k in ["контакт", "телефон", "почта", "email"]) and ("старш" in tl)
    if not want_contacts:
        return None
    addr = parse_address_candidate(text)
    if not addr:
        return _fail("Не удалось распознать адрес", rule="elder_contact")

    elder = await brain_store.get_elder_contact_by_address(addr)
    if not elder:
        return _fail("Контакты старшего не найдены", rule="elder_contact")

    # also provide bitrix link from matched house
    houses = await brain_store.get_houses_by_address(addr, limit=1)
    bitrix_url = houses[0].bitrix_url if houses else None
    answer = format_elder_contact(elder.name, elder.phones, elder.emails)
    if bitrix_url:
        answer = f"{answer}\nСсылка в Bitrix: {bitrix_url}"
    return _success(answer, data={"elder": elder.__dict__}, sources={"addr": addr}, rule="elder_contact")


async def resolve_cleaning_month(text: str) -> Optional[Dict[str, Any]]:
    tl = (text or "").lower()
    # simple heuristic: requires word root "уборк"
    if "уборк" not in tl:
        return None
    addr = parse_address_candidate(text)
    if not addr:
        return _fail("Не удалось распознать адрес", rule="cleaning_month")
    month_key = detect_month_key(text) or "october"
    cd: Optional[CleaningDates] = await brain_store.get_cleaning_for_month_by_address(addr, month_key)
    if not cd:
        return _fail("Нет данных по графику уборок", rule="cleaning_month")
    formatted = format_cleaning_for_month(cd, month_key)
    if not formatted:
        return _fail("Нет дат по указанному месяцу", rule="cleaning_month")
    # Provide context line
    houses = await brain_store.get_houses_by_address(addr, limit=1)
    h = houses[0] if houses else None
    intro = f"🏠 Адрес: {h.title if h else addr}"
    if h and h.periodicity:
        intro += f"\nПериодичность: {h.periodicity}"
    answer = f"{intro}\n{month_key.capitalize()} — даты уборок:\n{formatted}"
    if h and h.bitrix_url:
        answer += f"\nСсылка в Bitrix: {h.bitrix_url}"
    return _success(answer, data={"month": month_key}, sources={"addr": addr}, rule="cleaning_month")


async def resolve_brigade_by_address(text: str) -> Optional[Dict[str, Any]]:
    tl = (text or "").lower()
    if "бригад" not in tl and "ответствен" not in tl:
        return None
    addr = parse_address_candidate(text)
    if not addr:
        return _fail("Не удалось распознать адрес", rule="brigade")
    houses = await brain_store.get_houses_by_address(addr, limit=1)
    if not houses:
        return _fail("Дом не найден", rule="brigade")
    h = houses[0]
    brigade = h.brigade_name or (f"Бригада {h.brigade_number}" if h.brigade_number else None)
    if not brigade:
        return _fail("Бригада не указана", rule="brigade")
    answer = f"🏠 Адрес: {h.title or h.address}\nБригада: {brigade}"
    if h.bitrix_url:
        answer += f"\nСсылка в Bitrix: {h.bitrix_url}"
    return _success(answer, data={"brigade_name": brigade}, sources={"addr": addr}, rule="brigade")


async def resolve_finance_basic(text: str, db: Any) -> Optional[Dict[str, Any]]:
    tl = (text or "").lower()
    if not any(k in tl for k in ["финанс", "расход", "доход", "прибыль", "пнл", "p&amp;l", "cashflow", "деньги"]):
        return None
    agg = await brain_store.get_finance_aggregate(db)
    income = agg.get("income", 0.0)
    expense = agg.get("expense", 0.0)
    profit = income - expense
    answer = f"Финансы (последний период):\nДоход: {income:.2f}\nРасход: {expense:.2f}\nПрибыль: {profit:.2f}"
    return _success(answer, data=agg, sources={}, rule="finance_basic")