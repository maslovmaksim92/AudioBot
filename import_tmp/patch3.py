p = '/opt/audiobot/backend/app/routers/cleaning.py'
s = open(p, encoding='utf-8').read()

OLD = '''@router.get("/filters")
async def get_cleaning_filters():
    try:
        brigades = await bitrix24_service.get_brigade_options()
        statuses = [{"id": "NEW", "name": "Новая"}, {"id": "WON", "name": "Закрыта"}]
        return {"brigades": brigades, "statuses": statuses}
    except Exception as e:
        logger.error(f"Error getting filters: {e}")
        return {"brigades": [], "statuses": []}'''

NEW = '''@router.get("/filters")
async def get_cleaning_filters(db: AsyncSession = Depends(get_db)):
    statuses = [{"id": "NEW", "name": "Новая"}, {"id": "WON", "name": "Закрыта"}]
    # Бригады и УК — из БД houses (автономно от Bitrix)
    try:
        from sqlalchemy import select, distinct
        from backend.app.models.house import House

        brig_rows = (await db.execute(
            select(distinct(House.brigade_number)).where(House.brigade_number.isnot(None))
        )).scalars().all()
        # сортировка: по числовому значению, потом строкой
        def _key(b):
            try:
                return (0, int(b))
            except Exception:
                return (1, str(b))
        brigades = [
            {"id": str(b), "name": f"{b} бригада"}
            for b in sorted([b for b in brig_rows if str(b).strip()], key=_key)
        ]
        companies = (await db.execute(
            select(distinct(House.company_title)).where(House.company_title.isnot(None))
        )).scalars().all()
        companies = sorted([c for c in companies if str(c).strip()])
        if brigades:
            return {"brigades": brigades, "statuses": statuses,
                    "companies": [{"id": c, "name": c} for c in companies], "source": "db"}
    except Exception as e:
        logger.error(f"[cleaning] filters DB read failed: {e}")
    # fallback на Bitrix
    try:
        brigades = await bitrix24_service.get_brigade_options()
        return {"brigades": brigades, "statuses": statuses}
    except Exception as e:
        logger.error(f"Error getting filters: {e}")
        return {"brigades": [], "statuses": statuses}'''

assert OLD in s, "OLD /filters не найден!"
s = s.replace(OLD, NEW)
open(p, 'w', encoding='utf-8').write(s)
print("OK: /cleaning/filters переключён на БД")
