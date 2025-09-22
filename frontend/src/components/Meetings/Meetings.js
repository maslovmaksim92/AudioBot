import React, { useEffect, useRef, useState } from 'react';
import { Mic, Square, FileText, Sparkles, Send, Save, ClipboardList } from 'lucide-react';

const BACKEND_URL = (typeof import.meta !== 'undefined' && import.meta.env && import.meta.env.REACT_APP_BACKEND_URL) || process.env.REACT_APP_BACKEND_URL;

const Meetings = () => {
  const [isLive, setIsLive] = useState(false);
  const [transcript, setTranscript] = useState([]);
  const [summary, setSummary] = useState('');
  const [exporting, setExporting] = useState(false);
  const [interim, setInterim] = useState('');
  const [protocolId, setProtocolId] = useState(null);
  const [recent, setRecent] = useState([]);
  const [showRecent, setShowRecent] = useState(false);
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
      const res = await fetch(`${BACKEND_URL}/api/meetings/summarize`, {
        method: 'POST', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ transcript })
      });
      const data = await res.json();
      setSummary(data.summary || '');
    } catch (e) {
      setSummary('Не удалось сгенерировать саммари. Попробуйте позже.');
    }
  };

  const saveToKB = async () => {
    const text = (summary || transcript.join('\n')).trim();
    if (!text) return;
    try {
      const res = await fetch(`${process.env.REACT_APP_BACKEND_URL}/api/meetings/save-to-kb`, {
        method: 'POST', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ protocol_text: text, filename: 'meeting-protocol.txt' })
      });
      const data = await res.json();
      if (!res.ok || !data.ok) throw new Error('Сохранение не удалось');
      setProtocolId(data.document_id || null);
      alert('Протокол сохранён в Базу знаний');
      await loadRecent();
    } catch (e) {
      alert('Не удалось сохранить протокол');
    }
  };

  const loadRecent = async () => {
    try {
      const res = await fetch(`${process.env.REACT_APP_BACKEND_URL}/api/meetings/protocols/recent?limit=20`);
      const data = await res.json();
      setRecent(data.protocols || []);
    } catch (e) {}
  };

  useEffect(() => { loadRecent(); }, []);

  const sendTelegram = async () => {
    const text = (summary || transcript.join('\n')).trim();
    if (!text) return;
    try {
      const res = await fetch(`${process.env.REACT_APP_BACKEND_URL}/api/meetings/send`, {
        method: 'POST', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ text, doc_id: protocolId || undefined, with_feedback: !!protocolId })
      });
      const data = await res.json();
      if (!res.ok || !data.ok) throw new Error('Ошибка отправки');
      alert('Отправлено в Telegram');
    } catch (e) {
      alert('Не удалось отправить в Telegram');
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

  const [form, setForm] = useState({
    title: '', datetime: '', participants: '', goal: '', agenda: [''], decisions: '', tasks: [{ title: '', owner: '', due: '', status: '' }], risks: '', next_steps: '', bitrix_link: ''
  });

  const updateForm = (field, value) => setForm(prev => ({ ...prev, [field]: value }));
  const updateAgenda = (idx, value) => setForm(prev => ({ ...prev, agenda: prev.agenda.map((a,i)=> i===idx? value: a) }));
  const addAgenda = () => setForm(prev => ({ ...prev, agenda: [...prev.agenda, ''] }));
  const updateTask = (idx, field, value) => setForm(prev => ({ ...prev, tasks: prev.tasks.map((t,i)=> i===idx? { ...t, [field]: value }: t) }));
  const addTask = () => setForm(prev => ({ ...prev, tasks: [...prev.tasks, { title: '', owner: '', due: '', status: '' }] }));

  useEffect(() => {
    if (summary && !form.decisions) {
      setForm(prev => ({ ...prev, decisions: summary }));
    }
  }, [summary]);

  const saveFormToKB = async () => {
    try {
      const res = await fetch(`${process.env.REACT_APP_BACKEND_URL}/api/meetings/save-to-kb`, {
        method: 'POST', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ form, filename: (form.title ? `${form.title}.txt` : 'meeting-protocol.txt') })
      });
      const data = await res.json();
      if (!res.ok || !data.ok) throw new Error('Сохранение не удалось');
      setProtocolId(data.document_id || null);
      alert('Протокол (форма) сохранён в Базу знаний');
      await loadRecent();
    } catch (e) {
      alert('Не удалось сохранить протокол (форма)');
    }
  };

  const [tab, setTab] = useState('transcribe'); // 'transcribe' | 'protocol' | 'history'

  return (
    <div className="px-3 pb-20 max-w-3xl mx-auto">
      <div className="sticky top-0 z-10 bg-white/90 backdrop-blur border-b">
        <div className="py-3 flex items-center justify-between gap-2">
          <h1 className="text-xl font-bold">Планёрка</h1>
          <div className="flex items-center gap-2">
            {!isLive ? (
              <button onClick={handleStart} className="px-3 py-2 rounded-lg bg-red-500 text-white flex items-center gap-2">
                <Mic className="w-4 h-4" /> Старт
              </button>
            ) : (
              <button onClick={handleStop} className="px-3 py-2 rounded-lg bg-gray-800 text-white flex items-center gap-2">
                <Square className="w-4 h-4" /> Стоп
              </button>
            )}
          </div>
        </div>
        <div className="flex gap-1 pb-2">
          <button onClick={()=>setTab('transcribe')} className={`flex-1 px-3 py-2 rounded-lg text-sm ${tab==='transcribe'?'bg-blue-600 text-white':'bg-gray-100 text-gray-800'}`}>Транскрипция</button>
          <button onClick={()=>setTab('protocol')} className={`flex-1 px-3 py-2 rounded-lg text-sm ${tab==='protocol'?'bg-blue-600 text-white':'bg-gray-100 text-gray-800'}`}>Протокол</button>
          <button onClick={()=>setTab('history')} className={`flex-1 px-3 py-2 rounded-lg text-sm ${tab==='history'?'bg-blue-600 text-white':'bg-gray-100 text-gray-800'}`}>История</button>
        </div>
      </div>

      {tab==='transcribe' && (
        <div className="mt-3">
          <div className="bg-white rounded-xl shadow-elegant p-3">
            <div className="flex items-center justify-between mb-2">
              <h2 className="text-base font-semibold">Онлайн транскрипция</h2>
              <span className={`text-xs ${isLive? 'text-green-600':'text-gray-500'}`}>{isLive? 'Запись идёт':'Ожидание'}</span>
            </div>
            <div className="h-[60vh] md:h-96 overflow-y-auto space-y-2">
              {transcript.map((line, idx) => (
                <div key={idx} className="text-sm text-gray-800 bg-gray-50 rounded-lg p-2">{line}</div>
              ))}
              {!!interim && (
                <div className="text-sm text-gray-500 italic bg-gray-50 rounded-lg p-2">{interim}</div>
              )}
              {!transcript.length && !interim && (
                <div className="text-sm text-gray-500">Нажмите Старт, чтобы включить онлайн расшифровку речи.</div>
              )}
            </div>
          </div>
          <div className="mt-3 flex gap-2">
            <button onClick={makeSummary} className="flex-1 px-4 py-3 rounded-lg bg-purple-600 text-white flex items-center justify-center gap-2">
              <Sparkles className="w-4 h-4" /> Сделать саммари
            </button>
            <button onClick={exportTxt} disabled={exporting} className="px-4 py-3 rounded-lg bg-white border flex items-center gap-2 disabled:opacity-50">
              <FileText className="w-4 h-4" /> Экспорт
            </button>
          </div>
        </div>
      )}

      {tab==='protocol' && (
        <div className="mt-3 space-y-3">
          <div className="bg-white rounded-xl shadow-elegant p-3">
            <h2 className="text-base font-semibold mb-2">Краткое саммари</h2>
            <div className="min-h-[8rem] text-sm text-gray-800 bg-gray-50 rounded-lg p-3">
              {summary || 'Здесь появится краткое саммари после генерации.'}
            </div>
          </div>

          <div className="bg-white rounded-xl shadow-elegant p-3">
            <div className="flex items-center justify-between mb-1">
              <h2 className="text-base font-semibold">Единая форма протокола</h2>
              <button onClick={saveFormToKB} className="px-3 py-2 text-xs rounded-lg bg-green-600 text-white flex items-center gap-2">
                <Save className="w-4 h-4" /> Сохранить форму в БЗ
              </button>
            </div>
            <div className="space-y-3 text-sm">
              <div>
                <label className="text-gray-600 text-xs">Заголовок</label>
                <input value={form.title} onChange={e=>updateForm('title', e.target.value)} className="w-full border rounded-lg px-2 py-2" placeholder="Например: Планёрка по объектам" />
              </div>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                <div>
                  <label className="text-gray-600 text-xs">Дата и время</label>
                  <input value={form.datetime} onChange={e=>updateForm('datetime', e.target.value)} className="w-full border rounded-lg px-2 py-2" placeholder="2025-09-20 10:00" />
                </div>
                <div>
                  <label className="text-gray-600 text-xs">Участники</label>
                  <input value={form.participants} onChange={e=>updateForm('participants', e.target.value)} className="w-full border rounded-lg px-2 py-2" placeholder="Имена через запятую" />
                </div>
              </div>

              <details className="border rounded-lg p-2">
                <summary className="cursor-pointer text-gray-700">Повестка</summary>
                <div className="mt-2 space-y-1">
                  {(form.agenda || []).map((a, idx) => (
                    <input key={idx} value={a} onChange={e=>updateAgenda(idx, e.target.value)} className="w-full border rounded-lg px-2 py-2" placeholder={`Пункт ${idx+1}`} />
                  ))}
                  <button onClick={addAgenda} className="mt-1 text-xs text-blue-600">+ добавить пункт</button>
                </div>
              </details>

              <details className="border rounded-lg p-2">
                <summary className="cursor-pointer text-gray-700">Принятые решения</summary>
                <textarea value={form.decisions} onChange={e=>updateForm('decisions', e.target.value)} className="w-full border rounded-lg px-2 py-2 min-h-[80px]" />
              </details>

              <details className="border rounded-lg p-2">
                <summary className="cursor-pointer text-gray-700">Поручения</summary>
                <div className="space-y-2 mt-2">
                  {(form.tasks || []).map((t, idx) => (
                    <div key={idx} className="grid grid-cols-2 md:grid-cols-4 gap-2">
                      <input value={t.title} onChange={e=>updateTask(idx, 'title', e.target.value)} className="border rounded-lg px-2 py-2" placeholder="Задача" />
                      <input value={t.owner} onChange={e=>updateTask(idx, 'owner', e.target.value)} className="border rounded-lg px-2 py-2" placeholder="Ответственный" />
                      <input value={t.due} onChange={e=>updateTask(idx, 'due', e.target.value)} className="border rounded-lg px-2 py-2" placeholder="Срок" />
                      <input value={t.status} onChange={e=>updateTask(idx, 'status', e.target.value)} className="border rounded-lg px-2 py-2" placeholder="Статус" />
                    </div>
                  ))}
                  <button onClick={addTask} className="text-xs text-blue-600">+ добавить задачу</button>
                </div>
              </details>

              <details className="border rounded-lg p-2">
                <summary className="cursor-pointer text-gray-700">Риски/блокеры</summary>
                <textarea value={form.risks} onChange={e=>updateForm('risks', e.target.value)} className="w-full border rounded-lg px-2 py-2 min-h-[60px]" />
              </details>

              <details className="border rounded-lg p-2">
                <summary className="cursor-pointer text-gray-700">Следующие шаги</summary>
                <textarea value={form.next_steps} onChange={e=>updateForm('next_steps', e.target.value)} className="w-full border rounded-lg px-2 py-2 min-h-[60px]" />
              </details>

              <div>
                <label className="text-gray-600 text-xs">Ссылка на сделку/объект Bitrix</label>
                <input value={form.bitrix_link} onChange={e=>updateForm('bitrix_link', e.target.value)} className="w-full border rounded-lg px-2 py-2" placeholder="https://vas-dom.bitrix24.ru/crm/deal/details/.../" />
              </div>
            </div>
          </div>

          <div className="h-4"></div>
        </div>
      )}

      {tab==='history' && (
        <div className="mt-3">
          <div className="bg-white rounded-xl shadow-elegant p-3">
            <div className="flex items-center justify-between mb-2">
              <h2 className="text-base font-semibold">Недавние протоколы</h2>
              <button onClick={loadRecent} className="text-xs text-blue-600">Обновить</button>
            </div>
            <div className="divide-y">
              {(recent || []).map((p) => (
                <div key={p.id} className="py-2 text-sm">
                  <div className="flex items-center justify-between">
                    <div className="min-w-0">
                      <div className="font-semibold truncate">{p.filename || p.id}</div>
                      <div className="text-gray-500 text-xs">{p.created_at?.replace('T',' ').replace('Z','')}</div>
                    </div>
                    <div className="text-xs text-gray-600 shrink-0 pl-2">👍 {p.likes} · 👎 {p.dislikes}</div>
                  </div>
                  {p.summary && (
                    <div className="text-gray-700 text-xs mt-1 line-clamp-3">{p.summary}</div>
                  )}
                </div>
              ))}
              {!recent.length && (
                <div className="text-xs text-gray-500 py-6 text-center">Нет сохранённых протоколов</div>
              )}
            </div>
          </div>
        </div>
      )}

      {/* Sticky action bar for protocol actions */}
      {tab==='protocol' && (
        <div className="fixed bottom-0 left-0 right-0 bg-white/95 border-t p-2 flex items-center gap-2 justify-center">
          <button onClick={saveToKB} className="flex-1 max-w-xs px-4 py-3 rounded-lg bg-green-600 text-white flex items-center justify-center gap-2">
            <Save className="w-4 h-4" /> Запомнить протокол
          </button>
          <button onClick={sendTelegram} className="flex-1 max-w-xs px-4 py-3 rounded-lg bg-sky-600 text-white flex items-center justify-center gap-2">
            <Send className="w-4 h-4" /> В Telegram
          </button>
        </div>
      )}
    </div>
  );
};

export default Meetings;