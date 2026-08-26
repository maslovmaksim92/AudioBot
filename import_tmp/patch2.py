p = '/opt/audiobot/backend/app/routers/cleaning.py'
s = open(p, encoding='utf-8').read()

OLD = '''@router.get("/house/{house_id}/details")
async def get_house_details(house_id: str):
    try:
        details = await bitrix24_service.get_deal_details(house_id)
        if details:
            return {"house": details}
        return {"error": "Дом не найден"}
    except Exception as e:
        logger.error(f"Error getting house details: {e}")
        return {"error": str(e)}'''

NEW = '''@router.get("/house/{house_id}/details")
async def get_house_details(house_id: str, db: AsyncSession = Depends(get_db)):
    # Сначала БД (автономно), затем Bitrix как fallback
    try:
        from sqlalchemy import select
        from backend.app.models.house import House
        from backend.app.routers._houses_front_mapper import house_to_details

        row = (await db.execute(select(House).where(House.id == str(house_id)))).scalar_one_or_none()
        if row is None:
            row = (await db.execute(select(House).where(House.bitrix_id == str(house_id)))).scalar_one_or_none()
        if row is not None:
            return {"house": house_to_details(row), "source": "db"}
    except Exception as e:
        logger.error(f"[cleaning] details DB read failed: {e}")
    try:
        details = await bitrix24_service.get_deal_details(house_id)
        if details:
            return {"house": details, "source": "bitrix"}
        return {"error": "Дом не найден"}
    except Exception as e:
        logger.error(f"Error getting house details: {e}")
        return {"error": str(e)}'''

assert OLD in s, "OLD блок /details не найден!"
s = s.replace(OLD, NEW)
open(p, 'w', encoding='utf-8').write(s)
print("OK: /cleaning/house/{id}/details переключён на БД")
