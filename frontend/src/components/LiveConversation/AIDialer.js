import React, { useState } from 'react';

const BACKEND_URL = (typeof import.meta !== 'undefined' && import.meta.env && import.meta.env.REACT_APP_BACKEND_URL) || process.env.REACT_APP_BACKEND_URL;

export default function AIDialer() {
  const [phone, setPhone] = useState('');
  const [status, setStatus] = useState('idle');
  const [callId, setCallId] = useState(null);
  const [roomName, setRoomName] = useState('');
  const [error, setError] = useState('');
  const [aiStatus, setAiStatus] = useState('');

  const startAICall = async () => {
    setError(''); 
    setStatus('starting');
    setAiStatus('');
    
    try {
      const res = await fetch(`${BACKEND_URL}/api/voice/ai-call`, {
        method: 'POST', 
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ 
          phone_number: phone,
          voice: 'marin',
          greeting: 'Здравствуйте! Это VasDom AudioBot.'
        })
      });
      
      const data = await res.json();
      
      if (!res.ok) {
        throw new Error(data?.detail || 'Не удалось инициировать AI звонок');
      }
      
      setCallId(data.call_id);
      setRoomName(data.room_name);
      setStatus(data.status || 'ringing');
      setAiStatus('starting');
      
      // Poll status to track AI agent
      setTimeout(() => checkStatus(), 2000);
      
    } catch (e) {
      setError(e.message || 'Ошибка'); 
      setStatus('idle');
    }
  };

  const checkStatus = async () => {
    if (!callId) return;
    
    try {
      const res = await fetch(`${BACKEND_URL}/api/voice/call/${callId}/status`);
      const data = await res.json();
      
      if (res.ok) {
        setStatus(data.status || 'unknown');
        
        if (data.details && data.details.ai_agent_status) {
          setAiStatus(data.details.ai_agent_status);
        }
        
        if (data.details && data.details.ai_agent_error) {
          setError(`AI: ${data.details.ai_agent_error}`);
        }
      }
    } catch (e) {
      console.error('Status check error:', e);
    }
  };

  return (
    <div className="border rounded-lg p-3 space-y-2 bg-gradient-to-r from-purple-50 to-blue-50">
      <div className="text-sm font-semibold text-purple-900">🤖 AI-звонок с промптом</div>
      
      <div className="flex gap-2">
        <input 
          value={phone} 
          onChange={e => setPhone(e.target.value)} 
          placeholder="+7XXXXXXXXXX" 
          className="flex-1 border rounded px-2 py-2"
          disabled={status !== 'idle'}
        />
        <button 
          onClick={startAICall} 
          disabled={status !== 'idle' || !phone}
          className="px-3 py-2 rounded bg-purple-600 hover:bg-purple-700 text-white disabled:bg-gray-400 disabled:cursor-not-allowed"
        >
          {status === 'starting' ? 'Запуск...' : 'AI Звонок'}
        </button>
      </div>
      
      {callId && (
        <div className="text-xs space-y-1">
          <div className="text-gray-700">
            <span className="font-semibold">Call ID:</span> {callId}
          </div>
          <div className="text-gray-700">
            <span className="font-semibold">Статус:</span> {status}
            {aiStatus && <span className="ml-2 text-purple-600">| AI: {aiStatus}</span>}
            <button className="ml-2 underline text-blue-600" onClick={checkStatus}>обновить</button>
          </div>
          {roomName && (
            <div className="text-gray-600">
              <span className="font-semibold">Room:</span> {roomName}
            </div>
          )}
        </div>
      )}
      
      {error && (
        <div className="text-xs text-red-600 bg-red-50 p-2 rounded">
          {error}
        </div>
      )}
      
      <div className="text-xs text-gray-500 mt-2 pt-2 border-t">
        💡 AI агент использует OpenAI Realtime API с вашим промптом
      </div>
    </div>
  );
}
