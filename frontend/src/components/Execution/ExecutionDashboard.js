import React, { useState, useEffect } from 'react';
import {
  CheckCircle, Clock, AlertTriangle, Camera, TrendingUp,
  Building2, Users, RefreshCw
} from 'lucide-react';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL || import.meta?.env?.REACT_APP_BACKEND_URL;

const MONTHS = ['', 'Январь', 'Февраль', 'Март', 'Апрель', 'Май', 'Июнь',
  'Июль', 'Август', 'Сентябрь', 'Октябрь', 'Ноябрь', 'Декабрь'];

function Bar({ pct, color }) {
  return (
    <div className="w-full bg-gray-100 rounded-full h-2.5">
      <div className={`h-2.5 rounded-full ${color}`} style={{ width: `${pct}%` }} />
    </div>
  );
}

function KpiCard({ icon: Icon, label, value, sub, color }) {
  return (
    <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-5">
      <div className="flex items-center justify-between">
        <div>
          <p className="text-sm text-gray-500">{label}</p>
          <p className="text-3xl font-semibold mt-1">{value}</p>
          {sub && <p className="text-xs text-gray-400 mt-1">{sub}</p>}
        </div>
        <div className={`p-3 rounded-lg ${color}`}><Icon size={24} /></div>
      </div>
    </div>
  );
}

export default function ExecutionDashboard() {
  const [data, setData] = useState(null);
  const [recent, setRecent] = useState([]);
  const [loading, setLoading] = useState(true);
  const now = new Date();
  const [year] = useState(now.getFullYear());
  const [month] = useState(now.getMonth() + 1);

  const load = async () => {
    try {
      const r = await fetch(`${BACKEND_URL}/api/execution/summary?year=${year}&month=${month}`);
      setData(await r.json());
      const rr = await fetch(`${BACKEND_URL}/api/execution/recent?limit=15`);
      setRecent((await rr.json()).items || []);
    } catch (e) {
      console.error('execution load error', e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    load();
    const t = setInterval(load, 30000);
    return () => clearInterval(t);
  }, []); // eslint-disable-line

  if (loading) return <div className="p-8 text-gray-500">Загрузка дашборда…</div>;
  if (!data) return <div className="p-8 text-gray-500">Нет данных.</div>;

  const t = data.totals;

  return (
    <div className="p-6 space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-semibold">Выполнение работ</h1>
          <p className="text-gray-500 text-sm">Уборки за {MONTHS[month]} {year} · план / факт по фотоотчётам</p>
        </div>
        <button onClick={load} className="flex items-center gap-2 text-sm text-gray-600 hover:text-gray-900">
          <RefreshCw size={16} /> Обновить
        </button>
      </div>

      {/* KPI */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <KpiCard icon={TrendingUp} label="Выполнение" value={`${t.completion_pct}%`}
          sub={`${t.done} из ${t.planned} уборок`} color="bg-blue-50 text-blue-600" />
        <KpiCard icon={CheckCircle} label="Выполнено" value={t.done}
          sub="фото в группе" color="bg-green-50 text-green-600" />
        <KpiCard icon={Clock} label="Ожидается" value={t.pending}
          sub="по плану впереди" color="bg-amber-50 text-amber-600" />
        <KpiCard icon={AlertTriangle} label="Просрочено" value={t.overdue}
          sub="дата прошла, фото нет" color="bg-red-50 text-red-600" />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* По бригадам */}
        <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-5">
          <h2 className="font-semibold mb-4 flex items-center gap-2"><Users size={18} /> По бригадам</h2>
          <div className="space-y-3">
            {data.by_brigade.map((b) => (
              <div key={b.brigade}>
                <div className="flex justify-between text-sm mb-1">
                  <span>Бригада {b.brigade}</span>
                  <span className="text-gray-500">{b.done}/{b.planned} · {b.completion_pct}%</span>
                </div>
                <Bar pct={b.completion_pct} color={b.completion_pct >= 80 ? 'bg-green-500' : b.completion_pct >= 50 ? 'bg-amber-500' : 'bg-red-500'} />
                {b.overdue > 0 && <p className="text-xs text-red-500 mt-1">просрочено: {b.overdue}</p>}
              </div>
            ))}
          </div>
        </div>

        {/* По УК */}
        <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-5">
          <h2 className="font-semibold mb-4 flex items-center gap-2"><Building2 size={18} /> По управляющим компаниям</h2>
          <div className="space-y-3">
            {data.by_uk.map((u) => (
              <div key={u.uk}>
                <div className="flex justify-between text-sm mb-1">
                  <span className="truncate pr-2">{u.uk}</span>
                  <span className="text-gray-500 whitespace-nowrap">{u.done}/{u.planned} · {u.completion_pct}%</span>
                </div>
                <Bar pct={u.completion_pct} color={u.completion_pct >= 80 ? 'bg-green-500' : u.completion_pct >= 50 ? 'bg-amber-500' : 'bg-red-500'} />
              </div>
            ))}
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Просрочено */}
        <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-5">
          <h2 className="font-semibold mb-4 flex items-center gap-2 text-red-600">
            <AlertTriangle size={18} /> Просроченные уборки ({data.overdue.length})
          </h2>
          {data.overdue.length === 0 ? (
            <p className="text-sm text-gray-400">Нет просроченных уборок 🎉</p>
          ) : (
            <div className="space-y-2 max-h-80 overflow-y-auto">
              {data.overdue.map((o, i) => (
                <div key={i} className="border-l-4 border-red-400 pl-3 py-1">
                  <p className="text-sm font-medium">{o.address}</p>
                  <p className="text-xs text-gray-500">
                    {o.date} · {o.uk} · бригада {o.brigade}
                  </p>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Лента фотоотчётов */}
        <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-5">
          <h2 className="font-semibold mb-4 flex items-center gap-2"><Camera size={18} /> Последние фотоотчёты</h2>
          {recent.length === 0 ? (
            <p className="text-sm text-gray-400">Пока нет фотоотчётов.</p>
          ) : (
            <div className="space-y-2 max-h-80 overflow-y-auto">
              {recent.map((r, i) => (
                <div key={i} className="flex items-center justify-between border-b border-gray-50 pb-2">
                  <div>
                    <p className="text-sm font-medium">{r.address}</p>
                    <p className="text-xs text-gray-500">{r.date} · бригада {r.brigade}</p>
                  </div>
                  <span className="text-xs bg-green-50 text-green-600 px-2 py-1 rounded-full whitespace-nowrap">
                    {r.photo_count} фото
                  </span>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
