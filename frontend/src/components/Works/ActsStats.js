import React, { useState, useEffect } from 'react';
import { FileCheck, Calendar, TrendingUp, CheckCircle, XCircle, RefreshCw } from 'lucide-react';

const ActsStats = () => {
  const [selectedMonth, setSelectedMonth] = useState(() => {
    const now = new Date();
    return `${now.getFullYear()}-${String(now.getMonth() + 1).padStart(2, '0')}`;
  });
  
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const loadStats = async () => {
    setLoading(true);
    setError(null);
    
    try {
      const backendUrl = process.env.REACT_APP_BACKEND_URL;
      const response = await fetch(`${backendUrl}/api/houses/acts/stats?month=${selectedMonth}`);
      
      if (!response.ok) {
        throw new Error('Не удалось загрузить статистику');
      }
      
      const data = await response.json();
      setStats(data);
      
    } catch (err) {
      console.error('[ActsStats] Error loading stats:', err);
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadStats();
  }, [selectedMonth]);

  const changeMonth = (delta) => {
    const [year, month] = selectedMonth.split('-').map(Number);
    const date = new Date(year, month - 1);
    date.setMonth(date.getMonth() + delta);
    
    const newMonth = `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, '0')}`;
    setSelectedMonth(newMonth);
  };

  const formatMonth = (monthStr) => {
    const [year, month] = monthStr.split('-');
    const months = [
      'Январь', 'Февраль', 'Март', 'Апрель', 'Май', 'Июнь',
      'Июль', 'Август', 'Сентябрь', 'Октябрь', 'Ноябрь', 'Декабрь'
    ];
    return `${months[parseInt(month) - 1]} ${year}`;
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="flex items-center gap-3 text-gray-600">
          <RefreshCw className="w-6 h-6 animate-spin" />
          <span>Загружаем статистику актов...</span>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-red-50 border border-red-200 rounded-lg p-6 text-center">
        <XCircle className="w-12 h-12 text-red-500 mx-auto mb-3" />
        <p className="text-red-800 font-medium mb-2">Ошибка загрузки</p>
        <p className="text-red-600 text-sm mb-4">{error}</p>
        <button
          onClick={loadStats}
          className="px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 transition-colors"
        >
          Повторить
        </button>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header с выбором месяца */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <FileCheck className="w-8 h-8 text-green-600" />
          <div>
            <h2 className="text-2xl font-bold text-gray-900">Статистика актов</h2>
            <p className="text-sm text-gray-600">Ключевой показатель компании</p>
          </div>
        </div>

        {/* Навигация по месяцам */}
        <div className="flex items-center gap-3">
          <button
            onClick={() => changeMonth(-1)}
            className="p-2 hover:bg-gray-100 rounded-lg transition-colors"
            data-testid="prev-month-btn"
          >
            ←
          </button>
          
          <div className="flex items-center gap-2 px-4 py-2 bg-white border border-gray-200 rounded-lg">
            <Calendar className="w-4 h-4 text-gray-600" />
            <span className="font-medium text-gray-900">{formatMonth(selectedMonth)}</span>
          </div>
          
          <button
            onClick={() => changeMonth(1)}
            className="p-2 hover:bg-gray-100 rounded-lg transition-colors"
            data-testid="next-month-btn"
          >
            →
          </button>

          <button
            onClick={loadStats}
            className="p-2 hover:bg-gray-100 rounded-lg transition-colors ml-2"
            title="Обновить"
          >
            <RefreshCw className="w-4 h-4 text-gray-600" />
          </button>
        </div>
      </div>

      {/* Основная статистика */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
        {/* Всего домов */}
        <div className="bg-white rounded-lg border border-gray-200 p-6">
          <div className="flex items-center gap-3 mb-2">
            <div className="w-10 h-10 bg-blue-100 rounded-lg flex items-center justify-center">
              <FileCheck className="w-5 h-5 text-blue-600" />
            </div>
            <span className="text-sm text-gray-600">Всего домов</span>
          </div>
          <p className="text-3xl font-bold text-gray-900">{stats?.total_houses || 0}</p>
        </div>

        {/* Подписано */}
        <div className="bg-white rounded-lg border border-gray-200 p-6">
          <div className="flex items-center gap-3 mb-2">
            <div className="w-10 h-10 bg-green-100 rounded-lg flex items-center justify-center">
              <CheckCircle className="w-5 h-5 text-green-600" />
            </div>
            <span className="text-sm text-gray-600">Подписано</span>
          </div>
          <p className="text-3xl font-bold text-green-600">{stats?.signed_acts || 0}</p>
        </div>

        {/* Не подписано */}
        <div className="bg-white rounded-lg border border-gray-200 p-6">
          <div className="flex items-center gap-3 mb-2">
            <div className="w-10 h-10 bg-red-100 rounded-lg flex items-center justify-center">
              <XCircle className="w-5 h-5 text-red-600" />
            </div>
            <span className="text-sm text-gray-600">Не подписано</span>
          </div>
          <p className="text-3xl font-bold text-red-600">{stats?.unsigned_acts || 0}</p>
        </div>

        {/* Процент */}
        <div className="bg-white rounded-lg border border-gray-200 p-6">
          <div className="flex items-center gap-3 mb-2">
            <div className="w-10 h-10 bg-purple-100 rounded-lg flex items-center justify-center">
              <TrendingUp className="w-5 h-5 text-purple-600" />
            </div>
            <span className="text-sm text-gray-600">Выполнено</span>
          </div>
          <p className="text-3xl font-bold text-purple-600">{stats?.signed_percentage || 0}%</p>
        </div>
      </div>

      {/* Прогресс бар */}
      <div className="bg-white rounded-lg border border-gray-200 p-6">
        <div className="flex items-center justify-between mb-3">
          <span className="text-sm font-medium text-gray-700">Прогресс подписания актов</span>
          <span className="text-sm text-gray-600">
            {stats?.signed_acts || 0} из {stats?.total_houses || 0}
          </span>
        </div>
        <div className="w-full bg-gray-200 rounded-full h-4">
          <div
            className="bg-green-600 h-4 rounded-full transition-all duration-500"
            style={{ width: `${stats?.signed_percentage || 0}%` }}
          />
        </div>
      </div>

      {/* Список подписанных актов */}
      {stats?.acts && stats.acts.length > 0 && (
        <div className="bg-white rounded-lg border border-gray-200">
          <div className="p-6 border-b border-gray-200">
            <h3 className="text-lg font-semibold text-gray-900">Подписанные акты ({stats.acts.length})</h3>
          </div>
          <div className="divide-y divide-gray-200 max-h-96 overflow-y-auto">
            {stats.acts.map((act, index) => (
              <div key={index} className="p-4 hover:bg-gray-50 transition-colors">
                <div className="flex items-start justify-between">
                  <div className="flex-1">
                    <p className="font-medium text-gray-900">{act.house_address}</p>
                    <div className="flex items-center gap-4 mt-2 text-sm text-gray-600">
                      <span className="flex items-center gap-1">
                        <Calendar className="w-4 h-4" />
                        {act.signed_date}
                      </span>
                      <span>Уборок: {act.cleaning_count}</span>
                      {act.signed_by && <span>Подписал: {act.signed_by}</span>}
                    </div>
                  </div>
                  <div className="flex items-center gap-1">
                    <CheckCircle className="w-5 h-5 text-green-600" />
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Пустое состояние */}
      {stats && stats.signed_acts === 0 && (
        <div className="bg-gray-50 rounded-lg border border-gray-200 p-12 text-center">
          <FileCheck className="w-16 h-16 text-gray-400 mx-auto mb-4" />
          <h3 className="text-lg font-medium text-gray-900 mb-2">Нет подписанных актов</h3>
          <p className="text-gray-600">
            За {formatMonth(selectedMonth)} ещё не подписан ни один акт.<br />
            Подписывайте акты через кнопку "Акт подписан" в карточках домов.
          </p>
        </div>
      )}
    </div>
  );
};

export default ActsStats;
