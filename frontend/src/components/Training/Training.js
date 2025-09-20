import React, { useEffect, useMemo, useRef, useState } from 'react';

const BASE_URL = process.env.REACT_APP_BACKEND_URL;

const fmtBytes = (bytes = 0) => {
  if (!bytes) return '0 B';
  const k = 1024;
  const sizes = ['B', 'KB', 'MB', 'GB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return `${(bytes / Math.pow(k, i)).toFixed(2)} ${sizes[i]}`;
};

const categories = ['Маркетинг','Бухгалтерия','HR','Офис','Клининг','Строительство'];

const parseCategoryFromMime = (mime = '') => {
  // mime like: "text/plain; category=Маркетинг"
  try {
    const parts = String(mime || '').split(';').map(s => s.trim());
    const kv = parts.find(p => p.startsWith('category='));
    if (!kv) return '';
    return decodeURIComponent(kv.split('=')[1] || '').trim();
  } catch (_) { return ''; }
};

const SectionTitle = ({ children }) => (
  <h2 className="text-lg font-semibold mb-3 text-gray-900">{children}</h2>
);

const QueueItem = ({ item, onCategory, onStudy, onRemove, onTogglePreview }) => {
  const previewText = String(item.preview || '');
  const showFull = !!item.expanded;
  const shown = showFull ? previewText : previewText.slice(0, 400);
  const canStudy = !!item.uploadId && !!item.category && item.status !== 'изучено' && !item.processing;
  return (
    <div className="border rounded-lg p-3 bg-gray-50">
      <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-2">
        <div className="text-sm text-gray-900 font-medium">{item.file?.name}</div>
        <div className="text-xs text-gray-600">{fmtBytes(item.file?.size || 0)}</div>
      </div>
      <div className="mt-2 text-xs text-gray-600">Статус: {item.status}</div>
      {previewText && (
        <div className="mt-2 text-sm text-gray-800 whitespace-pre-wrap bg-white p-2 rounded border">
          {shown}{previewText.length > 400 && !showFull ? '…' : ''}
          {previewText.length > 400 && (
            <button className="ml-2 text-indigo-600 hover:underline text-xs" onClick={() => onTogglePreview(item.id)}>
              {showFull ? 'Скрыть' : 'Показать больше'}
            </button>
          )}
        </div>
      )}
      <div className="mt-2 flex flex-col md:flex-row gap-2 md:items-center">
        <select
          value={item.category || ''}
          onChange={(e)=>onCategory(item.id, e.target.value)}
          className="px-2 py-1 border rounded text-sm"
        >
          <option value="">Выберите категорию…</option>
          {categories.map(c => <option key={c} value={c}>{c}</option>)}
        </select>
        <button
          onClick={() => onStudy(item.id)}
          disabled={!canStudy}
          className="px-3 py-1.5 rounded bg-green-600 text-white disabled:opacity-50"
        >
          {item.processing ? 'Обучение…' : 'Обучить'}
        </button>
        <button onClick={() => onRemove(item.id)} className="px-3 py-1.5 rounded bg-gray-300 text-gray-800">Убрать</button>
      </div>
    </div>
  );
};

function Training() {
  const [files, setFiles] = useState([]);
  const [queue, setQueue] = useState([]); // {id,file,preview,uploadId,category,status,processing,expanded}
  const [status, setStatus] = useState('');
  const [chunkTokens, setChunkTokens] = useState(1200);
  const [overlap, setOverlap] = useState(200);
  const [messages, setMessages] = useState([]); // mini-chat

  const [documents, setDocuments] = useState([]);
  const [loadingDocs, setLoadingDocs] = useState(false);

  const [docCategoryFilter, setDocCategoryFilter] = useState('');
  const [docSort, setDocSort] = useState('date_desc'); // date_desc | date_asc | name

  const [query, setQuery] = useState('');
  const [topK, setTopK] = useState(10);
  const [results, setResults] = useState([]);
  const [searching, setSearching] = useState(false);

  const uploadPreviewXHR = useRef(null);

  const canProcess = useMemo(() => queue.some(it => !!it.uploadId && !!it.category && it.status !== 'изучено' && !it.processing), [queue]);

  const handleFileChange = (e) => {
    const list = Array.from(e.target.files || []);
    if (!list.length) return;
    // Проверка лимитов: 50МБ/файл, 200МБ суммарно
    const tooBig = list.find(f => (f.size||0) > 50*1024*1024);
    const total = list.reduce((a,f)=>a+(f.size||0), 0);
    if (tooBig) { setStatus('Один из файлов превышает 50 МБ'); return; }
    if (total > 200*1024*1024) { setStatus('Суммарный размер превышает 200 МБ'); return; }
    setFiles(list);
    const q = list.map(f => ({ id: crypto.randomUUID(), file: f, preview: '', uploadId: '', category: '', status: 'ожидает', processing: false, expanded: false }));
    setQueue(q);
    setMessages([]);
    setStatus('Файлы добавлены в очередь. Запускаю предпросмотр…');
    // Запускаем последовательный предпросмотр
    sequentialPreview(q);
  };

  const sequentialPreview = async (items) => {
    for (const it of items) {
      // eslint-disable-next-line no-await-in-loop
      await doPreview(it.id, it.file);
    }
    setStatus('Предпросмотр завершён. Выберите категории и запустите обучение.');
  };

  const doPreview = async (id, file) => {
    if (!BASE_URL) { setStatus('REACT_APP_BACKEND_URL не задан.'); return; }
    const form = new FormData();
    form.append('file', file);
    form.append('chunk_tokens', String(chunkTokens));
    form.append('overlap', String(overlap));
    try {
      const data = await new Promise((resolve, reject) => {
        const xhr = new XMLHttpRequest();
        uploadPreviewXHR.current = xhr;
        xhr.open('POST', `${BASE_URL}/api/ai-knowledge/preview`, true);
        xhr.onreadystatechange = () => {
          if (xhr.readyState === 4) {
            if (xhr.status >= 200 && xhr.status < 300) {
              try { resolve(JSON.parse(xhr.responseText||'{}')); } catch (e) { reject(e); }
            } else {
              try { const err = JSON.parse(xhr.responseText||'{}'); reject(new Error(err.detail||`Ошибка ${xhr.status}`)); } catch(_) { reject(new Error(`Ошибка ${xhr.status}`)); }
            }
          }
        };
        xhr.onerror = () => reject(new Error('Ошибка сети'));
        xhr.send(form);
      });
      setQueue(prev => prev.map(x => x.id===id ? { ...x, preview: data.preview||'', uploadId: data.upload_id||'', status: 'готов' } : x));
      setMessages(prev => [...prev, {type:'info', text:`AI‑превью готово: ${file.name} (чанков: ${data.chunks||0})`}]);
    } catch (e) {
      setQueue(prev => prev.map(x => x.id===id ? { ...x, status: 'ошибка предпросмотра' } : x));
      setMessages(prev => [...prev, {type:'error', text:`Ошибка предпросмотра ${file.name}: ${e.message||e}`}]);
    }
  };

  const onCategory = (id, cat) => setQueue(prev => prev.map(x => x.id===id ? { ...x, category: cat } : x));
  const onTogglePreview = (id) => setQueue(prev => prev.map(x => x.id===id ? { ...x, expanded: !x.expanded } : x));

  const onStudy = async (id) => {
    const it = queue.find(q => q.id===id);
    if (!it || !it.uploadId || !it.category) return;
    if (!BASE_URL) return;
    setQueue(prev => prev.map(x => x.id===id ? { ...x, processing: true } : x));
    try {
      const form = new FormData();
      form.append('upload_id', it.uploadId);
      form.append('filename', it.file?.name || 'document.txt');
      form.append('category', it.category);
      const res = await fetch(`${BASE_URL}/api/ai-knowledge/study`, { method: 'POST', body: form });
      if (!res.ok) {
        const err = await res.json().catch(()=>({}));
        throw new Error(err.detail || `Ошибка ${res.status}`);
      }
      const data = await res.json();
      setQueue(prev => prev.map(x => x.id===id ? { ...x, processing: false, status: 'изучено' } : x));
      setMessages(prev => [...prev, {type:'success', text:`Изучено: ${it.file?.name} • Чанков: ${data.chunks} • Документ: ${data.document_id}`}]);
      await fetchDocs();
    } catch (e) {
      setQueue(prev => prev.map(x => x.id===id ? { ...x, processing: false, status: 'ошибка обучения' } : x));
      setMessages(prev => [...prev, {type:'error', text:`Ошибка обучения ${it.file?.name}: ${e.message||e}`}]);
    }
  };

  const studyAll = async () => {
    for (const it of queue) {
      if (!it.uploadId || !it.category || it.status === 'изучено') continue;
      // eslint-disable-next-line no-await-in-loop
      await onStudy(it.id);
    }
  };

  const fetchDocs = async () => {
    if (!BASE_URL) return;
    setLoadingDocs(true);
    try {
      const res = await fetch(`${BASE_URL}/api/ai-knowledge/documents`);
      const data = await res.json();
      const docs = (data.documents || []).map(d => ({...d, category: d.category || parseCategoryFromMime(d.mime)}));
      setDocuments(docs);
    } catch (e) {
      // ignore
    } finally {
      setLoadingDocs(false);
    }
  };

  const displayedDocuments = useMemo(() => {
    let rows = [...documents];
    if (docCategoryFilter) rows = rows.filter(d => (d.category||'') === docCategoryFilter);
    if (docSort === 'date_desc') rows.sort((a,b) => new Date(b.created_at||0) - new Date(a.created_at||0));
    if (docSort === 'date_asc') rows.sort((a,b) => new Date(a.created_at||0) - new Date(b.created_at||0));
    if (docSort === 'name') rows.sort((a,b) => String(a.filename||'').localeCompare(String(b.filename||''), 'ru'));
    return rows;
  }, [documents, docCategoryFilter, docSort]);

  const removeDoc = async (id) => {
    if (!BASE_URL) return;
    if (!window.confirm('Удалить документ?')) return;
    try {
      const res = await fetch(`${BASE_URL}/api/ai-knowledge/document/${id}`, { method: 'DELETE' });
      if (!res.ok) throw new Error('Ошибка удаления');
      await fetchDocs();
    } catch (e) {
      setStatus(String(e.message || e));
    }
  };

  const doSearch = async () => {
    if (!query.trim()) return;
    if (!BASE_URL) return;
    setSearching(true);
    setResults([]);
    try {
      const res = await fetch(`${BASE_URL}/api/ai-knowledge/search`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ query, top_k: Number(topK) || 10 })
      });
      if (!res.ok) {
        const err = await res.json().catch(()=>({}));
        throw new Error(err.detail || `Ошибка ${res.status}`);
      }
      const data = await res.json();
      setResults(data.results || []);
    } catch (e) {
      setStatus(String(e.message || e));
    } finally {
      setSearching(false);
    }
  };

  useEffect(() => { fetchDocs(); return () => { try { uploadPreviewXHR.current?.abort(); } catch(_) {} } }, []);

  return (
    <div className="pt-2 px-4 pb-6 max-w-6xl mx-auto">
      <h1 className="text-2xl font-bold gradient-text mb-4">Обучение AI</h1>

      <div className="bg-white rounded-xl shadow-elegant p-6 mb-6">
        <SectionTitle>Очередь файлов</SectionTitle>
        <div className="flex flex-col md:flex-row md:items-center gap-3">
          <input type="file" multiple accept=".pdf,.docx,.txt,.xlsx,.zip" onChange={handleFileChange} className="block text-sm" />
          <div className="flex gap-2 items-center">
            <label className="text-xs text-gray-600">Chunk tokens</label>
            <input type="number" className="w-24 px-2 py-1 rounded border border-gray-300" value={chunkTokens} min={300} max={3000} onChange={(e)=>setChunkTokens(Number(e.target.value)||1200)} />
            <label className="text-xs text-gray-600">Overlap</label>
            <input type="number" className="w-20 px-2 py-1 rounded border border-gray-300" value={overlap} min={0} max={500} onChange={(e)=>setOverlap(Number(e.target.value)||200)} />
          </div>
          <button onClick={studyAll} disabled={!canProcess} className="px-4 py-2 rounded-lg bg-indigo-600 text-white disabled:opacity-50">Обучить все</button>
          {!!status && <div className="text-sm text-gray-700">{status}</div>}
        </div>
        <div className="mt-2 text-xs text-gray-600">
          Поддерживаемые форматы: PDF, DOCX, TXT, XLSX, ZIP • Ограничения: до 50 МБ на файл и 200 МБ за раз
        </div>
        <div className="mt-4 grid gap-3">
          {queue.length === 0 && <div className="text-sm text-gray-500">Файлы не выбраны</div>}
          {queue.map(item => (
            <QueueItem
              key={item.id}
              item={item}
              onCategory={(id, c)=>onCategory(id, c)}
              onStudy={(id)=>onStudy(id)}
              onRemove={(id)=>setQueue(prev=>prev.filter(x=>x.id!==id))}
              onTogglePreview={onTogglePreview}
            />
          ))}
        </div>
        {/* mini chat */}
        {messages.length > 0 && (
          <div className="mt-4 bg-gray-50 rounded-lg p-3">
            <div className="text-sm font-medium text-gray-900 mb-2">Подтверждения</div>
            <div className="space-y-1 text-sm">
              {messages.map((m,i)=> (
                <div key={i} className={m.type==='error' ? 'text-red-700' : m.type==='success' ? 'text-green-700' : 'text-gray-800'}>• {m.text}</div>
              ))}
            </div>
          </div>
        )}
      </div>

      {/* Documents */}
      <div className="bg-white rounded-xl shadow-elegant p-6 mb-6">
        <SectionTitle>Сохранённые документы</SectionTitle>
        <div className="flex flex-col md:flex-row md:items-center gap-3 mb-3">
          <select value={docCategoryFilter} onChange={(e)=>setDocCategoryFilter(e.target.value)} className="px-2 py-1 border rounded text-sm w-full md:w-auto">
            <option value="">Все категории</option>
            {categories.map(c => <option key={c} value={c}>{c}</option>)}
          </select>
          <select value={docSort} onChange={(e)=>setDocSort(e.target.value)} className="px-2 py-1 border rounded text-sm w-full md:w-auto">
            <option value="date_desc">Сначала новые</option>
            <option value="date_asc">Сначала старые</option>
            <option value="name">По имени</option>
          </select>
        </div>
        {loadingDocs ? (
          <div className="text-sm text-gray-600">Загрузка...</div>
        ) : (
          <div className="overflow-x-auto">
            <table className="min-w-full text-sm">
              <thead>
                <tr className="text-left text-gray-600 border-b">
                  <th className="py-2 pr-4">Имя</th>
                  <th className="py-2 pr-4">Категория</th>
                  <th className="py-2 pr-4">Размер</th>
                  <th className="py-2 pr-4">Дата</th>
                  <th className="py-2 pr-4">Чанков</th>
                  <th className="py-2 pr-4">Действия</th>
                </tr>
              </thead>
              <tbody>
                {displayedDocuments.length === 0 && (
                  <tr><td className="py-3 text-gray-500" colSpan={6}>Документов пока нет</td></tr>
                )}
                {displayedDocuments.map((d) => (
                  <tr key={d.id} className="border-b last:border-b-0">
                    <td className="py-2 pr-4 text-gray-900">{d.filename || 'document'}</td>
                    <td className="py-2 pr-4">
                      {d.category ? (
                        <span className="inline-flex items-center px-2 py-0.5 rounded-full text-xs bg-indigo-50 text-indigo-700 border border-indigo-200">{d.category}</span>
                      ) : '—'}
                    </td>
                    <td className="py-2 pr-4 text-gray-700">{d.size_bytes ? fmtBytes(d.size_bytes) : '—'}</td>
                    <td className="py-2 pr-4 text-gray-700">{d.created_at ? new Date(d.created_at).toLocaleString() : '—'}</td>
                    <td className="py-2 pr-4 text-gray-700">{d.chunks_count ?? '—'}</td>
                    <td className="py-2 pr-4">
                      <button onClick={() => removeDoc(d.id)} className="text-red-600 hover:underline">Удалить</button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Search */}
      <div className="bg-white rounded-xl shadow-elegant p-6">
        <SectionTitle>Семантический поиск</SectionTitle>
        <div className="flex flex-col md:flex-row gap-3 md:items-center">
          <input value={query} onChange={(e)=>setQuery(e.target.value)} placeholder="Введите запрос..." className="flex-1 px-3 py-2 rounded border border-gray-300" />
          <input type="number" min={1} max={50} value={topK} onChange={(e)=>setTopK(e.target.value)} className="w-24 px-3 py-2 rounded border border-gray-300" />
          <button onClick={doSearch} disabled={searching || !query.trim()} className="px-4 py-2 rounded bg-indigo-600 text-white disabled:opacity-50">{searching ? 'Поиск...' : 'Искать'}</button>
        </div>
        {query.trim() && !searching && results.length === 0 && (
          <div className="mt-3 text-sm text-gray-600">Ничего не найдено. Попробуйте более общий запрос.</div>
        )}
        {results.length > 0 && (
          <div className="mt-4">
            <div className="text-sm text-gray-700 mb-2">Найдено фрагментов: {results.length}</div>
            <div className="space-y-3">
              {results.map((r,idx)=> (
                <div key={idx} className="bg-gray-50 rounded p-3">
                  <div className="text-xs text-gray-600 mb-1">Документ: {r.filename} • Чанк #{r.chunk_index} • Релевантность: {(Number(r.score||0)*100).toFixed(1)}%</div>
                  <div className="text-sm text-gray-900 whitespace-pre-wrap">{r.content}</div>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

export default Training;