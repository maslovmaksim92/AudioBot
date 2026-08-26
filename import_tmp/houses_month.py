p = '/opt/audiobot/backend/app/routers/cleaning.py'
s = open(p, encoding='utf-8').read()

# 1) добавить параметр month в сигнатуру
OLD_SIG = '''    cleaning_date: Optional[str] = None,
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    current: Optional[CurrentUser] = Depends(get_current_user_optional)
):'''
NEW_SIG = '''    cleaning_date: Optional[str] = None,
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
    month: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    current: Optional[CurrentUser] = Depends(get_current_user_optional)
):'''
assert OLD_SIG in s
s = s.replace(OLD_SIG, NEW_SIG)

# 2) month -> month_key (may_2026) и передать в house_to_front + подтянуть акты
OLD_MAP = '''        total = (await db.execute(select(func.count()).select_from(base.subquery()))).scalar() or 0
        rows = (await db.execute(
            base.order_by(House.address).offset((page - 1) * limit).limit(limit)
        )).scalars().all()
        houses = [house_to_front(h) for h in rows]'''
NEW_MAP = '''        total = (await db.execute(select(func.count()).select_from(base.subquery()))).scalar() or 0
        rows = (await db.execute(
            base.order_by(House.address).offset((page - 1) * limit).limit(limit)
        )).scalars().all()

        # month (YYYY-MM) -> ключ графика month_key (may_2026)
        _MEN = {1:"january",2:"february",3:"march",4:"april",5:"may",6:"june",
                7:"july",8:"august",9:"september",10:"october",11:"november",12:"december"}
        month_key = None
        if month:
            try:
                yy, mm = month.split("-"); month_key = f"{_MEN[int(mm)]}_{int(yy)}"
            except Exception:
                month_key = None

        houses = [house_to_front(h, month_key=month_key) for h in rows]

        # подтянуть статус актов за выбранный месяц
        try:
            from backend.app.config.database import get_db_pool
            pool = await get_db_pool()
            act_month = month or None
            if pool and act_month and houses:
                ids = [h["id"] for h in houses]
                async with pool.acquire() as conn:
                    arows = await conn.fetch(
                        "SELECT house_id, act_signed_date, act_photo_count, bitrix_status "
                        "FROM house_acts WHERE act_month=$1 AND house_id = ANY($2::text[])",
                        act_month, ids)
                    acts = {str(a["house_id"]): a for a in arows}
                for h in houses:
                    a = acts.get(h["id"])
                    h["act_signed"] = bool(a)
                    h["act_photo_count"] = (a["act_photo_count"] if a else 0)
                    h["act_status"] = (a["bitrix_status"] if a else None)
            else:
                for h in houses:
                    h["act_signed"] = False
        except Exception as _e:
            logger.warning(f"[cleaning] acts join: {_e}")
            for h in houses:
                h.setdefault("act_signed", False)'''
assert OLD_MAP in s
s = s.replace(OLD_MAP, NEW_MAP)

open(p, 'w', encoding='utf-8').write(s)
print("OK: /houses принимает month и отдаёт периодичность за месяц + статус актов")
