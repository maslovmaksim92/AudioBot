p = '/opt/audiobot/frontend/src/components/Works/Works.js'
s = open(p, encoding='utf-8').read()

anchor = "      {activeTab === 'acts' && (<div className=\"-m-6 p-6\"><ActsStats /></div>)}"
assert anchor in s

calc_block = anchor + '''

      {/* Вкладка "Расчёты" — побригадно */}
      {activeTab === 'calc' && (
        <div>
          <div className="flex items-center gap-3 mb-4">
            <Calculator className="w-5 h-5 text-blue-600" />
            <span className="text-sm text-gray-600">Месяц расчёта:</span>
            <input
              type="month"
              value={calcMonth}
              onChange={(e) => setCalcMonth(e.target.value)}
              className="px-3 py-1.5 border border-gray-300 rounded-lg text-sm"
            />
            <button onClick={fetchCalc} className="px-3 py-1.5 text-sm rounded-lg bg-gray-100 hover:bg-gray-200 flex items-center gap-1">
              <RefreshCw className={`w-3.5 h-3.5 ${calcLoading ? 'animate-spin' : ''}`} /> Обновить
            </button>
          </div>

          {/* Карточки-итоги */}
          {calcData?.totals && (
            <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-6 gap-3 mb-5">
              {[
                { label: 'Бригад', value: calcData.brigades?.length || 0, color: 'from-slate-500 to-slate-600' },
                { label: 'Домов', value: calcData.totals.houses, color: 'from-blue-500 to-blue-600' },
                { label: 'Подъездов', value: calcData.totals.entrances, color: 'from-indigo-500 to-indigo-600' },
                { label: 'Уборок (план)', value: calcData.totals.plan_cleanings, color: 'from-purple-500 to-purple-600' },
                { label: 'Уборок (факт)', value: calcData.totals.fact_cleanings, color: 'from-green-500 to-green-600' },
                { label: 'Сумма по тарифу, ₽', value: (calcData.totals.revenue || 0).toLocaleString('ru-RU'), color: 'from-amber-500 to-orange-600' },
              ].map((c, i) => (
                <div key={i} className={`bg-gradient-to-br ${c.color} text-white rounded-xl p-3 shadow-sm`}>
                  <div className="text-xl font-bold leading-none">{c.value}</div>
                  <div className="text-xs opacity-90 mt-1">{c.label}</div>
                </div>
              ))}
            </div>
          )}

          {/* Таблица по бригадам */}
          <div className="bg-white rounded-xl border border-gray-200 shadow-sm overflow-hidden">
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="bg-gray-50 border-b border-gray-200 text-left text-xs uppercase tracking-wide text-gray-500">
                    <th className="px-4 py-3 font-semibold">Бригада</th>
                    <th className="px-3 py-3 font-semibold text-center">Домов</th>
                    <th className="px-3 py-3 font-semibold text-center">Подъездов</th>
                    <th className="px-3 py-3 font-semibold text-center">Этажей</th>
                    <th className="px-3 py-3 font-semibold text-center">Квартир</th>
                    <th className="px-3 py-3 font-semibold text-center">Ср. подъездов/дом</th>
                    <th className="px-3 py-3 font-semibold text-center">Уборок план</th>
                    <th className="px-3 py-3 font-semibold text-center">Уборок факт</th>
                    <th className="px-4 py-3 font-semibold text-right">Сумма по тарифу, ₽</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-100">
                  {calcLoading && (<tr><td colSpan={9} className="px-4 py-10 text-center text-gray-400">Загрузка…</td></tr>)}
                  {!calcLoading && (!calcData?.brigades || calcData.brigades.length === 0) && (
                    <tr><td colSpan={9} className="px-4 py-10 text-center text-gray-400">Нет данных за выбранный месяц.</td></tr>
                  )}
                  {!calcLoading && calcData?.brigades?.map((b) => {
                    const planFactPct = b.plan_cleanings > 0 ? Math.round((b.fact_cleanings / b.plan_cleanings) * 100) : null;
                    return (
                      <tr key={b.brigade} className="hover:bg-blue-50/40 transition-colors">
                        <td className="px-4 py-3">
                          <span className="inline-flex items-center px-2.5 py-1 rounded-full text-xs font-semibold bg-green-50 text-green-700 border border-green-200">{b.brigade} бригада</span>
                        </td>
                        <td className="px-3 py-3 text-center font-medium text-gray-800">{b.houses}</td>
                        <td className="px-3 py-3 text-center font-medium text-gray-800">{b.entrances}</td>
                        <td className="px-3 py-3 text-center text-gray-700">{b.floors}</td>
                        <td className="px-3 py-3 text-center text-gray-700">{b.apartments}</td>
                        <td className="px-3 py-3 text-center text-gray-600">{b.avg_entrances_per_house}</td>
                        <td className="px-3 py-3 text-center text-purple-700 font-medium">{b.plan_cleanings}</td>
                        <td className="px-3 py-3 text-center">
                          <span className="text-green-700 font-medium">{b.fact_cleanings}</span>
                          {planFactPct !== null && (
                            <span className={`ml-1 text-xs ${planFactPct >= 100 ? 'text-green-500' : planFactPct >= 50 ? 'text-amber-500' : 'text-red-400'}`}>({planFactPct}%)</span>
                          )}
                        </td>
                        <td className="px-4 py-3 text-right font-semibold text-gray-900">{(b.revenue || 0).toLocaleString('ru-RU')}</td>
                      </tr>
                    );
                  })}
                </tbody>
                {!calcLoading && calcData?.totals && calcData.brigades?.length > 0 && (
                  <tfoot>
                    <tr className="bg-gray-50 border-t-2 border-gray-200 font-semibold text-gray-900">
                      <td className="px-4 py-3">ИТОГО</td>
                      <td className="px-3 py-3 text-center">{calcData.totals.houses}</td>
                      <td className="px-3 py-3 text-center">{calcData.totals.entrances}</td>
                      <td className="px-3 py-3 text-center">{calcData.totals.floors}</td>
                      <td className="px-3 py-3 text-center">{calcData.totals.apartments}</td>
                      <td className="px-3 py-3 text-center">—</td>
                      <td className="px-3 py-3 text-center text-purple-700">{calcData.totals.plan_cleanings}</td>
                      <td className="px-3 py-3 text-center text-green-700">{calcData.totals.fact_cleanings}</td>
                      <td className="px-4 py-3 text-right">{(calcData.totals.revenue || 0).toLocaleString('ru-RU')} ₽</td>
                    </tr>
                  </tfoot>
                )}
              </table>
            </div>
          </div>

          <div className="mt-3 text-xs text-gray-400">
            Сумма по тарифу = (уборок/мес из тарифа) × (подъезды) × (цена за подъезд). Формулу уточним под вашу методику.
          </div>
        </div>
      )}'''

s = s.replace(anchor, calc_block, 1)
open(p, 'w', encoding='utf-8').write(s)
print("OK: рендер вкладки 'Расчёты' добавлен")
