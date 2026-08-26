#!/usr/bin/env python3
import re, time, shutil

P = "/opt/hermes-max-bridge/bridge.py"
src = open(P, encoding="utf-8").read()
shutil.copy(P, P + ".bak_schema_" + str(int(time.time())))

new_schema = '''_CURTAIN_SCHEMA = (
    "Извлеки параметры для расчёта штор/жалюзи. Верни ТОЛЬКО JSON без пояснений, без markdown.\\n"
    "Схема: {\\"product\\": \\"классические|рулонные|зебра|вертикальные|плиссе\\" "
    "(зебра = рулонные день-ночь; вертикальные = вертикальные жалюзи), "
    "\\"width\\": число_метры_ширина, "
    "\\"height\\": число_метры_высота_или_null (нужна для рулонных/зебры/вертикальных/плиссе), "
    "\\"fabric\\": название_ткани_или_коллекции_как_сказал_клиент_или_null "
    "(классические: портьера|тюль|вуаль|блэкаут|римская|лён; "
    "рулонные: Arcadia, MAT SUN, MAT BLACKOUT, SCREEN и т.п.; "
    "зебра: Zebra ...; вертикальные: Trend|Alis|Mila; "
    "плиссе: коллекция (Креп, Плайн, Гоби, Мадрид...) или номер ценовой группы 1-5), "
    "\\"system\\": для_рулонных_и_зебры_название_системы_или_null "
    "(Мини, Мини с леской, Мини с магнитом, UNI 1, UNI 2, Люкс 25, Люкс 32, Люкс 38; цвет в скобках), "
    "\\"fullness\\": число_или_null_коэффициент_сборки_для_классических, "
    "\\"lining\\": true_или_false_подкладка_для_классических, "
    "\\"cornice_type\\": для_классических(профильный|круглый|электро) "
    "или_для_плиссе(Стандарт|50 мм со шнуром|С двойным управлением|Люкс COSIFLOR простой|сложный|сложный 2)_или_null, "
    "\\"cornice_len\\": число_или_null_длина_карниза_для_классических, "
    "\\"hardware\\": \\"лента|люверсы\\"_или_null, "
    "\\"brackets\\": число_кронштейнов_для_вертикальных_или_null, "
    "\\"rama_plus\\": true_если_просят_систему_Рама_Плюс_для_плиссе, "
    "\\"zamer\\": true_или_false, \\"montazh\\": true_или_false, "
    "\\"qty\\": целое_количество_одинаковых_изделий}.\\n"
    "Если параметр не указан — поставь null (для zamer/montazh/lining/rama_plus — false, qty — 1).\\nТекст: "
)'''

m = re.search(r"_CURTAIN_SCHEMA = \(.*?\n\)", src, re.S)
if not m:
    print("SCHEMA BLOCK NOT FOUND")
    raise SystemExit(1)
src = src[:m.start()] + new_schema + src[m.end():]

# подсказка при отсутствии width — обновить пример
old_hint = 'max_send_text(chat_id, "🧮 Посчитаю шторы. Укажи хотя бы ширину окна/карниза (м) и ткань. Например: «шторы, окно 3 м, портьера с подкладкой, карниз профильный 3.2 м, с монтажом».")'
new_hint = 'max_send_text(chat_id, "🧮 Посчитаю шторы. Укажи тип (классические / рулонные / зебра / вертикальные / плиссе), ширину и высоту (м), ткань. Например: «рулонная штора 0.7×1.4, ткань MAT SUN, система Мини, 3 окна, с монтажом и замером».")'
if old_hint in src:
    src = src.replace(old_hint, new_hint)
else:
    print("HINT NOT FOUND (ok, skipping)")

open(P, "w", encoding="utf-8").write(src)
print("PATCHED OK")
import py_compile
py_compile.compile(P, doraise=True)
print("COMPILE OK")
