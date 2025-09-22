import React, { useEffect, useMemo, useState } from 'react';
import { Calendar, RefreshCw, User, CheckCircle, AlertCircle, Plus } from 'lucide-react';

const BACKEND_URL = (typeof import.meta !== 'undefined' && import.meta.env && import.meta.env.REACT_APP_BACKEND_URL) || process.env.REACT_APP_BACKEND_URL;

const Tasks = () => {
  const [date, setDate] = useState(() => new Date().toISOString().slice(0,10));
  const [employees, setEmployees] = useState([]);
  const [selected, setSelected] = useState(null);
  const [loading, setLoading] = useState(false);
  const [tasks, setTasks] = useState([]);

  const loadEmployees = async () => {
    try {
      const res = await fetch(`${BACKEND_URL}/api/employees/office`);
      const data = await res.json();
      setEmployees(data.employees || []);
      if (!selected && (data.employees||[])[0]) setSelected(data.employees[0].id);
    } catch {}
  };

  const loadTasks = async () => {
    if (!date) return;
    setLoading(true);
    try {
      const url = new URL(`${BACKEND_URL}/api/tasks/bitrix/list`);
      url.searchParams.set('date', date);
      if (selected) url.searchParams.set('responsible_id', selected);
      const res = await fetch(url.toString());
      const data = await res.json();
      setTasks(data.tasks || []);
    } catch { setTasks([]); }
    finally { setLoading(false); }
  };

  useEffect(() => { loadEmployees(); }, []);
  useEffect(() => { loadTasks(); }, [date, selected]);

  const grouped = useMemo(() => {
    if (!selected) return { all: tasks };
    return { all: tasks };
  }, [tasks, selected]);

  return (
    <div className="pt-2 px-3 pb-6 max-w-6xl mx-auto">
      <div className="mb-3 flex items-center justify-between">
        <h1 className="text-xl font-bold">Задачи</h1>
        <button onClick={loadTasks} className="px-3 py-2 rounded-lg bg-white border flex items-center gap-2 text-sm">
          <RefreshCw className="w-4 h-4" /> Обновить
        </button>
      </div>

      <div className="bg-white rounded-xl shadow-elegant p-3 mb-3">
        <div className="grid grid-cols-1 md:grid-cols-4 gap-2 items-center">
          <div className="flex items-center gap-2">
            <Calendar className="w-4 h-4 text-blue-600" />
            <input type="date" value={date} onChange={e=>setDate(e.target.value)} className="border rounded px-2 py-1 text-sm" />
          </div>
          <div className="md:col-span-2 flex items-center gap-2">
            <User className="w-4 h-4 text-purple-600" />
            <select value={selected || ''} onChange={e=>setSelected(e.target.value? Number(e.target.value): null)} className="border rounded px-2 py-1 text-sm w-full">
              {(employees||[]).map(e => <option key={e.id} value={e.id}>{e.name}</option>)}
            </select>
          </div>
          <div className="text-right">
            <a href="#/meetings" className="inline-flex items-center gap-2 text-sm text-blue-600"><Plus className="w-4 h-4" /> Создать задачи из планёрки</a>
          </div>
        </div>
      </div>

      {loading ? (
        <div className="p-6 text-sm text-gray-600">Загрузка задач…</div>
      ) : (
        <div className="space-y-2">
          {(grouped.all||[]).map(t => (
            <div key={t.ID} className="bg-white rounded-xl shadow-elegant p-3 flex items-center justify-between">
              <div>
                <div className="text-sm font-medium text-gray-900">{t.TITLE}</div>
                <div className="text-xs text-gray-500">До: {t.DEADLINE || '—'} · Ответственный: {t.RESPONSIBLE_ID}</div>
              </div>
              <div className="text-xs">
                {String(t.STATUS) === '5' ? (
                  <span className="text-green-600 flex items-center gap-1"><CheckCircle className="w-4 h-4" /> Готово</span>
                ) : (
                  <span className="text-amber-600 flex items-center gap-1"><AlertCircle className="w-4 h-4" /> В работе / Ожидает</span>
                )}
              </div>
            </div>
          ))}
          {!grouped.all?.length && (
            <div className="text-sm text-gray-500">Нет задач на выбранную дату.</div>
          )}
        </div>
      )}
    </div>
  );
};

export default Tasks;