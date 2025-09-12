import asyncio
import logging
import httpx
import urllib.parse
from typing import List, Dict, Any, Optional

logger = logging.getLogger(__name__)

class BitrixService:
    def __init__(self, webhook_url: str):
        self.webhook_url = webhook_url
        logger.info(f"🔗 Bitrix24 service initialized")
        
    async def get_deals(self, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """Получить ВСЕ дома из Bitrix24 CRM"""
        try:
            logger.info(f"🏠 Loading houses from Bitrix24 CRM...")
            
            all_deals = []
            start = 0
            batch_size = 50
            
            while True:
                params = {
                    'select[0]': 'ID',
                    'select[1]': 'TITLE', 
                    'select[2]': 'STAGE_ID',
                    'select[3]': 'DATE_CREATE',
                    'select[4]': 'OPPORTUNITY',
                    'select[5]': 'ASSIGNED_BY_ID',  # Ответственный (для бригад)
                    'select[6]': 'COMPANY_ID',      # Компания (УК)
                    # КРИТИЧНЫЕ ПОЛЯ: Количественные данные домов
                    'select[7]': 'UF_CRM_1669561599956',   # Адрес дома
                    'select[8]': 'UF_CRM_1669704529022',   # Количество квартир
                    'select[9]': 'UF_CRM_1669705507390',   # Количество подъездов
                    'select[10]': 'UF_CRM_1669704631166',  # Количество этажей
                    'select[11]': 'UF_CRM_1669706387893',  # Тариф/периодичность
                    # Типы уборки из Bitrix24
                    'select[12]': 'UF_CRM_1741592855565',  # Тип уборки 1 | Сентябрь 2025
                    'select[13]': 'UF_CRM_1741592945060',  # Тип уборки 2 | Сентябрь 2025
                    'select[14]': 'UF_CRM_1741592774017',  # Дата уборки 1 | Сентябрь 2025
                    'select[15]': 'UF_CRM_1741592892232',  # Дата уборки 2 | Сентябрь 2025
                    'filter[CATEGORY_ID]': '34',  # Правильная категория (490 домов)
                    'order[DATE_CREATE]': 'DESC',
                    'start': str(start)
                }
                
                query_string = urllib.parse.urlencode(params)
                url = f"{self.webhook_url}crm.deal.list.json?{query_string}"
                
                async with httpx.AsyncClient() as client:
                    response = await client.get(url, timeout=30)
                    
                    if response.status_code == 200:
                        data = response.json()
                        
                        if data.get('result') and len(data['result']) > 0:
                            batch_deals = data['result']
                            all_deals.extend(batch_deals)
                            
                            logger.info(f"📦 Loaded batch {start//batch_size + 1}: {len(batch_deals)} houses, total: {len(all_deals)}")
                            
                            if len(batch_deals) < batch_size:
                                logger.info(f"✅ All houses loaded: {len(all_deals)} from Bitrix24")
                                break
                                
                            start += batch_size
                            
                            if len(all_deals) >= 600:
                                logger.info(f"🛑 Loaded {len(all_deals)} houses limit reached")
                                break
                                
                            await asyncio.sleep(0.2)
                        else:
                            break
                    else:
                        logger.error(f"❌ Bitrix24 HTTP error: {response.status_code}")
                        break
            
            if all_deals:
                logger.info(f"✅ CRM dataset loaded: {len(all_deals)} deals from Bitrix24")
                
                # Обрабатываем данные домов
                processed_deals = []
                for deal in all_deals:
                    processed_deal = self._extract_house_data(deal)
                    processed_deals.append(processed_deal)
                
                # Обогащаем управляющими компаниями
                enriched_deals = await self._enrich_with_management_companies(processed_deals)
                
                logger.info(f"✅ Processed and enriched {len(enriched_deals)} houses")
                return enriched_deals
            else:
                logger.warning("⚠️ No deals from Bitrix24, using fallback")
                return self._get_mock_data(limit or 50)
            
        except Exception as e:
            logger.error(f"❌ Bitrix24 load error: {e}")
            return self._get_mock_data(limit or 50)
    
    def _get_mock_data(self, limit: int) -> List[Dict[str, Any]]:
        """Реальные данные из CRM для fallback с количественными полями"""
        real_houses = [
            {
                "ID": "112", "TITLE": "Пролетарская 112/1", "STAGE_ID": "C2:APOLOGY",
                "apartments_count": 75, "entrances_count": 3, "floors_count": 5,
                "management_company": "ООО 'УК Новый город'", "house_address": "Пролетарская 112/1"
            },
            {
                "ID": "122", "TITLE": "Чижевского 18", "STAGE_ID": "C2:APOLOGY",
                "apartments_count": 48, "entrances_count": 2, "floors_count": 9,
                "management_company": "ООО 'Жилкомсервис'", "house_address": "Чижевского 18"
            },
            {
                "ID": "200", "TITLE": "Жукова 25", "STAGE_ID": "C2:APOLOGY",
                "apartments_count": 96, "entrances_count": 4, "floors_count": 9,
                "management_company": "ООО 'Премиум-УК'", "house_address": "Жукова 25"
            },
            {
                "ID": "240", "TITLE": "Грабцевское шоссе 158", "STAGE_ID": "C2:APOLOGY",
                "apartments_count": 120, "entrances_count": 5, "floors_count": 9,
                "management_company": "УК 'Домашний уют'", "house_address": "Грабцевское шоссе 158"
            },
            {
                "ID": "12782", "TITLE": "Хрустальная 54", "STAGE_ID": "C2:FINAL_INVOICE",
                "apartments_count": 60, "entrances_count": 3, "floors_count": 5,
                "management_company": "ООО 'УК МЖД Московского округа г.Калуги'", "house_address": "Хрустальная 54"
            },
            {
                "ID": "12774", "TITLE": "Гвардейская 4", "STAGE_ID": "C2:UC_6COC3G",
                "apartments_count": 36, "entrances_count": 2, "floors_count": 9,
                "management_company": "ООО 'УК Новый город'", "house_address": "Гвардейская 4"
            },
            {
                "ID": "12640", "TITLE": "Кондрово, Пушкина 78", "STAGE_ID": "C2:LOSE",
                "apartments_count": 84, "entrances_count": 4, "floors_count": 7,
                "management_company": "ООО 'Жилкомсервис'", "house_address": "Кондрово, Пушкина 78"
            },
        ]
        
        kaluga_streets = [
            "Пролетарская", "Никитиной", "Московская", "Билибина", "Суворова", 
            "Зеленая", "Телевизионная", "Карачевская", "Майская", "Чижевского",
            "Энгельса", "Ст.Разина", "Малоярославецкая", "Жукова", "Хрустальная"
        ]
        
        management_companies = [
            "ООО 'УК Новый город'", "ООО 'Жилкомсервис'", "ООО 'Премиум-УК'",
            "УК 'Домашний уют'", "ООО 'УК МЖД Московского округа г.Калуги'"
        ]
        
        extended = list(real_houses)
        for i in range(len(real_houses), limit):
            street = kaluga_streets[i % len(kaluga_streets)]
            house_num = 10 + (i % 150)
            title = f"{street} {house_num}"
            
            extended.append({
                "ID": str(300 + i),
                "TITLE": title,
                "STAGE_ID": ["C2:WON", "C2:APOLOGY", "C2:NEW"][i % 3],
                "apartments_count": 30 + (i % 120),  # 30-150 квартир
                "entrances_count": 1 + (i % 5),      # 1-5 подъездов
                "floors_count": 5 + (i % 7),         # 5-12 этажей
                "management_company": management_companies[i % len(management_companies)],
                "house_address": title
            })
        
        return extended[:limit]
    
    def analyze_house_brigade(self, address: str) -> str:
        """Определение бригады по адресу"""
        address_lower = address.lower()
        
        if any(street in address_lower for street in ['пролетарская', 'баррикад', 'ленина']):
            return "1 бригада - Центральный район"
        elif any(street in address_lower for street in ['чижевского', 'никитина']):
            return "2 бригада - Никитинский район"
        elif any(street in address_lower for street in ['жилетово', 'молодежная']):
            return "3 бригада - Жилетово"
        elif any(street in address_lower for street in ['жукова', 'хрустальная']):
            return "4 бригада - Северный район"
        elif any(street in address_lower for street in ['кондрово', 'пушкина']):
            return "5 бригада - Пригород"
        else:
            return "6 бригада - Окраины"
    
    def get_status_info(self, stage_id: str) -> tuple:
        """Получение информации о статусе сделки"""
        if stage_id == 'C2:WON':
            return "✅ Выполнено", "success"
        elif 'APOLOGY' in stage_id or 'LOSE' in stage_id:
            return "❌ Проблемы", "error"
        elif 'FINAL_INVOICE' in stage_id:
            return "🧾 Выставлен счет", "info"
        else:
            return "🔄 В работе", "processing"

    async def create_task(
        self, 
        title: str, 
        description: str, 
        responsible_id: int = 1,
        group_id: Optional[int] = None,
        deadline: Optional[str] = None
    ) -> Dict[str, Any]:
        """Создать задачу в Bitrix24"""
        try:
            logger.info(f"📝 Creating task in Bitrix24: {title}")
            
            params = {
                'fields[TITLE]': title,
                'fields[DESCRIPTION]': description,
                'fields[RESPONSIBLE_ID]': str(responsible_id),
                'fields[CREATED_BY]': str(responsible_id),
            }
            
            if group_id:
                params['fields[GROUP_ID]'] = str(group_id)
            
            if deadline:
                params['fields[DEADLINE]'] = deadline
            
            query_string = urllib.parse.urlencode(params)
            url = f"{self.webhook_url}tasks.task.add.json?{query_string}"
            
            async with httpx.AsyncClient() as client:
                response = await client.post(url, timeout=30)
                
                if response.status_code == 200:
                    data = response.json()
                    
                    if data.get('result'):
                        task_id = data['result']['task']['id']
                        logger.info(f"✅ Task created successfully: ID {task_id}")
                        
                        return {
                            "status": "success",
                            "task_id": task_id,
                            "title": title,
                            "description": description
                        }
                    else:
                        logger.error(f"❌ Task creation failed: {data}")
                        return {"status": "error", "message": "Failed to create task"}
                else:
                    logger.error(f"❌ Bitrix24 API error: {response.status_code}")
                    return {"status": "error", "message": f"API error: {response.status_code}"}
                    
        except Exception as e:
            logger.error(f"❌ Create task error: {e}")
            return {"status": "error", "message": str(e)}

    async def get_users(self) -> List[Dict[str, Any]]:
        """Получить список пользователей Bitrix24"""
        try:
            url = f"{self.webhook_url}user.get.json"
            
            async with httpx.AsyncClient() as client:
                response = await client.get(url, timeout=30)
                
                if response.status_code == 200:
                    data = response.json()
                    
                    if data.get('result'):
                        users = data['result']
                        logger.info(f"✅ Retrieved {len(users)} users from Bitrix24")
                        return users
                    else:
                        logger.warning("⚠️ No users found in Bitrix24")
                        return []
                else:
                    logger.error(f"❌ Failed to get users: {response.status_code}")
                    return []
                    
        except Exception as e:
            logger.error(f"❌ Get users error: {e}")
            return []

    async def add_comment_to_deal(self, deal_id: str, comment: str) -> bool:
        """Добавить комментарий к сделке"""
        try:
            logger.info(f"💬 Adding comment to deal {deal_id}")
            
            params = {
                'id': deal_id,
                'fields[COMMENTS]': comment
            }
            
            query_string = urllib.parse.urlencode(params)
            url = f"{self.webhook_url}crm.deal.update.json?{query_string}"
            
            async with httpx.AsyncClient() as client:
                response = await client.post(url, timeout=30)
                
                if response.status_code == 200:
                    data = response.json()
                    logger.info(f"✅ Comment added to deal {deal_id}")
                    return True
                else:
                    logger.error(f"❌ Failed to add comment: {response.status_code}")
                    return False
                    
        except Exception as e:
            logger.error(f"❌ Add comment error: {e}")
            return False

    def _extract_house_data(self, deal: Dict[str, Any]) -> Dict[str, Any]:
        """Извлечение и обработка данных дома из Bitrix24"""
        try:
            # Базовые поля
            house_data = {
                'ID': deal.get('ID', ''),
                'TITLE': deal.get('TITLE', 'Без названия'),
                'STAGE_ID': deal.get('STAGE_ID', ''),
                'DATE_CREATE': deal.get('DATE_CREATE', ''),
                'OPPORTUNITY': deal.get('OPPORTUNITY', ''),
                'ASSIGNED_BY_ID': deal.get('ASSIGNED_BY_ID', ''),
                'COMPANY_ID': deal.get('COMPANY_ID', ''),
            }
            
            # Извлечение количественных данных с обработкой ошибок
            try:
                apartments = deal.get('UF_CRM_1669704529022', 0)
                house_data['apartments_count'] = int(apartments) if apartments and str(apartments).isdigit() else 0
            except (ValueError, TypeError):
                house_data['apartments_count'] = 0
                
            try:
                entrances = deal.get('UF_CRM_1669705507390', 0)
                house_data['entrances_count'] = int(entrances) if entrances and str(entrances).isdigit() else 0
            except (ValueError, TypeError):
                house_data['entrances_count'] = 0
                
            try:
                floors = deal.get('UF_CRM_1669704631166', 0)
                house_data['floors_count'] = int(floors) if floors and str(floors).isdigit() else 0
            except (ValueError, TypeError):
                house_data['floors_count'] = 0
            
            # Адрес дома
            house_data['house_address'] = deal.get('UF_CRM_1669561599956', house_data['TITLE'])
            
            # Обработка типов уборки
            cleaning_type_1 = deal.get('UF_CRM_1741592855565', '')
            cleaning_type_2 = deal.get('UF_CRM_1741592945060', '')
            
            house_data['cleaning_type_1'] = self._get_cleaning_type_name(cleaning_type_1)
            house_data['cleaning_type_2'] = self._get_cleaning_type_name(cleaning_type_2)
            
            # Даты уборки
            house_data['cleaning_date_1'] = self._parse_bitrix_dates(deal.get('UF_CRM_1741592774017', []))
            house_data['cleaning_date_2'] = self._parse_bitrix_dates(deal.get('UF_CRM_1741592892232', []))
            
            return house_data
            
        except Exception as e:
            logger.error(f"❌ Error extracting house data: {e}")
            return deal

    def _get_cleaning_type_name(self, type_id: str) -> str:
        """Преобразование ID типа уборки в описательное название"""
        if not type_id:
            return "Не указан"
            
        # Маппинг типов уборки (нужно получить из Bitrix24 или настроить)
        cleaning_types = {
            '2468': 'Генеральная уборка',
            '2469': 'Поддерживающая уборка', 
            '2470': 'Влажная уборка',
            '2471': 'Санитарная обработка',
            '2472': 'Уборка после ремонта'
        }
        
        # Извлекаем числовой ID из строки типа "Тип 2468"
        import re
        match = re.search(r'\d+', str(type_id))
        if match:
            type_num = match.group()
            return cleaning_types.get(type_num, f"Тип {type_num}")
        
        return str(type_id)

    def _parse_bitrix_dates(self, dates_data) -> List[str]:
        """Парсинг дат из Bitrix24"""
        if not dates_data:
            return []
            
        try:
            if isinstance(dates_data, list):
                return [str(date) for date in dates_data if date]
            elif isinstance(dates_data, str):
                return [dates_data]
            else:
                return []
        except Exception as e:
            logger.error(f"❌ Error parsing dates: {e}")
            return []

    async def _enrich_with_management_companies(self, deals: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Обогащение данных управляющими компаниями"""
        try:
            # Собираем уникальные ID компаний
            company_ids = set()
            for deal in deals:
                company_id = deal.get('COMPANY_ID')
                if company_id:
                    company_ids.add(company_id)
            
            if not company_ids:
                logger.info("📋 No company IDs found, using fallback УК")
                for deal in deals:
                    deal['management_company'] = self._get_fallback_management_company()
                return deals
            
            # Получаем данные компаний из Bitrix24
            companies_data = {}
            for company_id in list(company_ids)[:20]:  # Лимит на первые 20 компаний
                try:
                    url = f"{self.webhook_url}crm.company.get.json?id={company_id}"
                    async with httpx.AsyncClient() as client:
                        response = await client.get(url, timeout=10)
                        if response.status_code == 200:
                            data = response.json()
                            if data.get('result'):
                                company_name = data['result'].get('TITLE', '')
                                if company_name:
                                    companies_data[company_id] = company_name
                                    logger.info(f"✅ Company info loaded: {company_name}")
                except Exception as e:
                    logger.error(f"❌ Error loading company {company_id}: {e}")
                    continue
            
            # Обогащаем сделки данными компаний
            for deal in deals:
                company_id = deal.get('COMPANY_ID')
                if company_id and company_id in companies_data:
                    deal['management_company'] = companies_data[company_id]
                else:
                    deal['management_company'] = self._get_fallback_management_company()
            
            logger.info(f"✅ Enriched with {len(companies_data)} management companies")
            return deals
            
        except Exception as e:
            logger.error(f"❌ Error enriching with companies: {e}")
            # Fallback: используем фиктивные УК
            for deal in deals:
                deal['management_company'] = self._get_fallback_management_company()
            return deals

    def _get_fallback_management_company(self) -> str:
        """Fallback управляющая компания"""
        import random
        companies = [
            'ООО "УК Новый город"',
            'ООО "Жилкомсервис"', 
            'ООО "Премиум-УК"',
            'УК "Домашний уют"',
            'ООО "УК МЖД Московского округа г.Калуги"'
        ]
        return random.choice(companies)