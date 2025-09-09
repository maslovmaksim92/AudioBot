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
    &lt;div className="p-6"&gt;
      &lt;div className="flex justify-between items-center mb-6"&gt;
        &lt;div&gt;
          &lt;h1 className="text-3xl font-bold text-gray-900"&gt;Системные логи&lt;/h1&gt;
          &lt;p className="text-gray-600"&gt;Мониторинг активности и отладка&lt;/p&gt;
        &lt;/div&gt;
        &lt;Button onClick={fetchLogs} loading={loading}&gt;
          🔄 Обновить
        &lt;/Button&gt;
      &lt;/div&gt;

      {/* Tabs */}
      &lt;Card className="mb-6"&gt;
        &lt;div className="flex space-x-1 p-1 bg-gray-100 rounded-lg"&gt;
          {tabs.map(tab => (
            &lt;button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={`flex-1 flex items-center justify-center px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
                activeTab === tab.id
                  ? 'bg-white text-blue-600 shadow-sm'
                  : 'text-gray-600 hover:text-gray-900'
              }`}
            &gt;
              &lt;span className="mr-2"&gt;{tab.icon}&lt;/span&gt;
              {tab.name}
            &lt;/button&gt;
          ))}
        &lt;/div&gt;
      &lt;/Card&gt;

      {/* Logs Content */}
      {loading ? (
        &lt;div className="flex justify-center py-12"&gt;
          &lt;LoadingSpinner size="lg" text="Загрузка логов..." /&gt;
        &lt;/div&gt;
      ) : currentLogs.length > 0 ? (
        &lt;div className="space-y-4"&gt;
          {currentLogs.map((log, index) => (
            &lt;Card key={log.id || index} className="hover:shadow-md transition-shadow"&gt;
              &lt;div className="space-y-3"&gt;
                &lt;div className="flex justify-between items-start"&gt;
                  &lt;div className="flex-1"&gt;
                    &lt;div className="flex items-center space-x-2 mb-2"&gt;
                      {log.context && (
                        &lt;span className={`px-2 py-1 rounded-full text-xs font-medium ${getContextColor(log.context)}`}&gt;
                          {log.context}
                        &lt;/span&gt;
                      )}
                      {log.user_id && (
                        &lt;span className="text-xs text-gray-500"&gt;
                          Пользователь: {log.user_id}
                        &lt;/span&gt;
                      )}
                    &lt;/div&gt;
                    
                    {log.user_message && (
                      &lt;div className="mb-3"&gt;
                        &lt;div className="text-sm font-medium text-gray-700 mb-1"&gt;👤 Сообщение пользователя:&lt;/div&gt;
                        &lt;div className="bg-blue-50 p-3 rounded-lg text-sm text-blue-900"&gt;
                          {log.user_message}
                        &lt;/div&gt;
                      &lt;/div&gt;
                    )}
                    
                    {log.ai_response && (
                      &lt;div className="mb-3"&gt;
                        &lt;div className="text-sm font-medium text-gray-700 mb-1"&gt;🤖 Ответ AI:&lt;/div&gt;
                        &lt;div className="bg-gray-50 p-3 rounded-lg text-sm text-gray-900"&gt;
                          {log.ai_response}
                        &lt;/div&gt;
                      &lt;/div&gt;
                    )}
                  &lt;/div&gt;
                &lt;/div&gt;
                
                &lt;div className="pt-3 border-t border-gray-100"&gt;
                  &lt;div className="flex justify-between items-center text-xs text-gray-500"&gt;
                    &lt;span&gt;ID: {log.id || index + 1}&lt;/span&gt;
                    &lt;span&gt;{formatTimestamp(log.timestamp)}&lt;/span&gt;
                  &lt;/div&gt;
                &lt;/div&gt;
              &lt;/div&gt;
            &lt;/Card&gt;
          ))}
        &lt;/div&gt;
      ) : (
        &lt;Card&gt;
          &lt;div className="text-center py-12"&gt;
            &lt;div className="text-6xl mb-4"&gt;📝&lt;/div&gt;
            &lt;h3 className="text-lg font-medium text-gray-900 mb-2"&gt;Нет логов&lt;/h3&gt;
            &lt;p className="text-gray-600"&gt;
              {activeTab === 'system' ? 'Системные логи' : 'AI логи'} появятся после активности
            &lt;/p&gt;
          &lt;/div&gt;
        &lt;/Card&gt;
      )}

      {/* Log Stats */}
      &lt;Card title="📊 Статистика логов" className="mt-6"&gt;
        &lt;div className="grid grid-cols-2 md:grid-cols-4 gap-4"&gt;
          &lt;div className="text-center"&gt;
            &lt;div className="text-2xl font-bold text-blue-600"&gt;{logs.length}&lt;/div&gt;
            &lt;div className="text-sm text-gray-600"&gt;Системных логов&lt;/div&gt;
          &lt;/div&gt;
          &lt;div className="text-center"&gt;
            &lt;div className="text-2xl font-bold text-green-600"&gt;{aiLogs.length}&lt;/div&gt;
            &lt;div className="text-sm text-gray-600"&gt;AI взаимодействий&lt;/div&gt;
          &lt;/div&gt;
          &lt;div className="text-center"&gt;
            &lt;div className="text-2xl font-bold text-purple-600"&gt;0&lt;/div&gt;
            &lt;div className="text-sm text-gray-600"&gt;Telegram логов&lt;/div&gt;
          &lt;/div&gt;
          &lt;div className="text-center"&gt;
            &lt;div className="text-2xl font-bold text-orange-600"&gt;{logs.length + aiLogs.length}&lt;/div&gt;
            &lt;div className="text-sm text-gray-600"&gt;Всего записей&lt;/div&gt;
          &lt;/div&gt;
        &lt;/div&gt;
      &lt;/Card&gt;
    &lt;/div&gt;
  );
};

export default Logs;