import React, { useState, useRef } from 'react';
import { Mic, MicOff, Save, Sparkles } from 'lucide-react';
import axios from 'axios';

const Plannerka = () => {
  const [isRecording, setIsRecording] = useState(false);
  const [transcript, setTranscript] = useState('');
  const [title, setTitle] = useState(`Планёрка ${new Date().toLocaleDateString('ru-RU')}`);
  const [summary, setSummary] = useState('');
  const [tasks, setTasks] = useState([]);
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [status, setStatus] = useState('');
  
  const wsRef = useRef(null);
  const audioContextRef = useRef(null);
  const mediaStreamRef = useRef(null);
  const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;

  const startRecording = async () => {
    try {
      setStatus('Подключение...');
      
      // Получаем токен
      const tokenRes = await axios.get(`${BACKEND_URL}/api/openai/realtime-token`);
      const apiKey = tokenRes.data.token;
      
      // Получаем микрофон
      const stream = await navigator.mediaDevices.getUserMedia({ 
        audio: { channelCount: 1, sampleRate: 24000, echoCancellation: true } 
      });
      mediaStreamRef.current = stream;

      // Создаем AudioContext
      audioContextRef.current = new (window.AudioContext || window.webkitAudioContext)({ sampleRate: 24000 });
      const source = audioContextRef.current.createMediaStreamSource(stream);
      const processor = audioContextRef.current.createScriptProcessor(2048, 1, 1);
      
      source.connect(processor);
      processor.connect(audioContextRef.current.destination);

      // Подключаемся к OpenAI Realtime API
      const ws = new WebSocket(`wss://api.openai.com/v1/realtime?model=gpt-4o-realtime-preview-2024-10-01`, [
        'realtime',
        `openai-insecure-api-key.${apiKey}`,
        'openai-beta.realtime-v1'
      ]);
      wsRef.current = ws;

      ws.onopen = () => {
        console.log('✅ Connected to OpenAI Realtime API');
        setStatus('Записываю...');
        setIsRecording(true);

        // Настройка сессии
        ws.send(JSON.stringify({
          type: 'session.update',
          session: {
            modalities: ['text'],
            instructions: 'Ты помощник для транскрибации совещаний на русском языке. Транскрибируй речь точно.',
            input_audio_format: 'pcm16',
            input_audio_transcription: { model: 'whisper-1' },
            turn_detection: { type: 'server_vad', threshold: 0.5, silence_duration_ms: 700 }
          }
        }));
      };

      ws.onmessage = (event) => {
        const data = JSON.parse(event.data);
        
        if (data.type === 'conversation.item.input_audio_transcription.completed') {
          const text = data.transcript;
          setTranscript(prev => prev + text + ' ');
          console.log('✅ Транскрипция:', text);
        }
        
        if (data.type === 'error') {
          console.error('❌ Error:', data.error);
          setStatus('Ошибка: ' + data.error.message);
        }
      };

      ws.onerror = (error) => {
        console.error('❌ WebSocket error:', error);
        setStatus('Ошибка подключения');
      };

      // Отправка аудио
      processor.onaudioprocess = (e) => {
        if (ws.readyState === WebSocket.OPEN) {
          const inputData = e.inputBuffer.getChannelData(0);
          const pcm16 = new Int16Array(inputData.length);
          
          for (let i = 0; i < inputData.length; i++) {
            const s = Math.max(-1, Math.min(1, inputData[i]));
            pcm16[i] = s < 0 ? s * 0x8000 : s * 0x7FFF;
          }
          
          const base64 = btoa(String.fromCharCode(...new Uint8Array(pcm16.buffer)));
          ws.send(JSON.stringify({ type: 'input_audio_buffer.append', audio: base64 }));
        }
      };

    } catch (error) {
      console.error('Error:', error);
      alert('Ошибка: ' + error.message);
      setStatus('');
    }
  };

  const stopRecording = () => {
    if (wsRef.current) wsRef.current.close();
    if (audioContextRef.current) audioContextRef.current.close();
    if (mediaStreamRef.current) mediaStreamRef.current.getTracks().forEach(t => t.stop());
    
    setIsRecording(false);
    setStatus('');
  };

  const handleSave = async () => {
    if (!transcript.trim()) {
      alert('Нет транскрипции для сохранения');
      return;
    }

    try {
      setIsAnalyzing(true);
      
      // Сохраняем планёрку
      const saveRes = await axios.post(`${BACKEND_URL}/api/plannerka/create`, {
        title,
        transcription: transcript,
        participants: 'Участники совещания'
      });
      
      const meetingId = saveRes.data.id;
      
      // Анализируем
      const analyzeRes = await axios.post(`${BACKEND_URL}/api/plannerka/analyze/${meetingId}`);
      
      setSummary(analyzeRes.data.summary);
      setTasks(analyzeRes.data.tasks || []);
      
      alert('✅ Планёрка сохранена!');
      
    } catch (error) {
      console.error('Error:', error);
      alert('Ошибка при сохранении: ' + error.message);
    } finally {
      setIsAnalyzing(false);
    }
  };

  const handleClear = () => {
    if (window.confirm('Очистить всё?')) {
      setTranscript('');
      setSummary('');
      setTasks([]);
    }
  };

  return (
    <div className="p-6 max-w-6xl mx-auto">
      <h1 className="text-3xl font-bold mb-6">Планёрка</h1>
      
      <div className="bg-white rounded-lg shadow p-6 mb-6">
        <input
          type="text"
          value={title}
          onChange={(e) => setTitle(e.target.value)}
          className="w-full text-xl font-semibold mb-4 px-3 py-2 border rounded"
          placeholder="Название планёрки"
        />
        
        <div className="flex gap-4 mb-4">
          <button
            onClick={isRecording ? stopRecording : startRecording}
            className={`flex items-center gap-2 px-6 py-3 rounded-lg font-semibold ${
              isRecording 
                ? 'bg-red-600 hover:bg-red-700 text-white' 
                : 'bg-blue-600 hover:bg-blue-700 text-white'
            }`}
          >
            {isRecording ? <><MicOff className="h-5 w-5" /> Остановить</> : <><Mic className="h-5 w-5" /> Начать запись</>}
          </button>
          
          {transcript && !isRecording && (
            <>
              <button onClick={handleSave} disabled={isAnalyzing} className="flex items-center gap-2 px-6 py-3 bg-green-600 hover:bg-green-700 text-white rounded-lg font-semibold disabled:opacity-50">
                <Save className="h-5 w-5" /> {isAnalyzing ? 'Анализирую...' : 'Сохранить'}
              </button>
              <button onClick={handleClear} className="px-6 py-3 bg-gray-600 hover:bg-gray-700 text-white rounded-lg font-semibold">
                Очистить
              </button>
            </>
          )}
        </div>
        
        {status && <div className="text-sm text-blue-600 mb-4">{status}</div>}
        
        <textarea
          value={transcript}
          onChange={(e) => setTranscript(e.target.value)}
          className="w-full h-64 p-4 border rounded-lg font-mono text-sm"
          placeholder="Транскрипция появится здесь..."
        />
        
        <div className="text-sm text-gray-600 mt-2">
          Символов: {transcript.length}
        </div>
      </div>

      {summary && (
        <div className="bg-white rounded-lg shadow p-6 mb-6">
          <h2 className="text-xl font-bold mb-4 flex items-center gap-2">
            <Sparkles className="h-5 w-5 text-yellow-500" />
            Саммари
          </h2>
          <p className="text-gray-700 whitespace-pre-wrap">{summary}</p>
        </div>
      )}

      {tasks.length > 0 && (
        <div className="bg-white rounded-lg shadow p-6">
          <h2 className="text-xl font-bold mb-4">Задачи ({tasks.length})</h2>
          <div className="space-y-3">
            {tasks.map((task, idx) => (
              <div key={idx} className="border-l-4 border-blue-500 pl-4 py-2">
                <div className="font-semibold">{task.title}</div>
                {task.assignee && <div className="text-sm text-gray-600">Ответственный: {task.assignee}</div>}
                {task.deadline && <div className="text-sm text-gray-600">Срок: {task.deadline}</div>}
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};

export default Plannerka;
