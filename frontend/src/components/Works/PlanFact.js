import React, { useState, useEffect } from 'react';
import { CheckCircle2, AlertCircle, RefreshCw, Users, Calendar } from 'lucide-react';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL || (import.meta?.env?.REACT_APP_BACKEND_URL);

const PlanFact = () => {
  const [date, setDate] = useState(() => new Date().toISOString().split('T')[0]);
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [tab, setTab] = useState('pending'); // pending | done

  useEffect(() => { fetchData(); /* eslint-disable-next-line */ }, [date]);

  const fetchData = async () => {
    setLoading(true);
    try {
      const r = await fetch(`${BACKEND_URL}/api/cleaning/plan-fact?date=${date}`);
      if (!r.ok) throw new Error(`HTTP ${r.status}`);
      setData(await r.json());
    } catch (e) {
      console.error('plan-fact error', e);
      setData(null);
    } finally {
      setLoading(false);
    }
  };

  const pct = data?.completion_pct || 0;
  const pctColor = pct >= 80 ? 'text-green-600' : pct >= 40 ? 'text-amber-600' : 'text-red-500';
  const barColor = pct >= 80 ? 'bg-green-500' : pct >= 40 ? 'bg-amber-500' : 'bg-red-500';

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 to-emerald-50/30 p-6">
      <div className="flex flex-wrap items-center justify-between gap-4 mb-6">
        <div className="flex items-center gap-3">
          <div className="w-11 h-11 rounded-2xl bg-gradient-to-br from-emerald-400 to-teal-500 flex items-center justify-center shadow-lg shadow-emerald-200">
            <CheckCircle2 className="w-6 h-6 text-white" />
          </div>
          <div>
            <h1 className="text-2xl font-bold text-gray-900">Контроль уборок</h1>
            <p className="text-sm text-gray-500">План / факт по дням — кто убрался, кто нет</p>
          </div>
        </div>
        <div className="flex items-center gap-2">
          <input type="date" value={date} onChange={(e) => setDate(e.target.value)}
                 className="px-3 py-2 border border-gray-300 rounded-xl text-sm bg-white shadow-sm" />
          <button onClick={() => setDate(new Date().toISOString().split('T')[0])}
                  className="px-3 py-2 rounded-xl bg-white border border-gray-300 shadow-sm hover:bg-gray-50 text-sm">Сегодня</button>
          <button onClick={fetchData} className="px-4 py-2 rounded-xl bg-white border border-gray-300 shadow-sm hover:bg-gray-50 flex items-center gap-2 text-sm">
            <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} /> Обновить
          </button>
        </div>
      </div>

      {loading && <div className="text-center py-20 text-gray-400">Загрузка…</div>}

      {!loading && data && (
        <>
          {/* Сводка дня */}
          <div className="bg-white rounded-2xl border border-gray-100 p-6 shadow-sm mb-5">
            <div className="flex items-center justify-between mb-4">
              <div className="flex items-center gap-2 text-gray-600">
                <Calendar className="w-5 h-5" />
                <span className="font-medium">{data.weekday}, {date.split('-').reverse().join('.')}</span>
              </div>
              <div className={`text-3xl font-bold ${pctColor}`}>{pct}%</div>
            </div>
            <div className="w-full bg-gray-100 rounded-full h-3 mb-4 overflow-hidden">
              <div className={`h-3 rounded-full transition-all ${barColor}`} style={{ width: `${pct}%` }} />
            </div>
            <div className="grid grid-cols-3 gap-4 text-center">
              <div>
                <div className="text-2xl font-bold text-gray-900">{data.total_planned}</div>
                <div className="text-xs text-gray-500">По плану</div>
              </div>
              <div>
                <div className="text-2xl font-bold text-green-600">{data.total_done}</div>
                <div className="text-xs text-gray-500">Убрано</div>
              </div>
              <div>
                <div className="text-2xl font-bold text-red-500">{data.total_pending}</div>
                <div className="text-xs text-gray-500">Не отчитались</div>
              </div>
            </div>
          </div>

          {data.total_planned === 0 ? (
            <div className="bg-white rounded-2xl border border-gray-100 p-10 shadow-sm text-center text-gray-400">
              На эту дату уборок по графику нет.
            </div>
          ) : (
            <>
              {/* По бригадам */}
              <div className="bg-white rounded-2xl border border-gray-100 p-5 shadow-sm mb-5">
                <h3 className="font-semibold text-gray-800 mb-4 flex items-center gap-2">
                  <Users className="w-5 h-5 text-blue-600" /> По бригадам
                </h3>
                <div className="space-y-3">
                  {data.brigades.map((b) => (
                    <div key={b.brigade} className="flex items-center gap-3">
                      <div className="w-24 text-sm font-medium text-gray-700 flex-shrink-0">
                        {b.brigade === '—' ? 'Без бригады' : `Бригада ${b.brigade}`}
                      </div>
                      <div className="flex-1 bg-gray-100 rounded-full h-6 overflow-hidden relative">
                        <div className={`h-6 rounded-full flex items-center justify-end pr-2 text-xs text-white font-medium ${b.completion_pct >= 80 ? 'bg-green-500' : b.completion_pct >= 40 ? 'bg-amber-500' : 'bg-red-400'}`}
                             style={{ width: `${Math.max(b.completion_pct, 8)}%` }}>
                          {b.completion_pct}%
                        </div>
                      </div>
                      <div className="w-28 text-sm text-gray-600 flex-shrink-0 text-right">
                        {b.done}/{b.planned} <span className="text-gray-400">сделано</span>
                      </div>
                    </div>
                  ))}
                </div>
              </div>

              {/* Списки: не отчитались / убрано */}
              <div className="bg-white rounded-2xl border border-gray-100 shadow-sm overflow-hidden">
                <div className="flex border-b border-gray-100">
                  <button onClick={() => setTab('pending')}
                          className={`flex-1 px-4 py-3 text-sm font-medium flex items-center justify-center gap-2 ${tab === 'pending' ? 'text-red-600 border-b-2 border-red-500 bg-red-50/30' : 'text-gray-500'}`}>
                    <AlertCircle className="w-4 h-4" /> Не отчитались ({data.total_pending})
                  </button>
                  <button onClick={() => setTab('done')}
                          className={`flex-1 px-4 py-3 text-sm font-medium flex items-center justify-center gap-2 ${tab === 'done' ? 'text-green-600 border-b-2 border-green-500 bg-green-50/30' : 'text-gray-500'}`}>
                    <CheckCircle2 className="w-4 h-4" /> Убрано ({data.total_done})
                  </button>
                </div>
                <div className="divide-y divide-gray-50 max-h-[500px] overflow-y-auto">
                  {(tab === 'pending' ? data.pending : data.done).map((h, i) => (
                    <div key={h.id} className="px-5 py-3 flex items-center justify-between hover:bg-gray-50">
                      <div className="flex items-center gap-3">
                        {tab === 'pending'
                          ? <AlertCircle className="w-4 h-4 text-red-400 flex-shrink-0" />
                          : <CheckCircle2 className="w-4 h-4 text-green-500 flex-shrink-0" />}
                        <span className="text-sm text-gray-800">{h.address}</span>
                      </div>
                      <span className="text-xs text-gray-400 flex-shrink-0 ml-2">
                        {h.brigade ? `бр. ${h.brigade}` : 'без бригады'}
                      </span>
                    </div>
                  ))}
                  {(tab === 'pending' ? data.pending : data.done).length === 0 && (
                    <div className="px-5 py-10 text-center text-gray-400 text-sm">
                      {tab === 'pending' ? 'Все отчитались! 🎉' : 'Пока никто не отчитался'}
                    </div>
                  )}
                </div>
              </div>
            </>
          )}
        </>
      )}

      {!loading && !data && (
        <div className="text-center py-20 text-gray-400">Не удалось загрузить данные.</div>
      )}
    </div>
  );
};

export default PlanFact;
