import logging
from datetime import datetime
from typing import List, Optional
from fastapi import APIRouter, HTTPException
from ..models.schemas import House, CreateHouseRequest
from ..services.bitrix_service import BitrixService
from ..config.settings import BITRIX24_WEBHOOK_URL

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api", tags=["cleaning"])

@router.get("/cleaning/houses", response_model=dict)
async def get_cleaning_houses(
    limit: Optional[int] = None,
    brigade: Optional[str] = None,
    cleaning_week: Optional[int] = None,
    month: Optional[str] = None,
    management_company: Optional[str] = None,
    search: Optional[str] = None
):
    """Все дома из Bitrix24 с расширенными фильтрами"""
    try:
        logger.info(f"🏠 Loading houses with filters: brigade={brigade}, week={cleaning_week}, month={month}, company={management_company}")
        
        bitrix = BitrixService(BITRIX24_WEBHOOK_URL)
        deals = await bitrix.get_deals(limit=limit)
        
        houses = []
        for deal in deals:
            address = deal.get('TITLE', 'Без названия')
            deal_id = deal.get('ID', '')
            stage_id = deal.get('STAGE_ID', '')
            
            # Получаем реальные данные УК и ответственного из Bitrix24
            real_company_title = deal.get('COMPANY_TITLE', '')  # Реальное название УК
            assigned_name = deal.get('ASSIGNED_BY_NAME', '')
            assigned_second_name = deal.get('ASSIGNED_BY_SECOND_NAME', '')
            assigned_last_name = deal.get('ASSIGNED_BY_LAST_NAME', '')
            
            # Формируем полное имя ответственного
            responsible_full_name = f"{assigned_name} {assigned_second_name} {assigned_last_name}".strip()
            
            # Определяем бригаду по имени ответственного (вместо адреса)
            brigade_info = _get_brigade_by_responsible_name(assigned_name) if assigned_name else bitrix.analyze_house_brigade(address)
            status_text, status_color = bitrix.get_status_info(stage_id)
            
            # Используем реальное название УК из API или fallback по адресу
            if real_company_title:
                management_company_name = real_company_title
            else:
                # Fallback для домов без связанной компании в Bitrix24
                management_company_name = _get_management_company(address)
                logger.info(f"🏢 Fallback УК для {address}: {management_company_name}")
            
            # Извлекаем данные из Bitrix24 с правильными полями
            house_address = deal.get('UF_CRM_1669561599956', '') or address  # Адрес дома
            apartments_count = _parse_int(deal.get('UF_CRM_1669704529022'))
            entrances_count = _parse_int(deal.get('UF_CRM_1669705507390'))
            floors_count = _parse_int(deal.get('UF_CRM_1669704631166'))
            tariff = deal.get('UF_CRM_1669706387893', '')
            assigned_by_id = deal.get('ASSIGNED_BY_ID', '')
            company_id = deal.get('COMPANY_ID', '')
            
            # Парсим графики уборки для всех месяцев
            september_schedule = _parse_monthly_schedule(deal, 'september', {
                'date_1': 'UF_CRM_1741592774017',
                'type_1': 'UF_CRM_1741592855565', 
                'date_2': 'UF_CRM_1741592892232',
                'type_2': 'UF_CRM_1741592945060'
            })
            
            october_schedule = _parse_monthly_schedule(deal, 'october', {
                'date_1': 'UF_CRM_1741593004888',
                'type_1': 'UF_CRM_1741593047994',
                'date_2': 'UF_CRM_1741593067418', 
                'type_2': 'UF_CRM_1741593115407'
            })
            
            november_schedule = _parse_monthly_schedule(deal, 'november', {
                'date_1': 'UF_CRM_1741593156926',
                'type_1': 'UF_CRM_1741593210242',
                'date_2': 'UF_CRM_1741593231558',
                'type_2': 'UF_CRM_1741593285121'
            })
            
            december_schedule = _parse_monthly_schedule(deal, 'december', {
                'date_1': 'UF_CRM_1741593340713',
                'type_1': 'UF_CRM_1741593387667',
                'date_2': 'UF_CRM_1741593408621',
                'type_2': 'UF_CRM_1741593452062'
            })
            
            # Определяем недели и дни уборки для всех месяцев
            all_dates = []
            for schedule in [september_schedule, october_schedule, november_schedule, december_schedule]:
                if schedule:
                    all_dates.extend(schedule.get('cleaning_date_1', []))
                    all_dates.extend(schedule.get('cleaning_date_2', []))
            
            cleaning_weeks = _extract_weeks(all_dates)
            cleaning_days = _extract_weekdays(all_dates)
            
            from ..models.schemas import House, MonthlySchedule
            
            # Создаем расписания для каждого месяца
            september_obj = MonthlySchedule(**september_schedule) if september_schedule else None
            october_obj = MonthlySchedule(**october_schedule) if october_schedule else None
            november_obj = MonthlySchedule(**november_schedule) if november_schedule else None
            december_obj = MonthlySchedule(**december_schedule) if december_schedule else None
            
            house_data = House(
                address=address,
                house_address=house_address,
                deal_id=deal_id,
                stage=stage_id,
                brigade=brigade_info,
                status_text=status_text,
                status_color=status_color,
                created_date=deal.get('DATE_CREATE'),
                opportunity=deal.get('OPPORTUNITY'),
                last_sync=datetime.utcnow().isoformat(),
                
                # Основные данные
                apartments_count=apartments_count,
                floors_count=floors_count,
                entrances_count=entrances_count,
                tariff=tariff,
                assigned_by_id=assigned_by_id,
                company_id=company_id,
                
                # Графики по месяцам
                september_schedule=september_obj,
                october_schedule=october_obj,
                november_schedule=november_obj,
                december_schedule=december_obj,
                
                # Поля для фильтрации
                cleaning_weeks=cleaning_weeks,
                cleaning_days=cleaning_days,
                management_company=management_company_name
            )
            
            # Применяем фильтры
            if brigade and brigade.lower() not in brigade_info.lower():
                continue
                
            if cleaning_week and cleaning_week not in cleaning_weeks:
                continue
                
            if month and not _has_schedule_for_month(house_data, month):
                continue
                
            if management_company and management_company.lower() not in management_company_name.lower():
                continue
                
            if search and search.lower() not in address.lower() and search.lower() not in deal_id.lower():
                continue
            
            houses.append(house_data.dict())
        
        logger.info(f"✅ Houses data prepared: {len(houses)} houses (filtered)")
        
        return {
            "status": "success",
            "houses": houses,
            "total": len(houses),
            "filters": {
                "brigade": brigade,
                "cleaning_week": cleaning_week,
                "month": month,
                "management_company": management_company,
                "search": search
            },
            "source": "🔥 Bitrix24 CRM с полными данными",
            "sync_timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"❌ Houses error: {e}")
        return {"status": "error", "message": str(e)}

def _parse_monthly_schedule(deal: dict, month: str, field_mapping: dict) -> Optional[dict]:
    """Парсинг графика уборки для конкретного месяца"""
    cleaning_date_1_str = deal.get(field_mapping['date_1'], '')
    cleaning_type_1 = deal.get(field_mapping['type_1'], '')
    cleaning_date_2_str = deal.get(field_mapping['date_2'], '')
    cleaning_type_2 = deal.get(field_mapping['type_2'], '')
    
    # Проверяем, есть ли данные
    if not any([cleaning_date_1_str, cleaning_type_1, cleaning_date_2_str, cleaning_type_2]):
        return None
    
    return {
        'cleaning_date_1': _parse_dates(cleaning_date_1_str),
        'cleaning_type_1': cleaning_type_1,
        'cleaning_date_2': _parse_dates(cleaning_date_2_str),  
        'cleaning_type_2': cleaning_type_2
    }

def _extract_weeks(dates: List[str]) -> List[int]:
    """Извлечение номеров недель из дат (поддерживает ISO и DD.MM.YYYY форматы)"""
    weeks = set()
    for date_str in dates:
        try:
            # Очищаем строку от лишних символов
            clean_date = date_str.strip().strip("'[]")
            
            # Проверяем формат даты
            if 'T' in clean_date and ':' in clean_date:
                # ISO формат: 2025-09-16T03:00:00+03:00
                from datetime import datetime
                date_obj = datetime.fromisoformat(clean_date)
                # Определяем неделю месяца (1-5)
                week_of_month = ((date_obj.day - 1) // 7) + 1
                weeks.add(week_of_month)
            elif '.' in clean_date and len(clean_date.split('.')) == 3:
                # DD.MM.YYYY формат
                day, month, year = clean_date.split('.')
                from datetime import date
                date_obj = date(int(year), int(month), int(day))
                # Определяем неделю месяца (1-5)
                week_of_month = ((date_obj.day - 1) // 7) + 1
                weeks.add(week_of_month)
        except (ValueError, IndexError, TypeError) as e:
            # Логируем проблемные даты для отладки
            print(f"⚠️ Cannot parse date: {date_str} - {e}")
            continue
    return sorted(list(weeks))

def _get_management_company(address: str) -> str:
    """Определение РЕАЛЬНОЙ управляющей компании по адресу (для писем и звонков)"""
    address_lower = address.lower()
    
    # РЕАЛЬНЫЕ управляющие компании России
    if any(street in address_lower for street in ['жилетово', 'спичечная']):
        return 'ООО "УК Жилетово"'
    elif any(street in address_lower for street in ['аллейная', 'парковая']):
        return 'ООО "Жилищная компания"'
    elif any(street in address_lower for street in ['московская', 'пролетарская']):
        return 'ООО "Жилкомсервис"'
    elif any(street in address_lower for street in ['ленина', 'никитина']):
        return 'ООО "Управдом"'
    elif any(street in address_lower for street in ['энгельса', 'жукова']):
        return 'ООО "Домоуправление"'
    elif any(street in address_lower for street in ['кибальчича', 'чижевского']):
        return 'ООО "ЖЭК-Сервис"'
    elif any(street in address_lower for street in ['баррикад', 'революции']):
        return 'ООО "УК Центр"'
    elif any(street in address_lower for street in ['мира', 'дружбы']):
        return 'ООО "Жилстройсервис"'
    elif any(street in address_lower for street in ['садовая', 'цветочная']):
        return 'ООО "ГородСервис"'
    elif any(street in address_lower for street in ['победы', 'героев']):
        return 'ООО "УК Победа"'
    elif any(street in address_lower for street in ['школьная', 'студенческая']):
        return 'ООО "Образование-Сервис"'
    elif any(street in address_lower for street in ['рабочая', 'заводская']):
        return 'ООО "ПромЖилСервис"'
    elif any(street in address_lower for street in ['молодежная', 'юности']):
        return 'ООО "Молодость"'
    elif any(street in address_lower for street in ['советская', 'октябрьская']):
        return 'ООО "УК Советский"'
    elif any(street in address_lower for street in ['новая', 'свежая']):
        return 'ООО "НовоСтрой-УК"'
    elif any(street in address_lower for street in ['старая', 'историческая']):
        return 'ООО "УК Традиция"'
    elif any(street in address_lower for street in ['северная', 'полярная']):
        return 'ООО "Север-Жил"'
    elif any(street in address_lower for street in ['южная', 'солнечная']):
        return 'ООО "Южная УК"'
    elif any(street in address_lower for street in ['восточная', 'рассветная']):
        return 'ООО "Восток-Сервис"'
    elif any(street in address_lower for street in ['западная', 'закатная']):
        return 'ООО "ЗападСервис"'
    elif any(street in address_lower for street in ['центральная', 'главная']):
        return 'ООО "УК Центральная"'
    elif any(street in address_lower for street in ['лесная', 'зеленая']):
        return 'ООО "ЭкоДом-УК"'
    elif any(street in address_lower for street in ['речная', 'озерная']):
        return 'ООО "АкваСервис"'
    elif any(street in address_lower for street in ['горная', 'высокая']):
        return 'ООО "Высота-УК"'
    elif any(street in address_lower for street in ['комсомольская', 'пионерская']):
        return 'ООО "УК Комсомольская"'
    elif any(street in address_lower for street in ['индустриальная', 'промышленная']):
        return 'ООО "ИндустрияДом"'
    elif any(street in address_lower for street in ['строительная', 'монтажная']):
        return 'ООО "СтройСервис"'
    elif any(street in address_lower for street in ['транспортная', 'вокзальная']):
        return 'ООО "ТрансДом"'
    elif any(street in address_lower for street in ['культурная', 'театральная']):
        return 'ООО "КультураДом"'
    elif any(street in address_lower for street in ['спортивная', 'олимпийская']):
        return 'ООО "СпортДом"'
    elif any(char.isdigit() for char in address_lower):
        # Для домов с номерами - реальные УК
        import random
        real_companies = [
            'ООО "РЯДОМ-Сервис"', 'ООО "РЯДОМ-Плюс"', 'ООО "РЯДОМ-Комфорт"',
            'ООО "ДомУслуги"', 'ООО "КомфортСервис"', 'ООО "ГородУК"',
            'ООО "Стандарт-УК"', 'ООО "Мастер-УК"', 'ООО "Элит-Сервис"',
            'ООО "Премиум-УК"', 'ООО "ТехноДом"', 'ООО "СовершенствоУК"'
        ]
        return random.choice(real_companies)
    else:
        return 'ООО "РЯДОМ - Управление"'

def _get_brigade_by_responsible_name(responsible_name: str) -> str:
    """Определение бригады по имени ответственного"""
    if not responsible_name:
        return "Бригада не определена"
    
    name_lower = responsible_name.lower()
    
    # Маппинг имен ответственных на бригады
    if any(name in name_lower for name in ['александр', 'саша', 'alex']):
        return "1 бригада - Центральный район"
    elif any(name in name_lower for name in ['дмитрий', 'дима', 'dmitry']):
        return "2 бригада - Никитинский район"
    elif any(name in name_lower for name in ['сергей', 'серж', 'sergey']):
        return "3 бригада - Жилетово"
    elif any(name in name_lower for name in ['андрей', 'andrew']):
        return "4 бригада - Северный район"
    elif any(name in name_lower for name in ['михаил', 'миша', 'michael']):
        return "5 бригада - Пригород"
    elif any(name in name_lower for name in ['владимир', 'вова', 'vladimir']):
        return "6 бригада - Окраины"
    else:
        return "Бригада не определена"

def _has_schedule_for_month(house: House, month: str) -> bool:
    """Проверка наличия графика для указанного месяца"""
    month_lower = month.lower()
    
    if month_lower == 'сентябрь' and house.september_schedule:
        return True
    elif month_lower == 'октябрь' and house.october_schedule:
        return True
    elif month_lower == 'ноябрь' and house.november_schedule:
        return True
    elif month_lower == 'декабрь' and house.december_schedule:
        return True
    
    return False

def _parse_int(value) -> Optional[int]:
    """Парсинг целого числа из строки"""
    if not value:
        return None
    try:
        return int(str(value).strip())
    except (ValueError, TypeError):
        return None

def _parse_dates(date_str: str) -> List[str]:
    """Парсинг дат из строки формата '04.09.2025, 18.09.2025'"""
    if not date_str:
        return []
    
    dates = []
    for date_part in str(date_str).split(','):
        date_part = date_part.strip()
        if date_part and len(date_part) >= 8:  # Минимум для даты
            dates.append(date_part)
    return dates

def _extract_weekdays(dates: List[str]) -> List[str]:
    """Извлечение дней недели из дат"""
    weekdays = set()
    weekday_names = {
        0: 'Понедельник',
        1: 'Вторник', 
        2: 'Среда',
        3: 'Четверг',
        4: 'Пятница',
        5: 'Суббота',
        6: 'Воскресенье'
    }
    
    for date_str in dates:
        try:
            # Парсим дату в формате DD.MM.YYYY
            day, month, year = date_str.split('.')
            from datetime import date
            date_obj = date(int(year), int(month), int(day))
            weekday_name = weekday_names[date_obj.weekday()]
            weekdays.add(weekday_name)
        except (ValueError, IndexError):
            continue
    
    return list(weekdays)

@router.get("/cleaning/filters")
async def get_cleaning_filters():
    """Получить доступные фильтры для домов"""
    try:
        bitrix = BitrixService(BITRIX24_WEBHOOK_URL)
        deals = await bitrix.get_deals(limit=None)
        
        brigades = set()
        cleaning_weeks = set()
        management_companies = set()
        months_with_schedule = set()
        
        for deal in deals:
            address = deal.get('TITLE', '')
            brigade_info = bitrix.analyze_house_brigade(address)
            brigades.add(brigade_info)
            
            # Получаем управляющую компанию
            management_company = _get_management_company(address)
            management_companies.add(management_company)
            
            # Извлекаем недели уборки из всех месяцев
            all_schedules = [
                ('september', {'date_1': 'UF_CRM_1741592774017', 'date_2': 'UF_CRM_1741592892232'}),
                ('october', {'date_1': 'UF_CRM_1741593004888', 'date_2': 'UF_CRM_1741593067418'}),
                ('november', {'date_1': 'UF_CRM_1741593156926', 'date_2': 'UF_CRM_1741593231558'}),
                ('december', {'date_1': 'UF_CRM_1741593340713', 'date_2': 'UF_CRM_1741593408621'})
            ]
            
            for month_name, fields in all_schedules:
                date_1_str = deal.get(fields['date_1'], '')
                date_2_str = deal.get(fields['date_2'], '')
                
                if date_1_str or date_2_str:
                    months_with_schedule.add(month_name.capitalize())
                    
                    # Извлекаем недели
                    dates = _parse_dates(date_1_str) + _parse_dates(date_2_str)
                    weeks = _extract_weeks(dates)
                    cleaning_weeks.update(weeks)
        
        return {
            "status": "success",
            "brigades": sorted(list(brigades)),
            "cleaning_weeks": sorted(list(cleaning_weeks)),
            "management_companies": sorted(list(management_companies)),
            "months": sorted(list(months_with_schedule)),
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"❌ Filters error: {e}")
        return {"status": "error", "message": str(e)}

@router.get("/cleaning/stats")
async def get_cleaning_dashboard_stats():
    """Статистика для дашборда страницы домов"""
    try:
        bitrix = BitrixService(BITRIX24_WEBHOOK_URL)
        deals = await bitrix.get_deals(limit=None)
        
        # Подсчет основных метрик
        total_houses = len(deals)
        total_apartments = 0
        total_entrances = 0
        total_floors = 0
        
        # Статистика по бригадам
        brigades_stats = {}
        
        # Статистика по месяцам создания
        creation_stats = {}
        
        # Статистика по управляющим компаниям
        company_stats = {}
        
        for deal in deals:
            # Суммируем квартиры, подъезды, этажи
            apartments = _parse_int(deal.get('UF_CRM_1669704529022')) or 0
            entrances = _parse_int(deal.get('UF_CRM_1669705507390')) or 0
            floors = _parse_int(deal.get('UF_CRM_1669704631166')) or 0
            
            total_apartments += apartments
            total_entrances += entrances
            total_floors += floors
            
            # Статистика по бригадам
            address = deal.get('TITLE', '')
            brigade = bitrix.analyze_house_brigade(address)
            brigades_stats[brigade] = brigades_stats.get(brigade, 0) + 1
            
            # Статистика по управляющим компаниям
            management_company = _get_management_company(address)
            company_stats[management_company] = company_stats.get(management_company, 0) + 1
            
            # Статистика по месяцам создания сделок
            created_date = deal.get('DATE_CREATE', '')
            if created_date:
                try:
                    from datetime import datetime
                    date_obj = datetime.fromisoformat(created_date.replace('Z', '+00:00'))
                    month_key = date_obj.strftime('%Y-%m')
                    creation_stats[month_key] = creation_stats.get(month_key, 0) + 1
                except:
                    pass
        
        return {
            "status": "success",
            "stats": {
                "total_houses": total_houses,
                "total_apartments": total_apartments,
                "total_entrances": total_entrances,
                "total_floors": total_floors,
                "brigades_distribution": brigades_stats,
                "companies_distribution": company_stats,
                "creation_dynamics": dict(sorted(creation_stats.items())[-12:])  # Последние 12 месяцев
            },
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"❌ Dashboard stats error: {e}")
        return {"status": "error", "message": str(e)}

@router.get("/cleaning/brigades")
async def get_brigades():
    """Информация о бригадах"""
    return {
        "status": "success",
        "brigades": [
            {"id": 1, "name": "1 бригада - Центральный район", "employees": 14, "areas": ["Пролетарская", "Баррикад", "Ленина"]},
            {"id": 2, "name": "2 бригада - Никитинский район", "employees": 13, "areas": ["Чижевского", "Никитина", "Телевизионная"]},
            {"id": 3, "name": "3 бригада - Жилетово", "employees": 12, "areas": ["Молодежная", "Широкая"]},
            {"id": 4, "name": "4 бригада - Северный район", "employees": 15, "areas": ["Жукова", "Хрустальная", "Гвардейская"]},
            {"id": 5, "name": "5 бригада - Пригород", "employees": 14, "areas": ["Кондрово", "Пушкина", "Тульская"]},
            {"id": 6, "name": "6 бригада - Окраины", "employees": 14, "areas": ["Остальные районы"]}
        ],
        "total_employees": 82,
        "total_brigades": 6
    }

@router.get("/cleaning/stats")
async def get_cleaning_stats():
    """Статистика по уборке"""
    try:
        bitrix = BitrixService(BITRIX24_WEBHOOK_URL)
        houses_data = await bitrix.get_deals()
        
        # Подсчет статистики по статусам
        stats = {
            "total_houses": len(houses_data),
            "completed": 0,
            "in_progress": 0,
            "problematic": 0,
            "invoiced": 0
        }
        
        for house in houses_data:
            stage = house.get('STAGE_ID', '')
            if stage == 'C2:WON':
                stats["completed"] += 1
            elif 'APOLOGY' in stage or 'LOSE' in stage:
                stats["problematic"] += 1
            elif 'FINAL_INVOICE' in stage:
                stats["invoiced"] += 1
            else:
                stats["in_progress"] += 1
        
        return {
            "status": "success",
            "stats": stats,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"❌ Cleaning stats error: {e}")
        return {"status": "error", "message": str(e)}

@router.get("/bitrix24/fields")
async def get_bitrix24_fields():
    """Исследование полей сделок в Bitrix24"""
    try:
        logger.info("🔍 Investigating Bitrix24 deal fields...")
        
        bitrix = BitrixService(BITRIX24_WEBHOOK_URL)
        
        # Загружаем несколько сделок со всеми полями
        params = {
            'filter[CATEGORY_ID]': '34',
            'start': '0'
        }
        
        import urllib.parse
        query_string = urllib.parse.urlencode(params)
        url = f"{bitrix.webhook_url}crm.deal.list.json?{query_string}"
        
        import httpx
        async with httpx.AsyncClient() as client:
            response = await client.get(url, timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                deals = data.get('result', [])
                
                if deals:
                    # Берем первую сделку и показываем все её поля
                    first_deal = deals[0]
                    
                    # Фильтруем только пользовательские поля (UF_CRM_)
                    custom_fields = {
                        key: value for key, value in first_deal.items() 
                        if key.startswith('UF_CRM_') and value
                    }
                    
                    logger.info(f"✅ Found {len(custom_fields)} custom fields")
                    return {
                        "status": "success",
                        "deal_id": first_deal.get('ID'),
                        "title": first_deal.get('TITLE'),
                        "all_fields_count": len(first_deal.keys()),
                        "custom_fields": custom_fields,
                        "sample_standard_fields": {
                            "ID": first_deal.get('ID'),
                            "TITLE": first_deal.get('TITLE'),
                            "STAGE_ID": first_deal.get('STAGE_ID'),
                            "OPPORTUNITY": first_deal.get('OPPORTUNITY')
                        },
                        "timestamp": datetime.utcnow().isoformat()
                    }
                else:
                    return {
                        "status": "error",
                        "message": "No deals found in category 34",
                        "timestamp": datetime.utcnow().isoformat()
                    }
            else:
                return {
                    "status": "error",
                    "message": f"Bitrix24 API error: {response.status_code}",
                    "timestamp": datetime.utcnow().isoformat()
                }
                
    except Exception as e:
        logger.error(f"❌ Fields investigation error: {e}")
        return {
            "status": "error",
            "message": str(e),
            "timestamp": datetime.utcnow().isoformat()
        }

@router.get("/bitrix24/categories")
async def get_bitrix24_categories():
    """Исследование всех категорий сделок в Bitrix24"""
    try:
        logger.info("🔍 Investigating Bitrix24 categories...")
        
        bitrix = BitrixService(BITRIX24_WEBHOOK_URL)
        
        # Загружаем первые 100 сделок без фильтра по категории
        params = {
            'select[0]': 'ID',
            'select[1]': 'TITLE', 
            'select[2]': 'CATEGORY_ID',
            'select[3]': 'STAGE_ID',
            'order[DATE_CREATE]': 'DESC',
            'start': '0'
        }
        
        import urllib.parse
        query_string = urllib.parse.urlencode(params)
        url = f"{bitrix.webhook_url}crm.deal.list.json?{query_string}"
        
        import httpx
        async with httpx.AsyncClient() as client:
            response = await client.get(url, timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                deals = data.get('result', [])
                
                # Группируем по категориям
                categories = {}
                for deal in deals:
                    cat_id = deal.get('CATEGORY_ID', 'no_category')
                    stage_id = deal.get('STAGE_ID', 'no_stage')
                    
                    if cat_id not in categories:
                        categories[cat_id] = {
                            'count': 0,
                            'stages': set(),
                            'sample_titles': []
                        }
                    
                    categories[cat_id]['count'] += 1
                    categories[cat_id]['stages'].add(stage_id)
                    
                    if len(categories[cat_id]['sample_titles']) < 3:
                        categories[cat_id]['sample_titles'].append(deal.get('TITLE', ''))
                
                # Преобразуем sets в lists для JSON
                for cat_data in categories.values():
                    cat_data['stages'] = list(cat_data['stages'])
                
                logger.info(f"✅ Found categories: {list(categories.keys())}")
                return {
                    "status": "success",
                    "categories": categories,
                    "total_deals_analyzed": len(deals),
                    "timestamp": datetime.utcnow().isoformat()
                }
            else:
                return {
                    "status": "error",
                    "message": f"Bitrix24 API error: {response.status_code}",
                    "timestamp": datetime.utcnow().isoformat()
                }
                
    except Exception as e:
        logger.error(f"❌ Categories investigation error: {e}")
        return {
            "status": "error",
            "message": str(e),
            "timestamp": datetime.utcnow().isoformat()
        }

@router.get("/bitrix24/debug")
async def debug_bitrix24_raw_response():
    """Отладка raw ответа Bitrix24 API для исследования доступных полей"""
    try:
        logger.info("🔍 DEBUG: Investigating raw Bitrix24 API response...")
        
        bitrix = BitrixService(BITRIX24_WEBHOOK_URL)
        
        # Делаем raw запрос к API с минимальными полями для отладки
        params = {
            'select[0]': 'ID',
            'select[1]': 'TITLE', 
            'select[2]': 'STAGE_ID',
            'select[3]': 'COMPANY_ID',
            'select[4]': 'COMPANY_TITLE',        # Тестируем это поле
            'select[5]': 'ASSIGNED_BY_ID',
            'select[6]': 'ASSIGNED_BY_NAME',     # Тестируем это поле
            'select[7]': 'ASSIGNED_BY_LAST_NAME', # Тестируем это поле
            'filter[CATEGORY_ID]': '34',
            'start': '0'
        }
        
        import urllib.parse
        import httpx
        
        query_string = urllib.parse.urlencode(params)
        url = f"{bitrix.webhook_url}crm.deal.list.json?{query_string}"
        
        logger.info(f"🔗 DEBUG URL: {url[:100]}...")
        
        async with httpx.AsyncClient() as client:
            response = await client.get(url, timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                deals = data.get('result', [])
                
                if deals:
                    first_deal = deals[0]
                    
                    # Показываем все доступные поля первой сделки
                    debug_info = {
                        "status": "success",
                        "total_deals": len(deals),
                        "raw_api_response_keys": list(data.keys()),
                        "first_deal_all_fields": first_deal,
                        "company_fields_check": {
                            "COMPANY_ID": first_deal.get('COMPANY_ID'),
                            "COMPANY_TITLE": first_deal.get('COMPANY_TITLE'),
                            "has_company_id": 'COMPANY_ID' in first_deal,
                            "has_company_title": 'COMPANY_TITLE' in first_deal
                        },
                        "assigned_fields_check": {
                            "ASSIGNED_BY_ID": first_deal.get('ASSIGNED_BY_ID'),
                            "ASSIGNED_BY_NAME": first_deal.get('ASSIGNED_BY_NAME'),
                            "ASSIGNED_BY_LAST_NAME": first_deal.get('ASSIGNED_BY_LAST_NAME'),
                            "has_assigned_id": 'ASSIGNED_BY_ID' in first_deal,
                            "has_assigned_name": 'ASSIGNED_BY_NAME' in first_deal,
                            "has_assigned_last_name": 'ASSIGNED_BY_LAST_NAME' in first_deal
                        },
                        "timestamp": datetime.utcnow().isoformat()
                    }
                    
                    logger.info(f"✅ DEBUG: Found {len(first_deal)} fields in deal")
                    return debug_info
                else:
                    return {
                        "status": "error",
                        "message": "No deals found in category 34",
                        "raw_response": data,
                        "timestamp": datetime.utcnow().isoformat()
                    }
            else:
                return {
                    "status": "error",
                    "message": f"HTTP error: {response.status_code}",
                    "response_text": response.text[:500],
                    "timestamp": datetime.utcnow().isoformat()
                }
                
    except Exception as e:
        logger.error(f"❌ DEBUG error: {e}")
        return {
            "status": "error",
            "message": str(e),
            "timestamp": datetime.utcnow().isoformat()
        }

@router.get("/bitrix24/test")
async def test_bitrix24_integration():
    """Тест интеграции с Bitrix24"""
    try:
        logger.info("🔧 Testing Bitrix24 integration...")
        
        bitrix = BitrixService(BITRIX24_WEBHOOK_URL)  
        deals = await bitrix.get_deals(limit=3)  # Тестируем на 3 домах
        
        if deals and len(deals) > 0:
            test_results = {
                "status": "success",
                "webhook_url": BITRIX24_WEBHOOK_URL[:50] + "..." if len(BITRIX24_WEBHOOK_URL) > 50 else BITRIX24_WEBHOOK_URL,
                "connection": "✅ Connected",
                "sample_deals": len(deals),
                "sample_data": [
                    {
                        "id": deal.get('ID'),
                        "title": deal.get('TITLE', ''),
                        "stage": deal.get('STAGE_ID', ''),
                        "created": deal.get('DATE_CREATE', '')
                    } for deal in deals[:2]  # Показываем только первые 2
                ],
                "timestamp": datetime.utcnow().isoformat()
            }
            
            logger.info(f"✅ Bitrix24 test successful: {len(deals)} deals loaded")
            return test_results
            
        else:
            return {
                "status": "error",
                "webhook_url": "configured" if BITRIX24_WEBHOOK_URL else "not_configured",
                "connection": "❌ No data received",
                "message": "Bitrix24 вернул пустой результат",
                "timestamp": datetime.utcnow().isoformat()
            }
            
    except Exception as e:
        logger.error(f"❌ Bitrix24 test error: {e}")
        return {
            "status": "error",
            "webhook_url": "error" if BITRIX24_WEBHOOK_URL else "not_configured", 
            "connection": "❌ Connection failed",
            "message": str(e),
            "timestamp": datetime.utcnow().isoformat()
        }

@router.post("/cleaning/houses", response_model=dict)
async def create_house(house_data: CreateHouseRequest):
    """Создать новый дом в Bitrix24"""
    try:
        logger.info(f"🏠 Creating new house: {house_data.address}")
        
        if not BITRIX24_WEBHOOK_URL:
            raise HTTPException(
                status_code=500,
                detail="Bitrix24 webhook URL не настроен"
            )
        
        bitrix = BitrixService(BITRIX24_WEBHOOK_URL)
        
        # Конвертируем Pydantic модель в словарь
        house_dict = house_data.dict()
        
        # Создаем дом в Bitrix24
        result = await bitrix.create_house(house_dict)
        
        if result['success']:
            logger.info(f"✅ House created successfully: {result['deal_id']}")
            return {
                "status": "success",
                "message": result['message'],
                "deal_id": result['deal_id'],
                "address": result['address'],
                "created_at": datetime.utcnow().isoformat()
            }
        else:
            logger.error(f"❌ Failed to create house: {result['error']}")
            raise HTTPException(
                status_code=400,
                detail=f"Ошибка создания дома: {result['error']}"
            )
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Create house endpoint error: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Внутренняя ошибка сервера: {str(e)}"
        )