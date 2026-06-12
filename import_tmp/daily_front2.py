p = '/opt/audiobot/frontend/src/components/Works/Works.js'
s = open(p, encoding='utf-8').read()

# вставляем после закрытия блока вкладки 'calc'. Якорь — уникальная подпись формулы из calc-блока.
anchor = '''          <div className="mt-3 text-xs text-gray-400">
            Сумма по тарифу = (уборок/мес из тарифа) × (подъезды) × (цена за подъезд). Формулу уточним под вашу методику.
          </div>
        </div>
      )}'''
assert anchor in s

daily_block = anchor + '''

      {/* Вкладка "Расчёты по дням" */}
      {activeTab === 'daily' && (
        <div>
          <div className="flex items-center gap-3 mb-4">
            <CalendarRange className="w-5 h-5 text-blue-600" />
            <span className="text-sm text-gray-600">Месяц:</span>
            <input
              type="month"
              value={calcMonth}
              onChange={(e) => setCalcMonth(e.target.value)}
              className="px-3 py-1.5 border border-gray-300 rounded-lg text-sm"
            />
            <button onClick={fetchDaily} className="px-3 py-1.5 text-sm rounded-lg bg-gray-100 hover:bg-gray-200 flex items-center gap-1">
              <RefreshCw className={`w-3.5 h-3.5 ${dailyLoading ? 'animate-spin' : ''}`} /> Обновить
            </button>
          </div>

          {/* Итоги за месяц */}
          {dailyData?.totals && (
            <div className="grid grid-cols-2 md:grid-cols-5 gap-3 mb-5">
              {[
                { label: 'Дней с уборками', value: dailyData.totals.days, color: 'from-slate-500 to-slate-600' },
                { label: 'Всего уборок', value: dailyData.totals.cleanings, color: 'from-blue-500 to-blue-600' },
                { label: 'Подъездов (сумма)', value: dailyData.totals.entrances, color: 'from-indigo-500 to-indigo-600' },
                { label: 'Этажей (сумма)', value: dailyData.totals.floors, color: 'from-purple-500 to-purple-600' },
                { label: 'Деньги, ₽', value: (dailyData.totals.money || 0).toLocaleString('ru-RU'), color: 'from-amber-500 to-orange-600' },
              ].map((c, i) => (
                <div key={i} className={`bg-gradient-to-br ${c.color} text-white rounded-xl p-3 shadow-sm`}>
                  <div className="text-xl font-bold leading-none">{c.value}</div>
                  <div className="text-xs opacity-90 mt-1">{c.label}</div>
                </div>
              ))}
            </div>
          )}

          {/* Таблица по дням */}
          <div className="bg-white rounded-xl border border-gray-200 shadow-sm overflow-hidden">
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="bg-gray-50 border-b border-gray-200 text-left text-xs uppercase tracking-wide text-gray-500">
                    <th className="px-4 py-3 font-semibold">Дата</th>
                    <th className="px-3 py-3 font-semibold text-center">День</th>
                    <th className="px-3 py-3 font-semibold text-center">Уборок</th>
                    <th className="px-3 py-3 font-semibold text-center">Подъездов</th>
                    <th className="px-3 py-3 font-semibold text-center">Этажей</th>
                    <th className="px-4 py-3 font-semibold text-right">Деньги, ₽</th>
                    <th className="px-3 py-3 font-semibold text-center">Бригады</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-100">
                  {dailyLoading && (<tr><td colSpan={7} className="px-4 py-10 text-center text-gray-400">Загрузка…</td></tr>)}
                  {!dailyLoading && (!dailyData?.days || dailyData.days.length === 0) && (
                    <tr><td colSpan={7} className="px-4 py-10 text-center text-gray-400">Нет уборок в этом месяце.</td></tr>
                  )}
                  {!dailyLoading && dailyData?.days?.map((d) => {
                    const isWeekend = d.weekday === 'Сб' || d.weekday === 'Вс';
                    const open = expandedDay === d.date;
                    const [yy, mm, dd] = d.date.split('-');
                    return (
                      <React.Fragment key={d.date}>
                        <tr
                          className={`hover:bg-blue-50/40 transition-colors cursor-pointer ${isWeekend ? 'bg-amber-50/40' : ''}`}
                          onClick={() => setExpandedDay(open ? null : d.date)}
                        >
                          <td className="px-4 py-3 font-medium text-gray-900">{dd}.{mm}.{yy}</td>
                          <td className={`px-3 py-3 text-center text-xs font-medium ${isWeekend ? 'text-amber-600' : 'text-gray-500'}`}>{d.weekday}</td>
                          <td className="px-3 py-3 text-center font-semibold text-blue-700">{d.cleanings}</td>
                          <td className="px-3 py-3 text-center text-gray-800">{d.entrances}</td>
                          <td className="px-3 py-3 text-center text-gray-700">{d.floors}</td>
                          <td className="px-4 py-3 text-right font-semibold text-gray-900">{(d.money || 0).toLocaleString('ru-RU')}</td>
                          <td className="px-3 py-3 text-center">
                            <span className="inline-flex items-center gap-1 text-xs text-gray-500">
                              {d.brigades?.length || 0} {open ? '▲' : '▼'}
                            </span>
                          </td>
                        </tr>
                        {open && d.brigades?.map((b) => (
                          <tr key={d.date + '_' + b.brigade} className="bg-gray-50/70 text-xs">
                            <td className="px-4 py-2 pl-8 text-gray-400">↳ {b.brigade === '—' ? 'без бригады' : b.brigade + ' бригада'}</td>
                            <td></td>
                            <td className="px-3 py-2 text-center text-blue-600">{b.cleanings}</td>
                            <td className="px-3 py-2 text-center text-gray-600">{b.entrances}</td>
                            <td className="px-3 py-2 text-center text-gray-600">{b.floors}</td>
                            <td className="px-4 py-2 text-right text-gray-700">{(b.money || 0).toLocaleString('ru-RU')}</td>
                            <td></td>
                          </tr>
                        ))}
                      </React.Fragment>
                    );
                  })}
                </tbody>
                {!dailyLoading && dailyData?.totals && dailyData.days?.length > 0 && (
                  <tfoot>
                    <tr className="bg-gray-50 border-t-2 border-gray-200 font-semibold text-gray-900">
                      <td className="px-4 py-3" colSpan={2}>ИТОГО за месяц</td>
                      <td className="px-3 py-3 text-center text-blue-700">{dailyData.totals.cleanings}</td>
                      <td className="px-3 py-3 text-center">{dailyData.totals.entrances}</td>
                      <td className="px-3 py-3 text-center">{dailyData.totals.floors}</td>
                      <td className="px-4 py-3 text-right">{(dailyData.totals.money || 0).toLocaleString('ru-RU')} ₽</td>
                      <td></td>
                    </tr>
                  </tfoot>
                )}
              </table>
            </div>
          </div>

          <div className="mt-3 text-xs text-gray-400">
            Деньги за день = Σ по уборкам (цена за подъезд из тарифа × подъезды дома). Нажмите на строку дня — разбивка по бригадам.
          </div>
        </div>
      )}'''

s = s.replace(anchor, daily_block, 1)
open(p, 'w', encoding='utf-8').write(s)
print("OK: рендер вкладки 'Расчёты по дням' добавлен")
