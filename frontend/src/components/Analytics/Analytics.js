import React, { useState, useEffect } from 'react';
import analyticsService from '../../services/analyticsService';

const Analytics = () => {
  const [analytics, setAnalytics] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [activeTab, setActiveTab] = useState('overview');

  useEffect(() => {
    loadAnalytics();
  }, []);

  const loadAnalytics = async () => {
    setLoading(true);
    try {
      const data = await analyticsService.getDashboardAnalytics();
      if (data.error) {
        setError(data.error);
      } else {
        setAnalytics(data);
      }
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="p-6 max-w-7xl mx-auto">
        <div className="text-center py-12">
          <div className="animate-spin w-12 h-12 border-4 border-blue-500 border-t-transparent rounded-full mx-auto mb-4"></div>
          <p className="text-gray-600">Загрузка аналитики...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="p-6 max-w-7xl mx-auto">
        <div className="bg-red-50 p-6 rounded-2xl border-l-4 border-red-500">
          <h2 className="text-lg font-bold text-red-800 mb-2">❌ Ошибка загрузки аналитики</h2>
          <p className="text-red-600">{error}</p>
          <button
            onClick={loadAnalytics}
            className="mt-4 bg-red-500 hover:bg-red-600 text-white px-4 py-2 rounded-lg"
          >
            🔄 Повторить
          </button>
        </div>
      </div>
    );
  }

  const renderOverview = () => (
    <div className="space-y-6">
      {/* KPI Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <div className="bg-white p-6 rounded-2xl shadow-lg border-l-4 border-blue-500">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-600">Всего домов</p>
              <p className="text-3xl font-bold text-blue-600">{analyticsService.formatters.number(analytics.overview.total_houses)}</p>
            </div>
            <div className="text-4xl">🏠</div>
          </div>
        </div>

        <div className="bg-white p-6 rounded-2xl shadow-lg border-l-4 border-green-500">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-600">Покрытие графиками</p>
              <p className="text-3xl font-bold text-green-600">{analytics.overview.coverage_rate}%</p>
            </div>
            <div className="text-4xl">📅</div>
          </div>
        </div>

        <div className="bg-white p-6 rounded-2xl shadow-lg border-l-4 border-purple-500">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-600">События уборки</p>
              <p className="text-3xl font-bold text-purple-600">{analyticsService.formatters.number(analytics.overview.total_cleaning_events)}</p>
            </div>
            <div className="text-4xl">🧹</div>
          </div>
        </div>

        <div className="bg-white p-6 rounded-2xl shadow-lg border-l-4 border-orange-500">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-600">Всего квартир</p>
              <p className="text-3xl font-bold text-orange-600">{analyticsService.formatters.number(analytics.overview.total_apartments)}</p>
            </div>
            <div className="text-4xl">🏢</div>
          </div>
        </div>
      </div>

      {/* KPI Insights */}
      <div className="bg-white p-6 rounded-2xl shadow-lg">
        <h3 className="text-xl font-bold text-gray-900 mb-4">🎯 Ключевые показатели</h3>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <div className="text-center p-4 bg-green-50 rounded-lg">
            <div className="text-2xl mb-2">🏆</div>
            <p className="text-sm text-gray-600">Лучшая бригада</p>
            <p className="font-bold text-green-700">{analytics.kpi.best_brigade?.name || 'Не определена'}</p>
            <p className="text-sm text-green-600">{analytics.kpi.best_brigade?.coverage || 0}% покрытие</p>
          </div>

          <div className="text-center p-4 bg-blue-50 rounded-lg">
            <div className="text-2xl mb-2">👥</div>
            <p className="text-sm text-gray-600">Активных бригад</p>
            <p className="font-bold text-blue-700">{analytics.kpi.total_brigades}</p>
            <p className="text-sm text-blue-600">~{analytics.kpi.avg_houses_per_brigade} домов/бригада</p>
          </div>

          <div className="text-center p-4 bg-purple-50 rounded-lg">
            <div className="text-2xl mb-2">🏢</div>
            <p className="text-sm text-gray-600">Управляющих компаний</p>
            <p className="font-bold text-purple-700">{analytics.kpi.companies_count}</p>
            <p className="text-sm text-purple-600">В системе</p>
          </div>
        </div>
      </div>
    </div>
  );

  const renderBrigades = () => (
    <div className="space-y-6">
      <div className="bg-white p-6 rounded-2xl shadow-lg">
        <h3 className="text-xl font-bold text-gray-900 mb-4">👥 Аналитика по бригадам</h3>
        <div className="space-y-4">
          {Object.entries(analytics.brigade_stats).map(([brigade, stats]) => (
            <div key={brigade} className="p-4 border border-gray-200 rounded-lg">
              <div className="flex justify-between items-start mb-3">
                <div>
                  <h4 className="font-bold text-gray-900">{brigade}</h4>
                  <p className="text-sm text-gray-600">{stats.houses} домов в обслуживании</p>
                </div>
                <div className="text-right">
                  <div className={`px-3 py-1 rounded-full text-sm font-medium ${
                    stats.coverage_rate >= 90 ? 'bg-green-100 text-green-800' :
                    stats.coverage_rate >= 70 ? 'bg-yellow-100 text-yellow-800' :
                    'bg-red-100 text-red-800'
                  }`}>
                    {stats.coverage_rate}% покрытие
                  </div>
                </div>
              </div>

              <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                <div className="text-center p-2 bg-gray-50 rounded">
                  <p className="text-xs text-gray-600">Дома</p>
                  <p className="font-bold text-gray-900">{stats.houses}</p>
                </div>
                <div className="text-center p-2 bg-blue-50 rounded">
                  <p className="text-xs text-gray-600">Квартиры</p>
                  <p className="font-bold text-blue-700">{analyticsService.formatters.number(stats.apartments)}</p>
                </div>
                <div className="text-center p-2 bg-green-50 rounded">
                  <p className="text-xs text-gray-600">Запланировано</p>
                  <p className="font-bold text-green-700">{stats.scheduled_houses}</p>
                </div>
                <div className="text-center p-2 bg-red-50 rounded">
                  <p className="text-xs text-gray-600">Проблемные</p>
                  <p className="font-bold text-red-700">{stats.problem_houses}</p>
                </div>
              </div>

              {/* Прогресс-бар покрытия */}
              <div className="mt-3">
                <div className="flex justify-between text-xs text-gray-600 mb-1">
                  <span>Покрытие графиками</span>
                  <span>{stats.coverage_rate}%</span>
                </div>
                <div className="w-full bg-gray-200 rounded-full h-2">
                  <div 
                    className={`h-2 rounded-full ${
                      stats.coverage_rate >= 90 ? 'bg-green-500' :
                      stats.coverage_rate >= 70 ? 'bg-yellow-500' :
                      'bg-red-500'
                    }`}
                    style={{ width: `${stats.coverage_rate}%` }}
                  ></div>
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );

  const renderCalendar = () => (
    <div className="space-y-6">
      <div className="bg-white p-6 rounded-2xl shadow-lg">
        <h3 className="text-xl font-bold text-gray-900 mb-4">📅 Календарь уборок (Сентябрь 2025)</h3>
        
        {/* Статистика календаря */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
          <div className="text-center p-4 bg-blue-50 rounded-lg">
            <div className="text-2xl mb-2">📅</div>
            <p className="text-sm text-gray-600">Всего событий</p>
            <p className="font-bold text-blue-700">{analytics.calendar_events.length}</p>
          </div>
          <div className="text-center p-4 bg-green-50 rounded-lg">
            <div className="text-2xl mb-2">🏠</div>
            <p className="text-sm text-gray-600">Домов с графиком</p>
            <p className="font-bold text-green-700">{analytics.overview.scheduled_houses}</p>
          </div>
          <div className="text-center p-4 bg-purple-50 rounded-lg">
            <div className="text-2xl mb-2">👥</div>
            <p className="text-sm text-gray-600">Участвующих бригад</p>
            <p className="font-bold text-purple-700">{Object.keys(analytics.brigade_stats).filter(b => analytics.brigade_stats[b].scheduled_houses > 0).length}</p>
          </div>
        </div>

        {/* Список событий */}
        <div className="space-y-2 max-h-96 overflow-y-auto">
          {analytics.calendar_events.slice(0, 20).map(event => (
            <div key={event.id} className="flex items-center justify-between p-3 border border-gray-200 rounded-lg hover:bg-gray-50">
              <div className="flex items-center space-x-3">
                <div className="text-sm font-medium text-blue-600">
                  {analyticsService.formatters.date(event.date)}
                </div>
                <div className="text-sm text-gray-600">
                  {event.time}
                </div>
                <div className="text-sm font-medium text-gray-900">
                  {event.address}
                </div>
              </div>
              <div className="flex items-center space-x-2">
                <span className="px-2 py-1 bg-blue-100 text-blue-800 text-xs rounded">
                  {event.brigade?.split(' - ')[0] || 'Бригада'}
                </span>
                <span className="px-2 py-1 bg-gray-100 text-gray-800 text-xs rounded">
                  {event.type}
                </span>
              </div>
            </div>
          ))}
          {analytics.calendar_events.length > 20 && (
            <div className="text-center py-2 text-gray-500 text-sm">
              И еще {analytics.calendar_events.length - 20} событий...
            </div>
          )}
        </div>
      </div>
    </div>
  );

  const renderCompanies = () => (
    <div className="space-y-6">
      <div className="bg-white p-6 rounded-2xl shadow-lg">
        <h3 className="text-xl font-bold text-gray-900 mb-4">🏢 Аналитика по УК</h3>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {Object.entries(analytics.company_stats)
            .sort((a, b) => b[1].houses - a[1].houses)
            .slice(0, 12)
            .map(([company, stats]) => (
            <div key={company} className="p-4 border border-gray-200 rounded-lg">
              <h4 className="font-medium text-gray-900 mb-2 text-sm">
                {company.replace('ООО "', '').replace('"', '')}
              </h4>
              <div className="space-y-2">
                <div className="flex justify-between text-sm">
                  <span className="text-gray-600">Домов:</span>
                  <span className="font-medium">{stats.houses}</span>
                </div>
                <div className="flex justify-between text-sm">
                  <span className="text-gray-600">Квартир:</span>
                  <span className="font-medium">{analyticsService.formatters.number(stats.apartments)}</span>
                </div>
                <div className="flex justify-between text-sm">
                  <span className="text-gray-600">Среднее:</span>
                  <span className="font-medium">{stats.avg_apartments} кв/дом</span>
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );

  return (
    <div className="p-6 max-w-7xl mx-auto">
      {/* Header */}
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900 mb-2">📊 Аналитика и отчеты</h1>
        <p className="text-gray-600">Детальная аналитика по работе бригад и управлению домами</p>
      </div>

      {/* Tabs */}
      <div className="flex space-x-1 mb-8 bg-gray-100 p-1 rounded-lg">
        {[
          { id: 'overview', label: '📊 Обзор', icon: '📊' },
          { id: 'brigades', label: '👥 Бригады', icon: '👥' },
          { id: 'calendar', label: '📅 Календарь', icon: '📅' },
          { id: 'companies', label: '🏢 УК', icon: '🏢' }
        ].map(tab => (
          <button
            key={tab.id}
            onClick={() => setActiveTab(tab.id)}
            className={`flex-1 px-4 py-2 rounded-lg text-sm font-medium transition-all ${
              activeTab === tab.id
                ? 'bg-white text-blue-600 shadow-sm'
                : 'text-gray-600 hover:text-gray-900'
            }`}
          >
            <span className="mr-2">{tab.icon}</span>
            {tab.label}
          </button>
        ))}
      </div>

      {/* Content */}
      {activeTab === 'overview' && renderOverview()}
      {activeTab === 'brigades' && renderBrigades()}
      {activeTab === 'calendar' && renderCalendar()}
      {activeTab === 'companies' && renderCompanies()}

      {/* Refresh Button */}
      <div className="fixed bottom-6 right-6">
        <button
          onClick={loadAnalytics}
          className="bg-blue-500 hover:bg-blue-600 text-white p-3 rounded-full shadow-lg transition-all hover:scale-110"
          title="Обновить аналитику"
        >
          🔄
        </button>
      </div>
    </div>
  );
};

export default Analytics;