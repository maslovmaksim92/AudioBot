"""
Improve address NER (Stage 6): handle free forms like "стр 1", "к1", "лит А"
"""
from __future__ import annotations

from typing import Optional
import re

from backend.app.services.brain import normalize_address as _norm_base, parse_address_candidate as _parse_base


def normalize_address(text: Optional[str]) -> str:
    s = _norm_base(text)
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
    cand = _parse_base(text)
    if cand:
        return normalize_address(cand)
    return None