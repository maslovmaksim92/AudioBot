p = '/opt/audiobot/frontend/src/components/Works/Works.js'
s = open(p, encoding='utf-8').read()

# 1) colSpan 8 -> 9 в строках "загрузка"/"не найдено" (только в списке домов)
s = s.replace(
    '<tr><td colSpan={8} className="px-4 py-10 text-center text-gray-400">Загрузка…</td></tr>',
    '<tr><td colSpan={9} className="px-4 py-10 text-center text-gray-400">Загрузка…</td></tr>'
)
s = s.replace(
    '<tr><td colSpan={8} className="px-4 py-10 text-center text-gray-400">Дома не найдены. Измените фильтры.</td></tr>',
    '<tr><td colSpan={9} className="px-4 py-10 text-center text-gray-400">Дома не найдены. Измените фильтры.</td></tr>'
)

# 2) график за выбранный месяц + ячейка Акт
OLD = '''                          <td className="px-4 py-3">
                            {sched ? (
                              <div className="flex items-center gap-1 flex-wrap">
                                <span className="text-xs font-medium text-purple-700">{sched.label}:</span>
                                {sched.days.map((d, i) => (
                                  <span key={i} className="inline-flex items-center justify-center min-w-[24px] px-1.5 py-0.5 rounded bg-purple-50 text-purple-700 text-xs font-semibold border border-purple-100">{d}</span>
                                ))}
                                {sched.more > 0 && <span className="text-xs text-gray-400">+{sched.more} мес.</span>}
                              </div>
                            ) : <span className="text-xs text-gray-300">нет графика</span>}
                          </td>
                        </tr>'''
NEW = '''                          <td className="px-4 py-3">
                            {monthDays(h).length > 0 ? (
                              <div className="flex items-center gap-1 flex-wrap">
                                {monthDays(h).map((d, i) => (
                                  <span key={i} className="inline-flex items-center justify-center min-w-[24px] px-1.5 py-0.5 rounded bg-purple-50 text-purple-700 text-xs font-semibold border border-purple-100">{d}</span>
                                ))}
                              </div>
                            ) : <span className="text-xs text-gray-300">нет в этом месяце</span>}
                          </td>
                          <td className="px-3 py-3 text-center">
                            {h.act_signed
                              ? <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-medium bg-green-100 text-green-700 border border-green-200" title={`Фото: ${h.act_photo_count || 0}`}>✓ подписан</span>
                              : <span className="text-xs text-gray-300">—</span>}
                          </td>
                        </tr>'''
assert OLD in s
s = s.replace(OLD, NEW)

# 3) хелпер monthDays — дни уборки выбранного месяца. Добавим рядом со scheduleSummary.
anchor = "const Works = () => {"
helper = """// дни уборки выбранного месяца (listMonth -> month_key)
const monthKeyFromYM = (ym) => {
  const M = {1:'january',2:'february',3:'march',4:'april',5:'may',6:'june',7:'july',8:'august',9:'september',10:'october',11:'november',12:'december'};
  if (!ym) return null;
  const [y, m] = ym.split('-'); return `${M[parseInt(m)]}_${parseInt(y)}`;
};

const Works = () => {"""
assert anchor in s
s = s.replace(anchor, helper, 1)

# monthDays использует listMonth из замыкания — определим внутри компонента, рядом с visibleHouses
anchor2 = "  const periodicityOptions = "
fn = """  const monthDays = (h) => {
    const key = monthKeyFromYM(listMonth);
    const cd = (h.cleaning_dates || {})[key];
    if (!cd || !cd.dates) return [];
    return cd.dates.map(d => (d || '').split('T')[0].split('-')[2]).filter(Boolean);
  };

  const periodicityOptions = """
assert anchor2 in s
s = s.replace(anchor2, fn, 1)

open(p, 'w', encoding='utf-8').write(s)
print("OK: график за месяц + колонка Акт + хелперы")
