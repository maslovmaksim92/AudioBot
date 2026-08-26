p = '/opt/audiobot/frontend/src/components/Works/Works.js'
s = open(p, encoding='utf-8').read()

# 1) helper очистки названия УК — вставим перед scheduleSummary
anchor = "// Короткая сводка графика для ячейки таблицы"
helper = '''// Очистка названия УК: убираем организационную форму (ООО, ОАО, ЗАО, АО, ПАО, ТСЖ, ИП, УК, "РКЦ" и т.п.) и кавычки
const cleanUK = (name) => {
  if (!name) return '';
  let s = String(name).trim();
  // убрать орг-формы в начале (возможно несколько подряд, напр. ООО "УК ...")
  s = s.replace(/^(\\s*(ООО|ОАО|ЗАО|ПАО|АО|ТСЖ|ТСН|ЖСК|ИП|МУП|ГУП|УК)\\b[\\s"«»]*)+/iu, '');
  // снять обрамляющие кавычки
  s = s.replace(/^[«"']+|[«"'»]+$/g, '').trim();
  return s || String(name).trim();
};

// Короткая сводка графика для ячейки таблицы'''
assert anchor in s
s = s.replace(anchor, helper, 1)

# 2) применить в ячейке таблицы
s = s.replace(
    '<td className="px-4 py-3 text-gray-700">{h.management_company || <span className="text-gray-300">—</span>}</td>',
    '<td className="px-4 py-3 text-gray-700">{cleanUK(h.management_company) || <span className="text-gray-300">—</span>}</td>'
)

# 3) применить в выпадающем фильтре УК (показываем очищенное имя, value оставляем оригинальным для бэкенда)
s = s.replace(
    '''                  {filters.companies?.map((c, i) => {
                    const val = typeof c === 'object' ? c.id : c;
                    const lbl = typeof c === 'object' ? c.name : c;
                    return <option key={i} value={val}>{lbl}</option>;
                  })}''',
    '''                  {filters.companies?.map((c, i) => {
                    const val = typeof c === 'object' ? c.id : c;
                    const lbl = typeof c === 'object' ? c.name : c;
                    return <option key={i} value={val}>{cleanUK(lbl)}</option>;
                  })}'''
)

open(p, 'w', encoding='utf-8').write(s)
print("OK: cleanUK применён в таблице и фильтре УК")
