"""
Improve address NER (Stage 6): handle free forms like "стр 1", "к1", "лит А"
"""
from __future__ import annotations

from typing import Optional
import re


_ADDR_STOPWORDS = {
    "контакт", "контакты", "старшего", "старший", "телефон", "почта", "email",
    "номер", "по", "адресу", "на", "—", "-",
    # general query words to strip from address extraction
    "уборка", "уборки", "график", "расписан", "когда", "дат", "дата", "даты",
    "нужно", "интересует", "покажи", "сколько", "какая", "где", "месяц",
    # month words to avoid polluting address candidates
    "октябрь", "ноябрь", "декабрь", "окт", "ноя", "дек",
}


def _normalize_address_base(text: Optional[str]) -> str:
    """Base address normalization"""
    if not text:
        return ""
    
    # Basic cleanup
    s = str(text).strip().lower()
    s = re.sub(r"\s+", " ", s)
    return s


def _parse_address_candidate_base(text: Optional[str]) -> Optional[str]:
    """Base address parsing"""
    if not text:
        return None
    
    # Look for address patterns
    s = str(text).strip()
    if any(marker in s.lower() for marker in ["ул", "улица", "пр", "проспект", "д", "дом"]):
        return s
    
    return None


def normalize_address(text: Optional[str]) -> str:
    s = _normalize_address_base(text)
    if not s:
        return s
    # normalize corpus/building markers
    s = re.sub(r"\bк\.?\s*(\w+)", r"к \1", s)
    s = re.sub(r"\bкорп\.?\s*(\w+)", r"к \1", s)
    s = re.sub(r"\bстр\.?\s*(\w+)", r"стр \1", s)
    s = re.sub(r"\bстроен\w*\s*(\w+)", r"стр \1", s)
    s = re.sub(r"\bлит\.?\s*([a-zа-я])", r"лит \1", s)
    s = re.sub(r"\s+", " ", s).strip()
    return s


def parse_address_candidate(text: Optional[str]) -> Optional[str]:
    cand = _parse_address_candidate_base(text)
    if cand:
        return normalize_address(cand)
    return None