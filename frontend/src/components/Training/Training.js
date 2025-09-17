import React, { useState } from 'react';
import { Upload, CheckCircle2 } from 'lucide-react';

const Training = () => {
  const [file, setFile] = useState(null);
  const [preview, setPreview] = useState('');
  const [status, setStatus] = useState('');

  const handleFile = async (e) => {
    const f = e.target.files?.[0];
    setFile(f || null);
    if (!f) return;
    // Заглушка "что понял ИИ" — до подключения эмбеддингов
    setPreview('ИИ извлёк основные темы: графики уборок, бригады, УК, отчётность. Готов сохранить в базу знаний.');
  };

  const confirm = async () => {
    setStatus('Сохранено в базу знаний');
  };

  return (
    <div className="pt-2 px-4 pb-6 max-w-4xl mx-auto">
      <h1 className="text-2xl font-bold gradient-text mb-4">Обучение AI</h1>

      <div className="bg-white rounded-xl shadow-elegant p-6">
        <div className="flex items-center gap-3 mb-4">
          <label className="px-4 py-2 bg-blue-600 text-white rounded-lg flex items-center gap-2 cursor-pointer">
            <Upload className="w-4 h-4" /> Загрузить файл
            <input type="file" className="hidden" onChange={handleFile} />
          </label>
          {file && <span className="text-sm text-gray-700">{file.name}</span>}
        </div>

        {preview && (
          <div className="mb-4 text-sm text-gray-800 bg-gray-50 rounded-lg p-3">
            {preview}
          </div>
        )}

        <div className="flex items-center gap-3">
          <button onClick={confirm} disabled={!file} className="px-4 py-2 rounded-lg bg-green-600 text-white disabled:opacity-50 flex items-center gap-2">
            <CheckCircle2 className="w-4 h-4" /> Подтвердить
          </button>
          {status && <span className="text-sm text-green-700">{status}</span>}
        </div>
      </div>
    </div>
  );
};

export default Training;