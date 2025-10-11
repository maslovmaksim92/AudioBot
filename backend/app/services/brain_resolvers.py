"""
Brain resolvers (Stage 3/4): fast, rule-based answers without LLM
"""
from __future__ import annotations

from typing import Any, Dict, Optional, List
import logging
from datetime import date, timedelta

from backend.app.services.brain_store import brain_store
from backend.app.services.brain import (
    parse_address_candidate,
    detect_month_key,
    format_cleaning_for_month,
    format_elder_contact,
    CleaningDates,
    CleaningPeriod,
)
from backend.app.services.brain_math import compute_finance_basic, compute_structural_totals

logger = logging.getLogger(__name__)


def _success(answer: str, data: Optional[Dict[str, Any]] = None, sources: Optional[Dict[str, Any]] = None, rule: str = "") -> Dict[str, Any]:
    return {"success": True, "answer": answer, "data": data or {}, "sources": sources or {}, "rule": rule}


def _fail(reason: str, rule: str = "") -> Dict[str, Any]:
    return {"success": False, "error": reason, "rule": rule}


async def resolve_elder_contact(text: str, ent: Optional[Dict[str, Any]] = None) -> Optional[Dict[str, Any]]:
    tl = (text or "").lower()
    want_contacts = any(k in tl for k in ["контакт", "телефон", "почта", "email"]) and ("старш" in tl)
    if not want_contacts and not (ent and ent.get("type") == "elder_contact"):
        return None
    addr = (ent and ent.get("address")) or parse_address_candidate(text)
    if not addr:
        return _fail("Не удалось распознать адрес", rule="elder_contact")

    elder = await brain_store.get_elder_contact_by_address(addr)
    if not elder:
        return _fail("Контакты старшего не найдены", rule="elder_contact")

    houses = await brain_store.get_houses_by_address(addr, limit=1)
    h = houses[0] if houses else None
    answer = format_elder_contact(elder.name, elder.phones, elder.emails)
    if h and h.bitrix_url:
        answer = f"{answer}\nСсылка в Bitrix: {h.bitrix_url}"
    return _success(answer, data={"elder": elder.__dict__}, sources={"addr": addr}, rule="elder_contact")


async def resolve_cleaning_month(text: str, ent: Optional[Dict[str, Any]] = None) -> Optional[Dict[str, Any]]:
    tl = (text or "").lower()
    if "уборк" not in tl and not (ent and ent.get("type") == "cleaning_month"):
        return None
    addr = (ent and ent.get("address")) or parse_address_candidate(text)
    if not addr:
        return _fail("Не удалось распознать адрес", rule="cleaning_month")
    month_key = (ent and ent.get("month_key")) or detect_month_key(text) or "october"
    period_idx = ent and ent.get("period_idx")

    cd: Optional[CleaningDates] = await brain_store.get_cleaning_for_month_by_address(addr, month_key)
    if not cd:
        return _fail("Нет данных по графику уборок", rule="cleaning_month")

    # 1:1 формат по датам. Если указан период (1/2) — выводим только его
    def _lines_for_slot(slot: Optional[CleaningPeriod]) -> List[str]:
        lines: List[str] = []
        if isinstance(slot, CleaningPeriod) and slot.dates:
            t = (slot.type or "").strip()
            for d in slot.dates:
                lines.append(f"{d} — {t}" if t else str(d))
        return lines

    lines: List[str] = []
    if period_idx == 1:
        slot = getattr(cd, f"{month_key}_1", None)
        lines = _lines_for_slot(slot)
    elif period_idx == 2:
        slot = getattr(cd, f"{month_key}_2", None)
        lines = _lines_for_slot(slot)
    else:
        # оба периода
        for slot in [getattr(cd, f"{month_key}_1", None), getattr(cd, f"{month_key}_2", None)]:
            lines.extend(_lines_for_slot(slot))

    if not lines:
        return _fail("Нет дат по указанному месяцу", rule="cleaning_month")

    houses = await brain_store.get_houses_by_address(addr, limit=1)
    h = houses[0] if houses else None
    intro = f"🏠 Адрес: {h.title if h else addr}"
    if h and h.periodicity:
        intro += f"\nПериодичность: {h.periodicity}"
    answer = f"{intro}\n" + "\n".join(lines)
    if h and h.bitrix_url:
        answer += f"\nСсылка в Bitrix: {h.bitrix_url}"
    return _success(answer, data={"month": month_key, "period": period_idx}, sources={"addr": addr}, rule="cleaning_month")


async def resolve_brigade_by_address(text: str, ent: Optional[Dict[str, Any]] = None) -> Optional[Dict[str, Any]]:
    tl = (text or "").lower()
    if ("бригад" not in tl and "ответствен" not in tl) and not (ent and ent.get("type") == "brigade"):
        return None
    addr = (ent and ent.get("address")) or parse_address_candidate(text)
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


async def resolve_finance_basic(text: str, db: Any, ent: Optional[Dict[str, Any]] = None) -> Optional[Dict[str, Any]]:
    tl = (text or "").lower()
    if not any(k in tl for k in ["финанс", "расход", "доход", "прибыль", "пнл", "p&amp;l", "cashflow", "деньги"]) and not (ent and ent.get("type") == "finance_basic"):
        return None

    # detect time window
    range_days = ent and ent.get("range_days")
    date_from = None
    date_to = None
    if range_days:
        date_to = date.today().isoformat()
        date_from = (date.today() - timedelta(days=int(range_days))).isoformat()

    agg = await compute_finance_basic(db, date_from=date_from, date_to=date_to)
    answer = f"Финансы ({'за ' + str(range_days) + ' дней' if range_days else 'период по умолчанию'}):\nДоход: {agg.income:.2f}\nРасход: {agg.expense:.2f}\nПрибыль: {agg.profit:.2f}"
    return _success(answer, data={"aggregate": agg.__dict__, "date_from": date_from, "date_to": date_to}, sources={}, rule="finance_basic")


async def resolve_structural_totals(text: str, db: Any, ent: Optional[Dict[str, Any]] = None) -> Optional[Dict[str, Any]]:
    tl = (text or "").lower()
    if not any(k in tl for k in ["этаж", "подъезд", "квартир", "апартамент"]) and not (ent and ent.get("type") == "structural_totals"):
        return None
    totals = await compute_structural_totals(db)
    answer = f"Суммарно по домам:\nЭтажей: {totals['floors']}\nПодъездов: {totals['entrances']}\nКвартир: {totals['apartments']}"
    return _success(answer, data=totals, sources={}, rule="structural_totals")