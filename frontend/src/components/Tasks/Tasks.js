import React, { useState } from 'react';
import TasksList from './TasksList';
import AITaskGenerator from './AITaskGenerator';

const Tasks = () => {
  const [activeTab, setActiveTab] = useState('list');

  return (
    <div>
      {/* Табы */}
      <div className="bg-white border-b px-6">
        <div className="flex gap-4">
          <button
            onClick={() => setActiveTab('list')}
            className={`px-4 py-3 font-medium border-b-2 transition-colors ${
              activeTab === 'list'
                ? 'border-blue-600 text-blue-600'
                : 'border-transparent text-gray-600 hover:text-gray-900'
            }`}
          >
            📋 Список задач
          </button>
          <button
            onClick={() => setActiveTab('ai')}
            className={`px-4 py-3 font-medium border-b-2 transition-colors ${
              activeTab === 'ai'
                ? 'border-blue-600 text-blue-600'
                : 'border-transparent text-gray-600 hover:text-gray-900'
            }`}
          >
            🤖 AI Генератор
          </button>
        </div>
      </div>

      {/* Контент */}
      {activeTab === 'list' && <TasksList />}
      {activeTab === 'ai' && <AITaskGenerator />}
    </div>
  );
};

const Tasks_Old = () => {
  const [date, setDate] = useState(() => new Date().toISOString().slice(0,10));
  const [employees, setEmployees] = useState([]);
  const [selected, setSelected] = useState(null);
  const [loading, setLoading] = useState(false);
  const [tasks, setTasks] = useState([]);
  const [callMap, setCallMap] = useState({}); // taskId -> {callId, status}
  const pollersRef = useRef({});

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

  const startPollingStatus = (taskId, callId) => {
    if (pollersRef.current[taskId]) clearInterval(pollersRef.current[taskId]);
    pollersRef.current[taskId] = setInterval(async () => {
      try {
        const res = await fetch(`${BACKEND_URL}/api/voice/call/${callId}/status`);
        const data = await res.json();
        setCallMap(prev => ({ ...prev, [taskId]: { callId, status: data.status } }));
        if (!data || data.status === 'ended' || data.status === 'unknown') {
          clearInterval(pollersRef.current[taskId]);
          delete pollersRef.current[taskId];
        }
      } catch (e) {
        // stop polling on error
        clearInterval(pollersRef.current[taskId]);
        delete pollersRef.current[taskId];
      }
    }, 1500);
  };

  const handleCallAI = async (t) => {
    try {
      const override = window.prompt('Номер телефона сотрудника (можно оставить пустым — возьмём из Bitrix):', '');
      const body = {
        task_id: Number(t.ID),
        title: t.TITLE,
        description: t.DESCRIPTION,
        responsible_id: Number(t.RESPONSIBLE_ID || 0) || null,
      };
      if (override && override.trim()) body.phone_number = override.trim();

      const res = await fetch(`${BACKEND_URL}/api/tasks/call-ai`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(body)
      });
      const data = await res.json();
      if (!res.ok) {
        alert(`Ошибка звонка: ${data?.detail || res.status}`);
        return;
      }
      setCallMap(prev => ({ ...prev, [t.ID]: { callId: data.call_id, status: data.status } }));
      startPollingStatus(t.ID, data.call_id);
    } catch (e) {
      alert('Не удалось инициировать звонок ИИ');
    }
  };

  useEffect(() => {
    return () => {
      Object.values(pollersRef.current).forEach(id => clearInterval(id));
      pollersRef.current = {};
    };
  }, []);

  return (
    <div className="pt-2 px-3 pb-6 max-w-6xl mx-auto">
      <div className="mb-3 flex items-center justify-between">
        <h1 className="text-xl font-bold">Задачи</h1>
        <button onClick={loadTasks} className="px-3 py-2 rounded-lg bg-white border flex items-center gap-2 text-sm">
          <RefreshCw className="w-4 h-4" /> Обновить
        </button>
      </div>

      {/* Mind Map section */}
      <div className="bg-white rounded-xl shadow-elegant p-3 mb-4">
        <div className="text-sm font-medium mb-2">Майндмеппинг (структуры/схемы)</div>
        <div className="h-[520px]">
          <React.Suspense fallback={<div className="text-sm text-gray-500 p-2">Загрузка редактора…</div>}>
            <MindMapLazy />
          </React.Suspense>
        </div>
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
              <div className="flex-1">
                <div className="text-sm font-medium text-gray-900">{t.TITLE}</div>
                <div className="text-xs text-gray-500">До: {t.DEADLINE || '—'} · Ответственный: {t.RESPONSIBLE_ID}</div>
                {callMap[t.ID] && (
                  <div className="mt-1 text-xs text-blue-600">Статус звонка ИИ: {callMap[t.ID].status} (call: {callMap[t.ID].callId})</div>
                )}
              </div>
              <div className="flex items-center gap-3 text-xs">
                {String(t.STATUS) === '5' ? (
                  <span className="text-green-600 flex items-center gap-1"><CheckCircle className="w-4 h-4" /> Готово</span>
                ) : (
                  <span className="text-amber-600 flex items-center gap-1"><AlertCircle className="w-4 h-4" /> В работе / Ожидает</span>
                )}
                <button onClick={() => handleCallAI(t)} className="inline-flex items-center gap-2 px-3 py-2 rounded-lg bg-blue-50 border text-blue-700 hover:bg-blue-100">
                  <Phone className="w-4 h-4" /> Позвонить ИИ
                </button>
              </div>
            </div>
          ))}
          {!(grouped.all||[]).length && (
            <div className="text-sm text-gray-500">Нет задач на выбранную дату.</div>
          )}
        </div>
      )}
    </div>
  );
};

export default Tasks;