import re

p = '/opt/audiobot/backend/app/routers/cleaning.py'
s = open(p, encoding='utf-8').read()

OLD = '''    try:
        effective_brigade = brigade
        # RBAC: если пользователь-бригада, фильтруем строго по номеру из его логина (brigadaN)
        if current and current.is_brigade() and not brigade:
            # извлечём число из brigade_number
            if current.brigade_number:
                effective_brigade = current.brigade_number
        # Если есть поиск по адресу - загружаем ВСЕ дома (без пагинации)
        if address:
            logger.info(f"[cleaning] Searching for address: {address}")
            # Загружаем больше домов для поиска
            data = await bitrix24_service.list_houses(
                brigade=effective_brigade,
                status=status,
                management_company=management_company,
                cleaning_date=cleaning_date,
                date_from=date_from,
                date_to=date_to,
                page=1,
                limit=1000,  # Загружаем много домов для поиска
            )
            # Фильтрация по адресу
            all_houses = data.get('houses', [])
            filtered_houses = [
                h for h in all_houses 
                if address.lower() in (h.get('address') or '').lower() 
                or address.lower() in (h.get('title') or '').lower()
            ]
            logger.info(f"[cleaning] Found {len(filtered_houses)} houses matching '{address}'")
            
            # Применяем пагинацию к отфильтрованным домам
            total = len(filtered_houses)
            start = (page - 1) * limit
            end = start + limit
            paginated_houses = filtered_houses[start:end]
            
            return {
                'houses': paginated_houses,
                'total': total,
                'page': page,
                'limit': limit,
                'pages': (total + limit - 1) // limit if total > 0 else 0
            }
        else:
            # Обычная загрузка с пагинацией
            data = await bitrix24_service.list_houses(
                brigade=effective_brigade,
                status=status,
                management_company=management_company,
                cleaning_date=cleaning_date,
                date_from=date_from,
                date_to=date_to,
                page=page,
                limit=limit,
            )
            return data
    except Exception as e:
        logger.error(f"Error getting houses: {e}")
        # fallback mock
        mock_houses = [
            {"id": "1", "title": "Билибина 6", "address": "Билибина 6", "management_company": "УК Комфорт", "brigade_name": "5 бригада", "assigned_by_name": "5 бригада", "apartments": 120, "entrances": 4, "floors": 9, "cleaning_dates": {"october_1": {"dates": ["2025-10-02"], "type": "Влажная уборка"}}},
        ]
        return {"houses": mock_houses, "total": len(mock_houses), "page": 1, "limit": limit, "pages": 1}'''

NEW = '''    # ИСТОЧНИК ПРАВДЫ — БД houses (автономно от Bitrix; Bitrix = фоновый синк).
    # Та же таблица, что питает MAX-бот, поэтому веб и бот всегда согласованы.
    try:
        from sqlalchemy import select, func
        from backend.app.models.house import House
        from backend.app.routers._houses_front_mapper import house_to_front

        effective_brigade = brigade
        if current and current.is_brigade() and not brigade:
            if current.brigade_number:
                effective_brigade = current.brigade_number

        base = select(House)
        if effective_brigade:
            base = base.where(House.brigade_number == str(effective_brigade))
        if management_company:
            base = base.where(House.company_title == management_company)
        if address:
            like = f"%{address.lower()}%"
            base = base.where(func.lower(House.address).like(like))

        total = (await db.execute(select(func.count()).select_from(base.subquery()))).scalar() or 0
        rows = (await db.execute(
            base.order_by(House.address).offset((page - 1) * limit).limit(limit)
        )).scalars().all()
        houses = [house_to_front(h) for h in rows]

        if cleaning_date or date_from or date_to:
            def _match(h):
                alld = []
                for v in (h.get("cleaning_dates") or {}).values():
                    alld += (v.get("dates") or [])
                if cleaning_date and cleaning_date not in alld:
                    return False
                if date_from and not any(d >= date_from for d in alld):
                    return False
                if date_to and not any(d <= date_to for d in alld):
                    return False
                return True
            houses = [h for h in houses if _match(h)]
            total = len(houses)

        if total > 0 or address or effective_brigade or management_company:
            return {
                "houses": houses, "total": total, "page": page, "limit": limit,
                "pages": (total + limit - 1) // limit if total > 0 else 0,
                "source": "db",
            }
        logger.warning("[cleaning] houses table empty, fallback to Bitrix")
        return await bitrix24_service.list_houses(
            brigade=effective_brigade, status=status,
            management_company=management_company, cleaning_date=cleaning_date,
            date_from=date_from, date_to=date_to, page=page, limit=limit,
        )
    except Exception as e:
        logger.error(f"[cleaning] DB read failed, fallback to Bitrix: {e}")
        try:
            return await bitrix24_service.list_houses(
                brigade=brigade, status=status, management_company=management_company,
                cleaning_date=cleaning_date, date_from=date_from, date_to=date_to,
                page=page, limit=limit,
            )
        except Exception as e2:
            logger.error(f"[cleaning] Bitrix fallback failed: {e2}")
            return {"houses": [], "total": 0, "page": 1, "limit": limit, "pages": 0, "source": "error"}'''

assert OLD in s, "OLD блок /houses не найден!"
s = s.replace(OLD, NEW)
open(p, 'w', encoding='utf-8').write(s)
print("OK: /cleaning/houses переключён на БД")
