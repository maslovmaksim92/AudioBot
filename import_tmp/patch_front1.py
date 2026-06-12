p = '/opt/audiobot/frontend/src/components/Works/Works.js'
s = open(p, encoding='utf-8').read()

OLD = """const monthMeta = {
  september_1: { title: 'Сентябрь · 1', color: 'purple' },
  september_2: { title: 'Сентябрь · 2', color: 'purple' },
  october_1: { title: 'Октябрь · 1', color: 'orange' },
  october_2: { title: 'Октябрь · 2', color: 'orange' },
  november_1: { title: 'Ноябрь · 1', color: 'yellow' },
  november_2: { title: 'Ноябрь · 2', color: 'yellow' },
  december_1: { title: 'Декабрь · 1', color: 'blue' },
  december_2: { title: 'Декабрь · 2', color: 'blue' },
};"""

NEW = """const monthMeta = {
  september_1: { title: 'Сентябрь · 1', color: 'purple' },
  september_2: { title: 'Сентябрь · 2', color: 'purple' },
  october_1: { title: 'Октябрь · 1', color: 'orange' },
  october_2: { title: 'Октябрь · 2', color: 'orange' },
  november_1: { title: 'Ноябрь · 1', color: 'yellow' },
  november_2: { title: 'Ноябрь · 2', color: 'yellow' },
  december_1: { title: 'Декабрь · 1', color: 'blue' },
  december_2: { title: 'Декабрь · 2', color: 'blue' },
};

// Резолвер метаданных для ключей графика любого формата.
// Поддерживает: '<en_month>_<year>' (may_2026), '<en_month>_1/_2' (october_1), произвольные ключи.
const MONTH_EN_RU = {
  january: 'Январь', february: 'Февраль', march: 'Март', april: 'Апрель',
  may: 'Май', june: 'Июнь', july: 'Июль', august: 'Август',
  september: 'Сентябрь', october: 'Октябрь', november: 'Ноябрь', december: 'Декабрь',
};
const MONTH_COLOR = {
  january: 'blue', february: 'blue', march: 'purple', april: 'purple',
  may: 'yellow', june: 'orange', july: 'orange', august: 'orange',
  september: 'purple', october: 'orange', november: 'yellow', december: 'blue',
};
const resolveMonthMeta = (key) => {
  if (monthMeta[key]) return monthMeta[key];
  const m = String(key).toLowerCase().match(/^([a-z]+)_(\\d{4})$/);
  if (m && MONTH_EN_RU[m[1]]) {
    return { title: `${MONTH_EN_RU[m[1]]} ${m[2]}`, color: MONTH_COLOR[m[1]] || 'gray' };
  }
  const m2 = String(key).toLowerCase().match(/^([a-z]+)_([12])$/);
  if (m2 && MONTH_EN_RU[m2[1]]) {
    return { title: `${MONTH_EN_RU[m2[1]]} · ${m2[2]}`, color: MONTH_COLOR[m2[1]] || 'gray' };
  }
  return { title: key, color: 'gray' };
};"""

assert OLD in s, "monthMeta не найден!"
s = s.replace(OLD, NEW)

# Используем резолвер в renderMonthBlock и MonthBlock
s = s.replace(
    "const meta = monthMeta[key] || { title: key, color: 'gray' };",
    "const meta = resolveMonthMeta(key);"
)
s = s.replace(
    "const meta = monthMeta[k] || { title: k, color: 'gray' };",
    "const meta = resolveMonthMeta(k);"
)

open(p, 'w', encoding='utf-8').write(s)
print("OK: monthMeta -> resolveMonthMeta (любой месяц/год)")
