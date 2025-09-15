import React, { useState, useEffect } from 'react';
import { 
  FileText, 
  Search, 
  Filter, 
  Calendar,
  AlertTriangle,
  CheckCircle,
  Info,
  XCircle,
  Download,
  RefreshCw
} from 'lucide-react';

const Logs = () => {
  const [logs, setLogs] = useState([]);
  const [filteredLogs, setFilteredLogs] = useState([]);
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedLevel, setSelectedLevel] = useState('');
  const [selectedDate, setSelectedDate] = useState('');
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    // Симуляция загрузки логов
    setTimeout(() => {
      const mockLogs = [
        {
          id: 1,
          timestamp: new Date(Date.now() - 1000 * 60 * 5),
          level: 'info',
          service: 'Bitrix24 API',
          message: 'Успешно загружено 490 домов из CRM системы',
          details: 'GET /api/cleaning/houses - 200 OK',
          user: 'system'
        },
        {
          id: 2,
          timestamp: new Date(Date.now() - 1000 * 60 * 15),
          level: 'success',
          service: 'AI Консультант',
          message: 'Обработан запрос пользователя о графике уборки',
          details: 'Запрос: "Какие дома убирает бригада №3?" - Ответ сгенерирован за 1.2с',
          user: 'user123'
        },
        {
          id: 3,
          timestamp: new Date(Date.now() - 1000 * 60 * 30),
          level: 'warning',
          service: 'Telegram Bot',
          message: 'Превышено время ожидания ответа от Telegram API',
          details: 'Timeout после 10 секунд, повторная попытка через 30 секунд',
          user: 'system'
        },
        {
          id: 4,
          timestamp: new Date(Date.now() - 1000 * 60 * 45),
          level: 'info',
          service: 'Дашборд',
          message: 'Пользователь просмотрел статистику системы',
          details: 'GET /api/dashboard/stats - Загружены данные за текущий месяц',
          user: 'admin'
        },
        {
          id: 5,
          timestamp: new Date(Date.now() - 1000 * 60 * 60),
          level: 'error',
          service: 'Bitrix24 API',
          message: 'Ошибка подключения к CRM системе',
          details: 'Connection timeout - проверьте статус сети и webhook URL',
          user: 'system'
        },
        {
          id: 6,
          timestamp: new Date(Date.now() - 1000 * 60 * 75),
          level: 'success',
          service: 'Управление домами',
          message: 'Обновлен статус уборки для дома ID: 147',
          details: 'Статус изменен с "В процессе" на "Завершено" бригадой №2',
          user: 'brigade_2'
        },
        {
          id: 7,
          timestamp: new Date(Date.now() - 1000 * 60 * 90),
          level: 'info',
          service: 'AI Консультант',
          message: 'Голосовое сообщение обработано и преобразовано в текст',
          details: 'Распознано: "Покажи график работы на завтра" - Длительность: 3.2с',
          user: 'user456'
        },
        {
          id: 8,
          timestamp: new Date(Date.now() - 1000 * 60 * 120),
          level: 'warning',
          service: 'Сотрудники',
          message: 'Бригада №5 не отметилась в системе более 2 часов',
          details: 'Последняя активность: 12:30 - рекомендуется связаться с бригадиром',
          user: 'system'
        }
      ];
      
      setLogs(mockLogs);
      setFilteredLogs(mockLogs);
      setLoading(false);
    }, 1000);
  }, []);

  useEffect(() => {
    let filtered = logs;

    if (searchTerm) {
      filtered = filtered.filter(log =>
        log.message.toLowerCase().includes(searchTerm.toLowerCase()) ||
        log.service.toLowerCase().includes(searchTerm.toLowerCase()) ||
        log.details.toLowerCase().includes(searchTerm.toLowerCase())
      );
    }

    if (selectedLevel) {
      filtered = filtered.filter(log => log.level === selectedLevel);
    }

    if (selectedDate) {
      const filterDate = new Date(selectedDate);
      filtered = filtered.filter(log => {
        const logDate = new Date(log.timestamp);
        return logDate.toDateString() === filterDate.toDateString();
      });
    }

    setFilteredLogs(filtered);
  }, [logs, searchTerm, selectedLevel, selectedDate]);

  const getLevelIcon = (level) => {
    switch (level) {
      case 'success':
        return <CheckCircle className="w-5 h-5 text-green-500" />;
      case 'warning':
        return <AlertTriangle className="w-5 h-5 text-orange-500" />;
      case 'error':
        return <XCircle className="w-5 h-5 text-red-500" />;
      default:
        return <Info className="w-5 h-5 text-blue-500" />;
    }
  };

  const getLevelBg = (level) => {
    switch (level) {
      case 'success':
        return 'bg-green-50 border-green-200';
      case 'warning':
        return 'bg-orange-50 border-orange-200';
      case 'error':
        return 'bg-red-50 border-red-200';
      default:
        return 'bg-blue-50 border-blue-200';
    }
  };

  const exportLogs = () => {
    const csvContent = "data:text/csv;charset=utf-8," + 
      "Время,Уровень,Сервис,Сообщение,Детали,Пользователь\n" +
      filteredLogs.map(log => 
        `"${log.timestamp.toLocaleString('ru-RU')}","${log.level}","${log.service}","${log.message}","${log.details}","${log.user}"`
      ).join("\n");

    const encodedUri = encodeURI(csvContent);
    const link = document.createElement("a");
    link.setAttribute("href", encodedUri);
    link.setAttribute("download", `vasdom_logs_${new Date().toISOString().split('T')[0]}.csv`);
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  const refreshLogs = () => {
    setLoading(true);
    // Симуляция обновления
    setTimeout(() => {
      setLoading(false);
    }, 1000);
  };

  const stats = {
    total: logs.length,
    success: logs.filter(log => log.level === 'success').length,
    warning: logs.filter(log => log.level === 'warning').length,
    error: logs.filter(log => log.level === 'error').length,
    info: logs.filter(log => log.level === 'info').length
  };

  if (loading) {
    return (
      <div className="p-8 flex justify-center items-center min-h-96">
        <div className="flex items-center space-x-3">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
          <span className="text-lg font-medium text-gray-600">Загрузка логов...</span>
        </div>
      </div>
    );
  }

  return (
    <div className="p-8 max-w-7xl mx-auto space-y-8">
      {/* Header */}
      <div className="text-center space-y-4 animate-fade-scale">
        <h1 className="text-3xl font-bold gradient-text flex items-center justify-center">
          <FileText className="w-8 h-8 mr-3 text-blue-600" />
          Журнал событий системы
        </h1>
        <p className="text-lg text-gray-600">
          Мониторинг активности и событий VasDom AudioBot
        </p>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-2 md:grid-cols-5 gap-4 animate-slide-up">
        <div className="bg-gradient-to-br from-gray-500 to-gray-600 text-white p-4 rounded-xl shadow-elegant">
          <div className="text-center">
            <div className="text-2xl font-bold">{stats.total}</div>
            <div className="text-gray-200 text-sm">Всего событий</div>
          </div>
        </div>
        
        <div className="bg-gradient-to-br from-green-500 to-green-600 text-white p-4 rounded-xl shadow-elegant">
          <div className="text-center">
            <div className="text-2xl font-bold">{stats.success}</div>
            <div className="text-green-200 text-sm">Успешных</div>
          </div>
        </div>
        
        <div className="bg-gradient-to-br from-blue-500 to-blue-600 text-white p-4 rounded-xl shadow-elegant">
          <div className="text-center">
            <div className="text-2xl font-bold">{stats.info}</div>
            <div className="text-blue-200 text-sm">Информации</div>
          </div>
        </div>
        
        <div className="bg-gradient-to-br from-orange-500 to-orange-600 text-white p-4 rounded-xl shadow-elegant">
          <div className="text-center">
            <div className="text-2xl font-bold">{stats.warning}</div>
            <div className="text-orange-200 text-sm">Предупреждений</div>
          </div>
        </div>
        
        <div className="bg-gradient-to-br from-red-500 to-red-600 text-white p-4 rounded-xl shadow-elegant">
          <div className="text-center">
            <div className="text-2xl font-bold">{stats.error}</div>
            <div className="text-red-200 text-sm">Ошибок</div>
          </div>
        </div>
      </div>

      {/* Filters */}
      <div className="card-modern animate-slide-up">
        <div className="flex flex-col lg:flex-row lg:items-center lg:justify-between space-y-4 lg:space-y-0">
          <div className="flex flex-col md:flex-row md:items-center space-y-4 md:space-y-0 md:space-x-4">
            <div className="relative">
              <Search className="absolute left-3 top-3 w-5 h-5 text-gray-400" />
              <input
                type="text"
                placeholder="Поиск в логах..."
                className="w-full md:w-80 p-3 pl-10 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
              />
            </div>
            
            <select
              className="p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 bg-white"
              value={selectedLevel}
              onChange={(e) => setSelectedLevel(e.target.value)}
            >
              <option value="">Все уровни</option>
              <option value="success">Успех</option>
              <option value="info">Информация</option>
              <option value="warning">Предупреждение</option>
              <option value="error">Ошибка</option>
            </select>
            
            <input
              type="date"
              className="p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 bg-white"
              value={selectedDate}
              onChange={(e) => setSelectedDate(e.target.value)}
            />
          </div>
          
          <div className="flex items-center space-x-3">
            <button
              onClick={refreshLogs}
              className="p-3 bg-blue-500 hover:bg-blue-600 text-white rounded-lg transition-colors"
            >
              <RefreshCw className={`w-5 h-5 ${loading ? 'animate-spin' : ''}`} />
            </button>
            
            <button
              onClick={exportLogs}
              className="px-4 py-3 bg-green-500 hover:bg-green-600 text-white rounded-lg flex items-center space-x-2 transition-colors"
            >
              <Download className="w-4 h-4" />
              <span>Экспорт</span>
            </button>
          </div>
        </div>
        
        <div className="mt-4 text-sm text-gray-600">
          Показано: <span className="font-semibold">{filteredLogs.length}</span> из {logs.length} событий
        </div>
      </div>

      {/* Logs List */}
      <div className="space-y-4">
        {filteredLogs.map((log, index) => (
          <div
            key={log.id}
            className={`card-modern shadow-hover animate-slide-up border-l-4 ${getLevelBg(log.level)}`}
            style={{ animationDelay: `${index * 50}ms` }}
          >
            <div className="flex items-start space-x-4">
              <div className="flex-shrink-0 mt-1">
                {getLevelIcon(log.level)}
              </div>
              
              <div className="flex-1 min-w-0">
                <div className="flex items-center justify-between mb-2">
                  <div className="flex items-center space-x-2">
                    <span className="text-sm font-medium text-gray-900">{log.service}</span>
                    <span className="text-xs bg-gray-100 text-gray-600 px-2 py-1 rounded-full">
                      {log.user}
                    </span>
                  </div>
                  <div className="text-sm text-gray-500">
                    {log.timestamp.toLocaleString('ru-RU')}
                  </div>
                </div>
                
                <h3 className="text-base font-medium text-gray-900 mb-2">
                  {log.message}
                </h3>
                
                <p className="text-sm text-gray-600 bg-gray-50 p-3 rounded-lg">
                  {log.details}
                </p>
              </div>
            </div>
          </div>
        ))}
      </div>

      {/* Empty State */}
      {filteredLogs.length === 0 && (
        <div className="text-center py-12 animate-fade-scale">
          <div className="text-6xl mb-4">📋</div>
          <h2 className="text-2xl font-bold text-gray-900 mb-2">Логи не найдены</h2>
          <p className="text-gray-600">Попробуйте изменить параметры фильтрации</p>
        </div>
      )}
    </div>
  );
};

export default Logs;