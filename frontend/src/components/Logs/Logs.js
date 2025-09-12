import React, { useState, useEffect } from 'react';
import { useApp } from '../../context/AppContext';
import { apiService } from '../../services/apiService';
import { Card, Button, LoadingSpinner } from '../UI';

const Logs = () => {
  const { actions } = useApp();
  const [logs, setLogs] = useState([]);
  const [aiLogs, setAiLogs] = useState([]);
  const [loading, setLoading] = useState(false);
  const [activeTab, setActiveTab] = useState('system');

  useEffect(() => {
    fetchLogs();
  }, [activeTab]);

  const fetchLogs = async () => {
    setLoading(true);
    try {
      if (activeTab === 'system') {
        const response = await apiService.getLogs();
        if (response.status === 'success') {
          setLogs(response.voice_logs || []);
        }
      } else if (activeTab === 'ai') {
        const response = await apiService.getAILogs();
        if (response.status === 'success') {
          setAiLogs(response.ai_logs || []);
        }
      }
      
      actions.addNotification({
        type: 'success',
        message: `Загружены ${activeTab === 'system' ? 'системные' : 'AI'} логи`
      });
    } catch (error) {
      console.error('❌ Error fetching logs:', error);
      
      // Fallback demo data
      const mockSystemLogs = [
        {
          id: 1,
          user_message: 'Сколько у нас домов в управлении?',
          ai_response: 'У нас в управлении 348 домов, распределенных между 6 бригадами по районам Калуги.',
          user_id: 'dashboard_user',
          context: 'AI_VOICE_CHAT',
          timestamp: new Date().toISOString()
        },
        {
          id: 2,
          user_message: 'Покажи статистику по бригадам',
          ai_response: 'Центральный район: 58 домов (1 бригада), Никитинский: 62 дома (2 бригада), Жилетово: 45 домов (3 бригада)...',
          user_id: 'dashboard_user',
          context: 'AI_VOICE_CHAT',
          timestamp: new Date(Date.now() - 3600000).toISOString()
        }
      ];

      if (activeTab === 'system') {
        setLogs(mockSystemLogs);
      } else {
        setAiLogs(mockSystemLogs);
      }
      
      actions.addNotification({
        type: 'warning',
        message: 'Показаны демо логи'
      });
    } finally {
      setLoading(false);
    }
  };

  const formatTimestamp = (timestamp) => {
    if (!timestamp) return 'Неизвестно';
    try {
      return new Date(timestamp).toLocaleString('ru-RU');
    } catch {
      return 'Неверная дата';
    }
  };

  const getContextColor = (context) => {
    switch (context) {
      case 'AI_VOICE_CHAT': return 'bg-blue-100 text-blue-800';
      case 'telegram_bot': return 'bg-green-100 text-green-800';
      case 'API_REQUEST': return 'bg-purple-100 text-purple-800';
      case 'SYSTEM_ERROR': return 'bg-red-100 text-red-800';
      default: return 'bg-gray-100 text-gray-800';
    }
  };

  const tabs = [
    { id: 'system', name: 'Системные логи', icon: '📋' },
    { id: 'ai', name: 'AI логи', icon: '🤖' },
    { id: 'telegram', name: 'Telegram логи', icon: '📱' }
  ];

  const currentLogs = activeTab === 'system' ? logs : aiLogs;

  return (
    <div className="p-6">
      <div className="flex justify-between items-center mb-6">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Системные логи</h1>
          <p className="text-gray-600">Мониторинг активности и отладка</p>
        </div>
        <Button onClick={fetchLogs} loading={loading}>
          🔄 Обновить
        </Button>
      </div>

      {/* Tabs */}
      <Card className="mb-6">
        <div className="flex space-x-1 p-1 bg-gray-100 rounded-lg">
          {tabs.map(tab => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={`flex-1 flex items-center justify-center px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
                activeTab === tab.id
                  ? 'bg-white text-blue-600 shadow-sm'
                  : 'text-gray-600 hover:text-gray-900'
              }`}
            >
              <span className="mr-2">{tab.icon}</span>
              {tab.name}
            </button>
          ))}
        </div>
      </Card>

      {/* Logs Content */}
      {loading ? (
        <div className="flex justify-center py-12">
          <LoadingSpinner size="lg" text="Загрузка логов..." />
        </div>
      ) : currentLogs.length > 0 ? (
        <div className="space-y-4">
          {currentLogs.map((log, index) => (
            <Card key={log.id || index} className="hover:shadow-md transition-shadow">
              <div className="space-y-3">
                <div className="flex justify-between items-start">
                  <div className="flex-1">
                    <div className="flex items-center space-x-2 mb-2">
                      {log.context && (
                        <span className={`px-2 py-1 rounded-full text-xs font-medium ${getContextColor(log.context)}`}>
                          {log.context}
                        </span>
                      )}
                      {log.user_id && (
                        <span className="text-xs text-gray-500">
                          Пользователь: {log.user_id}
                        </span>
                      )}
                    </div>
                    
                    {log.user_message && (
                      <div className="mb-3">
                        <div className="text-sm font-medium text-gray-700 mb-1">👤 Сообщение пользователя:</div>
                        <div className="bg-blue-50 p-3 rounded-lg text-sm text-blue-900">
                          {log.user_message}
                        </div>
                      </div>
                    )}
                    
                    {log.ai_response && (
                      <div className="mb-3">
                        <div className="text-sm font-medium text-gray-700 mb-1">🤖 Ответ AI:</div>
                        <div className="bg-gray-50 p-3 rounded-lg text-sm text-gray-900">
                          {log.ai_response}
                        </div>
                      </div>
                    )}
                  </div>
                </div>
                
                <div className="pt-3 border-t border-gray-100">
                  <div className="flex justify-between items-center text-xs text-gray-500">
                    <span>ID: {log.id || index + 1}</span>
                    <span>{formatTimestamp(log.timestamp)}</span>
                  </div>
                </div>
              </div>
            </Card>
          ))}
        </div>
      ) : (
        <Card>
          <div className="text-center py-12">
            <div className="text-6xl mb-4">📝</div>
            <h3 className="text-lg font-medium text-gray-900 mb-2">Нет логов</h3>
            <p className="text-gray-600">
              {activeTab === 'system' ? 'Системные логи' : 'AI логи'} появятся после активности
            </p>
          </div>
        </Card>
      )}

      {/* Log Stats */}
      <Card title="📊 Статистика логов" className="mt-6">
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <div className="text-center">
            <div className="text-2xl font-bold text-blue-600">{logs.length}</div>
            <div className="text-sm text-gray-600">Системных логов</div>
          </div>
          <div className="text-center">
            <div className="text-2xl font-bold text-green-600">{aiLogs.length}</div>
            <div className="text-sm text-gray-600">AI взаимодействий</div>
          </div>
          <div className="text-center">
            <div className="text-2xl font-bold text-purple-600">0</div>
            <div className="text-sm text-gray-600">Telegram логов</div>
          </div>
          <div className="text-center">
            <div className="text-2xl font-bold text-orange-600">{logs.length + aiLogs.length}</div>
            <div className="text-sm text-gray-600">Всего записей</div>
          </div>
        </div>
      </Card>
    </div>
  );
};

export default Logs;
