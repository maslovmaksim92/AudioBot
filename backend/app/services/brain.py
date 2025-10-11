"""
Address parser improvements for corps/building markers (Stage 5)
"""
from __future__ import annotations

from typing import Optional
import re

# Patch normalize_address and parse_address_candidate in-place
from backend.app.services.brain import normalize_address as _norm_base, parse_address_candidate as _parse_base


def normalize_address(text: Optional[str]) -> str:
    s = _norm_base(text)
    # add building/corpus markers mapping
    s = s.replace('стр.', 'стр').replace('строение', 'стр')
    s = s.replace('литера', 'лит')
    s = re.sub(r"\s+", " ", s).strip()
    return s


def parse_address_candidate(text: Optional[str]) -> Optional[str]:
    cand = _parse_base(text)
    if cand:
        return normalize_address(cand)
    return None