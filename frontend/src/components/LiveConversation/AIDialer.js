import React, { useState } from 'react';

const BACKEND_URL = (typeof import.meta !== 'undefined' && import.meta.env && import.meta.env.REACT_APP_BACKEND_URL) || process.env.REACT_APP_BACKEND_URL;

export default function AIDialer() {
  const [phone, setPhone] = useState('');
  const [status, setStatus] = useState('idle');
  const [callId, setCallId] = useState(null);
  const [error, setError] = useState('');

  const startCall = async () => {
    setError(''); setStatus('starting');
    try {
      const res = await fetch(`${BACKEND_URL}/api/voice/call/start`, {
        method: 'POST', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ phone_number: phone })
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data?.detail || 'Не удалось инициировать звонок');
      setCallId(data.call_id); setStatus('ringing');
    } catch (e) {
      setError(e.message || 'Ошибка'); setStatus('idle');
    }
  };

  const checkStatus = async () => {
    if (!callId) return;
    try {
      const res = await fetch(`${BACKEND_URL}/api/voice/call/${callId}/status`);
      const data = await res.json();
      if (res.ok) setStatus(data.status || 'unknown');
    } catch {}
  };

  return (
    <div className="border rounded-lg p-3 space-y-2">
      <div className="text-sm font-semibold">Исходящий звонок ИИ</div>
      <div className="flex gap-2">
        <input value={phone} onChange={e=>setPhone(e.target.value)} placeholder="+7XXXXXXXXXX" className="flex-1 border rounded px-2 py-2" />
        <button onClick={startCall} className="px-3 py-2 rounded bg-green-600 text-white">Позвонить</button>
      </div>
      {callId && (
        <div className="text-xs text-gray-600">Call ID: {callId} · Статус: {status} <button className="underline" onClick={checkStatus}>обновить</button></div>
      )}
      {error && <div className="text-xs text-red-600">{error}</div>}
    </div>
  );
}
