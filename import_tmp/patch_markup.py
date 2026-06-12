#!/usr/bin/env python3
import time, shutil, json, re

# 1) curtains.py — посекционный markup
P = "/opt/vasdom-modules/curtains.py"
shutil.copy(P, P + ".bak_markup_" + str(int(time.time())))
src = open(P, encoding="utf-8").read()

old = '''    if product == "рулонные":
        _calc_rolled(params, P, items, warn, mk, "rolled")
    elif product == "зебра":
        _calc_rolled(params, P, items, warn, mk, "zebra")
    elif product == "вертикальные":
        _calc_vertical(params, P, items, warn, mk)
    elif product == "плиссе":
        _calc_plisse(params, P, items, warn, mk)'''
new = '''    def _sec_mk(name):
        return _f(P.get(name, {}).get("markup"), 0) or mk

    if product == "рулонные":
        _calc_rolled(params, P, items, warn, _sec_mk("rolled"), "rolled")
    elif product == "зебра":
        _calc_rolled(params, P, items, warn, _sec_mk("zebra"), "zebra")
    elif product == "вертикальные":
        _calc_vertical(params, P, items, warn, _sec_mk("vertical"))
    elif product == "плиссе":
        _calc_plisse(params, P, items, warn, _sec_mk("plisse"))'''
assert old in src, "calc dispatch block not found"
src = src.replace(old, new)

# докстринг про markup
src = src.replace(
    "Общее: markup (наценка) применяется к материалам, не к услугам VasDom.",
    "Общее: markup (наценка) применяется к материалам, не к услугам VasDom.\n"
    "Наценку можно задать посекционно: rolled.markup / zebra.markup / vertical.markup /\n"
    "plisse.markup перекрывают глобальный markup. Прайс ЗЕБРА1 уже содержит +40%.")
open(P, "w", encoding="utf-8").write(src)
import py_compile; py_compile.compile(P, doraise=True)
print("curtains.py PATCHED + COMPILED")

# 2) JSON — rolled.markup = 1.4, пометки
J = "/opt/vasdom-modules/curtains_prices.json"
shutil.copy(J, J + ".bak_markup_" + str(int(time.time())))
d = json.load(open(J, encoding="utf-8"))
d["rolled"]["markup"] = 1.4
d["rolled"]["note"] = ("Прайс Miamoza 23.09.2025, базовые цены вкладки «Рулонные шторы». "
                       "markup 1.4 = продажные цены (вкладка «Рулонные 40»). "
                       "Расчёт по ширине: ширина(м) × (ткань + система) × markup. "
                       "Эконом-ткани: высота × ткань + ширина × система.")
d["zebra"]["markup"] = 1.0
d["zebra"]["note"] = ("Рулонные день-ночь. Цены из вкладки ЗЕБРА1 — УЖЕ продажные (+40% к базе), "
                      "поэтому markup 1.0. Расчёт: ширина(м) × (ткань + система).")
json.dump(d, open(J, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
print("JSON updated: rolled.markup=1.4, zebra.markup=1.0")
