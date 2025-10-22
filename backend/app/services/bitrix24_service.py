"""
Bitrix24 service: listing houses, brigade/assigned resolution, enums, details
"""
from __future__ import annotations

import asyncio
import logging
import re
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple
from urllib.parse import urlparse
from uuid import uuid4

import httpx
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.config.settings import settings
from backend.app.models.house import House

logger = logging.getLogger(__name__)


class TTLCache:
    def __init__(self, ttl_seconds: int):
        self.ttl = ttl_seconds
        self.store: Dict[str, Tuple[float, Any]] = {}

    def get(self, key: str) -> Any:
        rec = self.store.get(key)
        if not rec:
            return None
        ts, val = rec
        if (datetime.now(timezone.utc).timestamp() - ts) > self.ttl:
            self.store.pop(key, None)
            return None
        return val

    def set(self, key: str, val: Any):
        self.store[key] = (datetime.now(timezone.utc).timestamp(), val)


def _portal_base(webhook_url: str) -> str:
    try:
        u = urlparse(webhook_url)
        return f"{u.scheme}://{u.netloc}"
    except Exception:
        return webhook_url.rstrip('/')


class Bitrix24Service:
    def __init__(self):
        self.webhook_url = settings.BITRIX24_WEBHOOK_URL.rstrip('/') + '/'
        self.timeout = httpx.Timeout(40.0)
        self.max_retries = 3
        self.company_cache = TTLCache(int(getattr(settings, 'BITRIX_COMPANY_CACHE_TTL', 1800)))
        self.user_cache = TTLCache(int(getattr(settings, 'BITRIX_USER_CACHE_TTL', 600)))
        self.enum_cache = TTLCache(int(getattr(settings, 'BITRIX_ENUM_CACHE_TTL', 3600)))
        self.deals_cache = TTLCache(int(getattr(settings, 'DEALS_CACHE_TTL', 120)))
        self.portal_base = _portal_base(self.webhook_url)
        
        # Rate limiting: максимум 2 одновременных запросов
        self._semaphore = asyncio.Semaphore(2)
        # Минимальная задержка между запросами (секунды)
        self._request_delay = 0.5
        self._last_request_time = 0.0
    def _normalize_address(self, s: Optional[str]) -> Optional[str]:
        if not s:
            return s
        try:
            txt = str(s)
            # remove anything after first pipe "|" (coords, ids etc.)
            if '|' in txt:
                txt = txt.split('|', 1)[0]
            return txt.strip().strip(',')
        except Exception:
            return s

    def _prefer_brigade_from_text(self, assigned_by_name: Optional[str], assigned_info: Optional[Dict[str, Any]]) -> Tuple[Optional[str], Optional[str]]:
        """Return (brigade_label, brigade_number). Prefer numeric like 'N бригада'. Avoid FIO.
        """
        # 1) Try raw ASSIGNED_BY_NAME (often contains 'N бригада')
        num = self._parse_brigade_number(assigned_by_name or '')
        if num:
            return (f"{num} бригада", num)
        # 2) Try to parse from assigned_info full_name (rare, but just in case)
        if assigned_info:
            full = (assigned_info.get('full_name') or '')
            num2 = self._parse_brigade_number(full)
            if num2:
                return (f"{num2} бригада", num2)
        # 3) Fallback: brigade unknown
        return (None, None)

    def _compute_periodicity(self, cleaning_dates: Dict[str, Any]) -> str:
        """
        Расчет периодичности по всем датам уборок согласно спецификации.
        
        3 типа уборок:
        - Тип 1: Влажная уборка лестничных площадок всех этажей
        - Тип 2: Подметание лестничных площадок и маршей всех этажей
        - Тип 3: Влажная уборка 1 этажа
        
        Правила расчёта:
        - 2 даты Тип 1 → "2 раза"
        - 4 даты Тип 1 → "4 раза"
        - 2 даты Тип 1 + 2 даты Тип 2 → "2 раза + 2 подметания"
        - 2 даты Тип 1 + 2 даты Тип 3 → "2 раза + 1 этаж"
        - Другое сочетание → "индивидуальная"
        - Нет дат → "не указана"
        """
        import logging
        logger = logging.getLogger(__name__)
        
        if not cleaning_dates:
            logger.info("[_compute_periodicity] No cleaning dates provided")
            return "не указана"
        
        # Считаем только по ТЕКУЩЕМУ или ПОСЛЕДНЕМУ месяцу в данных
        # Ищем месяц с данными (берем первый найденный месяц)
        month_periods = {}
        
        for period_name, period_data in cleaning_dates.items():
            if not isinstance(period_data, dict):
                continue
            
            dates = period_data.get('dates') or []
            if not dates:
                continue
            
            # Извлекаем месяц из первой даты периода
            first_date = dates[0] if dates else None
            if first_date:
                # Даты могут быть строками или dict
                if isinstance(first_date, dict):
                    date_str = first_date.get('date', '')
                else:
                    date_str = str(first_date)
                
                if date_str and '-' in date_str:
                    # Формат: 2025-10-13 или 2025-10-13T00:00:00 -> берем год-месяц
                    year_month = '-'.join(date_str.split('T')[0].split('-')[:2])  # "2025-10"
                    
                    if year_month not in month_periods:
                        month_periods[year_month] = []
                    
                    month_periods[year_month].append({
                        'period_name': period_name,
                        'dates': dates,
                        'type': period_data.get('type', '')
                    })
        
        # Если нет данных по месяцам, возвращаем "не указана"
        if not month_periods:
            logger.info("[_compute_periodicity] No valid month periods found")
            return "не указана"
        
        # Берем первый доступный месяц (обычно текущий или ближайший)
        month = sorted(month_periods.keys())[-1]  # Последний месяц
        periods = month_periods[month]
        
        logger.info(f"[_compute_periodicity] Analyzing month: {month} with {len(periods)} periods")
        
        type1_count = 0  # Влажная уборка всех этажей
        type2_count = 0  # Подметание
        type3_count = 0  # Влажная уборка 1 этажа
        
        # Анализируем периоды ТОЛЬКО выбранного месяца
        for period in periods:
            period_name = period['period_name']
            dates = period['dates']
            type_text = period['type'].lower()
            num_dates = len(dates)
            
            logger.debug(f"[_compute_periodicity] Period: {period_name}, Type: '{type_text}', Dates: {num_dates}")
            
            # Определяем тип уборки по ключевым словам
            # Тип 1: Влажная + всех этажей
            if 'влажная' in type_text and ('всех этаж' in type_text or 'лестничных площадок всех' in type_text):
                type1_count += num_dates
                logger.debug(f"[_compute_periodicity] Type 1 detected: +{num_dates} dates")
            # Тип 2: Подметание
            elif 'подмет' in type_text:
                type2_count += num_dates
                logger.debug(f"[_compute_periodicity] Type 2 detected: +{num_dates} dates")
            # Тип 3: Влажная + 1 этаж (БЕЗ подметания)
            elif 'влажная' in type_text and ('1 этаж' in type_text or '1-го этажа' in type_text or 'первого этажа' in type_text):
                type3_count += num_dates
                logger.debug(f"[_compute_periodicity] Type 3 detected: +{num_dates} dates")
        
        logger.info(f"[_compute_periodicity] Counts - Type1: {type1_count}, Type2: {type2_count}, Type3: {type3_count}")
        
        total = type1_count + type2_count + type3_count
        
        if total == 0:
            logger.info("[_compute_periodicity] No valid dates found")
            return "не указана"
        
        # Применяем правила согласно требованиям
        
        # Только Тип 1 (влажная уборка всех этажей)
        if type1_count > 0 and type2_count == 0 and type3_count == 0:
            result = f"{type1_count} раза" if type1_count in [2, 3, 4] else f"{type1_count} раз"
            logger.info(f"[_compute_periodicity] Result: '{result}' (only Type 1)")
            return result
        
        # Тип 1 + Тип 2 (влажная + подметание)
        if type1_count > 0 and type2_count > 0 and type3_count == 0:
            t1_word = "раза" if type1_count in [2, 3, 4] else "раз"
            # БЕЗ количества для подметания!
            result = f"{type1_count} {t1_word} + подметания"
            logger.info(f"[_compute_periodicity] Result: '{result}' (Type 1 + Type 2)")
            return result
        
        # Тип 1 + Тип 3 (влажная всех этажей + влажная 1 этаж)
        if type1_count > 0 and type3_count > 0 and type2_count == 0:
            t1_word = "раза" if type1_count in [2, 3, 4] else "раз"
            # ВСЕГДА "1 этажи" независимо от количества!
            result = f"{type1_count} {t1_word} + 1 этажи"
            logger.info(f"[_compute_periodicity] Result: '{result}' (Type 1 + Type 3)")
            return result
        
        # Все три типа или другие нестандартные сочетания
        if type1_count > 0 or type2_count > 0 or type3_count > 0:
            result = "индивидуальная"
            logger.info(f"[_compute_periodicity] Result: '{result}' (mixed/custom)")
            return result
        
        # Не должны сюда дойти, но на всякий случай
        logger.warning("[_compute_periodicity] Unexpected case, returning 'не указана'")
        return "не указана"


    async def _make_request(self, client: httpx.AsyncClient, method: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Выполнить запрос к Bitrix24 API с rate limiting и обработкой 503 ошибок"""
        url = f"{self.webhook_url}{method}"
        select_fields = payload.get('select') or []
        
        # Используем семафор для ограничения одновременных запросов
        async with self._semaphore:
            # Добавляем задержку между запросами
            current_time = asyncio.get_event_loop().time()
            time_since_last = current_time - self._last_request_time
            if time_since_last < self._request_delay:
                await asyncio.sleep(self._request_delay - time_since_last)
            self._last_request_time = asyncio.get_event_loop().time()
            
            for attempt in range(1, self.max_retries + 1):
                try:
                    query = []
                    if 'filter' in payload and isinstance(payload['filter'], dict):
                        for k, v in payload['filter'].items():
                            query.append((f"filter[{k}]", v))
                    if 'order' in payload and isinstance(payload['order'], dict):
                        for k, v in payload['order'].items():
                            query.append((f"order[{k}]", v))
                    query.append(('start', payload.get('start', 0)))
                    if 'limit' in payload:
                        query.append(('limit', payload['limit']))
                    for f in select_fields:
                        query.append(("select[]", f))
                    
                    resp = await client.get(url, params=query, timeout=self.timeout)
                    
                    # Обработка 503 ошибок (rate limiting)
                    if resp.status_code == 503:
                        wait_time = min(2.0 ** attempt, 10.0)  # Exponential backoff: 2, 4, 8 секунд
                        logger.warning(f"Bitrix24 rate limit (503) for {method}, waiting {wait_time}s (attempt {attempt}/{self.max_retries})")
                        await asyncio.sleep(wait_time)
                        continue
                    
                    if resp.status_code == 200:
                        j = resp.json()
                        return {
                            'ok': True,
                            'result': j.get('result') or [],
                            'next': j.get('next'),
                            'total': j.get('total'),
                        }
                    
                    # Для других ошибок пробуем POST
                    if resp.status_code != 200:
                        resp2 = await client.post(url, json=payload, timeout=self.timeout)
                        
                        if resp2.status_code == 503:
                            wait_time = min(2.0 ** attempt, 10.0)
                            logger.warning(f"Bitrix24 rate limit (503) for {method} POST, waiting {wait_time}s")
                            await asyncio.sleep(wait_time)
                            continue
                        
                        if resp2.status_code == 200:
                            j = resp2.json()
                            return {
                                'ok': True,
                                'result': j.get('result') or [],
                                'next': j.get('next'),
                                'total': j.get('total'),
                            }
                
                except Exception as e:
                    logger.warning(f"Bitrix {method} attempt {attempt} error: {e}")
                
                # Задержка перед следующей попыткой
                if attempt < self.max_retries:
                    await asyncio.sleep(min(0.5 * attempt, 2.0))
            
            logger.error(f"Bitrix {method} failed after {self.max_retries} attempts")
            return {'ok': False, 'result': [], 'next': None, 'total': None}

    async def _company_title(self, client: httpx.AsyncClient, company_id: Any) -> Optional[str]:
        """Получить название компании по ID с кэшированием"""
        # Проверяем, что company_id валидный
        if not company_id:
            return None
        
        # Проверяем, что это число или строка с числом
        try:
            company_id_str = str(company_id).strip()
            if not company_id_str or company_id_str == '0':
                return None
            int(company_id_str)  # Проверяем, что это число
        except (ValueError, AttributeError):
            logger.warning(f"Invalid company_id: {company_id}")
            return None
        
        key = f"company:{company_id}"
        cached = self.company_cache.get(key)
        if cached is not None:
            return cached
        
        data = await self._make_request(client, 'crm.company.get', {'id': company_id})
        title = None
        if data.get('ok') and isinstance(data.get('result'), dict):
            title = data['result'].get('TITLE')
        self.company_cache.set(key, title)
        return title

    async def _get_enum_map(self, client: httpx.AsyncClient, field_code: str) -> Dict[str, str]:
        key = f"enum:{field_code}"
        cached = self.enum_cache.get(key)
        if cached is not None:
            return cached or {}
        try:
            url = f"{self.webhook_url}crm.deal.userfield.list"
            start = 0
            found = None
            for _ in range(0, 10):
                resp = await client.get(url, params={'start': start, 'filter[FIELD_NAME]': field_code}, timeout=self.timeout)
                if resp.status_code != 200:
                    break
                j = resp.json()
                arr = j.get('result') or []
                for uf in arr:
                    if str(uf.get('FIELD_NAME')) == field_code:
                        found = uf
                        break
                if found:
                    break
                nxt = j.get('next')
                if nxt is None:
                    break
                start = nxt
            if not found:
                resp2 = await client.get(url, timeout=self.timeout)
                if resp2.status_code == 200:
                    j2 = resp2.json()
                    for uf in (j2.get('result') or []):
                        if str(uf.get('FIELD_NAME')) == field_code:
                            found = uf
                            break
            if found:
                mp = {str(it.get('ID')): (it.get('VALUE') or '') for it in (found.get('LIST') or [])}
                # Кешируем только если нашли хотя бы одно значение
                if mp:
                    self.enum_cache.set(key, mp)
                    logger.info(f"Enum cached for {field_code}: {len(mp)} values")
                return mp
        except Exception as e:
            logger.warning(f"enum map load failed for {field_code}: {e}")
        # НЕ кешируем пустой результат - попробуем еще раз при следующем запросе
        return {}

    def _normalize_date(self, s: Any) -> Optional[str]:
        if s is None:
            return None
        try:
            ss = str(s)
            if 'T' in ss:
                return ss.split('T', 1)[0]
            return datetime.fromisoformat(ss).date().isoformat()
        except Exception:
            if isinstance(s, str) and len(s) >= 10:
                return s[:10]
            return None

    async def _collect_month(self, client: httpx.AsyncClient, deal: Dict[str, Any], d_code: str, t_code: str) -> Optional[Dict[str, Any]]:
        date_val = deal.get(d_code)
        type_val = deal.get(t_code)
        if not date_val:
            return None
        dates: List[str] = []
        if isinstance(date_val, list):
            for x in date_val:
                d = self._normalize_date(x)
                if d:
                    dates.append(d)
        else:
            s = str(date_val)
            parts = [p.strip() for p in s.replace(',', ';').split(';') if p.strip()]
            for p in parts:
                d = self._normalize_date(p)
                if d:
                    dates.append(d)
        type_text = ''
        if type_val is not None:
            # Если type_val уже текст (не число), используем его напрямую
            if isinstance(type_val, str) and not type_val.isdigit():
                type_text = type_val
            else:
                # Иначе пытаемся найти в enum_map
                enum_map = await self._get_enum_map(client, t_code)
                if enum_map:
                    type_text = enum_map.get(str(type_val)) or ''
                    
                # Если не нашли в карте - логируем и пробуем альтернативный метод
                if not type_text and str(type_val).isdigit():
                    logger.warning(f"Enum not found for {t_code}, ID={type_val}, trying alternative method")
                    # Пробуем получить значение напрямую из сделки через список
                    try:
                        # Bitrix может хранить список значений прямо в deal
                        if isinstance(deal.get(t_code), dict):
                            type_text = deal[t_code].get('value') or ''
                    except Exception:
                        pass
                    
                    if not type_text:
                        type_text = ''  # Пустая строка если не нашли
        return {'dates': dates, 'type': type_text or ''}

    def _calculate_frequency(self, cleaning_dates: Dict[str, Any]) -> str:
        """Рассчитывает периодичность уборки на основе типов"""
        full_cleanings = 0
        first_floor_cleanings = 0
        
        for period_name, period_data in cleaning_dates.items():
            type_text = (period_data.get('type') or '').lower()
            dates = period_data.get('dates') or []
            
            # Определяем полная уборка или только первый этаж
            if 'всех этажей' in type_text or 'лестничных площадок всех' in type_text:
                full_cleanings += len(dates)
            elif '1 этажа' in type_text or 'первого этажа' in type_text or 'подметание' in type_text:
                first_floor_cleanings += len(dates)
            elif dates:
                # Если не можем определить, считаем как полную
                full_cleanings += len(dates)
        
        # Формируем текст периодичности
        if full_cleanings > 0 and first_floor_cleanings > 0:
            return f"{full_cleanings} раза + первые этажи"
        elif full_cleanings > 0:
            if full_cleanings == 1:
                return "1 раз"
            elif full_cleanings in [2, 3, 4]:
                return f"{full_cleanings} раза"
            else:
                return f"{full_cleanings} раз"
        elif first_floor_cleanings > 0:
            return f"Первые этажи {first_floor_cleanings} раза"
        else:
            return "Не указана"

    async def _build_cleaning_dates(self, client: httpx.AsyncClient, deal: Dict[str, Any]) -> Dict[str, Any]:
        md: Dict[str, Any] = {}
        o1 = await self._collect_month(client, deal, 'UF_CRM_1741593004888', 'UF_CRM_1741593047994')
        o2 = await self._collect_month(client, deal, 'UF_CRM_1741593067418', 'UF_CRM_1741593115407')
        if o1:
            md['october_1'] = o1
        if o2:
            md['october_2'] = o2
        n1 = await self._collect_month(client, deal, 'UF_CRM_1741593156926', 'UF_CRM_1741593210242')
        n2 = await self._collect_month(client, deal, 'UF_CRM_1741593231558', 'UF_CRM_1741593285121')
        if n1:
            md['november_1'] = n1
        if n2:
            md['november_2'] = n2
        d1 = await self._collect_month(client, deal, 'UF_CRM_1741593340713', 'UF_CRM_1741593387667')
        d2 = await self._collect_month(client, deal, 'UF_CRM_1741593408621', 'UF_CRM_1741593452062')
        if d1:
            md['december_1'] = d1
        if d2:
            md['december_2'] = d2
        return md

    async def _get_user_info(self, client: httpx.AsyncClient, user_id: Any) -> Optional[Dict[str, Any]]:
        if not user_id:
            return None
        
        # Проверяем кеш
        cache_key = f"user_{user_id}"
        cached = self.user_cache.get(cache_key)
        if cached:
            return cached
        
        try:
            data = await self._make_request(client, 'user.get', {'filter': {'ID': str(user_id)}})
            arr = data.get('result') or []
            if not arr:
                return None
            u = arr[0]
            name = (u.get('NAME') or '').strip()
            last = (u.get('LAST_NAME') or '').strip()
            second = (u.get('SECOND_NAME') or '').strip()
            full = ' '.join([p for p in [name, last, second] if p]).strip() or (u.get('LOGIN') or '')
            emails = []
            if u.get('EMAIL'):
                emails.append(u.get('EMAIL'))
            phones = []
            for key in ('PERSONAL_PHONE', 'WORK_PHONE', 'PERSONAL_MOBILE'):
                v = u.get(key)
                if v:
                    phones.append(v)
            prof = u.get('WORK_POSITION') or u.get('TITLE')
            dept = u.get('UF_DEPARTMENT')
            user_info = {
                'id': u.get('ID'),
                'name': name,
                'last_name': last,
                'second_name': second,
                'full_name': full,
                'emails': emails,
                'phones': phones,
                'profession': prof,
                'department_ids': dept if isinstance(dept, list) else ([dept] if dept else []),
            }
            # Сохраняем в кеш
            self.user_cache.set(cache_key, user_info)
            return user_info
        except Exception:
            return None

    @staticmethod
    def _parse_brigade_number(text: Optional[str]) -> Optional[str]:
        if not text:
            return None
        s = str(text).lower()
        # patterns: "5 бригада", "бригада 5", "№5", "5-я бригада"
        m = re.search(r"(\d{1,2})\s*(?:-?я)?\s*(?:брига\w*|№)?", s)
        if m:
            return m.group(1)
        return None

    async def get_brigade_options(self) -> List[Dict[str, str]]:
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                payload = {'select': ['ASSIGNED_BY_ID'], 'filter': {'CATEGORY_ID': '34'}, 'order': {'ID': 'DESC'}, 'start': 0, 'limit': 1000}
                data = await self._make_request(client, 'crm.deal.list', payload)
                
                # Собираем уникальные ASSIGNED_BY_ID
                user_ids = set()
                for d in data.get('result') or []:
                    uid = d.get('ASSIGNED_BY_ID')
                    if uid:
                        user_ids.add(str(uid))
                
                # Получаем информацию о каждом пользователе
                opts: Dict[str, str] = {}
                for uid in user_ids:
                    user_info = await self._get_user_info(client, uid)
                    if user_info:
                        full_name = user_info.get('full_name', '').strip()
                        if full_name and 'бригад' in full_name.lower():
                            opts[uid] = full_name
                
                # Формируем список для фильтра
                res: List[Dict[str, str]] = []
                seen_numeric: set[str] = set()
                
                # Добавляем по номерам бригад (1-7)
                for num in ['1', '2', '3', '4', '5', '6', '7']:
                    # Проверяем есть ли бригада с этим номером
                    found = False
                    for k, v in opts.items():
                        if self._parse_brigade_number(v) == num:
                            found = True
                            break
                    
                    if found or True:  # Всегда показываем все 7 бригад
                        res.append({'id': num, 'name': f'{num} бригада'})
                        seen_numeric.add(num)
                
                return res
        except Exception as e:
            logger.error(f"get_brigade_options error: {e}")
            return []

    def _match_brigade(self, item: Dict[str, Any], brigade: str) -> bool:
        if not brigade:
            return True
        val = brigade.strip().lower()
        assigned_name = (item.get('assigned_by_name') or item.get('brigade_name') or '').lower()
        assigned_id = str(item.get('assigned_by_id') or '')
        # id:123 exact
        if val.startswith('id:'):
            return assigned_id == val.split(':', 1)[1]
        # numeric value -> match number inside name like "5" in "5 бригада" or via brigade_number field
        if val.isdigit():
            return (item.get('brigade_number') and str(item.get('brigade_number')) == val) or f"{val} " in assigned_name or assigned_name.startswith(val) or assigned_name.endswith(val)
        # text contains
        return val in assigned_name

    async def _deal_to_house_dto(self, client: httpx.AsyncClient, deal: Dict[str, Any], company_title_enriched: Optional[str]) -> Dict[str, Any]:
        cleaning_dates = await self._build_cleaning_dates(client, deal)
        # Brigade: получаем из user.get (ASSIGNED_BY_ID)
        # Формат: NAME может быть "1 " или "4 бригада", LAST_NAME может быть "бригада" или ""
        assigned_info = await self._get_user_info(client, deal.get('ASSIGNED_BY_ID'))
        brigade_label = None
        
        if assigned_info:
            name = (assigned_info.get('name') or '').strip()
            last_name = (assigned_info.get('last_name') or '').strip()
            full_name = f"{name} {last_name}".strip()
            
            # Проверяем, является ли это бригадой (содержит слово "бригада")
            if 'бригад' in full_name.lower():
                # Формируем название бригады
                if last_name.lower() == 'бригада' and name:
                    # Случай: NAME="1 ", LAST_NAME="бригада" → "1 бригада"
                    brigade_label = f"{name} {last_name}"
                else:
                    # Случай: NAME="4 бригада", LAST_NAME="" → "4 бригада"
                    brigade_label = full_name
        
        # Если бригада не найдена через user.get, пробуем ASSIGNED_BY_NAME
        if not brigade_label:
            assigned_by_name = (deal.get('ASSIGNED_BY_NAME') or '').strip()
            if assigned_by_name and 'бригад' in assigned_by_name.lower():
                brigade_label = assigned_by_name
        
        # Если ничего не нашли - значит бригада не назначена
        if not brigade_label:
            brigade_label = 'Бригада не назначена'
        
        # Try to extract numeric brigade
        brigade_number = self._parse_brigade_number(brigade_label)
        return {
            'id': str(deal.get('ID')),
            'title': deal.get('TITLE') or (deal.get('UF_CRM_1669561599956') or ''),
            'address': self._normalize_address(deal.get('UF_CRM_1669561599956') or deal.get('TITLE') or ''),
            'brigade': brigade_label,
            'brigade_name': brigade_label,
            'brigade_number': brigade_number,
            'assigned_by_id': deal.get('ASSIGNED_BY_ID'),
            'assigned_by_name': (deal.get('ASSIGNED_BY_NAME') or '').strip(),
            'management_company': company_title_enriched or (deal.get('COMPANY_TITLE') or ''),
            'status': deal.get('STAGE_ID'),
            'apartments': self._safe_int(deal.get('UF_CRM_1669704529022')) or 0,
            'entrances': self._safe_int(deal.get('UF_CRM_1669705507390')) or 0,
            'floors': self._safe_int(deal.get('UF_CRM_1669704631166')) or 0,
            'cleaning_dates': cleaning_dates,
            'periodicity': self._compute_periodicity(cleaning_dates),
            'bitrix_url': f"{self.portal_base}/crm/deal/details/{deal.get('ID')}/",
        }

    def _safe_int(self, v: Any) -> Optional[int]:
        try:
            return int(v) if v not in (None, '') else None
        except Exception:
            return None

    async def list_houses(
        self,
        *,
        brigade: Optional[str] = None,
        status: Optional[str] = None,
        management_company: Optional[str] = None,
        address: Optional[str] = None,
        cleaning_date: Optional[str] = None,
        date_from: Optional[str] = None,
        date_to: Optional[str] = None,
        page: int = 1,
        limit: int = 3,
    ) -> Dict[str, Any]:
        cache_key = f"deals:{brigade}:{status}:{management_company}:{cleaning_date}:{date_from}:{date_to}"
        cached = self.deals_cache.get(cache_key)
        if cached is not None:
            items: List[Dict[str, Any]] = cached
            total = len(items)
            start = (page - 1) * limit
            end = start + limit
            return {'houses': items[start:end], 'total': total, 'page': page, 'limit': limit, 'pages': (total + limit - 1) // limit}

        select_fields = [
            'ID','TITLE','CATEGORY_ID','STAGE_ID','COMPANY_ID','COMPANY_TITLE','ASSIGNED_BY_ID','ASSIGNED_BY_NAME',
            'UF_CRM_1669561599956','UF_CRM_1669704529022','UF_CRM_1669705507390','UF_CRM_1669704631166','UF_CRM_1669706387893',
            'UF_CRM_1741592774017','UF_CRM_1741592855565','UF_CRM_1741592892232','UF_CRM_1741592945060',
            'UF_CRM_1741593004888','UF_CRM_1741593047994','UF_CRM_1741593067418','UF_CRM_1741593115407',
            'UF_CRM_1741593156926','UF_CRM_1741593210242','UF_CRM_1741593231558','UF_CRM_1741593285121',
            'UF_CRM_1741593340713','UF_CRM_1741593387667','UF_CRM_1741593408621','UF_CRM_1741593452062',
        ]

        all_items: List[Dict[str, Any]] = []

        # Нормализация адреса (локальная)
        def _normalize_addr_local(s: Optional[str]) -> str:
            if not s:
                return ''
            ss = str(s).lower().strip()
            ss = ss.replace('улица', 'ул').replace('проспект', 'пр-кт').replace('просп.', 'пр-кт').replace('пр-т', 'пр-кт')
            ss = ss.replace('дом', 'д').replace('корпус', 'к').replace('корп.', 'к')
            ss = ss.replace(',', ' ').replace('.', ' ').replace('  ', ' ')
            return ss

        norm_addr = _normalize_addr_local(address) if address else None
        
        # Импортируем функцию умного сравнения адресов
        from backend.app.services.brain import address_match_score

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                start_param = 0
                while True:
                    payload = {'start': start_param, 'select': select_fields, 'filter': {'CATEGORY_ID': '34'}, 'order': {'ID': 'DESC'}}
                    data = await self._make_request(client, 'crm.deal.list', payload)
                    if not data.get('ok'):
                        break
                    deals = data.get('result') or []
                    if not deals:
                        break

                    # Обрабатываем сделки последовательно (с rate limiting внутри)
                    for d in deals:
                        try:
                            # Быстрая проверка адреса до дорогих запросов
                            if address:
                                raw_addr = (d.get('UF_CRM_1669561599956') or d.get('TITLE') or '')
                                # Используем умное сравнение адресов - снижаем порог до 70 для более гибкого поиска
                                match_score = address_match_score(address, raw_addr)
                                if match_score < 70:  # Было 100, стало 70
                                    continue
                            # Только при потенциальном совпадении грузим компанию и строим DTO
                            company_title = await self._company_title(client, d.get('COMPANY_ID'))
                            item = await self._deal_to_house_dto(client, d, company_title)
                            # Добавляем score для сортировки
                            if address:
                                item['_match_score'] = address_match_score(address, item.get('address') or item.get('title') or '')
                            all_items.append(item)
                            # При поиске по адресу продолжаем искать во всех страницах
                            # Убираем раннее прерывание, чтобы найти все совпадения
                        except Exception as e:
                            logger.warning(f"deal parse skip: {e}")

                    # Продолжаем поиск по всем страницам при поиске по адресу
                    # чтобы найти все совпадения, не ограничиваясь первой страницей

                    next_val = data.get('next')
                    if next_val is None:
                        break
                    start_param = next_val
        except Exception as e:
            logger.error(f"Bitrix list error: {e}")
            all_items = []

        # Server filters

        def _match(item: Dict[str, Any]) -> bool:
            if brigade and not self._match_brigade(item, brigade):
                return False
            if status and str(status).lower() not in str(item.get('status') or '').lower():
                return False
            if management_company and management_company.lower() not in (item.get('management_company') or '').lower():
                return False
            # Address match with smart scoring - снижаем порог до 70 для гибкости
            if norm_addr:
                target = item.get('address') or item.get('title') or ''
                match_score = address_match_score(address, target)
                if match_score < 70:  # Было 100, стало 70
                    return False
            def has_date(d: str) -> bool:
                for v in (item.get('cleaning_dates') or {}).values():
                    if not isinstance(v, dict):
                        continue
                    for dd in (v.get('dates') or []):
                        if dd == d:
                            return True
                return False
            def in_range(fr: Optional[str], to: Optional[str]) -> bool:
                if not fr and not to:
                    return True
                for v in (item.get('cleaning_dates') or {}).values():
                    if not isinstance(v, dict):
                        continue
                    for dd in (v.get('dates') or []):
                        if fr and dd < fr:
                            continue
                        if to and dd > to:
                            continue
                        return True
                return False
            if cleaning_date and not has_date(cleaning_date):
                return False
            if not in_range(date_from, date_to):
                return False
            return True

        filtered = [x for x in all_items if _match(x)]
        
        # Сортировка по match_score (если есть адрес)
        if address:
            filtered.sort(key=lambda x: x.get('_match_score', 0), reverse=True)
        
        total = len(filtered)
        self.deals_cache.set(cache_key, filtered)

        start = (page - 1) * limit
        end = start + limit
        return {'houses': filtered[start:end], 'total': total, 'page': page, 'limit': limit, 'pages': (total + limit - 1) // limit}

    async def get_deal_details(self, deal_id: str) -> Optional[Dict[str, Any]]:
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                url = f"{self.webhook_url}crm.deal.get"
                resp = await client.get(url, params={"id": deal_id}, timeout=self.timeout)
                if resp.status_code != 200:
                    return None
                j = resp.json()
                deal = j.get('result') or None
                if not deal:
                    return None

                # company
                company_id = deal.get('COMPANY_ID')
                company = None
                company_title_fallback = deal.get('COMPANY_TITLE')
                if company_id:
                    cu = f"{self.webhook_url}crm.company.get"
                    rc = await client.get(cu, params={"id": company_id}, timeout=self.timeout)
                    if rc.status_code == 200:
                        cj = rc.json().get('result') or {}
                        phones = [p.get('VALUE') for p in (cj.get('PHONE') or []) if p.get('VALUE')]
                        emails = [e.get('VALUE') for e in (cj.get('EMAIL') or []) if e.get('VALUE')]
                        company = {'id': cj.get('ID'), 'title': cj.get('TITLE') or company_title_fallback, 'phones': phones, 'emails': emails}
                if not company and company_title_fallback:
                    company = {'id': None, 'title': company_title_fallback, 'phones': [], 'emails': []}

                # contact (senior): пробуем CONTACT_ID, CONTACT_IDS, и crm.deal.contact.items.get
                contact = None
                contact_id = deal.get('CONTACT_ID')
                
                # Сначала пробуем CONTACT_ID (один контакт)
                if contact_id and contact_id != 0 and contact_id != '0':
                    try:
                        cu = f"{self.webhook_url}crm.contact.get"
                        rc = await client.get(cu, params={"id": contact_id}, timeout=self.timeout)
                        if rc.status_code == 200:
                            cj = rc.json().get('result') or {}
                            phones = [p.get('VALUE') for p in (cj.get('PHONE') or []) if p.get('VALUE')]
                            emails = [e.get('VALUE') for e in (cj.get('EMAIL') or []) if e.get('VALUE')]
                            name = ((cj.get('NAME') or '') + ' ' + (cj.get('LAST_NAME') or '')).strip() or cj.get('HONORIFIC')
                            contact = {'id': cj.get('ID'), 'name': name, 'phones': phones, 'emails': emails}
                    except Exception as e:
                        logger.warning(f"CONTACT_ID fetch failed: {e}")
                
                # Fallback 1: CONTACT_IDS (множественные контакты)
                if not contact:
                    contact_ids = deal.get('CONTACT_IDS')
                    if contact_ids and isinstance(contact_ids, list) and len(contact_ids) > 0:
                        try:
                            cu = f"{self.webhook_url}crm.contact.get"
                            rc = await client.get(cu, params={"id": contact_ids[0]}, timeout=self.timeout)
                            if rc.status_code == 200:
                                cj = rc.json().get('result') or {}
                                phones = [p.get('VALUE') for p in (cj.get('PHONE') or []) if p.get('VALUE')]
                                emails = [e.get('VALUE') for e in (cj.get('EMAIL') or []) if e.get('VALUE')]
                                name = ((cj.get('NAME') or '') + ' ' + (cj.get('LAST_NAME') or '')).strip() or cj.get('HONORIFIC')
                                contact = {'id': cj.get('ID'), 'name': name, 'phones': phones, 'emails': emails}
                        except Exception as e:
                            logger.warning(f"CONTACT_IDS fetch failed: {e}")
                
                # Fallback 2: crm.deal.contact.items.get
                if not contact:
                    try:
                        cu = f"{self.webhook_url}crm.deal.contact.items.get"
                        rc2 = await client.get(cu, params={"id": deal.get('ID')}, timeout=self.timeout)
                        if rc2.status_code == 200:
                            arr = rc2.json().get('result') or []
                            if isinstance(arr, list) and arr:
                                cid = arr[0].get('CONTACT_ID') or arr[0].get('contact_id')
                                if cid:
                                    rc3 = await client.get(f"{self.webhook_url}crm.contact.get", params={"id": cid}, timeout=self.timeout)
                                    if rc3.status_code == 200:
                                        cj = rc3.json().get('result') or {}
                                        phones = [p.get('VALUE') for p in (cj.get('PHONE') or []) if p.get('VALUE')]
                                        emails = [e.get('VALUE') for e in (cj.get('EMAIL') or []) if e.get('VALUE')]
                                        name = ((cj.get('NAME') or '') + ' ' + (cj.get('LAST_NAME') or '')).strip() or cj.get('HONORIFIC')
                                        contact = {'id': cj.get('ID'), 'name': name, 'phones': phones, 'emails': emails}
                    except Exception as e:
                        logger.warning(f"Elder contact fallback via crm.deal.contact.items.get failed: {e}")

                # assigned: получаем из user.get (ASSIGNED_BY_ID)
                assigned_info = await self._get_user_info(client, deal.get('ASSIGNED_BY_ID'))
                brigade_label = None
                
                if assigned_info:
                    name = (assigned_info.get('name') or '').strip()
                    last_name = (assigned_info.get('last_name') or '').strip()
                    full_name = f"{name} {last_name}".strip()
                    
                    # Проверяем, является ли это бригадой (содержит слово "бригада")
                    if 'бригад' in full_name.lower():
                        # Формируем название бригады
                        if last_name.lower() == 'бригада' and name:
                            brigade_label = f"{name} {last_name}"
                        else:
                            brigade_label = full_name
                
                # Если бригада не найдена, пробуем ASSIGNED_BY_NAME
                if not brigade_label:
                    assigned_by_name = (deal.get('ASSIGNED_BY_NAME') or '').strip()
                    if assigned_by_name and 'бригад' in assigned_by_name.lower():
                        brigade_label = assigned_by_name
                
                # Если ничего не нашли - бригада не назначена
                if not brigade_label:
                    brigade_label = 'Бригада не назначена'
                
                brigade_number = self._parse_brigade_number(brigade_label)

                cleaning_dates = await self._build_cleaning_dates(client, deal)

                return {
                    'id': str(deal.get('ID')),
                    'title': deal.get('TITLE') or (deal.get('UF_CRM_1669561599956') or ''),
                    'address': self._normalize_address(deal.get('UF_CRM_1669561599956') or deal.get('TITLE') or ''),
                    'brigade_name': brigade_label,
                    'brigade_number': brigade_number,
                    'assigned': assigned_info,
                    'management_company': company and company.get('title'),
                    'company': company,
                    'elder_contact': contact,
                    'status': deal.get('STAGE_ID'),
                    'apartments': self._safe_int(deal.get('UF_CRM_1669704529022')) or 0,
                    'entrances': self._safe_int(deal.get('UF_CRM_1669705507390')) or 1,
                    'floors': self._safe_int(deal.get('UF_CRM_1669704631166')) or 5,
                    'cleaning_dates': cleaning_dates,
                    'periodicity': self._compute_periodicity(cleaning_dates),
                    'bitrix_url': f"{self.portal_base}/crm/deal/details/{deal.get('ID')}/",
                }
        except Exception as e:
            logger.error(f"get_deal_details error: {e}")
            return None

    async def get_all_deals(self) -> List[Dict[str, Any]]:
        items: List[Dict[str, Any]] = []
        select_fields = [
            'ID','TITLE','COMPANY_ID','COMPANY_TITLE','ASSIGNED_BY_ID','ASSIGNED_BY_NAME',
            'UF_CRM_1669561599956','UF_CRM_1669704529022','UF_CRM_1669705507390','UF_CRM_1669704631166','UF_CRM_1669706387893',
            'UF_CRM_1741592774017','UF_CRM_1741592855565','UF_CRM_1741592892232','UF_CRM_1741592945060',
            'UF_CRM_1741593004888','UF_CRM_1741593047994','UF_CRM_1741593067418','UF_CRM_1741593115407',
            'UF_CRM_1741593156926','UF_CRM_1741593210242','UF_CRM_1741593231558','UF_CRM_1741593285121',
            'UF_CRM_1741593340713','UF_CRM_1741593387667','UF_CRM_1741593408621','UF_CRM_1741593452062',
        ]
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                start_param = 0
                while True:
                    payload = {'start': start_param, 'select': select_fields, 'filter': {'CATEGORY_ID': '34'}, 'order': {'ID': 'DESC'}}
                    data = await self._make_request(client, 'crm.deal.list', payload)
                    if not data.get('ok'):
                        break
                    batch = data.get('result') or []
                    if not batch:
                        break
                    items.extend(batch)
                    next_val = data.get('next')
                    if next_val is None:
                        break
                    start_param = next_val
        except Exception as e:
            logger.error(f"❌ Ошибка загрузки домов из Bitrix24: {e}")
        return items

    def parse_deal_to_house(self, deal: Dict[str, Any]) -> Dict[str, Any]:
        return {
            'id': str(uuid4()),
            'bitrix_id': str(deal.get('ID', '')),
            'address': self._normalize_address(deal.get('UF_CRM_1669561599956', '') or (deal.get('TITLE') or '')),
            'apartments_count': self._safe_int(deal.get('UF_CRM_1669704529022')),
            'entrances_count': self._safe_int(deal.get('UF_CRM_1669705507390')),
            'floors_count': self._safe_int(deal.get('UF_CRM_1669704631166')),
            'company_id': deal.get('COMPANY_ID'),
            'company_title': deal.get('COMPANY_TITLE'),
            'assigned_by_id': deal.get('ASSIGNED_BY_ID'),
            'assigned_by_name': deal.get('ASSIGNED_BY_NAME'),
            'brigade_number': self._parse_brigade_number(deal.get('ASSIGNED_BY_NAME') or ''),
            'tariff': deal.get('UF_CRM_1669706387893'),
            'cleaning_schedule': {},
            'complaints': [],
            'notes': None,
            'elder_contact': None,
            'act_signed': None,
            'last_cleaning': None,
            'synced_at': datetime.utcnow(),
        }

    async def sync_houses(self, db: AsyncSession) -> Dict[str, int]:
        deals = await self.get_all_deals()
        created = 0
        updated = 0
        total = 0
        for deal in deals:
            try:
                data = self.parse_deal_to_house(deal)
                if not (data.get('bitrix_id') and data.get('address')):
                    continue
                total += 1
                res = await db.execute(select(House).where(House.bitrix_id == data['bitrix_id']))
                existing = res.scalar_one_or_none()
                if existing:
                    for k, v in data.items():
                        if k == 'id':
                            continue
                        setattr(existing, k, v)
                    updated += 1
                else:
                    db.add(House(**data))
                    created += 1
            except Exception as e:
                logger.warning(f"Deal sync skipped due to error: {e}")
        await db.commit()
        return {'total': total, 'created': created, 'updated': updated}

    async def get_all_brigades(self) -> List[Dict[str, Any]]:
        """Получить список всех бригад (пользователей с 'бригада' в имени)"""
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                brigades = []
                start = 0
                while True:
                    data = await self._make_request(client, 'user.get', {'start': start})
                    users = data.get('result') or []
                    if not users:
                        break
                    for user in users:
                        name = (user.get('NAME') or '').strip()
                        last_name = (user.get('LAST_NAME') or '').strip()
                        full_name = f"{name} {last_name}".strip()
                        # Фильтруем только бригады
                        if 'бригад' in full_name.lower():
                            brigades.append({
                                'id': user.get('ID'),
                                'name': full_name
                            })
                    next_val = data.get('next')
                    if next_val is None:
                        break
                    start = next_val
                return brigades
        except Exception as e:
            logger.error(f"Error getting brigades: {e}")
            return []

    async def get_cleaning_types(self) -> List[Dict[str, Any]]:
        """Получить список типов уборки (enum из UF_CRM_1741593047994)"""
        try:
            # Получаем enum для октября type 1
            field_name = 'UF_CRM_1741593047994'
            cache_key = f"enum_{field_name}"
            cached = self.enum_cache.get(cache_key)
            if cached:
                return cached
            
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                data = await self._make_request(client, 'crm.deal.userfield.list', {'filter': {'FIELD_NAME': field_name}})
                fields = data.get('result') or []
                if not fields:
                    return []
                
                field = fields[0]
                enum_list = field.get('LIST') or []
                types = [{'id': item.get('ID'), 'name': item.get('VALUE')} for item in enum_list if item.get('VALUE')]
                
                self.enum_cache.set(cache_key, types)
                return types
        except Exception as e:
            logger.error(f"Error getting cleaning types: {e}")
            return []

    async def get_all_contacts(self) -> List[Dict[str, Any]]:
        """Получить список всех контактов из Bitrix24"""
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                contacts = []
                start = 0
                while True:
                    data = await self._make_request(client, 'crm.contact.list', {'start': start, 'select': ['ID', 'NAME', 'LAST_NAME', 'PHONE', 'EMAIL']})
                    items = data.get('result') or []
                    if not items:
                        break
                    for contact in items:
                        name = ((contact.get('NAME') or '') + ' ' + (contact.get('LAST_NAME') or '')).strip()
                        phones = [p.get('VALUE') for p in (contact.get('PHONE') or []) if p.get('VALUE')]
                        phone_str = phones[0] if phones else ''
                        contacts.append({
                            'id': contact.get('ID'),
                            'name': name,
                            'phone': phone_str
                        })
                    next_val = data.get('next')
                    if next_val is None or len(contacts) >= 100:  # Ограничение 100 контактов для производительности
                        break
                    start = next_val
                return contacts
        except Exception as e:
            logger.error(f"Error getting contacts: {e}")
            return []

    async def create_contact(self, name: str, phone: str = '', comment: str = '') -> Optional[str]:
        """Создать новый контакт в Bitrix24"""
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                fields = {
                    'NAME': name,
                }
                
                # Добавляем телефон если есть
                if phone:
                    fields['PHONE'] = [{'VALUE': phone, 'VALUE_TYPE': 'WORK'}]
                
                # Добавляем комментарий если есть
                if comment:
                    fields['COMMENTS'] = comment
                
                url = f"{self.webhook_url}crm.contact.add"
                resp = await client.post(url, json={'fields': fields}, timeout=self.timeout)
                
                if resp.status_code != 200:
                    logger.error(f"Failed to create contact: {resp.status_code}")
                    return None
                
                result = resp.json()
                contact_id = result.get('result')
                if contact_id:
                    logger.info(f"Created new contact: {contact_id} - {name}")
                    return str(contact_id)
                return None
        except Exception as e:
            logger.error(f"Error creating contact: {e}")
            return None

    async def update_deal(self, deal_id: str, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Обновить сделку в Bitrix24"""
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                # Подготовим данные для обновления
                update_fields = {'id': deal_id}
                
                # Квартиры, этажи, подъезды
                if 'apartments' in data:
                    update_fields['UF_CRM_1669704529022'] = data['apartments']
                if 'floors' in data:
                    update_fields['UF_CRM_1669704631166'] = data['floors']
                if 'entrances' in data:
                    update_fields['UF_CRM_1669705507390'] = data['entrances']
                
                # Бригада (ASSIGNED_BY_ID)
                if 'brigade_id' in data:
                    update_fields['ASSIGNED_BY_ID'] = data['brigade_id']
                
                # Контакт старшего - создаем новый если нужно
                if 'elder_name' in data and data['elder_name']:
                    # Создаем новый контакт
                    contact_id = await self.create_contact(
                        name=data['elder_name'],
                        phone=data.get('elder_phone', ''),
                        comment=data.get('elder_comment', '')
                    )
                    if contact_id:
                        update_fields['CONTACT_ID'] = contact_id
                elif 'contact_id' in data:
                    update_fields['CONTACT_ID'] = data['contact_id']
                
                # График уборки - октябрь
                if 'october_1_dates' in data:
                    update_fields['UF_CRM_1741593004888'] = data['october_1_dates']
                if 'october_1_type' in data:
                    update_fields['UF_CRM_1741593047994'] = data['october_1_type']
                if 'october_2_dates' in data:
                    update_fields['UF_CRM_1741593067418'] = data['october_2_dates']
                if 'october_2_type' in data:
                    update_fields['UF_CRM_1741593115407'] = data['october_2_type']
                
                # График уборки - ноябрь
                if 'november_1_dates' in data:
                    update_fields['UF_CRM_1741593156926'] = data['november_1_dates']
                if 'november_1_type' in data:
                    update_fields['UF_CRM_1741593210242'] = data['november_1_type']
                if 'november_2_dates' in data:
                    update_fields['UF_CRM_1741593231558'] = data['november_2_dates']
                if 'november_2_type' in data:
                    update_fields['UF_CRM_1741593285121'] = data['november_2_type']
                
                # График уборки - декабрь
                if 'december_1_dates' in data:
                    update_fields['UF_CRM_1741593340713'] = data['december_1_dates']
                if 'december_1_type' in data:
                    update_fields['UF_CRM_1741593387667'] = data['december_1_type']
                if 'december_2_dates' in data:
                    update_fields['UF_CRM_1741593408621'] = data['december_2_dates']
                if 'december_2_type' in data:
                    update_fields['UF_CRM_1741593452062'] = data['december_2_type']
                
                # Отправляем обновление
                url = f"{self.webhook_url}crm.deal.update"
                resp = await client.post(url, json={'fields': update_fields}, timeout=self.timeout)
                
                if resp.status_code != 200:
                    logger.error(f"Failed to update deal {deal_id}: {resp.status_code}")
                    return None
                
                result = resp.json()
                if not result.get('result'):
                    logger.error(f"Bitrix24 update failed: {result}")
                    return None
                
                # После обновления получаем свежие данные
                updated_deal = await self.get_deal_details(deal_id)
                return updated_deal
                
        except Exception as e:
            logger.error(f"Error updating deal {deal_id}: {e}")
            return None



bitrix24_service = Bitrix24Service()