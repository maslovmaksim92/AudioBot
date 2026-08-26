import React, { useEffect, useState } from 'react';
import {
  Crown, Building2, Wallet, TrendingUp, Users, AlertTriangle,
  RefreshCw, CheckCircle2, DoorOpen, Layers, Home as HomeIcon, Target
} from 'lucide-react';
import {
  ResponsiveContainer, AreaChart, Area, BarChart, Bar, XAxis, YAxis,
  CartesianGrid, Tooltip, Cell, PieChart, Pie, Legend
} from 'recharts';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL || (import.meta?.env?.REACT_APP_BACKEND_URL);

const money = (v) => (v || 0).toLocaleString('ru-RU');
const cleanUK = (name) => {
  if (!name) return 'Без УК';
  let s = String(name).trim();
  s = s.replace(/^(\s*(ООО|ОАО|ЗАО|ПАО|АО|ТСЖ|ТСН|ЖСК|ИП|МУП|ГУП|УК|РКЦ)\b[\s"«»]*)+/iu, '');
  s = s.replace(/^[«"']+|[«"'»]+$/g, '').trim();
  return s || String(name).trim();
};

const BRIGADE_COLORS = ['#3b82f6', '#8b5cf6', '#ec4899', '#f59e0b', '#10b981', '#06b6d4', '#ef4444', '#6366f1'];

const OwnerDashboard = () => {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [month, setMonth] = useState(() => {
    const n = new Date(); return `${n.getFullYear()}-${String(n.getMonth() + 1).padStart(2, '0')}`;
  });

  useEffect(() => { fetchData(); /* eslint-disable-next-line */ }, [month]);

  const fetchData = async () => {
    setLoading(true);
    try {
      const r = await fetch(`${BACKEND_URL}/api/cleaning/owner-overview?month=${month}`);
      const d = await r.json();
      setData(d);
    } catch (e) {
      console.error('owner overview error', e);
      setData(null);
    } finally {
      setLoading(false);
    }
  };

  const k = data?.kpi || {};
  const risks = data?.risks || {};
  const daily = (data?.daily || []).map(d => ({ ...d, name: String(d.day).padStart(2, '0') }));
  const brigades = (data?.brigades || []).filter(b => b.brigade !== '—');
  const topCompanies = (data?.top_companies || []).map(c => ({ ...c, short: cleanUK(c.company) }));

  const riskTotal = (risks.no_brigade || 0) + (risks.no_amount || 0) + (risks.no_schedule || 0);

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 to-blue-50/40 -m-6 p-6">
      {/* Заголовок */}
      <div className="flex flex-wrap items-center justify-between gap-4 mb-6">
        <div className="flex items-center gap-3">
          <div className="w-12 h-12 rounded-2xl bg-gradient-to-br from-amber-400 to-orange-500 flex items-center justify-center shadow-lg shadow-orange-200">
            <Crown className="w-7 h-7 text-white" />
          </div>
          <div>
            <h1 className="text-2xl font-bold text-gray-900">Кабинет собственника</h1>
            <p className="text-sm text-gray-500">Управленческая сводка по бизнесу клининга</p>
          </div>
        </div>
        <div className="flex items-center gap-2">
          <input type="month" value={month} onChange={(e) => setMonth(e.target.value)}
                 className="px-3 py-2 border border-gray-300 rounded-xl text-sm bg-white shadow-sm" />
          <button onClick={fetchData}
                  className="px-4 py-2 rounded-xl bg-white border border-gray-300 shadow-sm hover:bg-gray-50 flex items-center gap-2 text-sm">
            <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} /> Обновить
          </button>
        </div>
      </div>

      {loading && <div className="text-center py-20 text-gray-400">Загрузка сводки…</div>}

      {!loading && data && (
        <>
          {/* Главные финансовые карточки */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-5">
            <div className="bg-gradient-to-br from-emerald-500 to-green-600 rounded-2xl p-5 text-white shadow-lg shadow-green-200/50">
              <div className="flex items-center justify-between">
                <Wallet className="w-8 h-8 opacity-80" />
                <span className="text-xs bg-white/20 px-2 py-1 rounded-full">в месяц</span>
              </div>
              <div className="text-3xl font-bold mt-3">{money(k.total_revenue)} ₽</div>
              <div className="text-sm opacity-90 mt-1">Выручка по договорам</div>
            </div>

            <div className="bg-gradient-to-br from-blue-500 to-indigo-600 rounded-2xl p-5 text-white shadow-lg shadow-blue-200/50">
              <div className="flex items-center justify-between">
                <Building2 className="w-8 h-8 opacity-80" />
                <span className="text-xs bg-white/20 px-2 py-1 rounded-full">активных</span>
              </div>
              <div className="text-3xl font-bold mt-3">{k.total_houses}</div>
              <div className="text-sm opacity-90 mt-1">Домов на обслуживании</div>
            </div>

            <div className="bg-gradient-to-br from-purple-500 to-fuchsia-600 rounded-2xl p-5 text-white shadow-lg shadow-purple-200/50">
              <div className="flex items-center justify-between">
                <Target className="w-8 h-8 opacity-80" />
                <span className="text-xs bg-white/20 px-2 py-1 rounded-full">ARPU</span>
              </div>
              <div className="text-3xl font-bold mt-3">{money(k.avg_check)} ₽</div>
              <div className="text-sm opacity-90 mt-1">Средний чек на дом</div>
            </div>

            <div className="bg-gradient-to-br from-amber-500 to-orange-600 rounded-2xl p-5 text-white shadow-lg shadow-orange-200/50">
              <div className="flex items-center justify-between">
                <CheckCircle2 className="w-8 h-8 opacity-80" />
                <span className="text-xs bg-white/20 px-2 py-1 rounded-full">план/факт</span>
              </div>
              <div className="text-3xl font-bold mt-3">{k.completion_pct}%</div>
              <div className="text-sm opacity-90 mt-1">Выполнение уборок ({k.fact_cleanings}/{k.plan_cleanings})</div>
            </div>
          </div>

          {/* Вторичные метрики */}
          <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-3 mb-6">
            {[
              { icon: DoorOpen, label: 'Подъездов', value: k.total_entrances, color: 'text-indigo-600 bg-indigo-50' },
              { icon: Layers, label: 'Этажей', value: k.total_floors, color: 'text-purple-600 bg-purple-50' },
              { icon: HomeIcon, label: 'Квартир', value: k.total_apartments, color: 'text-blue-600 bg-blue-50' },
              { icon: TrendingUp, label: 'Уборок/мес', value: k.plan_cleanings, color: 'text-emerald-600 bg-emerald-50' },
              { icon: Users, label: 'Бригад', value: k.brigades_count, color: 'text-orange-600 bg-orange-50' },
              { icon: Building2, label: 'УК', value: k.companies_count, color: 'text-pink-600 bg-pink-50' },
            ].map((m, i) => (
              <div key={i} className="bg-white rounded-xl border border-gray-100 p-3 shadow-sm">
                <div className={`w-9 h-9 rounded-lg flex items-center justify-center ${m.color} mb-2`}>
                  <m.icon className="w-5 h-5" />
                </div>
                <div className="text-xl font-bold text-gray-900">{money(m.value)}</div>
                <div className="text-xs text-gray-500">{m.label}</div>
              </div>
            ))}
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-3 gap-5 mb-5">
            {/* График выручки по дням */}
            <div className="lg:col-span-2 bg-white rounded-2xl border border-gray-100 p-5 shadow-sm">
              <h3 className="font-semibold text-gray-800 mb-4 flex items-center gap-2">
                <TrendingUp className="w-5 h-5 text-emerald-600" /> Поступления по дням месяца
              </h3>
              <ResponsiveContainer width="100%" height={260}>
                <AreaChart data={daily} margin={{ top: 5, right: 10, left: 0, bottom: 0 }}>
                  <defs>
                    <linearGradient id="rev" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="0%" stopColor="#10b981" stopOpacity={0.4} />
                      <stop offset="100%" stopColor="#10b981" stopOpacity={0} />
                    </linearGradient>
                  </defs>
                  <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" />
                  <XAxis dataKey="name" tick={{ fontSize: 11 }} stroke="#94a3b8" />
                  <YAxis tick={{ fontSize: 11 }} stroke="#94a3b8" tickFormatter={(v) => v >= 1000 ? `${(v/1000).toFixed(0)}к` : v} />
                  <Tooltip formatter={(v, n) => n === 'money' ? [`${money(v)} ₽`, 'Поступления'] : [v, 'Уборок']}
                           labelFormatter={(l) => `День ${l}`} />
                  <Area type="monotone" dataKey="money" stroke="#10b981" strokeWidth={2} fill="url(#rev)" />
                </AreaChart>
              </ResponsiveContainer>
            </div>

            {/* Топ УК — pie */}
            <div className="bg-white rounded-2xl border border-gray-100 p-5 shadow-sm">
              <h3 className="font-semibold text-gray-800 mb-4 flex items-center gap-2">
                <Building2 className="w-5 h-5 text-pink-600" /> Выручка по УК
              </h3>
              <ResponsiveContainer width="100%" height={260}>
                <PieChart>
                  <Pie data={topCompanies} dataKey="revenue" nameKey="short" cx="50%" cy="50%"
                       outerRadius={90} innerRadius={45} paddingAngle={2}>
                    {topCompanies.map((e, i) => <Cell key={i} fill={BRIGADE_COLORS[i % BRIGADE_COLORS.length]} />)}
                  </Pie>
                  <Tooltip formatter={(v) => `${money(v)} ₽`} />
                </PieChart>
              </ResponsiveContainer>
              <div className="space-y-1 mt-2 max-h-28 overflow-y-auto">
                {topCompanies.map((c, i) => (
                  <div key={i} className="flex items-center justify-between text-xs">
                    <span className="flex items-center gap-1.5 text-gray-600 truncate">
                      <span className="w-2.5 h-2.5 rounded-full flex-shrink-0" style={{ background: BRIGADE_COLORS[i % BRIGADE_COLORS.length] }} />
                      <span className="truncate">{c.short}</span>
                    </span>
                    <span className="font-medium text-gray-800 flex-shrink-0 ml-2">{money(c.revenue)} ₽</span>
                  </div>
                ))}
              </div>
            </div>
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-3 gap-5">
            {/* Эффективность бригад */}
            <div className="lg:col-span-2 bg-white rounded-2xl border border-gray-100 p-5 shadow-sm">
              <h3 className="font-semibold text-gray-800 mb-4 flex items-center gap-2">
                <Users className="w-5 h-5 text-orange-600" /> Бригады: выручка и нагрузка
              </h3>
              <ResponsiveContainer width="100%" height={240}>
                <BarChart data={brigades.map(b => ({ ...b, name: `${b.brigade} бр.` }))}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" />
                  <XAxis dataKey="name" tick={{ fontSize: 11 }} stroke="#94a3b8" />
                  <YAxis yAxisId="l" tick={{ fontSize: 11 }} stroke="#94a3b8" tickFormatter={(v) => v >= 1000 ? `${(v/1000).toFixed(0)}к` : v} />
                  <YAxis yAxisId="r" orientation="right" tick={{ fontSize: 11 }} stroke="#94a3b8" />
                  <Tooltip formatter={(v, n) => n === 'revenue' ? [`${money(v)} ₽`, 'Выручка'] : [v, n === 'houses' ? 'Домов' : 'Уборок']} />
                  <Legend wrapperStyle={{ fontSize: 12 }} />
                  <Bar yAxisId="l" dataKey="revenue" name="Выручка" radius={[6, 6, 0, 0]}>
                    {brigades.map((e, i) => <Cell key={i} fill={BRIGADE_COLORS[i % BRIGADE_COLORS.length]} />)}
                  </Bar>
                  <Bar yAxisId="r" dataKey="houses" name="Домов" fill="#cbd5e1" radius={[6, 6, 0, 0]} />
                </BarChart>
              </ResponsiveContainer>
            </div>

            {/* Риски / на что обратить внимание */}
            <div className="bg-white rounded-2xl border border-gray-100 p-5 shadow-sm">
              <h3 className="font-semibold text-gray-800 mb-4 flex items-center gap-2">
                <AlertTriangle className="w-5 h-5 text-amber-500" /> Требует внимания
              </h3>
              {riskTotal === 0 ? (
                <div className="flex flex-col items-center justify-center py-8 text-center">
                  <CheckCircle2 className="w-12 h-12 text-green-500 mb-2" />
                  <p className="text-sm text-gray-500">Все данные заполнены</p>
                </div>
              ) : (
                <div className="space-y-3">
                  {[
                    { label: 'Дома без бригады', value: risks.no_brigade, color: 'bg-orange-50 text-orange-700 border-orange-200' },
                    { label: 'Дома без суммы договора', value: risks.no_amount, color: 'bg-red-50 text-red-700 border-red-200' },
                    { label: 'Дома без графика уборок', value: risks.no_schedule, color: 'bg-amber-50 text-amber-700 border-amber-200' },
                  ].filter(r => r.value > 0).map((r, i) => (
                    <div key={i} className={`flex items-center justify-between px-3 py-2.5 rounded-xl border ${r.color}`}>
                      <span className="text-sm">{r.label}</span>
                      <span className="text-lg font-bold">{r.value}</span>
                    </div>
                  ))}
                  <div className="text-xs text-gray-400 mt-3">
                    Чем меньше — тем точнее аналитика и выставление актов.
                  </div>
                </div>
              )}
            </div>
          </div>
        </>
      )}

      {!loading && !data && (
        <div className="text-center py-20 text-gray-400">Не удалось загрузить сводку. Нажмите «Обновить».</div>
      )}
    </div>
  );
};

export default OwnerDashboard;
