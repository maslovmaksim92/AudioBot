import React, { useEffect, useMemo, useRef, useState } from 'react';

const BASE_URL = process.env.REACT_APP_BACKEND_URL;

const fmtBytes = (bytes = 0) => {
  if (!bytes) return '0 B';
  const k = 1024;
  const sizes = ['B', 'KB', 'MB', 'GB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return `${(bytes / Math.pow(k, i)).toFixed(2)} ${sizes[i]}`;
};

const SectionTitle = ({ children }) => (
  <h2 className="text-lg font-semibold mb-3 text-gray-900">{children}</h2>
);

const Training = () => {
  const [files, setFiles] = useState([]);
  const [uploading, setUploading] = useState(false);
  const [progress, setProgress] = useState(0);
  const [status, setStatus] = useState('');

  const [preview, setPreview] = useState('');
  const [uploadId, setUploadId] = useState('');
  const [chunksCount, setChunksCount] = useState(0);

  const [saving, setSaving] = useState(false);

  const [documents, setDocuments] = useState([]);
  const [loadingDocs, setLoadingDocs] = useState(false);

  const [query, setQuery] = useState('');
  const [topK, setTopK] = useState(10);
  const [searching, setSearching] = useState(false);
  const [results, setResults] = useState([]);

  const xhrRef = useRef(null);

  const canUpload = useMemo(() => files && files.length > 0 && !uploading, [files, uploading]);

  const handleFileChange = (e) => {
    const list = Array.from(e.target.files || []);
    setFiles(list);
    setPreview('');
    setUploadId('');
    setChunksCount(0);
    setStatus('Файлы выбраны. Нажмите \'Анализировать\' для извлечения и превью.');
  };

  const handleUpload = async () => {
    if (!BASE_URL) {
      alert('REACT_APP_BACKEND_URL не задан. Невозможно выполнить запрос.');
      return;
    }
    if (!files.length) return;
    setUploading(true);
    setProgress(0);
    setStatus('Загрузка и анализ...');

    const form = new FormData();
    files.forEach((f) => form.append('files', f));
    // advanced controls
    form.append('chunk_tokens', String(topK > 0 ? 1200 : 1200));
    form.append('overlap', '200');

    try {
      await new Promise((resolve, reject) => {
        const xhr = new XMLHttpRequest();
        xhrRef.current = xhr;
        xhr.open('POST', `${BASE_URL}/api/ai-knowledge/upload`, true);
        xhr.upload.onprogress = (ev) => {
          if (ev.lengthComputable) {
            const p = Math.round((ev.loaded / ev.total) * 100);
            setProgress(p);
          }
        };
        xhr.onreadystatechange = () => {
          if (xhr.readyState === 4) {
            if (xhr.status >= 200 && xhr.status < 300) {
              try {
                const data = JSON.parse(xhr.responseText || '{}');
                setPreview(data.preview || '');
                setUploadId(data.upload_id || '');
                setChunksCount(data.chunks || 0);
                setStatus('Анализ завершён. Проверьте превью и сохраните.');
              } catch (e) {
                reject(e);
              }
              resolve();
            } else {
              try {
                const err = JSON.parse(xhr.responseText || '{}');
                reject(new Error(err.detail || `Ошибка ${xhr.status}`));
              } catch (e) {
                reject(new Error(`Ошибка ${xhr.status}`));
              }
            }
          }
        };
        xhr.onerror = () => reject(new Error('Ошибка сети при загрузке'));
        xhr.send(form);
      });
    } catch (err) {
      setStatus(String(err.message || err));
    } finally {
      setUploading(false);
    }
  };

  const handleSave = async () => {
    if (!uploadId) return;
    if (!BASE_URL) {
      alert('REACT_APP_BACKEND_URL не задан.');
      return;
    }
    setSaving(true);
    setStatus('Сохранение в базу знаний...');
    try {
      const form = new FormData();
      form.append('upload_id', uploadId);
      form.append('filename', files?.[0]?.name || 'document.txt');
      const res = await fetch(`${BASE_URL}/api/ai-knowledge/save`, {
        method: 'POST',
        body: form,
      });
      if (!res.ok) {
        const err = await res.json().catch(() => ({}));
        throw new Error(err.detail || `Ошибка ${res.status}`);
      }
      const data = await res.json();
      setStatus(`Сохранено. document_id=${data.document_id}`);
      setUploadId('');
      setPreview('');
      setChunksCount(0);
      setFiles([]);
      await fetchDocs();
    } catch (e) {
      setStatus(String(e.message || e));
    } finally {
      setSaving(false);
    }
  };

  const fetchDocs = async () => {
    if (!BASE_URL) return;
    setLoadingDocs(true);
    try {
      const res = await fetch(`${BASE_URL}/api/ai-knowledge/documents`);
      const data = await res.json();
      setDocuments(data.documents || []);
    } catch (e) {
      // no-op
    } finally {
      setLoadingDocs(false);
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
        body: JSON.stringify({ query, top_k: Number(topK) || 10 }),
      });
      if (!res.ok) {
        const err = await res.json().catch(() => ({}));
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

  useEffect(() => {
    fetchDocs();
    return () => {
      if (xhrRef.current) try { xhrRef.current.abort(); } catch {}
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  return (
    <div className="pt-2 px-4 pb-6 max-w-6xl mx-auto">
      <h1 className="text-2xl font-bold gradient-text mb-4">Обучение AI</h1>

      {/* Upload & preview */}
      <div className="bg-white rounded-xl shadow-elegant p-6 mb-6">
        <SectionTitle>Загрузка файлов</SectionTitle>
        <div className="flex flex-col gap-3 md:flex-row md:items-center md:gap-4">
          <input
            type="file"
            multiple
            accept=".pdf,.docx,.txt,.xlsx,.zip"
            onChange={handleFileChange}
            className="block text-sm"
          />
          <button
            onClick={handleUpload}
            disabled={!canUpload}
            className="px-4 py-2 rounded-lg bg-blue-600 text-white disabled:opacity-50"
          >
            {uploading ? 'Загрузка...' : 'Анализировать'}
          </button>
          {files.length > 0 && (
            <span className="text-xs text-gray-600">
              Выбрано: {files.length} • Общий размер: {fmtBytes(files.reduce((a,f)=>a+(f.size||0),0))}
            </span>
          )}
        </div>
        {uploading && (
          <div className="mt-3 w-full bg-gray-100 rounded h-2 overflow-hidden">
            <div className="h-2 bg-blue-600" style={{ width: `${progress}%` }} />
          </div>
        )}
        {!!status && (
          <div className="mt-3 text-sm text-gray-700">{status}</div>
        )}

        {preview && (
          <div className="mt-4">
            <SectionTitle>AI‑превью</SectionTitle>
            <div className="text-sm text-gray-800 bg-gray-50 rounded-lg p-3 whitespace-pre-wrap">
              {preview}
            </div>
            <div className="mt-2 text-xs text-gray-600">Чанков: {chunksCount}</div>
            <div className="mt-3 flex items-center gap-3">
              <button
                onClick={handleSave}
                disabled={!uploadId || saving}
                className="px-4 py-2 rounded-lg bg-green-600 text-white disabled:opacity-50"
              >
                {saving ? 'Сохранение...' : 'Сохранить в базу'}
              </button>
            </div>
          </div>
        )}
      </div>

      {/* Documents */}
      <div className="bg-white rounded-xl shadow-elegant p-6 mb-6">
        <SectionTitle>Сохранённые документы</SectionTitle>
        {loadingDocs ? (
          <div className="text-sm text-gray-600">Загрузка...</div>
        ) : (
          <div className="overflow-x-auto">
            <table className="min-w-full text-sm">
              <thead>
                <tr className="text-left text-gray-600 border-b">
                  <th className="py-2 pr-4">Имя</th>
                  <th className="py-2 pr-4">Размер</th>
                  <th className="py-2 pr-4">Дата</th>
                  <th className="py-2 pr-4">Действия</th>
                </tr>
              </thead>
              <tbody>
                {documents.length === 0 && (
                  <tr><td className="py-3 text-gray-500" colSpan={4}>Документов пока нет</td></tr>
                )}
                {documents.map((d) => (
                  <tr key={d.id} className="border-b last:border-b-0">
                    <td className="py-2 pr-4 text-gray-900">{d.filename || 'document'}</td>
                    <td className="py-2 pr-4 text-gray-700">{d.size_bytes ? fmtBytes(d.size_bytes) : '—'}</td>
                    <td className="py-2 pr-4 text-gray-700">{d.created_at ? new Date(d.created_at).toLocaleString() : '—'}</td>
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
          <input
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Введите запрос..."
            className="flex-1 px-3 py-2 rounded border border-gray-300"
          />
          <input
            type="number"
            min={1}
            max={50}
            value={topK}
            onChange={(e) => setTopK(e.target.value)}
            className="w-24 px-3 py-2 rounded border border-gray-300"
          />
          <button onClick={doSearch} disabled={searching || !query.trim()} className="px-4 py-2 rounded bg-indigo-600 text-white disabled:opacity-50">
            {searching ? 'Поиск...' : 'Искать'}
          </button>
        </div>
        {results.length > 0 && (
          <div className="mt-4 space-y-3">
            {results.map((r, idx) => (
              <div key={idx} className="bg-gray-50 rounded p-3">
                <div className="text-xs text-gray-600 mb-1">Документ: {r.filename} • Чанк #{r.chunk_index} • Релевантность: {(r.score*100).toFixed(1)}%</div>
                <div className="text-sm text-gray-900 whitespace-pre-wrap">
                  {(() => {
                    const q = (query || '').trim();
                    if (!q) return r.content;
                    try {
                      const esc = q.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
                      const re = new RegExp(esc, 'gi');
                      const parts = String(r.content || '').split(re);
                      const matches = String(r.content || '').match(re) || [];
                      const out = [];
                      for (let i = 0; i < parts.length; i++) {
                        out.push(parts[i]);
                        if (i < matches.length) {
                          out.push(<mark key={`m${i}`} className="bg-yellow-200 text-gray-900 px-0.5 rounded">{matches[i]}</mark>);
                        }
                      }
                      return out;
                    } catch {
                      return r.content;
                    }
                  })()}
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};

export default Training;