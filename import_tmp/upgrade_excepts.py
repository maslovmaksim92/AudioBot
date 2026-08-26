"""
Заменяет logger.error на logger.exception в строках, которые УЖЕ внутри except-блока.
Это даёт полный stacktrace без переписывания вручную.
"""
import re, sys

files = [
    "/opt/audiobot/backend/app/services/max_cleaning_bot.py",
    "/opt/audiobot/backend/app/services/max_service.py",
    "/opt/audiobot/backend/app/services/bitrix24_service.py",
    "/opt/audiobot/backend/app/routers/cleaning.py",
    "/opt/audiobot/backend/app/routers/max_bot.py",
]

# Найдём строки с `logger.error(f"... {e}")` и предшествующий им `except`,
# чтобы убедиться что мы внутри except. Лёгкий подход: для каждой строки
# смотрим назад до пустой строки или 'def ' — есть ли там 'except'.

total_changed = 0
for path in files:
    try:
        src = open(path, encoding="utf-8").read()
    except FileNotFoundError:
        continue
    lines = src.split("\n")
    changed = 0
    for i, ln in enumerate(lines):
        m = re.match(r"(\s+)logger\.error\((.*\{e[^}]*\}.*)\)\s*$", ln)
        if not m:
            continue
        indent = m.group(1)
        # ищем назад максимум 12 строк — встречен ли except?
        in_except = False
        for j in range(i - 1, max(-1, i - 30), -1):
            prev = lines[j]
            if re.match(r"\s*(def |async def |class )", prev):
                break
            if re.match(rf"\s{{0,{len(indent)}}}except\b", prev):
                in_except = True
                break
        if in_except:
            lines[i] = ln.replace("logger.error", "logger.exception", 1)
            changed += 1
    if changed:
        open(path, "w", encoding="utf-8").write("\n".join(lines))
        print(f"  {path}: {changed} замен")
        total_changed += changed
    else:
        print(f"  {path}: без изменений")

print(f"\nИтого замен logger.error -> logger.exception (только в except): {total_changed}")
