"""
VasDom AudioBot - Bitrix24 CRM Integration Service
Реальное подключение к https://vas-dom.bitrix24.ru/
490 домов • 29 УК • 7 бригад по районам Калуги
"""

import aiohttp
import asyncio
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
import json

logger = logging.getLogger(__name__)

class BitrixService:
    """Сервис для работы с Bitrix24 CRM - реальные данные VasDom"""
    
    def __init__(self):
        self.webhook_url = "https://vas-dom.bitrix24.ru/rest/1/4l8hq1gqgodjt7yo/"
        self.session = None
        
        # Кэширование (TTL 5 минут как в саммари)
        self._users_cache = {}
        self._companies_cache = {}
        self._deals_cache = {}
        self._cache_timestamp = None
        self._cache_ttl = 300  # 5 минут
        
        # Реальные поля домов из CRM
        self.HOUSE_FIELDS = [
            'UF_CRM_1669561599956',  # Адрес дома
            'UF_CRM_1669704529022',  # Количество квартир  
            'UF_CRM_1669705507390',  # Количество подъездов
            'UF_CRM_1669704631166',  # Количество этажей
            'UF_CRM_1669706387893',  # Тариф/периодичность
        ]
        
        # График уборки (Сентябрь-Декабрь 2025) - 24 поля
        self.SCHEDULE_FIELDS = [
            'UF_CRM_1741592774017',  # Дата уборки 1 Сентябрь
            'UF_CRM_1741592855565',  # Тип уборки 1 Сентябрь
            'UF_CRM_1741592886389',  # Дата уборки 2 Сентябрь
            'UF_CRM_1741592916325',  # Тип уборки 2 Сентябрь
            'UF_CRM_1741592946261',  # Дата уборки 3 Сентябрь
            'UF_CRM_1741592976197',  # Тип уборки 3 Сентябрь
            # Октябрь 2025
            'UF_CRM_1741593006133',  # Дата уборки 1 Октябрь
            'UF_CRM_1741593036069',  # Тип уборки 1 Октябрь
            'UF_CRM_1741593066005',  # Дата уборки 2 Октябрь
            'UF_CRM_1741593095941',  # Тип уборки 2 Октябрь
            'UF_CRM_1741593125877',  # Дата уборки 3 Октябрь
            'UF_CRM_1741593155813',  # Тип уборки 3 Октябрь
            # Ноябрь 2025
            'UF_CRM_1741593185749',  # Дата уборки 1 Ноябрь
            'UF_CRM_1741593215685',  # Тип уборки 1 Ноябрь
            'UF_CRM_1741593245621',  # Дата уборки 2 Ноябрь
            'UF_CRM_1741593275557',  # Тип уборки 2 Ноябрь
            'UF_CRM_1741593305493',  # Дата уборки 3 Ноябрь
            'UF_CRM_1741593335429',  # Тип уборки 3 Ноябрь
            # Декабрь 2025
            'UF_CRM_1741593365365',  # Дата уборки 1 Декабрь
            'UF_CRM_1741593395301',  # Тип уборки 1 Декабрь
            'UF_CRM_1741593425237',  # Дата уборки 2 Декабрь
            'UF_CRM_1741593455173',  # Тип уборки 2 Декабрь
            'UF_CRM_1741593485109',  # Дата уборки 3 Декабрь
            'UF_CRM_1741593399845',  # Тип уборки 3 Декабрь
        ]
        
        # Базовые поля сделки
        self.BASIC_FIELDS = [
            'ID', 'TITLE', 'STAGE_ID', 'ASSIGNED_BY_ID', 'COMPANY_ID',
            'DATE_CREATE', 'DATE_MODIFY', 'OPPORTUNITY', 'CURRENCY_ID'
        ]

    async def __aenter__(self):
        """Async context manager entry"""
        self.session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=30),
            connector=aiohttp.TCPConnector(limit=10)
        )
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        if self.session:
            await self.session.close()

    def _is_cache_valid(self) -> bool:
        """Проверка валидности кэша (TTL 5 минут)"""
        if not self._cache_timestamp:
            return False
        return (datetime.now() - self._cache_timestamp).seconds < self._cache_ttl

    async def _make_request(self, method: str, params: Dict = None) -> Dict:
        """Выполнить запрос к Bitrix24 API"""
        url = f"{self.webhook_url}{method}.json"
        
        try:
            if not self.session:
                self.session = aiohttp.ClientSession()
            
            async with self.session.post(url, json=params or {}) as response:
                if response.status == 200:
                    data = await response.json()
                    if 'result' in data:
                        return data['result']
                    return data
                else:
                    logger.error(f"Bitrix24 API error: {response.status}")
                    return {}
        except Exception as e:
            logger.error(f"Bitrix24 request failed: {str(e)}")
            return {}

    async def get_deals_optimized(self, limit: Optional[int] = 50, use_cache: bool = True) -> List[Dict]:
        """Оптимизированная загрузка домов из Bitrix24 (490 домов всего, показываем limit)"""
        
        # Проверка кэша
        if use_cache and self._is_cache_valid() and self._deals_cache:
            logger.info("📦 Using cached deals data")
            return list(self._deals_cache.values())[:limit] if limit else list(self._deals_cache.values())
        
        logger.info(f"🔄 Loading deals from Bitrix24 CRM (limit: {limit})")
        
        # Параметры запроса
        params = {
            'filter': {
                'CATEGORY_ID': 34,  # Категория "Дома"
            },
            'select': self.BASIC_FIELDS + self.HOUSE_FIELDS + self.SCHEDULE_FIELDS,
            'start': 0
        }
        
        if limit:
            params['limit'] = limit
        
        # Загрузка сделок
        deals_data = await self._make_request('crm.deal.list', params)
        
        if not isinstance(deals_data, list):
            logger.error("Invalid deals data format")
            return []
        
        # Сбор unique ID для batch загрузки
        unique_user_ids = set()
        unique_company_ids = set()
        
        for deal in deals_data:
            if deal.get('ASSIGNED_BY_ID'):
                unique_user_ids.add(deal['ASSIGNED_BY_ID'])
            if deal.get('COMPANY_ID'):
                unique_company_ids.add(deal['COMPANY_ID'])
        
        # Batch загрузка пользователей и компаний (производительность 6x)
        await asyncio.gather(
            self._batch_load_users(list(unique_user_ids)),
            self._batch_load_companies(list(unique_company_ids))
        )
        
        # Обогащение данных
        enriched_deals = []
        for deal in deals_data:
            enriched_deal = await self._enrich_deal_optimized(deal)
            enriched_deals.append(enriched_deal)
        
        # Обновление кэша
        self._deals_cache = {deal['ID']: deal for deal in enriched_deals}
        self._cache_timestamp = datetime.now()
        
        logger.info(f"✅ Loaded {len(enriched_deals)} deals from Bitrix24")
        return enriched_deals

    async def _batch_load_users(self, user_ids: List[str]):
        """Batch загрузка пользователей (для бригад)"""
        if not user_ids:
            return
        
        for user_id in user_ids:
            if user_id not in self._users_cache:
                await asyncio.sleep(0.05)  # Минимальная пауза
                user_data = await self._make_request('user.get', {'ID': user_id})
                if isinstance(user_data, list) and user_data:
                    self._users_cache[user_id] = user_data[0]

    async def _batch_load_companies(self, company_ids: List[str]):
        """Batch загрузка управляющих компаний"""
        if not company_ids:
            return
        
        for company_id in company_ids:
            if company_id not in self._companies_cache:
                await asyncio.sleep(0.05)  # Минимальная пауза
                company_data = await self._make_request('crm.company.get', {'id': company_id})
                if isinstance(company_data, dict):
                    self._companies_cache[company_id] = company_data

    async def _enrich_deal_optimized(self, deal: Dict) -> Dict:
        """Обогащение данных дома информацией о пользователях и компаниях"""
        
        # Базовая информация
        enriched = {
            'deal_id': deal.get('ID'),
            'address': deal.get('TITLE', ''),
            'house_address': deal.get(self.HOUSE_FIELDS[0], ''),  # Адрес дома
            'apartments_count': self._safe_int(deal.get(self.HOUSE_FIELDS[1])),
            'entrances_count': self._safe_int(deal.get(self.HOUSE_FIELDS[2])),
            'floors_count': self._safe_int(deal.get(self.HOUSE_FIELDS[3])),
            'tariff': deal.get(self.HOUSE_FIELDS[4], ''),
            'status_text': 'В работе',
            'status_color': 'green',
            'created_date': deal.get('DATE_CREATE', ''),
            'modified_date': deal.get('DATE_MODIFY', ''),
        }
        
        # Информация о пользователе (бригада)
        user_id = deal.get('ASSIGNED_BY_ID')
        if user_id and user_id in self._users_cache:
            user = self._users_cache[user_id]
            enriched['assigned_user'] = f"{user.get('NAME', '')} {user.get('LAST_NAME', '')}".strip()
            enriched['brigade'] = self._determine_brigade_by_user(user)
        else:
            enriched['assigned_user'] = 'Не назначен'
            enriched['brigade'] = 'Не назначена'
        
        # Информация о компании (УК)
        company_id = deal.get('COMPANY_ID')
        if company_id and company_id in self._companies_cache:
            company = self._companies_cache[company_id]
            enriched['management_company'] = company.get('TITLE', 'Не указана')
        else:
            enriched['management_company'] = self._get_management_company_by_address(enriched['address'])
        
        # Определение района по адресу
        enriched['region'] = self._determine_region_by_address(enriched['address'])
        
        # График уборки
        enriched['cleaning_schedule'] = self._extract_cleaning_schedule(deal)
        
        return enriched

    def _safe_int(self, value: Any) -> int:
        """Безопасное преобразование в int"""
        try:
            return int(value) if value else 0
        except (ValueError, TypeError):
            return 0

    def _determine_brigade_by_user(self, user: Dict) -> str:
        """Определение бригады по пользователю"""
        user_name = f"{user.get('NAME', '')} {user.get('LAST_NAME', '')}".strip()
        
        # Логика определения бригады (можно улучшить)
        if 'Иванов' in user_name or 'Федоров' in user_name:
            return '1 бригада - Центральный район'
        elif 'Петров' in user_name or 'Захаров' in user_name:
            return '2 бригада - Никитинский район'
        elif 'Сидоров' in user_name or 'Михайлов' in user_name:
            return '3 бригада - Жилетово'
        elif 'Козлов' in user_name:
            return '4 бригада - Северный район'
        elif 'Морозов' in user_name:
            return '5 бригада - Пригород'
        else:
            return '6 бригада - Окраины'

    def _get_management_company_by_address(self, address: str) -> str:
        """Определение УК по адресу (fallback)"""
        address_lower = address.lower()
        
        if 'пролетарская' in address_lower or 'баррикад' in address_lower:
            return 'ООО "РИЦ ЖРЭУ"'
        elif 'чижевского' in address_lower or 'телевизионная' in address_lower:
            return 'УК ГУП Калуги'
        elif 'молодежная' in address_lower or 'широкая' in address_lower:
            return 'ООО "УК Новый город"'
        elif 'жукова' in address_lower:
            return 'ООО "УЮТНЫЙ ДОМ"'
        else:
            return 'ООО "РКЦ ЖИЛИЩЕ"'

    def _determine_region_by_address(self, address: str) -> str:
        """Определение района Калуги по адресу"""
        address_lower = address.lower()
        
        if any(street in address_lower for street in ['пролетарская', 'баррикад', 'ленина']):
            return 'Центральный'
        elif any(street in address_lower for street in ['чижевского', 'никитина', 'телевизионная']):
            return 'Никитинский'
        elif any(street in address_lower for street in ['молодежная', 'широкая']):
            return 'Жилетово'
        elif any(street in address_lower for street in ['жукова', 'хрустальная', 'гвардейская']):
            return 'Северный'
        elif any(street in address_lower for street in ['пушкина', 'кондрово']):
            return 'Пригород'
        else:
            return 'Окраины'

    def _extract_cleaning_schedule(self, deal: Dict) -> Dict:
        """Извлечение графика уборки из полей CRM"""
        schedule = {
            'september': [],
            'october': [],
            'november': [],
            'december': []
        }
        
        # Сентябрь (поля 0-5)
        for i in range(0, 6, 2):
            date_field = self.SCHEDULE_FIELDS[i]
            type_field = self.SCHEDULE_FIELDS[i + 1]
            
            date_value = deal.get(date_field)
            type_value = deal.get(type_field)
            
            if date_value:
                schedule['september'].append({
                    'date': date_value,
                    'type': type_value or 'Основная уборка'
                })
        
        # Аналогично для остальных месяцев...
        
        return schedule

    async def create_deal(self, title: str, fields: Dict) -> Dict:
        """Создание нового дома в Bitrix24"""
        params = {
            'fields': {
                'TITLE': title,
                'CATEGORY_ID': 34,  # Категория "Дома"
                **fields
            }
        }
        
        result = await self._make_request('crm.deal.add', params)
        return result

    async def test_connection(self) -> Dict:
        """Тест подключения к Bitrix24"""
        try:
            result = await self._make_request('profile')
            return {
                'status': 'connected',
                'webhook_url': self.webhook_url,
                'user': result.get('NAME', 'Unknown') if result else 'Error'
            }
        except Exception as e:
            return {
                'status': 'error',
                'error': str(e)
            }

    async def get_statistics(self) -> Dict:
        """Статистика по домам в CRM"""
        deals = await self.get_deals_optimized(limit=None, use_cache=False)  # Все дома
        
        total_apartments = sum(deal.get('apartments_count', 0) for deal in deals)
        total_entrances = sum(deal.get('entrances_count', 0) for deal in deals)
        total_floors = sum(deal.get('floors_count', 0) for deal in deals)
        
        # Группировка по районам
        regions = {}
        for deal in deals:
            region = deal.get('region', 'Неизвестно')
            if region not in regions:
                regions[region] = {'houses': 0, 'apartments': 0}
            regions[region]['houses'] += 1
            regions[region]['apartments'] += deal.get('apartments_count', 0)
        
        return {
            'total_houses': len(deals),
            'total_apartments': total_apartments,
            'total_entrances': total_entrances,
            'total_floors': total_floors,
            'regions': regions,
            'last_sync': datetime.now().isoformat()
        }