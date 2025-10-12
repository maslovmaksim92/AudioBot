import React, { useState } from 'react';
import { X, Sparkles, Send, Loader } from 'lucide-react';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL || import.meta?.env?.REACT_APP_BACKEND_URL;

const AIImprovementModal = ({ isOpen, onClose, sectionName }) => {
  const [request, setRequest] = useState('');
  const [loading, setLoading] = useState(false);
  const [response, setResponse] = useState('');

  const handleSubmit = async () => {
    if (!request.trim()) return;
    
    setLoading(true);
    setResponse('');
    
    try {
      const res = await fetch(`${BACKEND_URL}/api/ai-agent/improve-section`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          section: sectionName,
          improvement_request: request
        })
      });
      
      const data = await res.json();
      
      if (data.success) {
        setResponse(data.message);
      } else {
        setResponse(`Ошибка: ${data.error}`);
      }
    } catch (error) {
      console.error('Error:', error);
      setResponse(`Ошибка подключения: ${error.message}`);
    } finally {
      setLoading(false);
    }
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 overflow-y-auto">
      {/* Backdrop */}
      <div 
        className="fixed inset-0 bg-black bg-opacity-50 transition-opacity"
        onClick={onClose}
      />
      
      {/* Modal */}
      <div className="flex min-h-full items-center justify-center p-4">
        <div className="relative bg-white rounded-2xl shadow-2xl w-full max-w-2xl transform transition-all">
          {/* Header */}
          <div className="bg-gradient-to-r from-blue-600 to-purple-600 px-6 py-4 rounded-t-2xl">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 bg-white/20 rounded-lg flex items-center justify-center">
                  <Sparkles className="w-6 h-6 text-white" />
                </div>
                <div>
                  <h3 className="text-xl font-bold text-white">AI Улучшение</h3>
                  <p className="text-sm text-blue-100">Раздел: {sectionName}</p>
                </div>
              </div>
              <button
                onClick={onClose}
                className="text-white hover:bg-white/20 rounded-lg p-2 transition-colors"
              >
                <X className="w-6 h-6" />
              </button>
            </div>
          </div>

          {/* Body */}
          <div className="p-6 space-y-4">
            {/* Input */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Опишите желаемое улучшение:
              </label>
              <textarea
                value={request}
                onChange={(e) => setRequest(e.target.value)}
                placeholder="Например: Добавить фильтр по датам, улучшить дизайн карточек, добавить экспорт в Excel..."
                className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent resize-none"
                rows={4}
                disabled={loading}
              />
            </div>

            {/* Response */}
            {response && (
              <div className="bg-gradient-to-r from-blue-50 to-purple-50 border border-blue-200 rounded-lg p-4">
                <div className="flex items-start gap-3">
                  <Sparkles className="w-5 h-5 text-blue-600 mt-1 flex-shrink-0" />
                  <div className="flex-1">
                    <h4 className="font-semibold text-gray-900 mb-2">Ответ AI агента:</h4>
                    <p className="text-gray-700 whitespace-pre-wrap">{response}</p>
                  </div>
                </div>
              </div>
            )}

            {/* Info */}
            <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4">
              <p className="text-sm text-yellow-800">
                <span className="font-semibold">Как это работает:</span> AI агент проанализирует ваш запрос, 
                внесет изменения в код, создаст коммит в GitHub и автоматически задеплоит на Render.
              </p>
            </div>
          </div>

          {/* Footer */}
          <div className="px-6 py-4 bg-gray-50 rounded-b-2xl flex items-center justify-between">
            <button
              onClick={onClose}
              className="px-4 py-2 text-gray-700 hover:bg-gray-200 rounded-lg transition-colors"
              disabled={loading}
            >
              Отмена
            </button>
            <button
              onClick={handleSubmit}
              disabled={loading || !request.trim()}
              className="flex items-center gap-2 px-6 py-2 bg-gradient-to-r from-blue-600 to-purple-600 text-white rounded-lg hover:from-blue-700 hover:to-purple-700 transition-all disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {loading ? (
                <>
                  <Loader className="w-5 h-5 animate-spin" />
                  Обработка...
                </>
              ) : (
                <>
                  <Send className="w-5 h-5" />
                  Отправить запрос
                </>
              )}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default AIImprovementModal;
