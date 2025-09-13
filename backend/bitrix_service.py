"""
🔗 Сервис интеграции с Bitrix24 для AudioBot
Обеспечивает загрузку домов, сотрудников и других данных из CRM
"""

import aiohttp
import asyncio
import os
from typing import List, Dict, Any, Optional
import logging
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv

# Загружаем .env файл
ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

logger = logging.getLogger(__name__)

class BitrixService:
    """Сервис для работы с Bitrix24 API"""
    
    def __init__(self):
        self.webhook_url = os.environ.get('BITRIX_WEBHOOK_URL', '')
        self.portal_url = os.environ.get('BITRIX_PORTAL_URL', 'https://vas-dom.bitrix24.ru')
        
        if not self.webhook_url:
            logger.warning("BITRIX_WEBHOOK_URL не настроен - используется заглушка")
            self.webhook_url = "https://vas-dom.bitrix24.ru/sample/"
        
        # Убеждаемся что URL заканчивается на /
        if not self.webhook_url.endswith('/'):
            self.webhook_url += '/'
    
    async def _make_request(self, method: str, params: Dict[str, Any] = None) -> Dict[str, Any]:
        """Выполнение запроса к Bitrix24 API"""
        url = f"{self.webhook_url}{method}"
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, params=params, timeout=aiohttp.ClientTimeout(total=30)) as response:
                    if response.status == 200:
                        data = await response.json()
                        return data
                    else:
                        logger.error(f"Ошибка запроса к Bitrix24: {response.status} - {await response.text()}")
                        return {"result": [], "error": f"HTTP {response.status}"}
                        
        except asyncio.TimeoutError:
            logger.error(f"Таймаут запроса к Bitrix24: {method}")
            return {"result": [], "error": "Timeout"}
        except Exception as e:
            logger.error(f"Исключение при запросе к Bitrix24: {e}")
            return {"result": [], "error": str(e)}
    
    async def get_houses(self, limit: int = 500) -> List[Dict[str, Any]]:
        """Получение списка домов из CRM (сделки)"""
        params = {
            'select[]': [
                'ID', 
                'TITLE',
                'UF_CRM_1669704529022',  # Количество квартир
                'UF_CRM_1669705507390',  # Количество подъездов  
                'UF_CRM_1669704631166',  # Количество этажей
                'UF_CRM_1669708345534',  # Управляющая компания
                'UF_CRM_1693297230181',  # График уборки сентября
            ],
            'filter[CATEGORY_ID]': '0',  # Основная воронка
            'start': '0'
        }
        
        if limit:
            params['ORDER'] = {'ID': 'DESC'}
        
        data = await self._make_request('crm.deal.list', params)
        houses = data.get('result', [])
        
        # Нормализация данных
        normalized_houses = []
        for house in houses[:limit] if limit else houses:
            normalized_house = {
                'id': house.get('ID'),
                'address': house.get('TITLE', 'Адрес не указан'),
                'apartments': int(house.get('UF_CRM_1669704529022', 0) or 0),
                'entrances': int(house.get('UF_CRM_1669705507390', 0) or 0),
                'floors': int(house.get('UF_CRM_1669704631166', 0) or 0),
                'management_company': house.get('UF_CRM_1669708345534', 'Не указана'),
                'september_schedule': house.get('UF_CRM_1693297230181', 'Не указан'),
                'has_apartments': int(house.get('UF_CRM_1669704529022', 0) or 0) > 0,
                'has_entrances': int(house.get('UF_CRM_1669705507390', 0) or 0) > 0,
                'has_floors': int(house.get('UF_CRM_1669704631166', 0) or 0) > 0,
            }
            normalized_houses.append(normalized_house)
        
        logger.info(f"Загружено домов из Bitrix24: {len(normalized_houses)}")
        return normalized_houses
    
    async def get_employees(self) -> List[Dict[str, Any]]:
        """Получение списка сотрудников"""
        params = {
            'select[]': [
                'ID',
                'NAME', 
                'LAST_NAME',
                'EMAIL',
                'WORK_POSITION',
                'UF_DEPARTMENT',
                'ACTIVE'
            ],
            'filter[ACTIVE]': 'Y'
        }
        
        data = await self._make_request('user.get', params)
        users = data.get('result', [])
        
        # Нормализация данных сотрудников
        normalized_employees = []
        for user in users:
            normalized_employee = {
                'id': user.get('ID'),
                'name': f"{user.get('NAME', '')} {user.get('LAST_NAME', '')}".strip(),
                'email': user.get('EMAIL', ''),
                'position': user.get('WORK_POSITION', 'Не указана'),
                'department_id': user.get('UF_DEPARTMENT', [None])[0] if user.get('UF_DEPARTMENT') else None,
                'active': user.get('ACTIVE') == 'Y'
            }
            normalized_employees.append(normalized_employee)
        
        logger.info(f"Загружено сотрудников из Bitrix24: {len(normalized_employees)}")
        return normalized_employees
    
    async def get_departments(self) -> List[Dict[str, Any]]:
        """Получение списка подразделений"""
        data = await self._make_request('department.get')
        departments = data.get('result', [])
        
        # Нормализация данных подразделений
        normalized_departments = []
        for dept in departments:
            normalized_department = {
                'id': dept.get('ID'),
                'name': dept.get('NAME', 'Без названия'),
                'parent_id': dept.get('PARENT'),
                'head_id': dept.get('UF_HEAD'),
                'sort': dept.get('SORT', 500)
            }
            normalized_departments.append(normalized_department)
        
        logger.info(f"Загружено подразделений из Bitrix24: {len(normalized_departments)}")
        return normalized_departments
    
    async def get_statistics(self) -> Dict[str, Any]:
        """Получение общей статистики для дашборда"""
        # Параллельно загружаем все необходимые данные
        houses_task = self.get_houses()
        employees_task = self.get_employees()
        departments_task = self.get_departments()
        
        houses, employees, departments = await asyncio.gather(
            houses_task, employees_task, departments_task, 
            return_exceptions=True
        )
        
        # Обработка ошибок
        if isinstance(houses, Exception):
            logger.error(f"Ошибка загрузки домов: {houses}")
            houses = []
        
        if isinstance(employees, Exception):
            logger.error(f"Ошибка загрузки сотрудников: {employees}")
            employees = []
            
        if isinstance(departments, Exception):
            logger.error(f"Ошибка загрузки подразделений: {departments}")
            departments = []
        
        # Расчет статистики
        total_apartments = sum(house.get('apartments', 0) for house in houses)
        total_entrances = sum(house.get('entrances', 0) for house in houses)
        total_floors = sum(house.get('floors', 0) for house in houses)
        
        # Подсчет управляющих компаний
        management_companies = set()
        houses_with_schedule = 0
        
        for house in houses:
            mc = house.get('management_company', '').strip()
            if mc and mc != 'Не указана':
                management_companies.add(mc)
            
            schedule = house.get('september_schedule', '').strip()
            if schedule and schedule != 'Не указан':
                houses_with_schedule += 1
        
        # Группировка сотрудников по подразделениям (бригадам)
        brigades = {}
        for employee in employees:
            dept_id = employee.get('department_id')
            if dept_id:
                if dept_id not in brigades:
                    brigades[dept_id] = {
                        'id': dept_id,
                        'name': f'Бригада {dept_id}',
                        'employees': []
                    }
                brigades[dept_id]['employees'].append(employee)
        
        # Найдем имена бригад из подразделений
        for dept in departments:
            dept_id = dept.get('id')
            if dept_id in brigades:
                brigades[dept_id]['name'] = dept.get('name', f'Бригада {dept_id}')
        
        statistics = {
            'houses': {
                'total': len(houses),
                'with_apartments': len([h for h in houses if h.get('has_apartments')]),
                'with_entrances': len([h for h in houses if h.get('has_entrances')]),
                'with_floors': len([h for h in houses if h.get('has_floors')]),
                'with_schedule': houses_with_schedule,
                'total_apartments': total_apartments,
                'total_entrances': total_entrances,  
                'total_floors': total_floors
            },
            'employees': {
                'total': len(employees),
                'active': len([e for e in employees if e.get('active')]),
                'brigades': len(brigades),
                'by_brigade': list(brigades.values())
            },
            'management_companies': {
                'total': len(management_companies),
                'list': sorted(list(management_companies))
            },
            'departments': {
                'total': len(departments)
            },
            'last_updated': datetime.now().isoformat()
        }
        
        logger.info(f"Статистика сформирована: {statistics['houses']['total']} домов, {statistics['employees']['total']} сотрудников")
        return statistics
    
    async def test_connection(self) -> Dict[str, Any]:
        """Тестирование подключения к Bitrix24"""
        try:
            data = await self._make_request('app.info')
            
            if 'error' not in data:
                return {
                    'status': 'success',
                    'message': 'Подключение к Bitrix24 работает',
                    'app_info': data.get('result', {})
                }
            else:
                return {
                    'status': 'error', 
                    'message': f"Ошибка Bitrix24: {data['error']}",
                    'webhook_url': self.webhook_url
                }
                
        except Exception as e:
            return {
                'status': 'error',
                'message': f"Исключение при подключении: {str(e)}",
                'webhook_url': self.webhook_url
            }

# Глобальный экземпляр сервиса
bitrix_service = BitrixService()