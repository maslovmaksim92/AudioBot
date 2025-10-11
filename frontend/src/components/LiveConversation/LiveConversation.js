import React, { useEffect, useMemo, useRef, useState } from 'react';
import './LiveConversation.css';
import AIDialer from './AIDialer';

const BACKEND_URL = (typeof import.meta !== 'undefined' && import.meta.env && import.meta.env.REACT_APP_BACKEND_URL) || process.env.REACT_APP_BACKEND_URL;

function useQuery() {
  const [q, setQ] = useState({});
  useEffect(() => {
    const usp = new URLSearchParams(window.location.hash.split('?')[1] || window.location.search);
    const obj = {};
    usp.forEach((v,k)=>{ obj[k]=v; });
    setQ(obj);
  }, [window.location.hash, window.location.search]);
  return q;
}

export default function LiveConversation() {
  const q = useQuery();
  const [invite, setInvite] = useState(null);
  const [status, setStatus] = useState(null);
  const [connecting, setConnecting] = useState(false);
  const [error, setError] = useState('');
  const [session, setSession] = useState(null);
  const [context, setContext] = useState('Напоминание по задачам');
  const [dt, setDt] = useState(()=>{
    const d = new Date(); d.setMinutes(d.getMinutes()+1); d.setSeconds(0); d.setMilliseconds(0); return d.toISOString().slice(0,16);
  });
  const [created, setCreated] = useState(null);

  // If opened with invite token in URL, resolve it and start session
  useEffect(() => {
    const token = q.invite || q.token;
    if (!token) return;
    setInvite(token);
    setError(''); setSession(null); setStatus(null);
    (async () => {
      try {
        const st = await fetch(`${BACKEND_URL}/api/ai-invite/${token}/status`).then(r=>r.json());
        setStatus(st);
        if (st.status === 'not_started') return; // show countdown
        setConnecting(true);
        const res = await fetch(`${BACKEND_URL}/api/ai-invite/${token}/resolve`,{ method:'POST' });
        const data = await res.json();
        if (!res.ok) throw new Error(data?.detail || 'Resolve failed');
        setSession(data);
      } catch(e) { setError(String(e.message||e)); }
      finally { setConnecting(false); }
    })();
  }, [q.invite, q.token]);

  // Poll countdown if not started
  useEffect(() => {
    if (!invite || !status || status.status !== 'not_started') return;
    const id = setInterval(async () => {
      const st = await fetch(`${BACKEND_URL}/api/ai-invite/${invite}/status`).then(r=>r.json());
      setStatus(st);
    }, 5000);
    return () => clearInterval(id);
  }, [invite, status]);

  const createInvite = async () => {
    try {
      const body = { start_at: new Date(dt).toISOString(), context };
      const res = await fetch(`${BACKEND_URL}/api/ai-invite/create`, { method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify(body)});
      const data = await res.json();
      if (!res.ok) throw new Error(data?.detail || 'Create failed');
      const url = `${window.location.origin}${window.location.pathname}#${window.location.hash.split('#')[1]?.split('?')[0]||'/live'}?invite=${data.token}`;
      setCreated({ ...data, url });
    } catch(e) { setError(String(e.message||e)); }
  };

  return (
    <div className="p-4 max-w-3xl mx-auto">
      <h1 className="text-xl font-bold mb-3">Живой разговор</h1>

      {/* AI Outbound Dialer */}
      <div className="bg-white rounded-xl shadow p-3 mb-4">
        <div className="text-sm font-medium mb-2">Исходящий звонок ИИ</div>
        <AIDialer />
      </div>

      {/* Invite creation */}
      <div className="bg-white rounded-xl shadow p-3 mb-4">
        <div className="text-sm font-medium mb-2">Создать ссылку на разговор с ИИ</div>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-2 items-center">
          <input type="datetime-local" value={dt} onChange={e=>setDt(e.target.value)} className="border rounded px-2 py-1" />
          <input type="text" value={context} onChange={e=>setContext(e.target.value)} placeholder="Контекст разговора" className="border rounded px-2 py-1" />
          <button onClick={createInvite} className="px-3 py-2 rounded bg-blue-600 text-white text-sm">Создать ссылку</button>
        </div>
        {created && (
          <div className="mt-2 text-sm">
            Ссылка: <a href={created.url} className="text-blue-700" target="_blank" rel="noreferrer">{created.url}</a>
            <div className="text-gray-500">Действительна до: {created.expires_at}</div>
          </div>
        )}
      </div>

      {/* Invite open state */}
      {invite && (
        <div className="bg-white rounded-xl shadow p-3 mb-4">
          <div className="text-sm">Приглашение: {invite}</div>
          {status?.status === 'not_started' && (
            <div className="text-amber-700 text-sm">Разговор ещё не начался. Осталось ~ {status.starts_in_sec} сек. Окно обновится автоматически.</div>
          )}
          {error && <div className="text-red-600 text-sm">{error}</div>}
        </div>
      )}

      {/* Session info (client_secret) */}
      {session && (
        <div className="bg-white rounded-xl shadow p-3">
          <div className="text-sm text-green-700 mb-2">Сессия готова. Подключаю аудио…</div>
          {/* Здесь ваш существующий компонент подключения WebRTC к OpenAI Realtime. 
              Если у вас есть отдельный компонент — его можно переиспользовать, 
              передав model/voice/instructions и client_secret из session.
              Для MVP можно оставить этот блок как индикатор, если уже есть автоподключение в другом месте. */}
          <pre className="text-xs bg-gray-50 p-2 rounded overflow-auto">{JSON.stringify(session, null, 2)}</pre>
        </div>
      )}
    </div>
  );
}