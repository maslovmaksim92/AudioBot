import React, { useState } from 'react';
import { MapPin, Route, Shuffle, Loader2 } from 'lucide-react';
import MapView from './MapView';

const Logistics = () => {
  const [points, setPoints] = useState([{ address: '' }, { address: '' }]);
  const [optimize, setOptimize] = useState(true);
  const [route, setRoute] = useState(null);
  const [loading, setLoading] = useState(false);
  const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;

  const updatePoint = (idx, field, value) => {
    const next = [...points];
    next[idx][field] = value;
    setPoints(next);
  };

  const addPoint = () => setPoints([...points, { address: '' }]);
  const removePoint = (idx) => setPoints(points.filter((_, i) => i !== idx));

  const buildRoute = async () => {
    setLoading(true);
    setRoute(null);
    try {
      const payload = {
        points: points.map(p => ({ address: p.address, lon: p.lon, lat: p.lat })),
        optimize,
        profile: 'driving-car',
        language: 'ru'
      };
      const res = await fetch(`${BACKEND_URL}/api/logistics/route`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || 'Ошибка построения маршрута');
      setRoute(data);
    } catch (e) {
      alert(e.message);
    } finally {
      setLoading(false);
    }
  };

  const formatDuration = (sec) => {
    const h = Math.floor(sec / 3600);
    const m = Math.round((sec % 3600) / 60);
    return `${h ? h + ' ч ' : ''}${m} мин`;
  };

  const formatDistance = (m) => (m >= 1000 ? (m / 1000).toFixed(1) + ' км' : m + ' м');

  return (
    <div className="p-6 max-w-4xl mx-auto">
      <h1 className="text-2xl font-bold mb-4 flex items-center gap-2"><Route className="w-6 h-6"/> Логистика</h1>

      <div className="bg-white rounded-xl border p-4 space-y-3">
        {points.map((p, idx) => (
          <div key={idx} className="flex gap-2 items-center">
            <MapPin className="w-4 h-4 text-gray-500"/>
            <input
              value={p.address || ''}
              onChange={(e) => updatePoint(idx, 'address', e.target.value)}
              placeholder={`Адрес точки ${idx + 1}`}
              className="flex-1 border rounded-lg px-3 py-2"
            />
            {points.length > 2 && (
              <button onClick={() => removePoint(idx)} className="px-3 py-2 border rounded-lg">Удалить</button>
            )}
          </div>
        ))}
        <div className="flex gap-2">
          <button onClick={addPoint} className="px-4 py-2 bg-gray-100 rounded-lg">+ Добавить точку</button>
          <label className="flex items-center gap-2 px-3 py-2 border rounded-lg">
            <input type="checkbox" checked={optimize} onChange={(e) => setOptimize(e.target.checked)}/>
            <Shuffle className="w-4 h-4"/> Оптимизировать порядок
          </label>
          <button onClick={buildRoute} disabled={loading} className="ml-auto px-4 py-2 bg-blue-600 text-white rounded-lg flex items-center gap-2">
            {loading ? <Loader2 className="w-4 h-4 animate-spin"/> : <Route className="w-4 h-4"/>}
            Построить маршрут
          </button>
        </div>
      </div>

      {route && (
        <div className="mt-4 bg-green-50 border border-green-200 rounded-xl p-4">
          <div className="font-semibold text-green-800 mb-2">Итоги</div>
          <div className="text-sm text-green-900">Дистанция: {formatDistance(route.distance)} · Время: {formatDuration(route.duration)}</div>
          {route.order && (
            <div className="mt-2 text-xs text-green-800">Порядок точек: {route.order.map((i) => i + 1).join(' → ')}</div>
          )}
          <div className="mt-3 bg-white p-3 rounded-lg border">
            <div className="font-medium mb-2">Шаги:</div>
            <ol className="list-decimal pl-5 space-y-1 text-sm">
              {(route.steps || []).slice(0, 20).map((s, i) => (
                <li key={i}>{s.instruction} · {formatDistance(s.distance)} · {formatDuration(s.duration)}</li>
              ))}
            </ol>
            {(route.steps || []).length > 20 && (
              <div className="text-xs text-gray-500 mt-1">Показаны первые 20 шагов</div>
            )}
          </div>
        </div>
      )}
    </div>
  );
};

export default Logistics;
