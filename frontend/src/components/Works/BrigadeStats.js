import React, { useState, useEffect } from 'react';
import {
  Users, RefreshCw, Wallet, DoorOpen, Layers, Home as HomeIcon,
  Building2, TrendingUp, Target, CheckCircle2
} from 'lucide-react';
import {
  ResponsiveContainer, BarChart, Bar, XAxis, YAxis, CartesianGrid,
  Tooltip, Cell, Legend, RadarChart, PolarGrid, PolarAngleAxis, PolarRadiusAxis, Radar
} from 'recharts';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL || (import.meta?.env?.REACT_APP_BACKEND_URL);
const money = (v) => Math.round(v || 0).toLocaleString('ru-RU');
const COLORS = ['#3b82f6', '#8b5cf6', '#ec4899', '#f59e0b', '#10b981', '#06b6d4', '#ef4444', '#6366f1'];

const BrigadeStats = () => {
  const [month, setMonth] = useState(() => {
    const n = new Date(); return `${n.getFullYear()}-${String(n.getMonth() + 1).padStart(2, '0')}`;
  });
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [sortKey, setSortKey] = useState('revenue');

  useEffect(() => { fetchData(); /* eslint-disable-next-line */ }, [month]);

  const fetchData = async () => {
    setLoading(true);
    try {
      const r = await fetch(`${BACKEND_URL}/api/cleaning/brigade-calc?month=${month}`);
      if (!r.ok) throw new Error(`HTTP ${r.status}`);
      setData(await r.json());
    } catch (e) {
      console.error('brigade-calc error', e);
      setData(null);
    } finally {
      setLoading(false);
    }
  };

  const brigades = (data?.brigades || []).filter(b => b.brigade !== '—');
  const totals = data?.totals || {};
  const sorted = [...brigades].sort((a, b) => (b[sortKey] || 0) - (a[sortKey] || 0));
  const chartData = brigades.map((b, i) => ({ ...b, name: `${b.brigade} бр.`, color: COLORS[i % COLORS.length] }));

  // данные для radar (нормализованные) — сравнение бригад по 4 осям
  const maxOf = (k) => Math.max(1, ...brigades.map(b => b[k] || 0));
  const radarAxes = [
    { key: 'revenue', label: 'Деньги' },
    { key: 'houses', label: 'Дома' },
    { key: 'entrances', label: 'Подъезды' },
    { key: 'floors', label: 'Этажи' },
    { key: 'plan_cleanings', label: 'Уборки' },
  ];
  const radarData = radarAxes.map(ax => {
    const row = { axis: ax.label };
    brigades.forEach(b => { row[`б${b.brigade}`] = Math.round((b[ax.key] || 0) / maxOf(ax.key) * 100); });
    return row;
  });

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 to-indigo-50/30 p-6">
      <div className="flex flex-wrap items-center justify-between gap-4 mb-6">
        <div className="flex items-center gap-3">
          <div className="w-11 h-11 rounded-2xl bg-gradient-to-br from-orange-400 to-pink-500 flex items-center justify-center shadow-lg shadow-orange-200">
            <Users className="w-6 h-6 text-white" />
          </div>
          <div>
            <h1 className="text-2xl font-bold text-gray-900">KPI бригад</h1>
            <p className="text-sm text-gray-500">Деньги, объёмы и выполнение по бригадам</p>
          </div>
        </div>
        <div className="flex items-center gap-2">
          <input type="month" value={month} onChange={(e) => setMonth(e.target.value)}
                 className="px-3 py-2 border border-gray-300 rounded-xl text-sm bg-white shadow-sm" />
          <button onClick={fetchData} className="px-4 py-2 rounded-xl bg-white border border-gray-300 shadow-sm hover:bg-gray-50 flex items-center gap-2 text-sm">
            <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} /> Обновить
          </button>
        </div>
      </div>

      {loading && <div className="text-center py-20 text-gray-400">Загрузка…</div>}

      {!loading && data && (
        <>
          {/* Итоги */}
          <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-3 mb-6">
            {[
              { icon: Users, label: 'Бригад', value: brigades.length, c: 'from-slate-500 to-slate-600' },
              { icon: Wallet, label: 'Выручка ₽', value: money(totals.revenue), c: 'from-emerald-500 to-green-600' },
              { icon: Building2, label: 'Домов', value: totals.houses, c: 'from-blue-500 to-indigo-600' },
              { icon: DoorOpen, label: 'Подъездов', value: totals.entrances, c: 'from-indigo-500 to-purple-600' },
              { icon: Layers, label: 'Этажей', value: totals.floors, c: 'from-purple-500 to-fuchsia-600' },
              { icon: TrendingUp, label: 'Уборок', value: totals.plan_cleanings, c: 'from-amber-500 to-orange-600' },
            ].map((m, i) => (
              <div key={i} className={`bg-gradient-to-br ${m.c} text-white rounded-2xl p-4 shadow-md`}>
                <m.icon className="w-6 h-6 opacity-80 mb-2" />
                <div className="text-2xl font-bold leading-none">{m.value}</div>
                <div className="text-xs opacity-90 mt-1">{m.label}</div>
              </div>
            ))}
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-3 gap-5 mb-5">
            {/* Выручка по бригадам */}
            <div className="lg:col-span-2 bg-white rounded-2xl border border-gray-100 p-5 shadow-sm">
              <h3 className="font-semibold text-gray-800 mb-4 flex items-center gap-2">
                <Wallet className="w-5 h-5 text-emerald-600" /> Выручка и объёмы по бригадам
              </h3>
              <ResponsiveContainer width="100%" height={280}>
                <BarChart data={chartData}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" />
                  <XAxis dataKey="name" tick={{ fontSize: 12 }} stroke="#94a3b8" />
                  <YAxis yAxisId="l" tick={{ fontSize: 11 }} stroke="#94a3b8" tickFormatter={(v) => v >= 1000 ? `${(v/1000).toFixed(0)}к` : v} />
                  <YAxis yAxisId="r" orientation="right" tick={{ fontSize: 11 }} stroke="#94a3b8" />
                  <Tooltip formatter={(v, n) => n === 'revenue' ? [`${money(v)} ₽`, 'Выручка'] : [v, n === 'entrances' ? 'Подъезды' : 'Этажи']} />
                  <Legend wrapperStyle={{ fontSize: 12 }} />
                  <Bar yAxisId="l" dataKey="revenue" name="Выручка ₽" radius={[6, 6, 0, 0]}>
                    {chartData.map((e, i) => <Cell key={i} fill={e.color} />)}
                  </Bar>
                  <Bar yAxisId="r" dataKey="entrances" name="Подъезды" fill="#cbd5e1" radius={[6, 6, 0, 0]} />
                </BarChart>
              </ResponsiveContainer>
            </div>

            {/* Radar сравнение */}
            <div className="bg-white rounded-2xl border border-gray-100 p-5 shadow-sm">
              <h3 className="font-semibold text-gray-800 mb-4 flex items-center gap-2">
                <Target className="w-5 h-5 text-purple-600" /> Сравнение бригад
              </h3>
              <ResponsiveContainer width="100%" height={280}>
                <RadarChart data={radarData} outerRadius={90}>
                  <PolarGrid stroke="#e2e8f0" />
                  <PolarAngleAxis dataKey="axis" tick={{ fontSize: 11 }} />
                  <PolarRadiusAxis tick={false} axisLine={false} />
                  {brigades.map((b, i) => (
                    <Radar key={b.brigade} name={`${b.brigade} бр.`} dataKey={`б${b.brigade}`}
                           stroke={COLORS[i % COLORS.length]} fill={COLORS[i % COLORS.length]} fillOpacity={0.08} strokeWidth={2} />
                  ))}
                  <Legend wrapperStyle={{ fontSize: 11 }} />
                </RadarChart>
              </ResponsiveContainer>
            </div>
          </div>

          {/* Детальная таблица */}
          <div className="bg-white rounded-2xl border border-gray-100 shadow-sm overflow-hidden">
            <div className="px-5 py-3 border-b border-gray-100 flex items-center justify-between">
              <h3 className="font-semibold text-gray-800">Детально по бригадам</h3>
              <div className="flex items-center gap-1 text-xs">
                <span className="text-gray-400 mr-1">сортировка:</span>
                {[['revenue', 'Деньги'], ['houses', 'Дома'], ['entrances', 'Подъезды'], ['plan_cleanings', 'Уборки']].map(([k, l]) => (
                  <button key={k} onClick={() => setSortKey(k)}
                          className={`px-2 py-1 rounded-md ${sortKey === k ? 'bg-blue-600 text-white' : 'bg-gray-100 hover:bg-gray-200 text-gray-600'}`}>{l}</button>
                ))}
              </div>
            </div>
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="bg-gray-50 border-b border-gray-200 text-left text-xs uppercase tracking-wide text-gray-500">
                    <th className="px-4 py-3 font-semibold">Бригада</th>
                    <th className="px-3 py-3 font-semibold text-center">Домов</th>
                    <th className="px-3 py-3 font-semibold text-center">Подъездов</th>
                    <th className="px-3 py-3 font-semibold text-center">Этажей</th>
                    <th className="px-3 py-3 font-semibold text-center">Квартир</th>
                    <th className="px-3 py-3 font-semibold text-center">Уборок (план)</th>
                    <th className="px-3 py-3 font-semibold text-center">Факт (%)</th>
                    <th className="px-4 py-3 font-semibold text-right">Выручка ₽</th>
                    <th className="px-4 py-3 font-semibold text-right">₽/дом</th>
                    <th className="px-4 py-3 font-semibold text-right">₽/подъезд</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-100">
                  {sorted.map((b, i) => (
                    <tr key={b.brigade} className="hover:bg-blue-50/40 transition-colors">
                      <td className="px-4 py-3">
                        <span className="inline-flex items-center gap-2">
                          <span className="w-3 h-3 rounded-full" style={{ background: COLORS[brigades.findIndex(x => x.brigade === b.brigade) % COLORS.length] }} />
                          <span className="font-semibold text-gray-800">{b.brigade} бригада</span>
                        </span>
                      </td>
                      <td className="px-3 py-3 text-center font-medium text-gray-800">{b.houses}</td>
                      <td className="px-3 py-3 text-center text-gray-700">{b.entrances}</td>
                      <td className="px-3 py-3 text-center text-gray-700">{b.floors}</td>
                      <td className="px-3 py-3 text-center text-gray-700">{b.apartments}</td>
                      <td className="px-3 py-3 text-center text-purple-700 font-medium">{b.plan_cleanings}</td>
                      <td className="px-3 py-3 text-center">
                        <span className={`inline-flex items-center gap-1 ${b.completion_pct >= 80 ? 'text-green-600' : b.completion_pct >= 40 ? 'text-amber-600' : 'text-red-500'}`}>
                          {b.fact_cleanings}/{b.plan_cleanings}
                          <span className="text-xs">({b.completion_pct}%)</span>
                        </span>
                      </td>
                      <td className="px-4 py-3 text-right font-bold text-gray-900">{money(b.revenue)}</td>
                      <td className="px-4 py-3 text-right text-gray-600">{money(b.revenue_per_house)}</td>
                      <td className="px-4 py-3 text-right text-gray-600">{money(b.revenue_per_entrance)}</td>
                    </tr>
                  ))}
                </tbody>
                <tfoot>
                  <tr className="bg-gray-50 border-t-2 border-gray-200 font-semibold text-gray-900">
                    <td className="px-4 py-3">ИТОГО</td>
                    <td className="px-3 py-3 text-center">{totals.houses}</td>
                    <td className="px-3 py-3 text-center">{totals.entrances}</td>
                    <td className="px-3 py-3 text-center">{totals.floors}</td>
                    <td className="px-3 py-3 text-center">{totals.apartments}</td>
                    <td className="px-3 py-3 text-center text-purple-700">{totals.plan_cleanings}</td>
                    <td className="px-3 py-3 text-center text-green-700">{totals.fact_cleanings}</td>
                    <td className="px-4 py-3 text-right">{money(totals.revenue)} ₽</td>
                    <td className="px-4 py-3"></td>
                    <td className="px-4 py-3"></td>
                  </tr>
                </tfoot>
              </table>
            </div>
          </div>

          {/* Карточки эффективности */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 mt-5">
            {sorted.map((b, i) => (
              <div key={b.brigade} className="bg-white rounded-2xl border border-gray-100 p-5 shadow-sm">
                <div className="flex items-center justify-between mb-3">
                  <span className="inline-flex items-center gap-2 font-semibold text-gray-800">
                    <span className="w-8 h-8 rounded-xl flex items-center justify-center text-white text-sm font-bold"
                          style={{ background: COLORS[brigades.findIndex(x => x.brigade === b.brigade) % COLORS.length] }}>
                      {b.brigade}
                    </span>
                    {b.brigade} бригада
                  </span>
                  <span className="text-lg font-bold text-emerald-600">{money(b.revenue)} ₽</span>
                </div>
                <div className="grid grid-cols-3 gap-2 text-center">
                  {[
                    { l: 'Домов', v: b.houses, icon: Building2 },
                    { l: 'Подъездов', v: b.entrances, icon: DoorOpen },
                    { l: 'Этажей', v: b.floors, icon: Layers },
                    { l: 'Квартир', v: b.apartments, icon: HomeIcon },
                    { l: 'Уборок', v: b.plan_cleanings, icon: TrendingUp },
                    { l: 'Выполн.', v: `${b.completion_pct}%`, icon: CheckCircle2 },
                  ].map((m, j) => (
                    <div key={j} className="bg-gray-50 rounded-xl py-2">
                      <m.icon className="w-4 h-4 mx-auto text-gray-400 mb-1" />
                      <div className="text-base font-bold text-gray-800">{m.v}</div>
                      <div className="text-[10px] text-gray-500">{m.l}</div>
                    </div>
                  ))}
                </div>
                <div className="mt-3 pt-3 border-t border-gray-100 flex justify-between text-xs text-gray-500">
                  <span>₽/дом: <b className="text-gray-700">{money(b.revenue_per_house)}</b></span>
                  <span>₽/подъезд: <b className="text-gray-700">{money(b.revenue_per_entrance)}</b></span>
                </div>
              </div>
            ))}
          </div>
        </>
      )}

      {!loading && !data && (
        <div className="text-center py-20 text-gray-400">Не удалось загрузить данные.</div>
      )}
    </div>
  );
};

export default BrigadeStats;
