import React, { useState, useEffect } from 'react';
import axios from 'axios';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

// Logs Dashboard Component - максимальное логирование
const LogsDashboard = () => {
  const [logs, setLogs] = useState([]);
  const [dashboard, setDashboard] = useState(null);
  const [systemStatus, setSystemStatus] = useState({});
  const [telegramMessages, setTelegramMessages] = useState([]);
  const [loading, setLoading] = useState(true);
  const [autoRefresh, setAutoRefresh] = useState(true);

  useEffect(() => {
    fetchAllData();
    
    // Auto-refresh every 30 seconds
    const interval = autoRefresh ? setInterval(fetchAllData, 30000) : null;
    
    return () => {
      if (interval) clearInterval(interval);
    };
  }, [autoRefresh]);

  const fetchAllData = async () => {
    try {
      setLoading(true);
      
      // Запрашиваем данные со всех endpoints
      const [dashboardRes, logsRes, healthRes] = await Promise.all([
        axios.get(`${API}/dashboard`).catch(() => ({ data: {} })),
        axios.get(`${API}/logs`).catch(() => ({ data: { logs: [] } })),
        axios.get(`${API}/health`).catch(() => ({ data: {} }))
      ]);
      
      setDashboard(dashboardRes.data);
      setLogs(logsRes.data.logs || []);
      setSystemStatus(healthRes.data);
      setTelegramMessages(dashboardRes.data.telegram_messages || []);
      
    } catch (error) {
      console.error('Error fetching data:', error);
    } finally {
      setLoading(false);
    }
  };

  const setupWebhook = async () => {
    try {
      const response = await axios.get(`${API}/telegram/set-webhook`);
      alert(`Webhook setup result: ${response.data.status}`);
      fetchAllData(); // Refresh data
    } catch (error) {
      alert(`Error: ${error.response?.data?.error || error.message}`);
    }
  };

  const getLogLevelColor = (level) => {
    switch (level) {
      case 'ERROR': return 'text-red-600 bg-red-50';
      case 'WARNING': return 'text-yellow-600 bg-yellow-50';
      case 'SUCCESS': return 'text-green-600 bg-green-50';
      default: return 'text-blue-600 bg-blue-50';
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-96">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500"></div>
        <span className="ml-3 text-gray-600">Загружаем логи системы...</span>
      </div>
    );
  }

  return (
    <div className="space-y-8">
      <div className="flex justify-between items-center">
        <h2 className="text-2xl font-bold text-gray-900">📋 Системные логи и мониторинг</h2>
        <div className="flex space-x-3">
          <button
            onClick={() => setAutoRefresh(!autoRefresh)}
            className={`px-4 py-2 rounded-lg transition-colors ${
              autoRefresh 
                ? 'bg-green-500 text-white' 
                : 'bg-gray-200 text-gray-700'
            }`}
          >
            {autoRefresh ? '⏸️ Авто-обновление' : '▶️ Авто-обновление'}
          </button>
          <button
            onClick={fetchAllData}
            className="bg-blue-500 text-white px-4 py-2 rounded-lg hover:bg-blue-600 transition-colors"
          >
            🔄 Обновить
          </button>
          <button
            onClick={setupWebhook}
            className="bg-purple-500 text-white px-4 py-2 rounded-lg hover:bg-purple-600 transition-colors"
          >
            🔗 Setup Webhook
          </button>
        </div>
      </div>

      {/* System Status Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
        <div className="bg-white rounded-lg shadow-lg p-6">
          <h3 className="text-sm font-medium text-gray-600">📊 Всего запросов</h3>
          <p className="text-3xl font-bold text-blue-600 mt-2">
            {dashboard?.system_status?.total_requests || 0}
          </p>
          <p className="text-sm text-gray-500 mt-1">С момента запуска</p>
        </div>
        
        <div className="bg-white rounded-lg shadow-lg p-6">
          <h3 className="text-sm font-medium text-gray-600">🤖 Telegram Updates</h3>
          <p className="text-3xl font-bold text-green-600 mt-2">
            {dashboard?.system_status?.telegram_updates || 0}
          </p>
          <p className="text-sm text-gray-500 mt-1">Сообщений от пользователей</p>
        </div>
        
        <div className="bg-white rounded-lg shadow-lg p-6">
          <h3 className="text-sm font-medium text-gray-600">❌ Ошибки</h3>
          <p className="text-3xl font-bold text-red-600 mt-2">
            {dashboard?.system_status?.errors || 0}
          </p>
          <p className="text-sm text-gray-500 mt-1">Системные ошибки</p>
        </div>
        
        <div className="bg-white rounded-lg shadow-lg p-6">
          <h3 className="text-sm font-medium text-gray-600">📈 Статус</h3>
          <p className="text-2xl font-bold text-purple-600 mt-2">
            {systemStatus?.status === 'healthy' ? '✅ Работает' : '❌ Проблемы'}
          </p>
          <p className="text-sm text-gray-500 mt-1">
            {dashboard?.system_status?.last_activity ? 
              new Date(dashboard.system_status.last_activity).toLocaleTimeString('ru-RU') :
              'Нет данных'
            }
          </p>
        </div>
      </div>

      {/* Environment Status */}
      {dashboard?.environment && (
        <div className="bg-white rounded-lg shadow-lg p-6">
          <h3 className="text-lg font-semibold mb-4">🔧 Конфигурация окружения</h3>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <div className="flex items-center space-x-2">
              <span className={`w-3 h-3 rounded-full ${dashboard.environment.telegram_configured ? 'bg-green-500' : 'bg-red-500'}`}></span>
              <span>Telegram Bot</span>
            </div>
            <div className="flex items-center space-x-2">
              <span className={`w-3 h-3 rounded-full ${dashboard.environment.webhook_configured ? 'bg-green-500' : 'bg-red-500'}`}></span>
              <span>Webhook URL</span>
            </div>
            <div className="flex items-center space-x-2">
              <span className={`w-3 h-3 rounded-full ${dashboard.environment.bitrix24_configured ? 'bg-green-500' : 'bg-red-500'}`}></span>
              <span>Bitrix24</span>
            </div>
            <div className="flex items-center space-x-2">
              <span className={`w-3 h-3 rounded-full ${dashboard.environment.ai_configured ? 'bg-green-500' : 'bg-red-500'}`}></span>
              <span>AI Keys</span>
            </div>
          </div>
        </div>
      )}

      {/* Telegram Messages */}
      {telegramMessages.length > 0 && (
        <div className="bg-white rounded-lg shadow-lg p-6">
          <h3 className="text-lg font-semibold mb-4">💬 Последние сообщения Telegram</h3>
          <div className="space-y-3 max-h-64 overflow-y-auto">
            {telegramMessages.map((msg, index) => (
              <div key={index} className="border-l-4 border-blue-500 bg-blue-50 p-3 rounded-r-lg">
                <div className="flex justify-between items-start">
                  <div>
                    <p className="font-medium text-blue-800">
                      {msg.user_name} (@{msg.username})
                    </p>
                    <p className="text-sm text-gray-700 mt-1">{msg.text}</p>
                  </div>
                  <span className="text-xs text-blue-600">
                    {new Date(msg.timestamp).toLocaleTimeString('ru-RU')}
                  </span>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* System Logs */}
      <div className="bg-white rounded-lg shadow-lg p-6">
        <h3 className="text-lg font-semibold mb-4">📋 Системные логи ({logs.length})</h3>
        <div className="space-y-2 max-h-96 overflow-y-auto">
          {logs.length === 0 ? (
            <p className="text-gray-500 text-center py-8">Логи пока отсутствуют</p>
          ) : (
            logs.slice().reverse().map((log, index) => (
              <div key={index} className={`p-3 rounded-lg ${getLogLevelColor(log.level)}`}>
                <div className="flex justify-between items-start">
                  <div className="flex-1">
                    <div className="flex items-center space-x-2">
                      <span className="font-medium text-xs uppercase">
                        {log.level}
                      </span>
                      <span className="text-sm">
                        {new Date(log.timestamp).toLocaleString('ru-RU')}
                      </span>
                    </div>
                    <p className="mt-1 text-sm font-medium">{log.message}</p>
                    {log.details && Object.keys(log.details).length > 0 && (
                      <details className="mt-2">
                        <summary className="text-xs cursor-pointer">Подробности</summary>
                        <pre className="text-xs mt-1 p-2 bg-gray-100 rounded overflow-x-auto">
                          {JSON.stringify(log.details, null, 2)}
                        </pre>
                      </details>
                    )}
                  </div>
                </div>
              </div>
            ))
          )}
        </div>
      </div>

      {/* Quick Actions */}
      <div className="bg-gradient-to-r from-purple-500 to-blue-500 text-white rounded-lg p-6">
        <h3 className="text-lg font-bold mb-4">⚡ Быстрые действия</h3>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div className="bg-white bg-opacity-20 rounded-lg p-4">
            <h4 className="font-medium">🤖 Telegram Bot</h4>
            <p className="text-sm opacity-90">@aitest123432_bot</p>
            <p className="text-xs opacity-75 mt-1">
              {dashboard?.environment?.telegram_configured ? 'Настроен' : 'Требует настройки'}
            </p>
          </div>
          <div className="bg-white bg-opacity-20 rounded-lg p-4">
            <h4 className="font-medium">🔗 Webhook</h4>
            <p className="text-xs opacity-75">
              {dashboard?.environment?.webhook_configured ? 'URL установлен' : 'Не настроен'}
            </p>
            <button 
              onClick={setupWebhook}
              className="mt-2 px-3 py-1 bg-white bg-opacity-30 rounded text-xs hover:bg-opacity-50"
            >
              Настроить
            </button>
          </div>
          <div className="bg-white bg-opacity-20 rounded-lg p-4">
            <h4 className="font-medium">📊 Мониторинг</h4>
            <p className="text-xs opacity-75">
              Авто-обновление: {autoRefresh ? 'Включено' : 'Выключено'}
            </p>
            <p className="text-xs opacity-75">
              Интервал: 30 секунд
            </p>
          </div>
        </div>
      </div>
    </div>
  );
};

export default LogsDashboard;