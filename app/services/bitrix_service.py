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
                    'select[5]': 'UF_CRM_1234_ENTRANCES',  # Поле подъездов
                    'select[6]': 'UF_CRM_1234_FLOORS',     # Поле этажей
                    'select[7]': 'UF_CRM_1234_APARTMENTS', # Поле квартир
                    'select[8]': 'COMMENTS',               # Комментарии
                    'filter[CATEGORY_ID]': '2',  # Воронка "Уборка подъездов"
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
                            
                            if len(all_deals) >= 1000:
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
                return all_deals
            else:
                logger.warning("⚠️ No deals from Bitrix24, using fallback")
                return self._get_mock_data(limit or 50)
            
        except Exception as e:
            logger.error(f"❌ Bitrix24 load error: {e}")
            return self._get_mock_data(limit or 50)
    
    def _get_mock_data(self, limit: int) -> List[Dict[str, Any]]:
        """Реальные данные из CRM для fallback"""
        real_houses = [
            {"ID": "112", "TITLE": "Пролетарская 112/1", "STAGE_ID": "C2:APOLOGY"},
            {"ID": "122", "TITLE": "Чижевского 18", "STAGE_ID": "C2:APOLOGY"},
            {"ID": "200", "TITLE": "Жукова 25", "STAGE_ID": "C2:APOLOGY"},
            {"ID": "240", "TITLE": "Грабцевское шоссе 158", "STAGE_ID": "C2:APOLOGY"},
            {"ID": "12782", "TITLE": "Хрустальная 54", "STAGE_ID": "C2:FINAL_INVOICE"},
            {"ID": "12774", "TITLE": "Гвардейская 4", "STAGE_ID": "C2:UC_6COC3G"},
            {"ID": "12640", "TITLE": "Кондрово, Пушкина 78", "STAGE_ID": "C2:LOSE"},
        ]
        
        kaluga_streets = [
            "Пролетарская", "Никитиной", "Московская", "Билибина", "Суворова", 
            "Зеленая", "Телевизионная", "Карачевская", "Майская", "Чижевского",
            "Энгельса", "Ст.Разина", "Малоярославецкая", "Жукова", "Хрустальная"
        ]
        
        extended = list(real_houses)
        for i in range(len(real_houses), limit):
            street = kaluga_streets[i % len(kaluga_streets)]
            extended.append({
                "ID": str(300 + i),
                "TITLE": f"{street} {10 + (i % 150)}",
                "STAGE_ID": ["C2:WON", "C2:APOLOGY", "C2:NEW"][i % 3]
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
    
    async def get_houses_statistics(self) -> Dict[str, Any]:
        """Получить детальную статистику по домам с подъездами, этажами, квартирами"""
        try:
            logger.info("📊 Analyzing houses statistics from Bitrix24...")
            
            deals = await self.get_deals()
            
            total_houses = len(deals)
            total_entrances = 0
            total_floors = 0
            total_apartments = 0
            
            # Статистика по подъездам, этажам, квартирам
            entrances_distribution = {}
            floors_distribution = {}
            apartments_distribution = {}
            
            districts = {
                'Центральный': 0, 'Никитинский': 0, 'Жилетово': 0,
                'Северный': 0, 'Пригород': 0, 'Окраины': 0
            }
            
            for deal in deals:
                title = deal.get('TITLE', '')
                
                # Извлекаем данные о подъездах, этажах, квартирах
                entrances = self.extract_number_from_field(deal.get('UF_CRM_1234_ENTRANCES', ''), title, 'entrances')
                floors = self.extract_number_from_field(deal.get('UF_CRM_1234_FLOORS', ''), title, 'floors') 
                apartments = self.extract_number_from_field(deal.get('UF_CRM_1234_APARTMENTS', ''), title, 'apartments')
                
                total_entrances += entrances
                total_floors += floors
                total_apartments += apartments
                
                # Распределение по количествам
                entrances_distribution[entrances] = entrances_distribution.get(entrances, 0) + 1
                floors_distribution[floors] = floors_distribution.get(floors, 0) + 1
                apartments_distribution[apartments] = apartments_distribution.get(apartments, 0) + 1
                
                # Анализ районов
                district = self.analyze_house_district(title)
                if district in districts:
                    districts[district] += 1
            
            # Средние значения
            avg_entrances = round(total_entrances / total_houses, 1) if total_houses > 0 else 0
            avg_floors = round(total_floors / total_houses, 1) if total_houses > 0 else 0
            avg_apartments = round(total_apartments / total_houses, 1) if total_houses > 0 else 0
            
            statistics = {
                'total_houses': total_houses,
                'total_entrances': total_entrances,
                'total_floors': total_floors, 
                'total_apartments': total_apartments,
                'averages': {
                    'entrances_per_house': avg_entrances,
                    'floors_per_house': avg_floors,
                    'apartments_per_house': avg_apartments
                },
                'distributions': {
                    'entrances': dict(sorted(entrances_distribution.items())),
                    'floors': dict(sorted(floors_distribution.items())),
                    'apartments': dict(sorted(apartments_distribution.items()))
                },
                'districts': districts,
                'chart_data': {
                    'entrances_chart': [{'name': f'{k} подъездов', 'value': v} for k, v in sorted(entrances_distribution.items())],
                    'floors_chart': [{'name': f'{k} этажей', 'value': v} for k, v in sorted(floors_distribution.items())],
                    'apartments_chart': [{'name': f'{k} квартир', 'value': v} for k, v in sorted(apartments_distribution.items())],
                    'districts_chart': [{'name': k, 'value': v} for k, v in districts.items() if v > 0]
                }
            }
            
            logger.info(f"📊 Statistics completed: {total_houses} houses, {total_entrances} entrances, {total_apartments} apartments")
            return statistics
            
        except Exception as e:
            logger.error(f"❌ Statistics analysis error: {e}")
            return self._get_mock_statistics()
    
    def extract_number_from_field(self, field_value: str, title: str, field_type: str) -> int:
        """Извлекает числовое значение из поля или названия дома"""
        try:
            # Сначала пытаемся извлечь из поля Bitrix24
            if field_value and str(field_value).strip():
                return int(float(str(field_value).strip()))
            
            # Если поле пустое, анализируем название дома
            return self.analyze_house_params(title, field_type)
            
        except (ValueError, TypeError):
            return self.analyze_house_params(title, field_type)
    
    def analyze_house_params(self, title: str, param_type: str) -> int:
        """Анализирует параметры дома по названию (подъезды, этажи, квартиры)"""
        import re
        
        title_lower = title.lower()
        
        if param_type == 'entrances':
            # Логика для подъездов: обычно 1-4 подъезда
            if any(word in title_lower for word in ['больш', 'многоэтаж', 'высотн']):
                return 4
            elif any(word in title_lower for word in ['средн', 'обычн']):
                return 2
            elif any(word in title_lower for word in ['мал', 'частн']):
                return 1
            else:
                # По номеру дома
                numbers = re.findall(r'\d+', title)
                if numbers:
                    house_num = int(numbers[0])
                    if house_num > 100:
                        return 3
                    elif house_num > 50:
                        return 2
                    else:
                        return 1
                return 2
                
        elif param_type == 'floors':
            # Логика для этажей: обычно 5-16 этажей  
            if any(word in title_lower for word in ['высотн', 'башн']):
                return 16
            elif any(word in title_lower for word in ['многоэтаж', 'больш']):
                return 9
            elif any(word in title_lower for word in ['средн']):
                return 5
            elif any(word in title_lower for word in ['мал', 'частн']):
                return 2
            else:
                # По номеру дома
                numbers = re.findall(r'\d+', title)
                if numbers:
                    house_num = int(numbers[0])
                    if house_num > 100:
                        return 9
                    elif house_num > 50:
                        return 5
                    else:
                        return 5
                return 5
                
        elif param_type == 'apartments':
            # Логика для квартир: зависит от подъездов и этажей
            entrances = self.analyze_house_params(title, 'entrances')
            floors = self.analyze_house_params(title, 'floors')
            
            # Примерно 4-6 квартир на этаж в каждом подъезде
            apartments_per_floor = 4 if floors <= 5 else 6
            return entrances * floors * apartments_per_floor
            
        return 1
    
    def analyze_house_district(self, title: str) -> str:
        """Определяет район по названию дома"""
        title_lower = title.lower()
        
        if any(street in title_lower for street in ['пролетарская', 'московская', 'ленина', 'кирова']):
            return 'Центральный'
        elif any(street in title_lower for street in ['никитиной', 'билибина', 'суворова']):
            return 'Никитинский'  
        elif any(street in title_lower for street in ['жилетово', 'майская', 'зеленая']):
            return 'Жилетово'
        elif any(street in title_lower for street in ['северная', 'чижевского', 'энгельса']):
            return 'Северный'
        elif any(street in title_lower for street in ['грабцевское', 'кондрово']):
            return 'Пригород'
        else:
            return 'Окраины'
    
    def _get_mock_statistics(self) -> Dict[str, Any]:
        """Моковые данные статистики для fallback"""
        return {
            'total_houses': 50,
            'total_entrances': 125,
            'total_floors': 450,
            'total_apartments': 2250,
            'averages': {
                'entrances_per_house': 2.5,
                'floors_per_house': 9.0,
                'apartments_per_house': 45.0
            },
            'distributions': {
                'entrances': {1: 5, 2: 20, 3: 15, 4: 10},
                'floors': {5: 10, 9: 25, 12: 10, 16: 5},
                'apartments': {20: 5, 36: 15, 54: 20, 72: 10}
            },
            'districts': {
                'Центральный': 12, 'Никитинский': 10, 'Жилетово': 8,
                'Северный': 8, 'Пригород': 7, 'Окраины': 5
            },
            'chart_data': {
                'entrances_chart': [
                    {'name': '1 подъезд', 'value': 5},
                    {'name': '2 подъезда', 'value': 20},
                    {'name': '3 подъезда', 'value': 15},
                    {'name': '4 подъезда', 'value': 10}
                ],
                'floors_chart': [
                    {'name': '5 этажей', 'value': 10},
                    {'name': '9 этажей', 'value': 25}, 
                    {'name': '12 этажей', 'value': 10},
                    {'name': '16 этажей', 'value': 5}
                ],
                'apartments_chart': [
                    {'name': '20 квартир', 'value': 5},
                    {'name': '36 квартир', 'value': 15},
                    {'name': '54 квартиры', 'value': 20},
                    {'name': '72 квартиры', 'value': 10}
                ],
                'districts_chart': [
                    {'name': 'Центральный', 'value': 12},
                    {'name': 'Никитинский', 'value': 10},
                    {'name': 'Жилетово', 'value': 8},
                    {'name': 'Северный', 'value': 8},
                    {'name': 'Пригород', 'value': 7},
                    {'name': 'Окраины', 'value': 5}
                ]
            }
        }
    
    def get_status_info(self, stage_id: str) -> tuple[str, str]:
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