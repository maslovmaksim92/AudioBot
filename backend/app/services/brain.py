"""
Brain DTOs and utilities: address normalization, data structures
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any
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


# DTOs

@dataclass
class ElderContact:
    """Контакт старшего по дому"""
    name: str = ""
    phones: List[str] = field(default_factory=list)
    emails: List[str] = field(default_factory=list)
    
    def is_empty(self) -> bool:
        return not self.name and not self.phones and not self.emails


@dataclass
class CompanyInfo:
    """Информация об управляющей компании"""
    id: Optional[str] = None
    title: str = ""
    phones: List[str] = field(default_factory=list)
    emails: List[str] = field(default_factory=list)


@dataclass
class CleaningDates:
    """Даты уборок по месяцам"""
    october_1: Optional[Dict[str, Any]] = None
    october_2: Optional[Dict[str, Any]] = None
    november_1: Optional[Dict[str, Any]] = None
    november_2: Optional[Dict[str, Any]] = None
    december_1: Optional[Dict[str, Any]] = None
    december_2: Optional[Dict[str, Any]] = None
    
    @staticmethod
    def from_dict(data: Dict[str, Any]) -> 'CleaningDates':
        return CleaningDates(
            october_1=data.get('october_1'),
            october_2=data.get('october_2'),
            november_1=data.get('november_1'),
            november_2=data.get('november_2'),
            december_1=data.get('december_1'),
            december_2=data.get('december_2'),
        )
    
    def get_for_month(self, month: str) -> List[Dict[str, Any]]:
        """Получить даты для заданного месяца (october/november/december)"""
        month_lower = month.lower()
        result = []
        if 'oct' in month_lower or 'окт' in month_lower:
            if self.october_1:
                result.append(('Первая половина октября', self.october_1))
            if self.october_2:
                result.append(('Вторая половина октября', self.october_2))
        elif 'nov' in month_lower or 'ноя' in month_lower:
            if self.november_1:
                result.append(('Первая половина ноября', self.november_1))
            if self.november_2:
                result.append(('Вторая половина ноября', self.november_2))
        elif 'dec' in month_lower or 'дек' in month_lower:
            if self.december_1:
                result.append(('Первая половина декабря', self.december_1))
            if self.december_2:
                result.append(('Вторая половина декабря', self.december_2))
        return result


@dataclass
class HouseDTO:
    """Дом с полной информацией"""
    id: str
    title: str
    address: str
    brigade_name: Optional[str] = None
    brigade_number: Optional[str] = None
    assigned_by_id: Optional[str] = None
    management_company: Optional[str] = None
    status: Optional[str] = None
    cleaning_dates: Optional[CleaningDates] = None
    periodicity: Optional[str] = None
    bitrix_url: Optional[str] = None
    elder_contact: Optional[ElderContact] = None
    company: Optional[CompanyInfo] = None


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