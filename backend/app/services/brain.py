"""
Unified "Single Brain" layer (Stage 1):
- Domain DTOs for core entities used by resolvers
- Normalization utilities (addresses, names, months)
- Lightweight formatters for cleaning schedules

This file is intentionally self-contained and does not couple to routers.
Subsequent stages will add aggregation, resolvers and router integration.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple
import re
import logging

logger = logging.getLogger(__name__)

# -----------------------------
# Domain DTOs (lightweight)
# -----------------------------

@dataclass
class CleaningPeriod:
    dates: List[str] = field(default_factory=list)
    type: str = ""

    def is_empty(self) -> bool:
        return len(self.dates) == 0

@dataclass
class CleaningDates:
    # Month slots follow Bitrix mapping (can be empty)
    october_1: Optional[CleaningPeriod] = None
    october_2: Optional[CleaningPeriod] = None
    november_1: Optional[CleaningPeriod] = None
    november_2: Optional[CleaningPeriod] = None
    december_1: Optional[CleaningPeriod] = None
    december_2: Optional[CleaningPeriod] = None

    @staticmethod
    def from_dict(d: Dict[str, Any]) -> "CleaningDates":
        def _cp(x: Any) -> Optional[CleaningPeriod]:
            if not isinstance(x, dict):
                return None
            dates = x.get("dates") or []
            ctype = x.get("type") or ""
            if not dates and not ctype:
                return None
            return CleaningPeriod(dates=list(map(str, dates)), type=str(ctype))

        return CleaningDates(
            october_1=_cp(d.get("october_1")),
            october_2=_cp(d.get("october_2")),
            november_1=_cp(d.get("november_1")),
            november_2=_cp(d.get("november_2")),
            december_1=_cp(d.get("december_1")),
            december_2=_cp(d.get("december_2")),
        )

    def month_slots(self) -> List[Tuple[str, CleaningPeriod]]:
        res: List[Tuple[str, CleaningPeriod]] = []
        for key in [
            "october_1", "october_2",
            "november_1", "november_2",
            "december_1", "december_2",
        ]:
            val = getattr(self, key)
            if isinstance(val, CleaningPeriod) and not val.is_empty():
                res.append((key, val))
        return res

@dataclass
class ElderContact:
    name: str = ""
    phones: List[str] = field(default_factory=list)
    emails: List[str] = field(default_factory=list)

    def is_empty(self) -> bool:
        return not self.name and not self.phones and not self.emails

@dataclass
class CompanyInfo:
    id: Optional[str] = None
    title: str = ""
    phones: List[str] = field(default_factory=list)
    emails: List[str] = field(default_factory=list)

@dataclass
class HouseDTO:
    id: str
    title: str
    address: str
    brigade_name: Optional[str] = None
    brigade_number: Optional[str] = None
    assigned_by_id: Optional[str] = None
    management_company: Optional[str] = None
    status: Optional[str] = None
    cleaning_dates: CleaningDates = field(default_factory=CleaningDates)
    periodicity: Optional[str] = None
    bitrix_url: Optional[str] = None
    elder_contact: Optional[ElderContact] = None
    company: Optional[CompanyInfo] = None

# -----------------------------
# Normalization & Parsing utils
# -----------------------------

_ADDR_STOPWORDS = {
    "контакт", "контакты", "старшего", "старший", "телефон", "почта", "email",
    "номер", "по", "адресу", "на", "—", "-",
}

_MONTH_ALIASES = {
    # russian month roots to canonical month key
    "окт": "october",
    "ноя": "november",
    "дек": "december",
}

_period_aliases = {
    # phrases pointing to first/second slots within month
    # not strict, just hints
    "перв": 1,
    "1 ": 1,
    "1-": 1,
    "втор": 2,
    "2 ": 2,
    "2-": 2,
}


def normalize_address(text: Optional[str]) -> str:
    """Normalize address for matching: lowercase, trim, unify street/house/corpus markers."""
    if not text:
        return ""
    s = str(text).lower().strip()
    # unify Russian address markers
    repl = [
        ("улица", "ул"), ("ул.", "ул"),
        ("проспект", "пр-кт"), ("просп.", "пр-кт"), ("пр-т", "пр-кт"),
        ("дом", "д"), ("д.", "д"),
        ("корпус", "к"), ("корп.", "к"), ("корп", "к"), ("к.", "к"),
    ]
    for a, b in repl:
        s = s.replace(a, b)
    # remove extra punctuation
    s = s.replace(",", " ").replace(".", " ")
    s = re.sub(r"\s+", " ", s).strip()
    return s


def parse_address_candidate(text: Optional[str]) -> Optional[str]:
    """Extract best-effort address candidate from a user text.
    Patterns:
    - "на <...> в ...", "на <...>?"
    - "по адресу <...>"
    - fallback: window around first token that looks like a house number
    """
    if not text:
        return None
    try:
        s = str(text).lower().replace("\n", " ").strip()
        # explicit patterns
        m = re.search(r"на\s+(.+?)(?:\s+в\s|\?|!|\.|$)", s)
        if not m:
            m = re.search(r"по\s+адресу\s+(.+?)(?:\s+в\s|\?|!|\.|$)", s)
        if m:
            cand = m.group(1).strip(" ,.!?")
            parts = [p for p in cand.split() if p]
            if len(parts) > 7:
                parts = parts[:7]
            return normalize_address(" ".join(parts))

        tokens = [t for t in re.split(r"[^\wа-яё]+", s) if t]
        # improve: if a house-like number found, try to pair with preceding non-stopword token as street
        for i, t in enumerate(tokens):
            if re.match(r"^\d+[а-яa-z]*$", t):
                street = None
                for j in range(i - 1, max(-1, i - 4), -1):
                    if j >= 0 and tokens[j] not in _ADDR_STOPWORDS and tokens[j].strip():
                        street = tokens[j]
                        break
                if street:
                    return normalize_address(f"{street} {t}")
                # fallback window
                left = [w for w in tokens[max(0, i - 2):i] if w not in _ADDR_STOPWORDS]
                right = [tokens[i + 1]] if i + 1 < len(tokens) else []
                cand = " ".join(left + [t] + right)
                if len(cand) >= 3:
                    return normalize_address(cand)
    except Exception as e:
        logger.warning(f"parse_address_candidate failed: {e}")
    return None


def detect_month_key(text: Optional[str]) -> Optional[str]:
    """Return canonical month key (october|november|december) if present in text."""
    if not text:
        return None
    s = str(text).lower()
    for root, key in _MONTH_ALIASES.items():
        if root in s:
            return key
    return None


def detect_period_index(text: Optional[str]) -> Optional[int]:
    """Try to infer first/second period (1 or 2) from text if present."""
    if not text:
        return None
    s = str(text).lower()
    for token, idx in _period_aliases.items():
        if token in s:
            return idx
    return None


# -----------------------------
# Formatters
# -----------------------------

def format_cleaning_for_month(cleaning: CleaningDates, month_key: str) -> Optional[str]:
    """Return formatted text for a given month (october|november|december)."""
    slots = []
    if month_key == "october":
        slots = [cleaning.october_1, cleaning.october_2]
    elif month_key == "november":
        slots = [cleaning.november_1, cleaning.november_2]
    elif month_key == "december":
        slots = [cleaning.december_1, cleaning.december_2]

    parts: List[str] = []
    labels = ["october_1", "october_2", "november_1", "november_2", "december_1", "december_2"]
    # Keep original slot ids to avoid confusion for now; can map to human labels later
    for idx, slot in enumerate(slots, start=1):
        if isinstance(slot, CleaningPeriod) and slot.dates:
            label = f"{month_key}_{idx}"
            dates_txt = ", ".join(slot.dates)
            t = slot.type.strip()
            parts.append(f"{label}: {dates_txt}{(' — ' + t) if t else ''}")
    if not parts:
        return None
    return "\n".join(parts)


def format_elder_contact(name: str, phones: List[str], emails: List[str]) -> str:
    lines = [f"Старший: {name or 'не указан'}"]
    if phones:
        lines.append(f"Телефон(ы): {', '.join(phones)}")
    if emails:
        lines.append(f"Email: {', '.join(emails)}")
    return "\n".join(lines)


__all__ = [
    "CleaningPeriod",
    "CleaningDates",
    "ElderContact",
    "CompanyInfo",
    "HouseDTO",
    "normalize_address",
    "parse_address_candidate",
    "detect_month_key",
    "detect_period_index",
    "format_cleaning_for_month",
    "format_elder_contact",
]
