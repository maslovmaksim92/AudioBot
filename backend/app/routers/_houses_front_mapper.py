"""
Маппер: строка БД House -> формат, который ожидает фронтенд (Works.js) и дашборд.

Делает данные автономными от Bitrix24: страница "Дома", график уборок и MAX-отчёты
читают из одной таблицы houses. Bitrix остаётся фоновым синхронизатором.
"""
from typing import Any, Dict, List, Optional

MONTHS_NUM2EN = {
    1: "january", 2: "february", 3: "march", 4: "april", 5: "may", 6: "june",
    7: "july", 8: "august", 9: "september", 10: "october", 11: "november", 12: "december",
}
MONTHS_RU = {
    1: "Январь", 2: "Февраль", 3: "Март", 4: "Апрель", 5: "Май", 6: "Июнь",
    7: "Июль", 8: "Август", 9: "Сентябрь", 10: "Октябрь", 11: "Ноябрь", 12: "Декабрь",
}


def _portal_base() -> Optional[str]:
    try:
        from backend.app.services.bitrix24_service import bitrix24_service
        pb = (bitrix24_service.portal_base or "").strip()
        if pb.startswith(("http://", "https://")) and "." in pb:
            return pb.rstrip("/")
    except Exception:
        pass
    return None


def _bitrix_url(bitrix_id: Optional[str]) -> Optional[str]:
    if not bitrix_id:
        return None
    pb = _portal_base()
    if not pb:
        return None
    return f"{pb}/crm/deal/details/{bitrix_id}/"


def _classify_type(text: str) -> str:
    """Тип уборки -> короткий код: wash_all / wash_1 / sweep_wash."""
    t = (text or "").lower()
    if "подметание" in t and "всех этаж" in t:
        return "sweep_wash"          # подметание всех + мытьё 1 этажа
    if "лестничных площадок всех этаж" in t:
        return "wash_all"            # мытьё всех этажей
    if "1 этаж" in t:
        return "wash_1"              # мытьё 1 этажа
    return "other"


def _periodicity_for_month(items: List[dict]) -> str:
    """
    Периодичность за конкретный месяц по числу уборок и их типам.
    Возвращает терминологию заказчика: '2 мытья', '2 подметания + 2 мытья',
    '4 мытья', '2 мытья + 1 этаж' и т.п.
    """
    if not items:
        return "—"
    codes = [_classify_type(it.get("type", "")) for it in items]
    n = len(codes)
    n_wash_all = codes.count("wash_all")
    n_wash_1 = codes.count("wash_1")
    n_sweep = codes.count("sweep_wash")

    parts = []
    if n_sweep:
        parts.append(f"{n_sweep} подметани{'е' if n_sweep == 1 else 'я'}")
    if n_wash_all:
        parts.append(f"{n_wash_all} мыть{'ё' if n_wash_all == 1 else 'я' if n_wash_all < 5 else 'ё'} всех этажей")
    if n_wash_1:
        parts.append(f"{n_wash_1} мыть{'ё' if n_wash_1 == 1 else 'я'} 1 этажа")
    if not parts:
        return f"{n} убор{'ка' if n == 1 else 'ки' if n < 5 else 'ок'}"
    return " + ".join(parts)


def _schedule_to_cleaning_dates(cleaning_schedule: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    out: Dict[str, Any] = {}
    if not cleaning_schedule or not isinstance(cleaning_schedule, dict):
        return out
    for key, items in cleaning_schedule.items():
        if not isinstance(items, list) or not items:
            continue
        dates: List[str] = []
        type_text = ""
        types: List[str] = []
        for it in items:
            if not isinstance(it, dict):
                continue
            d = it.get("date")
            if d:
                dates.append(d)
            if it.get("type"):
                types.append(it["type"])
                if not type_text:
                    type_text = it["type"]
        if dates:
            out[key] = {
                "dates": sorted(dates),
                "type": type_text,
                "types": types,
                "periodicity": _periodicity_for_month(items),
            }
    return out


def house_to_front(h, month_key: Optional[str] = None) -> Dict[str, Any]:
    """
    SQLAlchemy House -> dict формата фронта.
    Если month_key задан (напр. 'may_2026') — периодичность считается для этого месяца.
    """
    cleaning_dates = _schedule_to_cleaning_dates(getattr(h, "cleaning_schedule", None))
    brigade = getattr(h, "brigade_number", None)
    brigade_name = f"{brigade} бригада" if brigade else "Бригада не назначена"

    # периодичность: за выбранный месяц, иначе за самый поздний доступный
    if month_key and month_key in cleaning_dates:
        periodicity = cleaning_dates[month_key].get("periodicity", "—")
    elif cleaning_dates:
        last_key = sorted(cleaning_dates.keys(),
                          key=lambda k: (k.split("_")[-1], k))[-1]
        periodicity = cleaning_dates[last_key].get("periodicity", "—")
    else:
        periodicity = "не указана"

    return {
        "id": str(h.id),
        "bitrix_id": getattr(h, "bitrix_id", None),
        "title": h.address,
        "address": h.address,
        "management_company": getattr(h, "company_title", None) or "",
        "brigade_name": brigade_name,
        "brigade_number": brigade,
        "assigned_by_name": getattr(h, "assigned_by_name", None) or brigade_name,
        "apartments": getattr(h, "apartments_count", None) or 0,
        "entrances": getattr(h, "entrances_count", None) or 0,
        "floors": getattr(h, "floors_count", None) or 0,
        "tariff": getattr(h, "tariff", None) or "",
        "amount_monthly": float(getattr(h, "amount_monthly", None) or 0) or None,
        "notes": getattr(h, "notes", None) or "",
        "elder_contact": getattr(h, "elder_contact", None) or "",
        "service_start_date": getattr(h, "service_start_date", None) or "",
        "bitrix_url": _bitrix_url(getattr(h, "bitrix_id", None)),
        "cleaning_dates": cleaning_dates,
        "periodicity": periodicity,
        "selected_month": month_key,
        "last_cleaning": getattr(h, "last_cleaning", None).isoformat() if getattr(h, "last_cleaning", None) else None,
    }


def house_to_details(h) -> Dict[str, Any]:
    base = house_to_front(h)
    base["all_schedule"] = getattr(h, "cleaning_schedule", None) or {}
    return base
