import React, { useEffect, useRef, useState } from 'react';

const BACKEND_URL = (typeof import.meta !== 'undefined' && import.meta.env && import.meta.env.REACT_APP_BACKEND_URL) || process.env.REACT_APP_BACKEND_URL;

if (!process.env.REACT_APP_BACKEND_URL && !(typeof import.meta !== 'undefined' && import.meta.env && import.meta.env.REACT_APP_BACKEND_URL)) {
  console.warn('REACT_APP_BACKEND_URL is not defined. AI Chat may not work.');
}


const AIChat = () => {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const wsRef = useRef(null);

  useEffect(() => () => { try { wsRef.current?.close(); } catch (e) {} }, []);

  const send = async () => {
    const q = input.trim();
    if (!q) return;
    setMessages(prev => [...prev, { role: 'user', text: q }]);
    setInput('');
    setLoading(true);
    try {
      // Всегда опираемся на базу знаний
      const res = await fetch(`${BACKEND_URL}/api/ai-knowledge/answer`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ question: q })
      });
      const data = await res.json();
      const text = data.answer || 'Нет ответа.';
      setMessages(prev => [...prev, { role: 'assistant', text }]);
    } catch (e) {
      setMessages(prev => [...prev, { role: 'assistant', text: 'Ошибка ответа. Попробуйте ещё раз.' }]);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="p-8 max-w-4xl mx-auto h-screen flex flex-col">
      <h1 className="text-2xl font-bold mb-4">AI Chat</h1>

      <div className="flex-1 overflow-y-auto bg-white rounded-lg border p-4 space-y-2">
        {messages.length === 0 && (
          <div className="text-gray-500 text-sm">Задайте вопрос — ассистент ответит, опираясь на изучённые документы.</div>
        )}
        {messages.map((m, i) => (
          <div key={i} className={m.role === 'user' ? 'text-right' : ''}>
            <span className={`inline-block px-3 py-2 rounded-lg text-sm ${m.role === 'user' ? 'bg-blue-600 text-white' : 'bg-gray-100 text-gray-800'}`}>
              {m.text}
            </span>
          </div>
        ))}
      </div>
      <div className="mt-3 flex gap-2">
        <input
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={(e) => { if (e.key === 'Enter') send(); }}
          placeholder="Напишите сообщение..."
          className="flex-1 border rounded-lg px-3 py-2"
        />
        <button onClick={send} disabled={loading} className="px-4 py-2 bg-blue-600 text-white rounded-lg disabled:opacity-50">{loading ? 'Загрузка…' : 'Отправить'}</button>
      </div>
    </div>
  );
};

export default AIChat;