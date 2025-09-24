import React, { useCallback, useEffect, useRef, useState } from 'react';
import AIDialer from './AIDialer';


const BACKEND_URL = (typeof import.meta !== 'undefined' && import.meta.env && import.meta.env.REACT_APP_BACKEND_URL) || process.env.REACT_APP_BACKEND_URL;

const LiveConversation = () => {
  const [isConnecting, setIsConnecting] = useState(false);
  const [isConnected, setIsConnected] = useState(false);
  const [error, setError] = useState('');

  const [voice, setVoice] = useState('marin');
  const [instructions, setInstructions] = useState('Вы — голосовой ассистент VasDom. Отвечайте кратко и по делу.');

  const pcRef = useRef(null);
  const dcRef = useRef(null);
  const localStreamRef = useRef(null);
  const remoteAudioRef = useRef(null);

  const start = useCallback(async () => {
    if (isConnecting || isConnected) return;
    setIsConnecting(true); setError('');
    try {
      const res = await fetch(`${BACKEND_URL}/api/realtime/sessions`, {
        method: 'POST', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ voice, instructions })
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data?.detail || 'Не удалось создать сессию');

      const stream = await navigator.mediaDevices.getUserMedia({ audio: { echoCancellation: true, noiseSuppression: true, autoGainControl: true } });
      localStreamRef.current = stream;

      const pc = new RTCPeerConnection({
        iceServers: [ { urls: 'stun:stun.l.google.com:19302' } ]
      });
      pcRef.current = pc;

      pc.onconnectionstatechange = () => {
        if (pc.connectionState === 'connected') { setIsConnected(true); setIsConnecting(false); }
        if (pc.connectionState === 'failed' || pc.connectionState === 'disconnected' || pc.connectionState === 'closed') {
          setIsConnected(false); setIsConnecting(false);
        }
      };

      pc.ontrack = (event) => {
        if (event.track.kind === 'audio' && remoteAudioRef.current) {
          const ms = remoteAudioRef.current.srcObject || new MediaStream();
          ms.addTrack(event.track);
          remoteAudioRef.current.srcObject = ms;
          remoteAudioRef.current.play().catch(()=>{});
        }
      };

      stream.getTracks().forEach(t => pc.addTrack(t, stream));

      const dc = pc.createDataChannel('oai-events', { ordered: true });
      dcRef.current = dc;
      dc.onopen = () => {
        try {
          dc.send(JSON.stringify({ type: 'session.update', session: { voice, instructions, turn_detection: { type: 'server_vad', threshold: 0.5, prefix_padding_ms: 300, silence_duration_ms: 500, create_response: true } } }));
        } catch {}
      };

      const offer = await pc.createOffer();
      await pc.setLocalDescription(offer);

      const resp = await fetch('https://api.openai.com/v1/realtime?model=gpt-4o-realtime-preview', {
        method: 'POST',
        headers: { 'Authorization': `Bearer ${data.client_secret}`, 'Content-Type': 'application/sdp' },
        body: offer.sdp
      });
      if (!resp.ok) throw new Error(`OpenAI Realtime error: ${resp.status}`);
      const answerSdp = await resp.text();
      await pc.setRemoteDescription({ type: 'answer', sdp: answerSdp });
    } catch (e) {
      setError(e?.message || 'Ошибка запуска разговора');
      cleanup();
    } finally {
      setIsConnecting(false);
    }
  }, [isConnecting, isConnected, voice, instructions]);

  const cleanup = useCallback(() => {
    try { dcRef.current && dcRef.current.close(); } catch {}
    dcRef.current = null;
    try { pcRef.current && pcRef.current.close(); } catch {}
    pcRef.current = null;
    try { localStreamRef.current && localStreamRef.current.getTracks().forEach(t => t.stop()); } catch {}
    localStreamRef.current = null;
    setIsConnected(false);
  }, []);

  const stop = useCallback(() => { cleanup(); }, [cleanup]);

  useEffect(() => () => { cleanup(); }, [cleanup]);

  const voices = ['marin','alloy','shimmer','aria','verse','breeze','coral','cobalt','amber','nova'];

  return (
    <div className="px-3 py-3 max-w-3xl mx-auto">
      <div className="mb-3 flex items-center justify-between">
        <h1 className="text-xl font-bold">Живой разговор</h1>
        <div className="text-xs text-gray-500">WebRTC · Realtime</div>
      </div>

      <div className="bg-white rounded-xl shadow-elegant p-3 space-y-3">
        {/* AI Outbound Call (SIP via LiveKit) */}
        <AIDialer />
        <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
          <div>
            <label className="text-xs text-gray-600">Голос</label>
            <select value={voice} onChange={e=>setVoice(e.target.value)} className="w-full border rounded-lg px-2 py-2">
              {voices.map(v => <option key={v} value={v}>{v}</option>)}
            </select>
          </div>
          <div>
            <label className="text-xs text-gray-600">Инструкции</label>
            <input value={instructions} onChange={e=>setInstructions(e.target.value)} className="w-full border rounded-lg px-2 py-2" placeholder="Системные инструкции" />
          </div>
        </div>

        {error && <div className="text-sm text-red-600">{error}</div>}

        {!isConnected ? (
          <button onClick={start} disabled={isConnecting} className="w-full px-4 py-3 rounded-lg bg-blue-600 text-white disabled:opacity-60">
            {isConnecting ? 'Подключение…' : 'Начать разговор'}
          </button>
        ) : (
          <button onClick={stop} className="w-full px-4 py-3 rounded-lg bg-gray-800 text-white">Завершить разговор</button>
        )}

        <audio ref={remoteAudioRef} autoPlay playsInline />
      </div>
    </div>
  );
};

export default LiveConversation;