import React, { useState, useEffect } from 'react';
import { Card, Button } from '../UI';

const Logs = () => {
  const [logs, setLogs] = useState([]);
  const [loading, setLoading] = useState(false);

  const BACKEND_URL = process.env.REACT_APP_BACKEND_URL || 'https://audiobot-qci2.onrender.com';

  const fetchLogs = async () => {
    try {
      setLoading(true);
      // Simulate API call - replace with real endpoint
      const mockLogs = [
        { id: 1, timestamp: new Date(), level: 'INFO', message: 'VasDom AudioBot запущен', module: 'system' },
        { id: 2, timestamp: new Date(Date.now() - 300000), level: 'INFO', message: 'Emergent LLM подключен', module: 'ai' },
        { id: 3, timestamp: new Date(Date.now() - 600000), level: 'SUCCESS', message: 'Обработано 5 голосовых сообщений', module: 'voice' },
        { id: 4, timestamp: new Date(Date.now() - 900000), level: 'INFO', message: 'Синхронизация с Bitrix24 завершена', module: 'bitrix' }
      ];
      setLogs(mockLogs);
    } catch (error) {
      console.error('Error fetching logs:', error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchLogs();
  }, []);

  const getLevelColor = (level) => {
    switch (level) {
      case 'ERROR': return 'text-red-600 bg-red-50';
      case 'WARNING': return 'text-yellow-600 bg-yellow-50';
      case 'SUCCESS': return 'text-green-600 bg-green-50';
      case 'INFO':
      default: return 'text-blue-600 bg-blue-50';
    }
  };

  return (
    <div className="p-6">
      <div className="flex justify-between items-center mb-6">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Системные логи</h1>
          <p className="text-gray-600">Журнал событий системы</p>
        </div>
        <Button onClick={fetchLogs} loading={loading}>
          🔄 Обновить
        </Button>
      </div>

      <Card title="📝 Журнал событий">
        {logs.length > 0 ? (
          <div className="space-y-3">
            {logs.map((log) => (
              <div key={log.id} className="flex items-start space-x-3 p-3 border border-gray-200 rounded-lg">
                <span className={`px-2 py-1 rounded text-xs font-medium ${getLevelColor(log.level)}`}>
                  {log.level}
                </span>
                <div className="flex-1 min-w-0">
                  <p className="text-sm text-gray-900">{log.message}</p>
                  <div className="flex items-center mt-1 text-xs text-gray-500">
                    <span className="mr-2">📅 {log.timestamp.toLocaleString('ru-RU')}</span>
                    <span className="px-1 py-0.5 bg-gray-100 rounded">
                      {log.module}
                    </span>
                  </div>
                </div>
              </div>
            ))}
          </div>
        ) : (
          <div className="text-center py-12">
            <div className="text-6xl mb-4">📝</div>
            <h3 className="text-lg font-medium text-gray-900 mb-2">Логи загружаются</h3>
            <p className="text-gray-500">
              Здесь отображаются системные события и журнал работы AI.
            </p>
          </div>
        )}
      </Card>
    </div>
  );
};

export default Logs;