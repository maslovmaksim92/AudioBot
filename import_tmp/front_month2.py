p = '/opt/audiobot/frontend/src/components/Works/Works.js'
s = open(p, encoding='utf-8').read()

# 1) селектор месяца в фильтрах — перед "Поиск по адресу"
OLD_SEARCH = """              {/* Поиск по адресу */}
              <div>
                <label className="block text-xs font-medium text-gray-500 mb-1">Поиск по адресу</label>"""
NEW_SEARCH = """              {/* Месяц */}
              <div>
                <label className="block text-xs font-medium text-gray-500 mb-1">Месяц графика</label>
                <input
                  type="month"
                  value={listMonth}
                  onChange={(e) => setListMonth(e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm bg-white focus:ring-2 focus:ring-blue-500"
                />
              </div>

              {/* Поиск по адресу */}
              <div>
                <label className="block text-xs font-medium text-gray-500 mb-1">Поиск по адресу</label>"""
assert OLD_SEARCH in s
s = s.replace(OLD_SEARCH, NEW_SEARCH)

# 2) колонка "Акт" в шапке таблицы — после "График (ближайший)"
OLD_TH = '<th className="px-4 py-3 font-semibold">График (ближайший)</th>'
NEW_TH = '''<th className="px-4 py-3 font-semibold">График за месяц</th>
                      <th className="px-3 py-3 font-semibold text-center">Акт</th>'''
assert OLD_TH in s
s = s.replace(OLD_TH, NEW_TH)

open(p, 'w', encoding='utf-8').write(s)
print("OK: селектор месяца + колонка Акт (шапка)")
