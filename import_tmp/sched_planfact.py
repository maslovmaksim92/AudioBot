p = '/opt/audiobot/backend/app/tasks/scheduler.py'
s = open(p, encoding='utf-8').read()

# 1) добавить регистрацию задачи (после plannerka_reminder add_job)
ANCHOR_JOB = '''        # Напоминание о планерке каждый день в 8:25 MSK
        self.scheduler.add_job(
            self.send_plannerka_reminder,
            trigger=CronTrigger(hour=8, minute=25, timezone=moscow_tz),
            id='plannerka_reminder',
            name='Напоминание о планерке',
            replace_existing=True
        )'''
NEW_JOB = ANCHOR_JOB + '''

        # Вечерняя сводка план/факт уборок руководителю (19:00 MSK)
        self.scheduler.add_job(
            self.send_plan_fact_summary,
            trigger=CronTrigger(hour=19, minute=0, timezone=moscow_tz),
            id='plan_fact_summary',
            name='Сводка план/факт уборок (вечер)',
            replace_existing=True
        )'''
assert ANCHOR_JOB in s
s = s.replace(ANCHOR_JOB, NEW_JOB)

# 2) добавить метод после send_plannerka_reminder
ANCHOR_M = '''        except Exception as e:
            logger.error(f"❌ Plannerka reminder error: {e}")
    
    async def ai_call_employees(self):'''
NEW_M = '''        except Exception as e:
            logger.exception(f"❌ Plannerka reminder error: {e}")

    async def send_plan_fact_summary(self):
        """Вечерняя сводка: сколько домов по плану на сегодня и сколько отчиталось."""
        logger.info("📊 Формирую вечернюю сводку план/факт...")
        try:
            import os
            from datetime import date as _date
            from backend.app.config.database import get_db_pool
            from backend.app.models.house import House
            from sqlalchemy import select
            from backend.app.config.database import AsyncSessionLocal
            from backend.app.services import max_service as M

            today = _date.today().isoformat()
            _MEN = {1:"january",2:"february",3:"march",4:"april",5:"may",6:"june",7:"july",
                    8:"august",9:"september",10:"october",11:"november",12:"december"}
            y, mo, d = today.split("-")
            sched_key = f"{_MEN[int(mo)]}_{int(y)}"

            # план: дома с уборкой сегодня
            async with AsyncSessionLocal() as sess:
                rows = (await sess.execute(select(House))).scalars().all()
            planned = []
            for h in rows:
                sc = h.cleaning_schedule or {}
                arr = sc.get(sched_key) or [] if isinstance(sc, dict) else []
                if any(isinstance(it, dict) and it.get("date") == today for it in arr):
                    planned.append(h)

            if not planned:
                logger.info("[plan-fact] на сегодня уборок нет, сводку не шлю")
                return

            # факт
            fact_ids = set()
            pool = await get_db_pool()
            if pool:
                async with pool.acquire() as conn:
                    frows = await conn.fetch(
                        "SELECT DISTINCT house_id FROM cleaning_photos WHERE cleaning_date=$1", today)
                    fact_ids = {str(r["house_id"]) for r in frows}

            total = len(planned)
            done = len([h for h in planned if str(h.id) in fact_ids])
            pending = total - done
            pct = round(done / total * 100) if total else 0

            # по бригадам — кто не отчитался
            by_brig = {}
            for h in planned:
                if str(h.id) in fact_ids:
                    continue
                b = str(h.brigade_number) if h.brigade_number else "—"
                by_brig.setdefault(b, []).append(h.address)

            lines = [f"📊 Сводка уборок за {d}.{mo}.{y}",
                     f"План: {total} | Убрано: {done} | Не отчитались: {pending} ({pct}%)", ""]
            if by_brig:
                lines.append("⚠️ Не отчитались по бригадам:")
                for b in sorted(by_brig.keys(), key=lambda x: (len(x), x)):
                    addrs = by_brig[b]
                    bname = f"Бригада {b}" if b != "—" else "Без бригады"
                    lines.append(f"• {bname}: {len(addrs)} — {', '.join(a[:25] for a in addrs[:5])}{' и др.' if len(addrs) > 5 else ''}")
            else:
                lines.append("✅ Все отчитались!")

            text = "\\n".join(lines)
            target = os.getenv("OWNER_CHAT_ID") or os.getenv("MAX_PHOTOS_CHANNEL_ID")
            if not target:
                logger.warning("[plan-fact] нет OWNER_CHAT_ID/MAX_PHOTOS_CHANNEL_ID — сводку некуда слать")
                return
            await M.send_message(int(target), text)
            logger.info(f"✅ Сводка план/факт отправлена в {target}: план={total} факт={done}")
        except Exception as e:
            logger.exception(f"[plan-fact] ошибка сводки: {e}")

    async def ai_call_employees(self):'''
assert ANCHOR_M in s
s = s.replace(ANCHOR_M, NEW_M)

open(p, 'w', encoding='utf-8').write(s)
print("OK: задача вечерней сводки план/факт добавлена (19:00 MSK)")
