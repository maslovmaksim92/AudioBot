import React, { useState, useEffect } from 'react';
import { Phone, PhoneIncoming, PhoneOutgoing, Clock, Calendar, TrendingUp, AlertCircle } from 'lucide-react';

const CallSummaries = () => {
  const [calls, setCalls] = useState([]);
  const [bitrixCalls, setBitrixCalls] = useState([]);
  const [activeTab, setActiveTab] = useState('summaries'); // 'summaries' или 'bitrix'
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [processingCallId, setProcessingCallId] = useState(null);
  const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;

  useEffect(() => {
    if (activeTab === 'summaries') {
      fetchCallHistory();
    } else {
      fetchBitrixCalls();
    }
  }, [activeTab]);

  const fetchCallHistory = async () => {
    try {
      setLoading(true);
      const response = await fetch(`${BACKEND_URL}/api/call-summary/history?limit=50`);
      
      if (!response.ok) {
        throw new Error('Ошибка загрузки истории звонков');
      }

      const data = await response.json();
      setCalls(data.calls || []);
    } catch (err) {
      setError(err.message);
      console.error('Error fetching call history:', err);
    } finally {
      setLoading(false);
    }
  };

  const fetchBitrixCalls = async () => {
    try {
      setLoading(true);
      const response = await fetch(`${BACKEND_URL}/api/bitrix-calls/recent?limit=50`);
      
      if (!response.ok) {
        throw new Error('Ошибка загрузки звонков из Bitrix24');
      }

      const data = await response.json();
      setBitrixCalls(data.calls || []);
    } catch (err) {
      setError(err.message);
      console.error('Error fetching Bitrix calls:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleCreateSummary = async (callId) => {
    try {
      setProcessingCallId(callId);
      
      const response = await fetch(`${BACKEND_URL}/api/bitrix-calls/process/${callId}`, {
        method: 'POST'
      });
      
      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Ошибка создания саммари');
      }

      alert('✅ Саммари создаётся! Проверьте через 30-60 секунд в разделе "Саммари"');
      
    } catch (err) {
      alert(`❌ ${err.message}`);
      console.error('Error creating summary:', err);
    } finally {
      setProcessingCallId(null);
    }
  };

  const formatDuration = (seconds) => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins}м ${secs}с`;
  };

  const getSentimentColor = (sentiment) => {
    switch (sentiment) {
      case 'positive':
        return 'bg-green-100 text-green-700';
      case 'negative':
        return 'bg-red-100 text-red-700';
      default:
        return 'bg-gray-100 text-gray-700';
    }
  };

  const getSentimentEmoji = (sentiment) => {
    switch (sentiment) {
      case 'positive':
        return '😊';
      case 'negative':
        return '😟';
      default:
        return '😐';
    }
  };

  if (loading) {
    return (
      <div className="p-6">
        <div className="flex items-center justify-center">
          <div className="w-8 h-8 border-4 border-blue-500 border-t-transparent rounded-full animate-spin"></div>
          <span className="ml-3 text-gray-600">Загрузка истории звонков...</span>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="p-6">
        <div className="bg-red-50 border border-red-200 rounded-lg p-4">
          <div className="flex items-center gap-2 text-red-700">
            <AlertCircle className="w-5 h-5" />
            <span>{error}</span>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="p-6">
      {/* Заголовок */}
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-gray-900 flex items-center gap-2">
          <Phone className="w-7 h-7 text-blue-600" />
          Звонки и саммари
        </h1>
        <p className="text-gray-600 mt-1">
          Автоматическая транскрипция и анализ звонков
        </p>
      </div>

      {/* Табы */}
      <div className="bg-white border-b mb-6">
        <div className="flex gap-4">
          <button
            onClick={() => setActiveTab('summaries')}
            className={`px-4 py-3 font-medium border-b-2 transition-colors ${
              activeTab === 'summaries'
                ? 'border-blue-600 text-blue-600'
                : 'border-transparent text-gray-600 hover:text-gray-900'
            }`}
          >
            📝 Саммари ({calls.length})
          </button>
          <button
            onClick={() => setActiveTab('bitrix')}
            className={`px-4 py-3 font-medium border-b-2 transition-colors ${
              activeTab === 'bitrix'
                ? 'border-purple-600 text-purple-600'
                : 'border-transparent text-gray-600 hover:text-gray-900'
            }`}
          >
            📞 Звонки из Bitrix24 ({bitrixCalls.length})
          </button>
        </div>
      </div>

      {/* Статистика */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
        <div className="bg-white rounded-lg shadow p-4 border border-gray-200">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-600">Всего звонков</p>
              <p className="text-2xl font-bold text-gray-900">{calls.length}</p>
            </div>
            <Phone className="w-10 h-10 text-blue-500" />
          </div>
        </div>

        <div className="bg-white rounded-lg shadow p-4 border border-gray-200">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-600">Входящих</p>
              <p className="text-2xl font-bold text-green-600">
                {calls.filter(c => c.direction === 'in').length}
              </p>
            </div>
            <PhoneIncoming className="w-10 h-10 text-green-500" />
          </div>
        </div>

        <div className="bg-white rounded-lg shadow p-4 border border-gray-200">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-600">Исходящих</p>
              <p className="text-2xl font-bold text-orange-600">
                {calls.filter(c => c.direction === 'out').length}
              </p>
            </div>
            <PhoneOutgoing className="w-10 h-10 text-orange-500" />
          </div>
        </div>
      </div>

      {/* Список звонков */}
      {calls.length === 0 ? (
        <div className="bg-white rounded-lg shadow p-8 text-center">
          <Phone className="w-16 h-16 text-gray-400 mx-auto mb-4" />
          <p className="text-gray-600 text-lg">Пока нет саммари звонков</p>
          <p className="text-gray-500 text-sm mt-2">
            Саммари будут создаваться автоматически после завершения звонков
          </p>
        </div>
      ) : (
        <div className="space-y-4">
          {calls.map((call) => (
            <div key={call.id} className="bg-white rounded-lg shadow-md p-6 border border-gray-200 hover:shadow-lg transition-shadow">
              {/* Заголовок звонка */}
              <div className="flex items-start justify-between mb-4">
                <div className="flex items-center gap-3">
                  {call.direction === 'in' ? (
                    <PhoneIncoming className="w-6 h-6 text-green-600" />
                  ) : (
                    <PhoneOutgoing className="w-6 h-6 text-orange-600" />
                  )}
                  <div>
                    <h3 className="text-lg font-semibold text-gray-900">
                      {call.direction === 'in' ? 'Входящий звонок' : 'Исходящий звонок'}
                    </h3>
                    <div className="flex items-center gap-4 text-sm text-gray-600 mt-1">
                      <span>От: {call.caller}</span>
                      <span>Кому: {call.called}</span>
                      <span className="flex items-center gap-1">
                        <Clock className="w-4 h-4" />
                        {formatDuration(call.duration)}
                      </span>
                    </div>
                  </div>
                </div>

                <div className="flex items-center gap-2">
                  <span className={`px-3 py-1 rounded-full text-sm font-medium ${getSentimentColor(call.sentiment)}`}>
                    {getSentimentEmoji(call.sentiment)} {call.sentiment}
                  </span>
                  <span className="text-sm text-gray-500">
                    {new Date(call.created_at).toLocaleString('ru-RU')}
                  </span>
                </div>
              </div>

              {/* Саммари */}
              <div className="mb-4">
                <h4 className="text-sm font-semibold text-gray-700 mb-2">📝 Саммари:</h4>
                <p className="text-gray-800">{call.summary}</p>
              </div>

              {/* Ключевые пункты */}
              {call.key_points && call.key_points.length > 0 && (
                <div className="mb-4">
                  <h4 className="text-sm font-semibold text-gray-700 mb-2">🎯 Ключевые пункты:</h4>
                  <ul className="list-disc list-inside space-y-1">
                    {call.key_points.map((point, idx) => (
                      <li key={idx} className="text-gray-700">{point}</li>
                    ))}
                  </ul>
                </div>
              )}

              {/* Задачи */}
              {call.action_items && call.action_items.length > 0 && (
                <div className="mb-4">
                  <h4 className="text-sm font-semibold text-gray-700 mb-2">✅ Задачи:</h4>
                  <ul className="space-y-1">
                    {call.action_items.map((task, idx) => (
                      <li key={idx} className="flex items-start gap-2">
                        <input type="checkbox" className="mt-1" />
                        <span className="text-gray-700">{task}</span>
                      </li>
                    ))}
                  </ul>
                </div>
              )}

              {/* Запрос клиента */}
              {call.client_request && (
                <div className="mb-4">
                  <h4 className="text-sm font-semibold text-gray-700 mb-2">💬 Запрос клиента:</h4>
                  <p className="text-gray-700">{call.client_request}</p>
                </div>
              )}

              {/* Следующие шаги */}
              {call.next_steps && (
                <div>
                  <h4 className="text-sm font-semibold text-gray-700 mb-2">➡️ Следующие шаги:</h4>
                  <p className="text-gray-700">{call.next_steps}</p>
                </div>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

export default CallSummaries;
