import React, { useEffect, useRef, useState } from 'react';

const AIChat = () => {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState('');
  const wsRef = useRef(null);

  // Cleanup WS on unmount
  useEffect(() => {
    return () => {
      try { wsRef.current?.close(); } catch (e) {}
    };
  }, []);

  const sendMessage = () => {
    if (!input.trim()) return;
    setMessages(prev => [...prev, { role: 'user', text: input }]);
    setInput('');
  };

  return (
    <div className="p-8 max-w-4xl mx-auto h-screen flex flex-col">
      <h1 className="text-2xl font-bold mb-4">AI Chat</h1>
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
          onKeyDown={(e) => { if (e.key === 'Enter') sendMessage(); }}
          placeholder="Напишите сообщение..."
          className="flex-1 border rounded-lg px-3 py-2"
        />
        <button onClick={sendMessage} className="px-4 py-2 bg-blue-600 text-white rounded-lg">Отправить</button>
      </div>
    </div>
  );
};

export default AIChat;