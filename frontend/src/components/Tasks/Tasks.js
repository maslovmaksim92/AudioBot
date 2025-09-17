import React, { useState } from 'react';
import { CalendarClock, Send, Clock } from 'lucide-react';

const Tasks = () => {
  const [text, setText] = useState('Пришли мне отчёт завтра в 12:00 в Telegram');
  const [time, setTime] = useState('');
  const [items, setItems] = useState([]);

  const addTask = async () => {
    if (!text.trim()) return;
    const task = { id: Date.now(), text, time: time || 'завтра 12:00', status: 'запланировано' };
    setItems(prev => [task, ...prev]);
    setText('');
    setTime('');
  };

  return (
    <div className="pt-2 px-4 pb-6 max-w-4xl mx-auto">
      <h1 className="text-2xl font-bold gradient-text mb-4">AI Задачи</h1>

      <div className="bg-white rounded-xl shadow-elegant p-6 mb-6">
        <div className="grid grid-cols-1 md:grid-cols-6 gap-3 items-center">
          <div className="md:col-span-4">
            <input
              value={text}
              onChange={(e) => setText(e.target.value)}
              className="w-full p-3 border rounded-lg"
              placeholder="Опишите задачу для ИИ..."
            />
          </div>
          <div className="md:col-span-2 flex items-center gap-2">
            <CalendarClock className="w-5 h-5 text-blue-600" />
            <input
              type="datetime-local"
              value={time}
              onChange={(e) => setTime(e.target.value)}
              className="w-full p-3 border rounded-lg"
            />
          </div>
        </div>
        <div className="flex items-center gap-2 mt-3">
          <button onClick={addTask} className="px-4 py-2 rounded-lg bg-blue-600 text-white flex items-center gap-2">
            <Send className="w-4 h-4" /> Добавить
          </button>
          <div className="text-xs text-gray-500 flex items-center gap-1">
            <Clock className="w-3 h-3" /> Таймзона: Europe/Moscow
          </div>
        </div>
      </div>

      <div className="space-y-3">
        {items.map(it => (
          <div key={it.id} className="bg-white rounded-xl shadow-elegant p-4 flex items-center justify-between">
            <div>
              <div className="text-sm text-gray-800">{it.text}</div>
              <div className="text-xs text-gray-500">Время: {it.time}</div>
            </div>
            <div className="text-xs font-medium text-blue-600">{it.status}</div>
          </div>
        ))}
        {!items.length && (
          <div className="text-sm text-gray-500">Задач пока нет. Добавьте первую выше.</div>
        )}
      </div>
    </div>
  );
};

export default Tasks;