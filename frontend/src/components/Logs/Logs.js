import React, { useState, useEffect } from 'react';
import { 
  FileText, 
  AlertCircle, 
  Info, 
  CheckCircle, 
  XCircle,
  Filter,
  Download,
  Search,
  RefreshCw,
  Clock
} from 'lucide-react';

const Logs = () => {
  const [logs, setLogs] = useState([]);
  const [loading, setLoading] = useState(false);
  const [filter, setFilter] = useState('all');
  const [searchQuery, setSearchQuery] = useState('');

  // Симуляция загрузки логов
  useEffect(() => {
    loadLogs();
  }, []);

  const loadLogs = () => {
    setLoading(true);
    setTimeout(() => {
      const mockLogs = [
        {
          id: 1,
          timestamp: new Date().toISOString(),
          level: 'INFO',
          service: 'bitrix_sync',
          message: 'Синхронизация 490 домов завершена успешно',
          details: { houses: 490, duration: '2.3s' }
        },
        {
          id: 2,
          timestamp: new Date(Date.now() - 120000).toISOString(),
          level: 'SUCCESS',
          service: 'telegram',
          message: 'Отправлено 15 уведомлений бригадам',
          details: { recipients: ['Бригада 1', 'Бригада 2', 'Бригада 3'] }
        },
        {
          id: 3,
          timestamp: new Date(Date.now() - 300000).toISOString(),
          level: 'WARNING',
          service: 'ai_tasks',
          message: 'Планерка: напоминание отправлено с задержкой',
          details: { delay: '30s', reason: 'network_latency' }
        },
        {
          id: 4,
          timestamp: new Date(Date.now() - 600000).toISOString(),
          level: 'ERROR',
          service: 'voice',
          message: 'AI звонок не удался: нет ответа от абонента',
          details: { phone: '+79200924550', attempt: 2 }
        },
        {
          id: 5,
          timestamp: new Date(Date.now() - 900000).toISOString(),
          level: 'INFO',
          service: 'auth',
          message: 'Вход в систему: Маслов Максим (Директор)',
          details: { ip: '192.168.1.100', browser: 'Chrome' }
        },
        {
          id: 6,
          timestamp: new Date(Date.now() - 1200000).toISOString(),
          level: 'SUCCESS',
          service: 'works',
          message: 'Акт подписан: Билибина 6',
          details: { brigade: 'Бригада 1', house: 'Билибина 6' }
        },
        {
          id: 7,
          timestamp: new Date(Date.now() - 1500000).toISOString(),
          level: 'INFO',
          service: 'scheduler',
          message: 'Запущена автоматическая задача: сбор отчетности',
          details: { task: 'daily_report', schedule: '16:55' }
        },
        {
          id: 8,
          timestamp: new Date(Date.now() - 1800000).toISOString(),
          level: 'WARNING',
          service: 'database',
          message: 'Медленный запрос: получение списка домов',
          details: { duration: '3.5s', query: 'SELECT * FROM houses' }
        }
      ];
      setLogs(mockLogs);
      setLoading(false);
    }, 500);
  };

  const getLevelConfig = (level) => {
    const configs = {
      INFO: { icon: Info, color: 'text-blue-600', bg: 'bg-blue-50', border: 'border-blue-200' },
      SUCCESS: { icon: CheckCircle, color: 'text-green-600', bg: 'bg-green-50', border: 'border-green-200' },
      WARNING: { icon: AlertCircle, color: 'text-yellow-600', bg: 'bg-yellow-50', border: 'border-yellow-200' },
      ERROR: { icon: XCircle, color: 'text-red-600', bg: 'bg-red-50', border: 'border-red-200' }
    };
    return configs[level] || configs.INFO;
  };

  const filteredLogs = logs.filter(log => {
    const matchesFilter = filter === 'all' || log.level === filter;
    const matchesSearch = log.message.toLowerCase().includes(searchQuery.toLowerCase()) ||
                         log.service.toLowerCase().includes(searchQuery.toLowerCase());
    return matchesFilter && matchesSearch;
  });

  const formatTimestamp = (timestamp) => {
    const date = new Date(timestamp);
    const now = new Date();
    const diff = Math.floor((now - date) / 1000);
    
    if (diff < 60) return `${diff}с назад`;
    if (diff < 3600) return `${Math.floor(diff / 60)}м назад`;
    if (diff < 86400) return `${Math.floor(diff / 3600)}ч назад`;
    
    return date.toLocaleString('ru-RU', { 
      day: '2-digit', 
      month: '2-digit', 
      hour: '2-digit', 
      minute: '2-digit' 
    });
  };

  const exportLogs = () => {
    const csv = [
      ['Timestamp', 'Level', 'Service', 'Message', 'Details'].join(','),
      ...filteredLogs.map(log => 
        [log.timestamp, log.level, log.service, log.message, JSON.stringify(log.details)].join(',')
      )
    ].join('\n');
    
    const blob = new Blob([csv], { type: 'text/csv' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `vasdom_logs_${new Date().toISOString().split('T')[0]}.csv`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-50 via-white to-slate-100 p-6">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-4xl font-bold text-gray-900 mb-2 flex items-center gap-3">
            <FileText className="w-10 h-10 text-gray-700" />
            Журнал событий
          </h1>
          <p className="text-gray-600">
            Логи системы в стиле Render - мониторинг всех событий
          </p>
        </div>

        {/* Controls */}
        <div className="bg-white rounded-2xl shadow-lg p-6 border border-gray-100 mb-6">
          <div className="flex flex-col md:flex-row gap-4">
            {/* Search */}
            <div className="flex-1 relative">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-5 h-5 text-gray-400" />
              <input
                type="text"
                placeholder="Поиск по логам..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="w-full pl-10 pr-4 py-3 border border-gray-200 rounded-xl focus:ring-2 focus:ring-gray-500 focus:border-transparent"
              />
            </div>

            {/* Filter */}
            <div className="flex gap-2">
              {['all', 'INFO', 'SUCCESS', 'WARNING', 'ERROR'].map(level => (
                <button
                  key={level}
                  onClick={() => setFilter(level)}
                  className={`px-4 py-2 rounded-xl whitespace-nowrap transition-all ${
                    filter === level
                      ? 'bg-gray-700 text-white shadow-md'
                      : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                  }`}
                >
                  {level === 'all' ? 'Все' : level}
                </button>
              ))}
            </div>

            {/* Actions */}
            <div className="flex gap-2">
              <button
                onClick={loadLogs}
                disabled={loading}
                className="px-4 py-2 bg-blue-600 text-white rounded-xl hover:bg-blue-700 transition-all flex items-center gap-2"
              >
                <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
                Обновить
              </button>
              <button
                onClick={exportLogs}
                className="px-4 py-2 bg-green-600 text-white rounded-xl hover:bg-green-700 transition-all flex items-center gap-2"
              >
                <Download className="w-4 h-4" />
                Экспорт
              </button>
            </div>
          </div>
        </div>

        {/* Logs Table */}
        <div className="bg-black rounded-2xl shadow-2xl border border-gray-800 overflow-hidden">
          {/* Header */}
          <div className="bg-gray-900 px-6 py-4 border-b border-gray-800">
            <div className="grid grid-cols-12 gap-4 text-xs font-mono text-gray-400 uppercase">
              <div className="col-span-2">Время</div>
              <div className="col-span-1">Уровень</div>
              <div className="col-span-2">Сервис</div>
              <div className="col-span-5">Сообщение</div>
              <div className="col-span-2">Детали</div>
            </div>
          </div>

          {/* Logs */}
          <div className="bg-gray-950 max-h-[600px] overflow-y-auto">
            {loading ? (
              <div className="flex items-center justify-center py-12">
                <RefreshCw className="w-8 h-8 text-gray-600 animate-spin" />
              </div>
            ) : filteredLogs.length === 0 ? (
              <div className="text-center py-12 text-gray-600">
                <FileText className="w-12 h-12 mx-auto mb-3 text-gray-700" />
                <p>Логи не найдены</p>
              </div>
            ) : (
              <div className="divide-y divide-gray-900">
                {filteredLogs.map(log => {
                  const config = getLevelConfig(log.level);
                  return (
                    <div 
                      key={log.id} 
                      className="px-6 py-4 hover:bg-gray-900 transition-colors"
                    >
                      <div className="grid grid-cols-12 gap-4 items-start">
                        {/* Timestamp */}
                        <div className="col-span-2 text-xs text-gray-500 font-mono flex items-center gap-1">
                          <Clock className="w-3 h-3" />
                          {formatTimestamp(log.timestamp)}
                        </div>

                        {/* Level */}
                        <div className="col-span-1">
                          <span className={`inline-flex items-center gap-1 px-2 py-1 rounded text-xs font-semibold ${config.bg} ${config.color}`}>
                            <config.icon className="w-3 h-3" />
                            {log.level}
                          </span>
                        </div>

                        {/* Service */}
                        <div className="col-span-2">
                          <span className="text-sm text-blue-400 font-mono">
                            {log.service}
                          </span>
                        </div>

                        {/* Message */}
                        <div className="col-span-5 text-sm text-gray-300 font-mono">
                          {log.message}
                        </div>

                        {/* Details */}
                        <div className="col-span-2">
                          {log.details && (
                            <details className="text-xs text-gray-500 font-mono cursor-pointer">
                              <summary className="hover:text-gray-400">Подробнее...</summary>
                              <pre className="mt-2 p-2 bg-gray-900 rounded text-xs overflow-x-auto">
                                {JSON.stringify(log.details, null, 2)}
                              </pre>
                            </details>
                          )}
                        </div>
                      </div>
                    </div>
                  );
                })}
              </div>
            )}
          </div>

          {/* Footer */}
          <div className="bg-gray-900 px-6 py-3 border-t border-gray-800">
            <p className="text-xs text-gray-500 font-mono">
              Показано {filteredLogs.length} из {logs.length} логов
            </p>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Logs;