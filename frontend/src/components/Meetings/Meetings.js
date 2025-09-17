import React, { useEffect, useRef, useState } from 'react';
import { Mic, Square, FileText, Sparkles } from 'lucide-react';

const Meetings = () => {
  const [isLive, setIsLive] = useState(false);
  const [transcript, setTranscript] = useState([]);
  const [summary, setSummary] = useState('');
  const [exporting, setExporting] = useState(false);
  const [interim, setInterim] = useState('');
  const liveRef = useRef(null);

  useEffect(() => {
    let recognition;
    if (isLive) {
      const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
      if (SpeechRecognition) {
        recognition = new SpeechRecognition();
        recognition.lang = 'ru-RU';
        recognition.continuous = true;
        recognition.interimResults = true;
        recognition.onresult = (event) => {
          let finalText = '';
          let interimText = '';
          for (let i = event.resultIndex; i < event.results.length; ++i) {
            const res = event.results[i];
            if (res.isFinal) finalText += res[0].transcript.trim() + '.';
            else interimText += res[0].transcript;
          }
          if (interimText) setInterim(interimText.trim()); else setInterim('');
          if (finalText) setTranscript(prev => [...prev, finalText]);
        };
        recognition.onerror = () => {};
        recognition.start();
      } else {
        // Фоллбэк: имитация если Web Speech недоступен
        liveRef.current = setInterval(() => {
          setTranscript(prev => [...prev, `Фрагмент речи ${prev.length + 1}...`]);
        }, 1200);
      }
    } else {
      if (recognition) recognition.stop();
      if (liveRef.current) {
        clearInterval(liveRef.current);
        liveRef.current = null;
      }
    }
    return () => {
      if (recognition) recognition.stop();
      if (liveRef.current) clearInterval(liveRef.current);
    };
  }, [isLive]);

  const handleStart = () => setIsLive(true);
  const handleStop = () => setIsLive(false);

  const makeSummary = async () => {
    try {
      setSummary('Краткое резюме встречи: обсудили графики уборок, распределили задачи между бригадами, согласовали проблемные адреса.');
    } catch (e) {
      setSummary('Не удалось сгенерировать саммари. Попробуйте позже.');
    }
  };

  const exportTxt = () => {
    try {
      setExporting(true);
      const blob = new Blob([transcript.join('\n') + '\n\n' + summary], { type: 'text/plain;charset=utf-8' });
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = 'meeting-notes.txt';
      a.click();
      URL.revokeObjectURL(url);
    } finally {
      setExporting(false);
    }
  };

  return (
    <div className="pt-0 px-3 pb-4 max-w-6xl mx-auto">
      <div className="mb-4 flex items-center justify-between">
        <h1 className="text-2xl font-bold gradient-text">Планёрка (онлайн транскрипция)</h1>
        <div className="flex items-center gap-2">
          {!isLive ? (
            <button onClick={handleStart} className="px-4 py-2 rounded-lg bg-red-500 text-white flex items-center gap-2">
              <Mic className="w-4 h-4" /> Старт
            </button>
          ) : (
            <button onClick={handleStop} className="px-4 py-2 rounded-lg bg-gray-800 text-white flex items-center gap-2">
              <Square className="w-4 h-4" /> Стоп
            </button>
          )}
          <button onClick={makeSummary} className="px-4 py-2 rounded-lg bg-purple-600 text-white flex items-center gap-2">
            <Sparkles className="w-4 h-4" /> Сделать саммари
          </button>
          <button onClick={exportTxt} disabled={exporting} className="px-4 py-2 rounded-lg bg-white border flex items-center gap-2 disabled:opacity-50">
            <FileText className="w-4 h-4" /> Экспорт .txt
          </button>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div className="bg-white rounded-xl shadow-elegant p-4">
          <h2 className="text-lg font-semibold mb-2">Онлайн транскрипция</h2>
          <div className="h-96 overflow-y-auto space-y-2">
            {transcript.map((line, idx) => (
              <div key={idx} className="text-sm text-gray-800 bg-gray-50 rounded-lg p-2">{line}</div>
            ))}
            {!transcript.length && (
              <div className="text-sm text-gray-500">Нажмите Старт, чтобы включить онлайн расшифровку речи.</div>
            )}
          </div>
        </div>
        <div className="bg-white rounded-xl shadow-elegant p-4">
          <h2 className="text-lg font-semibold mb-2">Саммари</h2>
          <div className="min-h-[10rem] text-sm text-gray-800 bg-gray-50 rounded-lg p-3">
            {summary || 'Здесь появится краткое саммари встречи.'}
          </div>
        </div>
      </div>
    </div>
  );
};

export default Meetings;