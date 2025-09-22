import React, { useEffect, useRef, useState } from 'react';

const BASE_URL = process.env.REACT_APP_BACKEND_URL;

const AIChat = () => {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState('');
  const [usingKB, setUsingKB] = useState(true);
  const [topK, setTopK] = useState(5);
  const [category, setCategory] = useState('');
  const [minScore, setMinScore] = useState(0.12);
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
      if (usingKB) {
        const res = await fetch(`${BASE_URL}/api/ai-knowledge/answer`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ question: q, top_k: Number(topK)||5, category: category||undefined, min_score: Number(minScore)||0.12 })
        });
        const data = await res.json();
        const text = data.answer || '';
        const cites = data.citations || [];
        const citesNote = cites.length ? `\n\nИсточники: ${cites.map(c=>`${c.filename} #${c.chunk_index}`).join('; ')}` : '';
        setMessages(prev => [...prev, { role: 'assistant', text: text + citesNote }]);
      } else {
        // fallback: простой echo (или добавьте свой текущий чат)
        setMessages(prev => [...prev, { role: 'assistant', text: 'KB выключена. Включите переключатель сверху, чтобы опираться на базу знаний.' }]);
      }
    } catch (e) {
      setMessages(prev => [...prev, { role: 'assistant', text: 'Ошибка ответа. Попробуйте ещё раз.' }]);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="p-8 max-w-4xl mx-auto h-screen flex flex-col">
      <h1 className="text-2xl font-bold mb-4">AI Chat</h1>

      <div className="mb-3 flex flex-wrap gap-3 items-center text-sm">
        <label className="inline-flex items-center gap-2">
          <input type="checkbox" checked={usingKB} onChange={(e)=>setUsingKB(e.target.checked)} />
          Использовать базу знаний
        </label>
        <label className="inline-flex items-center gap-2">
          top_k
          <input type="number" className="w-20 border rounded px-2 py-1" value={topK} min={1} max={20} onChange={(e)=>setTopK(e.target.value)} />
        </label>
        <label className="inline-flex items-center gap-2">
          min_score
          <input type="number" className="w-24 border rounded px-2 py-1" step="0.01" value={minScore} onChange={(e)=>setMinScore(e.target.value)} />
        </label>
        <label className="inline-flex items-center gap-2">
          Категория
          <input type="text" className="w-40 border rounded px-2 py-1" value={category} onChange={(e)=>setCategory(e.target.value)} placeholder="например: Маркетинг" />
        </label>
      </div>

      <div className="flex-1 overflow-y-auto bg-white rounded-lg border p-4 space-y-2">
        {messages.length === 0 && (
          <div className="text-gray-500 text-sm">Начните диалог, отправив сообщение ниже.</div>
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