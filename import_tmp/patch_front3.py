p = '/opt/audiobot/frontend/src/components/Works/Works.js'
s = open(p, encoding='utf-8').read()

# helper-проверка "есть ли хоть какой-то график" вставим прямо в выражения через inline-функцию
# заменяем октябрьский блок предупреждения
OLD_OCT = """          {houses.filter(h=>!(h?.cleaning_dates?.october_1?.dates?.length||h?.cleaning_dates?.october_2?.dates?.length)).length>0 && (
            <li>Не заполнен график уборки (октябрь) у адресов: {houses.filter(h=>!(h?.cleaning_dates?.october_1?.dates?.length||h?.cleaning_dates?.october_2?.dates?.length)).slice(0,5).map(h=>h.address || h.title).join(', ')}{houses.filter(h=>!(h?.cleaning_dates?.october_1?.dates?.length||h?.cleaning_dates?.october_2?.dates?.length)).length>5?' и др.':''}</li>
          )}"""
NEW_OCT = """          {houses.filter(h=>!hasAnySchedule(h)).length>0 && (
            <li>Не заполнен график уборок у адресов: {houses.filter(h=>!hasAnySchedule(h)).slice(0,5).map(h=>h.address || h.title).join(', ')}{houses.filter(h=>!hasAnySchedule(h)).length>5?' и др.':''}</li>
          )}"""
assert OLD_OCT in s, "октябрьский блок предупреждения не найден"
s = s.replace(OLD_OCT, NEW_OCT)

# удаляем ноябрьский блок предупреждения (теперь покрыт универсальным выше)
OLD_NOV = """          {houses.filter(h=>!(h?.cleaning_dates?.november_1?.dates?.length||h?.cleaning_dates?.november_2?.dates?.length)).length>0 && (
            <li>Не заполнен график уборки (ноябрь) у адресов: {houses.filter(h=>!(h?.cleaning_dates?.november_1?.dates?.length||h?.cleaning_dates?.november_2?.dates?.length)).slice(0,3).map(h=>h.address || h.title).join(', ')}{houses.filter(h=>!(h?.cleaning_dates?.november_1?.dates?.length||h?.cleaning_dates?.november_2?.dates?.length)).length>3?' и др.':''}</li>
          )}"""
assert OLD_NOV in s, "ноябрьский блок предупреждения не найден"
s = s.replace(OLD_NOV, "")

# в итоговой проверке "всё заполнено" тоже меняем октябрьское условие на универсальное
OLD_OK = """            houses.filter(h=>!(h?.cleaning_dates?.october_1?.dates?.length||h?.cleaning_dates?.october_2?.dates?.length)).length === 0 && ("""
NEW_OK = """            houses.filter(h=>!hasAnySchedule(h)).length === 0 && ("""
assert OLD_OK in s, "итоговая проверка не найдена"
s = s.replace(OLD_OK, NEW_OK)

# добавим helper hasAnySchedule рядом с resolveMonthMeta
anchor = "const resolveMonthMeta = (key) => {"
helper = """const hasAnySchedule = (h) => {
  const cd = h?.cleaning_dates || {};
  return Object.values(cd).some(v => (v?.dates?.length || 0) > 0);
};
"""
assert anchor in s
s = s.replace(anchor, helper + anchor)

open(p, 'w', encoding='utf-8').write(s)
print("OK: предупреждения о графике -> универсальные (любой месяц)")
