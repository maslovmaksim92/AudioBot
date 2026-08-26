p = '/opt/audiobot/frontend/src/components/Works/Works.js'
s = open(p, encoding='utf-8').read()

OLD = """            {/* График уборки */}
            {house.cleaning_dates && (house.cleaning_dates.october_1 || house.cleaning_dates.october_2) && (
              <div className="mb-3 p-3 rounded-lg border bg-purple-50">
                <div className="text-sm font-semibold text-purple-800 mb-2">График уборок 2025: Октябрь</div>
                {house.cleaning_dates.october_1 && <MonthBlock k="october_1" block={house.cleaning_dates.october_1} />}
                {house.cleaning_dates.october_2 && <MonthBlock k="october_2" block={house.cleaning_dates.october_2} />}
              </div>
            )}"""

NEW = """            {/* График уборки — все месяцы из данных (БД), отсортированы по ключу */}
            {house.cleaning_dates && Object.keys(house.cleaning_dates).length > 0 && (
              <div className="mb-3 p-3 rounded-lg border bg-purple-50">
                <div className="text-sm font-semibold text-purple-800 mb-2">График уборок</div>
                {Object.entries(house.cleaning_dates)
                  .filter(([, v]) => (v?.dates?.length || 0) > 0)
                  .sort(([a], [b]) => {
                    const pa = (a.match(/_(\\d{4})$/) || [])[1] || '';
                    const pb = (b.match(/_(\\d{4})$/) || [])[1] || '';
                    return (pa + a).localeCompare(pb + b);
                  })
                  .map(([k, v]) => <MonthBlock key={k} k={k} block={v} />)}
              </div>
            )}"""

assert OLD in s, "Блок графика на карточке не найден!"
s = s.replace(OLD, NEW)
open(p, 'w', encoding='utf-8').write(s)
print("OK: блок графика на карточке -> динамический (все месяцы)")
