import React, { useState, useEffect } from 'react';
import axios from 'axios';
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
  Clock,
  Copy,
  Server,
  Monitor,
  Calendar
} from 'lucide-react';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL || 'http://localhost:8001';

const Logs = () => {
  const [logs, setLogs] = useState([]);
  const [logsText, setLogsText] = useState('');
  const [loading, setLoading] = useState(false);
  const [filter, setFilter] = useState('all');
  const [searchQuery, setSearchQuery] = useState('');
  const [logSource, setLogSource] = useState('render'); // 'render' or 'local'
  const [localLogFile, setLocalLogFile] = useState('backend');
  const [lines, setLines] = useState(100);
  const [timeRange, setTimeRange] = useState('1h'); // '1h', '6h', '24h', 'custom'
  const [customStartTime, setCustomStartTime] = useState('');
  const [customEndTime, setCustomEndTime] = useState('');
  const [copySuccess, setCopySuccess] = useState(false);

  useEffect(() => {
    loadLogs();
    const interval = setInterval(loadLogs, 30000); // Автообновление каждые 30 сек
    return () => clearInterval(interval);
  }, [logSource, localLogFile, lines, timeRange]);

  const loadLogs = async () => {
    try {
      setLoading(true);
      
      if (logSource === 'render') {
        await loadRenderLogs();
      } else {
        await loadLocalLogs();
      }
    } catch (error) {
      console.error('Error loading logs:', error);
    } finally {
      setLoading(false);
    }
  };

  const loadRenderLogs = async () => {
    try {
      const params = { tail: lines };
      
      // Добавляем временные фильтры
      if (timeRange === 'custom' && customStartTime) {
        params.start_time = customStartTime;
      }
      if (timeRange === 'custom' && customEndTime) {
        params.end_time = customEndTime;
      }
      
      const response = await axios.get(`${BACKEND_URL}/api/render-logs/stream`, { params });
      
      if (response.data.success) {
        setLogsText(response.data.logs_text);
        
        // Парсим логи в структурированный формат
        const logLines = response.data.logs_text.split('\n').filter(Boolean);
        const parsedLogs = logLines.map((line, idx) => ({
          id: idx,
          timestamp: extractTimestamp(line),
          level: extractLevel(line),
          message: line,
          raw: line
        }));
        
        setLogs(parsedLogs);
      }
    } catch (error) {
      console.error('Error loading Render logs:', error);
      if (error.response?.status === 500 && error.response?.data?.detail?.includes('RENDER_API_KEY')) {
        // Fallback to local logs если нет Render API key
        setLogSource('local');
        await loadLocalLogs();
      }
    }
  };

  const loadLocalLogs = async () => {
    try {
      const response = await axios.get(`${BACKEND_URL}/api/render-logs/local`, {
        params: { log_file: localLogFile, lines }
      });
      
      if (response.data.success) {
        setLogsText(response.data.logs_text);
        
        // Парсим логи
        const logLines = response.data.logs_text.split('\n').filter(Boolean);
        const parsedLogs = logLines.map((line, idx) => ({
          id: idx,
          timestamp: extractTimestamp(line),
          level: extractLevel(line),
          message: line,
          raw: line
        }));
        
        setLogs(parsedLogs);
      }
    } catch (error) {
      console.error('Error loading local logs:', error);
    }
  };

  const extractTimestamp = (line) => {
    // Попытка извлечь timestamp из строки лога
    const match = line.match(/(\d{4}-\d{2}-\d{2}[T\s]\d{2}:\d{2}:\d{2})/);
    return match ? match[1] : new Date().toISOString().slice(0, 19);
  };

  const extractLevel = (line) => {
    if (line.includes('ERROR') || line.includes('❌')) return 'ERROR';
    if (line.includes('WARNING') || line.includes('⚠️')) return 'WARNING';
    if (line.includes('SUCCESS') || line.includes('✅')) return 'SUCCESS';
    if (line.includes('INFO') || line.includes('ℹ️')) return 'INFO';
    return 'INFO';
  };

  const handleCopyLogs = () => {
    navigator.clipboard.writeText(logsText).then(() => {
      setCopySuccess(true);
      setTimeout(() => setCopySuccess(false), 2000);
    });
  };

  const handleDownloadLogs = () => {
    const blob = new Blob([logsText], { type: 'text/plain' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `logs_${logSource}_${new Date().toISOString().slice(0, 10)}.txt`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  };

  const filteredLogs = logs.filter(log => {
    if (filter !== 'all' && log.level !== filter) return false;
    if (searchQuery && !log.message.toLowerCase().includes(searchQuery.toLowerCase())) return false;
    return true;
  });

  const getLevelIcon = (level) => {
    switch (level) {
      case 'ERROR': return <XCircle className="w-5 h-5 text-red-600" />;
      case 'WARNING': return <AlertCircle className="w-5 h-5 text-yellow-600" />;
      case 'SUCCESS': return <CheckCircle className="w-5 h-5 text-green-600" />;
      default: return <Info className="w-5 h-5 text-blue-600" />;
    }
  };

  const getLevelColor = (level) => {
    switch (level) {
      case 'ERROR': return 'bg-red-50 border-red-200';
      case 'WARNING': return 'bg-yellow-50 border-yellow-200';
      case 'SUCCESS': return 'bg-green-50 border-green-200';
      default: return 'bg-blue-50 border-blue-200';
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-50 via-white to-blue-50 p-6">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-4xl font-bold text-gray-900 mb-2 flex items-center gap-3">
            <FileText className="w-10 h-10 text-indigo-600" />
            Логи системы
          </h1>
          <p className="text-gray-600">Мониторинг логов в реальном времени</p>
        </div>

        {/* Controls */}
        <div className="bg-white rounded-2xl shadow-lg border border-gray-100 p-6 mb-6">
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-4">
            {/* Log Source */}
            <div>
              <label className="block text-sm font-semibold text-gray-700 mb-2">Источник</label>
              <div className="flex gap-2">
                <button
                  onClick={() => setLogSource('render')}
                  className={`flex-1 flex items-center justify-center gap-2 px-4 py-2 rounded-lg border-2 transition-all ${
                    logSource === 'render'
                      ? 'border-indigo-600 bg-indigo-50 text-indigo-700'
                      : 'border-gray-200 hover:border-gray-300'
                  }`}
                >
                  <Server className="w-4 h-4" />
                  Render
                </button>
                <button
                  onClick={() => setLogSource('local')}
                  className={`flex-1 flex items-center justify-center gap-2 px-4 py-2 rounded-lg border-2 transition-all ${
                    logSource === 'local'
                      ? 'border-indigo-600 bg-indigo-50 text-indigo-700'
                      : 'border-gray-200 hover:border-gray-300'
                  }`}
                >
                  <Monitor className="w-4 h-4" />
                  Local
                </button>
              </div>
            </div>

            {/* Local Log File Selection */}
            {logSource === 'local' && (
              <div>
                <label className="block text-sm font-semibold text-gray-700 mb-2">Файл</label>
                <select
                  value={localLogFile}
                  onChange={(e) => setLocalLogFile(e.target.value)}
                  className="w-full px-4 py-2 border border-gray-200 rounded-lg focus:ring-2 focus:ring-indigo-500"
                >
                  <option value="backend">Backend</option>
                  <option value="frontend">Frontend</option>
                </select>
              </div>
            )}

            {/* Lines */}
            <div>
              <label className="block text-sm font-semibold text-gray-700 mb-2">Строк</label>
              <select
                value={lines}
                onChange={(e) => setLines(Number(e.target.value))}
                className="w-full px-4 py-2 border border-gray-200 rounded-lg focus:ring-2 focus:ring-indigo-500"
              >
                <option value="50">50</option>
                <option value="100">100</option>
                <option value="200">200</option>
                <option value="500">500</option>
                <option value="1000">1000</option>
              </select>
            </div>

            {/* Time Range */}
            <div>
              <label className="block text-sm font-semibold text-gray-700 mb-2">Период</label>
              <select
                value={timeRange}
                onChange={(e) => setTimeRange(e.target.value)}
                className="w-full px-4 py-2 border border-gray-200 rounded-lg focus:ring-2 focus:ring-indigo-500"
              >
                <option value="1h">1 час</option>
                <option value="6h">6 часов</option>
                <option value="24h">24 часа</option>
                <option value="custom">Свой период</option>
              </select>
            </div>
          </div>

          {/* Custom Time Range */}
          {timeRange === 'custom' && (
            <div className="grid grid-cols-2 gap-4 mb-4">
              <div>
                <label className="block text-sm font-semibold text-gray-700 mb-2">От</label>
                <input
                  type="datetime-local"
                  value={customStartTime}
                  onChange={(e) => setCustomStartTime(e.target.value)}
                  className="w-full px-4 py-2 border border-gray-200 rounded-lg focus:ring-2 focus:ring-indigo-500"
                />
              </div>
              <div>
                <label className="block text-sm font-semibold text-gray-700 mb-2">До</label>
                <input
                  type="datetime-local"
                  value={customEndTime}
                  onChange={(e) => setCustomEndTime(e.target.value)}
                  className="w-full px-4 py-2 border border-gray-200 rounded-lg focus:ring-2 focus:ring-indigo-500"
                />
              </div>
            </div>
          )}

          {/* Search and Filters */}
          <div className="flex flex-wrap gap-3">
            {/* Search */}
            <div className="flex-1 min-w-64">
              <div className="relative">
                <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-5 h-5 text-gray-400" />
                <input
                  type="text"
                  placeholder="Поиск в логах..."
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  className="w-full pl-10 pr-4 py-2 border border-gray-200 rounded-lg focus:ring-2 focus:ring-indigo-500"
                />
              </div>
            </div>

            {/* Level Filter */}
            <select
              value={filter}
              onChange={(e) => setFilter(e.target.value)}
              className="px-4 py-2 border border-gray-200 rounded-lg focus:ring-2 focus:ring-indigo-500"
            >
              <option value="all">Все уровни</option>
              <option value="ERROR">Ошибки</option>
              <option value="WARNING">Предупреждения</option>
              <option value="SUCCESS">Успех</option>
              <option value="INFO">Информация</option>
            </select>

            {/* Actions */}
            <button
              onClick={loadLogs}
              disabled={loading}
              className="flex items-center gap-2 px-4 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 transition-colors disabled:opacity-50"
            >
              <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
              Обновить
            </button>

            <button
              onClick={handleCopyLogs}
              className={`flex items-center gap-2 px-4 py-2 rounded-lg border-2 transition-all ${
                copySuccess
                  ? 'border-green-600 bg-green-50 text-green-700'
                  : 'border-gray-200 hover:border-gray-300'
              }`}
            >
              {copySuccess ? (
                <>
                  <CheckCircle className="w-4 h-4" />
                  Скопировано!
                </>
              ) : (
                <>
                  <Copy className="w-4 h-4" />
                  Копировать
                </>
              )}
            </button>

            <button
              onClick={handleDownloadLogs}
              className="flex items-center gap-2 px-4 py-2 border border-gray-200 rounded-lg hover:bg-gray-50 transition-colors"
            >
              <Download className="w-4 h-4" />
              Скачать
            </button>
          </div>
        </div>

        {/* Logs Display */}
        <div className="bg-white rounded-2xl shadow-lg border border-gray-100 p-6">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-xl font-bold text-gray-900">
              Логи ({filteredLogs.length})
            </h2>
            <div className="text-sm text-gray-600">
              {logSource === 'render' ? '🌐 Render Production' : '💻 Local Development'}
            </div>
          </div>

          {loading && logs.length === 0 ? (
            <div className="text-center py-12">
              <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-indigo-600 mx-auto mb-4"></div>
              <p className="text-gray-600">Загрузка логов...</p>
            </div>
          ) : filteredLogs.length === 0 ? (
            <div className="text-center py-12">
              <FileText className="w-16 h-16 mx-auto mb-4 text-gray-300" />
              <p className="text-gray-600">Нет логов</p>
            </div>
          ) : (
            <div className="space-y-2 max-h-[600px] overflow-y-auto">
              {filteredLogs.map((log) => (
                <div
                  key={log.id}
                  className={`p-3 rounded-lg border ${getLevelColor(log.level)} font-mono text-xs`}
                >
                  <div className="flex items-start gap-3">
                    {getLevelIcon(log.level)}
                    <div className="flex-1 overflow-x-auto">
                      <div className="flex items-center gap-3 mb-1">
                        <span className="text-gray-500">{log.timestamp}</span>
                        <span className={`px-2 py-0.5 rounded text-xs font-semibold ${
                          log.level === 'ERROR' ? 'bg-red-200 text-red-800' :
                          log.level === 'WARNING' ? 'bg-yellow-200 text-yellow-800' :
                          log.level === 'SUCCESS' ? 'bg-green-200 text-green-800' :
                          'bg-blue-200 text-blue-800'
                        }`}>
                          {log.level}
                        </span>
                      </div>
                      <pre className="text-gray-800 whitespace-pre-wrap break-words">{log.message}</pre>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default Logs;