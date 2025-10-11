import React, { useState, useEffect } from 'react';
import axios from 'axios';
import {
  Activity,
  CheckCircle,
  XCircle,
  Clock,
  TrendingUp,
  Zap,
  SkipForward,
  RefreshCw
} from 'lucide-react';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL || 'http://localhost:8001';

const AgentDashboard = () => {
  const [stats, setStats] = useState(null);
  const [logs, setLogs] = useState([]);
  const [loading, setLoading] = useState(true);
  const [selectedAgent, setSelectedAgent] = useState(null);

  useEffect(() => {
    loadData();
    const interval = setInterval(loadData, 30000); // Обновление каждые 30 сек
    return () => clearInterval(interval);
  }, [selectedAgent]);

  const loadData = async () => {
    try {
      setLoading(true);
      
      const statsUrl = selectedAgent 
        ? `${BACKEND_URL}/api/agents/dashboard/stats?agent_id=${selectedAgent}`
        : `${BACKEND_URL}/api/agents/dashboard/stats`;
      
      const logsUrl = selectedAgent
        ? `${BACKEND_URL}/api/agents/dashboard/execution-logs?agent_id=${selectedAgent}&limit=20`
        : `${BACKEND_URL}/api/agents/dashboard/execution-logs?limit=20`;
      
      const [statsRes, logsRes] = await Promise.all([
        axios.get(statsUrl),
        axios.get(logsUrl)
      ]);
      
      setStats(statsRes.data);
      setLogs(logsRes.data);
    } catch (error) {
      console.error('Error loading dashboard data:', error);
    } finally {
      setLoading(false);
    }
  };

  const getStatusIcon = (log) => {
    if (log.skipped) return <SkipForward className="w-5 h-5 text-gray-400" />;
    if (log.success) return <CheckCircle className="w-5 h-5 text-green-600" />;
    return <XCircle className="w-5 h-5 text-red-600" />;
  };

  const getStatusColor = (log) => {
    if (log.skipped) return 'bg-gray-50 border-gray-200';
    if (log.success) return 'bg-green-50 border-green-200';
    return 'bg-red-50 border-red-200';
  };

  if (loading && !stats) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-blue-50 to-indigo-50">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-indigo-600 mx-auto"></div>
          <p className="mt-4 text-gray-600">Загрузка dashboard...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 via-white to-purple-50 p-6">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="mb-8 flex items-center justify-between">
          <div>
            <h1 className="text-4xl font-bold text-gray-900 mb-2 flex items-center gap-3">
              <Activity className="w-10 h-10 text-indigo-600" />
              Мониторинг агентов
            </h1>
            <p className="text-gray-600">Реальное время выполнения и статистика</p>
          </div>
          
          <button
            onClick={loadData}
            className="flex items-center gap-2 px-4 py-2 bg-white border border-gray-200 rounded-xl hover:bg-gray-50 transition-colors"
          >
            <RefreshCw className="w-4 h-4" />
            Обновить
          </button>
        </div>

        {/* Stats Cards */}
        {stats && (
          <div className="grid grid-cols-1 md:grid-cols-5 gap-4 mb-8">
            <div className="bg-white rounded-2xl p-6 shadow-lg border border-gray-100">
              <div className="flex items-center justify-between mb-2">
                <Zap className="w-8 h-8 text-blue-600" />
                <span className="text-2xl font-bold text-gray-900">{stats.total_executions}</span>
              </div>
              <p className="text-sm text-gray-600">Всего выполнений</p>
            </div>

            <div className="bg-white rounded-2xl p-6 shadow-lg border border-gray-100">
              <div className="flex items-center justify-between mb-2">
                <CheckCircle className="w-8 h-8 text-green-600" />
                <span className="text-2xl font-bold text-gray-900">{stats.successful_executions}</span>
              </div>
              <p className="text-sm text-gray-600">Успешных</p>
            </div>

            <div className="bg-white rounded-2xl p-6 shadow-lg border border-gray-100">
              <div className="flex items-center justify-between mb-2">
                <XCircle className="w-8 h-8 text-red-600" />
                <span className="text-2xl font-bold text-gray-900">{stats.failed_executions}</span>
              </div>
              <p className="text-sm text-gray-600">Неудачных</p>
            </div>

            <div className="bg-white rounded-2xl p-6 shadow-lg border border-gray-100">
              <div className="flex items-center justify-between mb-2">
                <TrendingUp className="w-8 h-8 text-purple-600" />
                <span className="text-2xl font-bold text-gray-900">{stats.success_rate}%</span>
              </div>
              <p className="text-sm text-gray-600">Успешность</p>
            </div>

            <div className="bg-white rounded-2xl p-6 shadow-lg border border-gray-100">
              <div className="flex items-center justify-between mb-2">
                <Clock className="w-8 h-8 text-cyan-600" />
                <span className="text-2xl font-bold text-gray-900">{stats.last_24h_executions}</span>
              </div>
              <p className="text-sm text-gray-600">За 24 часа</p>
            </div>
          </div>
        )}

        {/* Execution Logs */}
        <div className="bg-white rounded-2xl shadow-lg border border-gray-100 p-6">
          <h2 className="text-2xl font-bold text-gray-900 mb-6">История выполнения</h2>
          
          {logs.length === 0 ? (
            <div className="text-center py-12">
              <Activity className="w-16 h-16 mx-auto mb-4 text-gray-300" />
              <p className="text-gray-600">Нет записей о выполнении</p>
            </div>
          ) : (
            <div className="space-y-3">
              {logs.map((log) => (
                <div
                  key={log.id}
                  className={`p-4 rounded-xl border-2 ${getStatusColor(log)} transition-all hover:shadow-md`}
                >
                  <div className="flex items-start justify-between">
                    <div className="flex items-start gap-3">
                      {getStatusIcon(log)}
                      <div>
                        <h3 className="font-semibold text-gray-900">{log.agent_name}</h3>
                        <p className="text-sm text-gray-600">
                          {new Date(log.executed_at).toLocaleString('ru-RU')}
                        </p>
                        
                        {log.skipped && log.skip_reason && (
                          <p className="text-xs text-gray-500 mt-1">Пропущено: {log.skip_reason}</p>
                        )}
                        
                        {log.error && (
                          <p className="text-xs text-red-600 mt-1">Ошибка: {log.error}</p>
                        )}
                      </div>
                    </div>
                    
                    <div className="text-right">
                      <div className="text-sm font-medium text-gray-700">
                        {log.actions_executed} действий
                      </div>
                      {log.duration_ms && (
                        <div className="text-xs text-gray-500">{log.duration_ms}ms</div>
                      )}
                    </div>
                  </div>
                  
                  {/* Results */}
                  {log.results && log.results.length > 0 && (
                    <div className="mt-3 pt-3 border-t border-gray-200">
                      <div className="space-y-1">
                        {log.results.map((result, idx) => (
                          <div key={idx} className="flex items-center gap-2 text-xs">
                            {result.success ? (
                              <CheckCircle className="w-3 h-3 text-green-600" />
                            ) : (
                              <XCircle className="w-3 h-3 text-red-600" />
                            )}
                            <span className="text-gray-700">{result.action}: {result.message || result.type}</span>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default AgentDashboard;
