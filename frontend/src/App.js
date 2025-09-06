import React, { useState, useEffect } from 'react';
import './App.css';
import axios from 'axios';
import VoiceAssistant from './VoiceAssistant';
import LiveVoiceChat from './LiveVoiceChat';
import OnboardingChat from './OnboardingChat';
import MeetingRecorder from './MeetingRecorder';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

// Navigation Component
const Navigation = ({ activeTab, setActiveTab }) => {
  const tabs = [
    { id: 'dashboard', name: '📊 Дашборд', icon: '📊' },
    { id: 'employees', name: '👥 Сотрудники', icon: '👥' },
    { id: 'analytics', name: '📈 Аналитика', icon: '📈' },
    { id: 'smart-planning', name: '🧠 Smart Планирование', icon: '🧠' },
    { id: 'client-management', name: '🤝 Клиенты', icon: '🤝' },
    { id: 'live-voice', name: '📞 Live Голос', icon: '📞' },
    { id: 'meetings', name: '🎙️ Планерка', icon: '🎙️' },
    { id: 'notifications', name: '📢 Уведомления', icon: '📢' },
    { id: 'telegram-info', name: '📱 Telegram Бот', icon: '📱' }
  ];

  return (
    <nav className="bg-white shadow-lg mb-8">
      <div className="container mx-auto px-4">
        <div className="flex space-x-8">
          {tabs.map((tab) => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={`py-4 px-6 border-b-2 font-medium text-sm transition-colors ${
                activeTab === tab.id
                  ? 'border-blue-500 text-blue-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
              }`}
            >
              <span className="mr-2">{tab.icon}</span>
              {tab.name}
            </button>
          ))}
        </div>
      </div>
    </nav>
  );
};

// Main Dashboard Component
const Dashboard = () => {
  const [dashboardData, setDashboardData] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchDashboardData();
  }, []);

  const fetchDashboardData = async () => {
    try {
      const response = await axios.get(`${API}/dashboard`);
      setDashboardData(response.data);
    } catch (error) {
      console.error('Error fetching dashboard data:', error);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-96">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500"></div>
      </div>
    );
  }

  return (
    <div className="space-y-8">
      {/* Metrics Cards */}
      {dashboardData && (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          <MetricCard
            title="Всего сотрудников"
            value={dashboardData.metrics.total_employees}
            icon="👥"
            color="bg-blue-500"
            change="+5 за месяц"
          />
          <MetricCard
            title="Активные сотрудники"
            value={dashboardData.metrics.active_employees}
            icon="✅"
            color="bg-green-500"
            change="98% активность"
          />
          <MetricCard
            title="Дома в Калуге"
            value={dashboardData.metrics.kaluga_houses}
            icon="🏠"
            color="bg-purple-500"
            change="500 домов"
          />
          <MetricCard
            title="Дома в Кемерово"
            value={dashboardData.metrics.kemerovo_houses}
            icon="🏘️"
            color="bg-orange-500"
            change="100 домов"
          />
        </div>
      )}

      {/* Recent Activities and AI Insights */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        <div className="bg-white rounded-lg shadow-lg p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-4 flex items-center">
            📊 Последние активности
          </h3>
          <div className="space-y-3">
            {dashboardData?.recent_activities.map((activity, index) => (
              <div key={index} className="flex items-start space-x-3">
                <div className="flex-shrink-0 w-2 h-2 bg-blue-500 rounded-full mt-2"></div>
                <div>
                  <p className="text-sm text-gray-900">{activity.message}</p>
                  <p className="text-xs text-gray-500">{activity.time}</p>
                </div>
              </div>
            ))}
          </div>
        </div>

        <div className="bg-white rounded-lg shadow-lg p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-4 flex items-center">
            🧠 AI Рекомендации
          </h3>
          <div className="space-y-3">
            {dashboardData?.ai_insights.map((insight, index) => (
              <div key={index} className="p-3 bg-blue-50 rounded-lg">
                <p className="text-sm text-blue-900">{insight}</p>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
};

// Employees Component
const Employees = () => {
  const [employees, setEmployees] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showAddForm, setShowAddForm] = useState(false);

  useEffect(() => {
    fetchEmployees();
  }, []);

  const fetchEmployees = async () => {
    try {
      const response = await axios.get(`${API}/employees`);
      setEmployees(response.data);
    } catch (error) {
      console.error('Error fetching employees:', error);
    } finally {
      setLoading(false);
    }
  };

  const positionNames = {
    'general_director': 'Генеральный директор',
    'director': 'Директор',
    'accountant': 'Бухгалтер',
    'hr_manager': 'HR менеджер',
    'cleaning_manager': 'Менеджер по клинингу',
    'construction_manager': 'Менеджер по стройке',
    'architect': 'Архитектор-сметчик',
    'cleaner': 'Уборщица',
    'other': 'Другое'
  };

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <h2 className="text-2xl font-bold text-gray-900">Управление сотрудниками</h2>
        <button
          onClick={() => setShowAddForm(true)}
          className="bg-blue-500 text-white px-4 py-2 rounded-lg hover:bg-blue-600"
        >
          + Добавить сотрудника
        </button>
      </div>

      {loading ? (
        <div className="flex justify-center py-8">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-500"></div>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {employees.length === 0 ? (
            <div className="col-span-full text-center py-8">
              <p className="text-gray-500">Сотрудники не найдены. Добавьте первого сотрудника!</p>
            </div>
          ) : (
            employees.map((employee) => (
              <div key={employee.id} className="bg-white rounded-lg shadow-lg p-6">
                <div className="flex items-center space-x-3 mb-4">
                  <div className="w-10 h-10 bg-blue-500 rounded-full flex items-center justify-center text-white font-bold">
                    {employee.name.charAt(0)}
                  </div>
                  <div>
                    <h3 className="font-semibold text-gray-900">{employee.name}</h3>
                    <p className="text-sm text-gray-600">{positionNames[employee.position] || employee.position}</p>
                  </div>
                </div>
                <div className="space-y-2 text-sm">
                  <p><span className="font-medium">Город:</span> {employee.city}</p>
                  <p><span className="font-medium">Email:</span> {employee.email || 'Не указан'}</p>
                  <p><span className="font-medium">Телефон:</span> {employee.phone || 'Не указан'}</p>
                  <p><span className="font-medium">Дата найма:</span> {new Date(employee.hire_date).toLocaleDateString('ru-RU')}</p>
                </div>
                <div className="mt-4 flex space-x-2">
                  <button className="flex-1 bg-gray-100 text-gray-700 py-2 px-3 rounded text-sm hover:bg-gray-200">
                    Редактировать
                  </button>
                  <button className="bg-red-100 text-red-700 py-2 px-3 rounded text-sm hover:bg-red-200">
                    Удалить
                  </button>
                </div>
              </div>
            ))
          )}
        </div>
      )}
    </div>
  );
};

// Enhanced Analytics Component with CYCLE 1 features
const Analytics = () => {
  const [forecast, setForecast] = useState(null);
  const [insights, setInsights] = useState([]);
  const [metrics, setMetrics] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchAnalyticsData();
  }, []);

  const fetchAnalyticsData = async () => {
    try {
      setLoading(true);
      
      // Fetch all analytics data
      const [forecastRes, insightsRes, metricsRes] = await Promise.all([
        axios.get(`${API}/analytics/forecast?months=3`),
        axios.get(`${API}/analytics/insights?force_refresh=true`),
        axios.get(`${API}/analytics/performance`)
      ]);
      
      setForecast(forecastRes.data);
      setInsights(insightsRes.data.insights || []);
      setMetrics(metricsRes.data);
      
    } catch (error) {
      console.error('Error fetching analytics:', error);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-96">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500"></div>
        <span className="ml-3 text-gray-600">Загружаем аналитику...</span>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <h2 className="text-2xl font-bold text-gray-900">📈 Аналитика и прогнозы</h2>
        <button
          onClick={fetchAnalyticsData}
          className="bg-purple-500 text-white px-4 py-2 rounded-lg hover:bg-purple-600 transition-colors"
        >
          🔄 Обновить данные
        </button>
      </div>
      
      {/* Financial Forecast */}
      {forecast && forecast.success && (
        <div className="bg-gradient-to-br from-green-50 to-blue-50 rounded-lg shadow-lg p-6">
          <h3 className="text-lg font-semibold mb-4 text-green-800">💰 Финансовый прогноз (3 месяца)</h3>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            {forecast.forecasts.map((f, index) => (
              <div key={index} className="bg-white rounded-lg p-4 shadow">
                <h4 className="font-medium text-gray-700">{f.period}</h4>
                <p className="text-2xl font-bold text-green-600">
                  {f.predicted_revenue.toLocaleString('ru-RU')} ₽
                </p>
                <p className="text-sm text-gray-500">
                  Уверенность: {(f.confidence_score * 100).toFixed(0)}%
                </p>
                <div className="mt-2">
                  <div className="w-full bg-gray-200 rounded-full h-1">
                    <div 
                      className="bg-green-500 h-1 rounded-full transition-all"
                      style={{width: `${f.confidence_score * 100}%`}}
                    />
                  </div>
                </div>
              </div>
            ))}
          </div>
          
          {forecast.historical_data && (
            <div className="mt-4 text-sm text-gray-600 bg-white rounded p-3">
              <p><strong>Базовые данные:</strong> {forecast.historical_data.total_deals} сделок, 
              средняя выручка {forecast.historical_data.avg_monthly_revenue?.toLocaleString('ru-RU') || 0} ₽/месяц</p>
            </div>
          )}
        </div>
      )}

      {/* Performance Metrics */}
      {metrics && (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <div className="bg-white rounded-lg shadow-lg p-6">
            <h3 className="text-lg font-semibold mb-4">📊 Метрики продаж</h3>
            <div className="space-y-3">
              <div className="flex justify-between">
                <span>Всего сделок:</span>
                <span className="font-semibold">{metrics.sales_metrics?.total_deals || 0}</span>
              </div>
              <div className="flex justify-between">
                <span>Конверсия:</span>
                <span className="font-semibold text-blue-600">{metrics.sales_metrics?.conversion_rate || 0}%</span>
              </div>
              <div className="flex justify-between">
                <span>Средняя сделка:</span>
                <span className="font-semibold">{(metrics.sales_metrics?.avg_deal_size || 0).toLocaleString('ru-RU')} ₽</span>
              </div>
              <div className="flex justify-between border-t pt-2">
                <span>Общий объем:</span>
                <span className="font-semibold text-green-600">
                  {(metrics.sales_metrics?.total_pipeline_value || 0).toLocaleString('ru-RU')} ₽
                </span>
              </div>
            </div>
          </div>

          <div className="bg-white rounded-lg shadow-lg p-6">
            <h3 className="text-lg font-semibold mb-4">🏢 Операционные метрики</h3>
            <div className="space-y-3">
              <div className="flex justify-between">
                <span>Команда Калуга:</span>
                <span className="font-semibold">{metrics.operational_metrics?.kaluga_team || 0} чел</span>
              </div>
              <div className="flex justify-between">
                <span>Команда Кемерово:</span>
                <span className="font-semibold">{metrics.operational_metrics?.kemerovo_team || 0} чел</span>
              </div>
              <div className="flex justify-between">
                <span>Объекты:</span>
                <span className="font-semibold">{metrics.operational_metrics?.houses_managed || 600} домов</span>
              </div>
              <div className="flex justify-between border-t pt-2">
                <span>Время отклика:</span>
                <span className="font-semibold text-blue-600">{metrics.operational_metrics?.avg_response_time_hours || 2} часа</span>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* AI Business Insights */}
      {insights.length > 0 && (
        <div className="bg-white rounded-lg shadow-lg p-6">
          <h3 className="text-lg font-semibold mb-4 flex items-center">
            🧠 AI-инсайты для бизнеса
            <span className="ml-2 text-sm bg-purple-100 text-purple-700 px-2 py-1 rounded-full">
              {insights.length} рекомендаций
            </span>
          </h3>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {insights.map((insight, index) => (
              <div key={index} className="border-l-4 border-purple-500 bg-purple-50 p-4 rounded-r-lg">
                <div className="flex items-start space-x-2">
                  <span className="text-purple-600 font-bold text-sm uppercase tracking-wide">
                    {insight.category}
                  </span>
                  <span className="text-xs bg-purple-200 text-purple-700 px-2 py-1 rounded-full">
                    {(insight.confidence_score * 100).toFixed(0)}%
                  </span>
                </div>
                <p className="text-gray-800 mt-2 text-sm leading-relaxed">
                  {insight.insight}
                </p>
                <div className="mt-2 text-xs text-gray-500">
                  Источники: {insight.data_sources?.join(', ') || 'AI анализ'}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Growth Metrics */}
      {metrics?.growth_metrics && (
        <div className="bg-gradient-to-br from-blue-50 to-indigo-50 rounded-lg shadow-lg p-6">
          <h3 className="text-lg font-semibold mb-4">📈 Показатели роста</h3>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <div className="text-center">
              <p className="text-2xl font-bold text-blue-600">{metrics.growth_metrics.quarterly_growth}</p>
              <p className="text-sm text-gray-600">Рост за квартал</p>
            </div>
            <div className="text-center">
              <p className="text-2xl font-bold text-green-600">{metrics.growth_metrics.revenue_target_achievement}%</p>
              <p className="text-sm text-gray-600">Выполнение плана</p>
            </div>
            <div className="text-center">
              <p className="text-2xl font-bold text-purple-600">{metrics.growth_metrics.new_clients_monthly}</p>
              <p className="text-sm text-gray-600">Новых клиентов/мес</p>
            </div>
            <div className="text-center">
              <p className="text-2xl font-bold text-orange-600">{metrics.client_metrics?.client_satisfaction || 4.8}</p>
              <p className="text-sm text-gray-600">Рейтинг клиентов</p>
            </div>
          </div>
        </div>
      )}

      {/* Classic Analytics for comparison */}
      <div className="bg-white rounded-lg shadow-lg p-6">
        <h3 className="text-lg font-semibold mb-4">📊 Производительность по городам</h3>
        <div className="space-y-4">
          <div className="flex justify-between items-center">
            <span>Калуга</span>
            <div className="flex items-center space-x-2">
              <div className="w-32 bg-gray-200 rounded-full h-2">
                <div className="bg-blue-500 h-2 rounded-full" style={{width: '85%'}}></div>
              </div>
              <span className="text-sm">85%</span>
            </div>
          </div>
          <div className="flex justify-between items-center">
            <span>Кемерово</span>
            <div className="flex items-center space-x-2">
              <div className="w-32 bg-gray-200 rounded-full h-2">
                <div className="bg-green-500 h-2 rounded-full" style={{width: '92%'}}></div>
              </div>
              <span className="text-sm">92%</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

// Metric Card Component
const MetricCard = ({ title, value, icon, color, change }) => {
  return (
    <div className="bg-white rounded-lg shadow-lg p-6 hover:shadow-xl transition-shadow">
      <div className="flex items-center justify-between">
        <div>
          <p className="text-sm font-medium text-gray-600">{title}</p>
          <p className="text-3xl font-bold text-gray-900 mt-1">{value}</p>
          {change && <p className="text-xs text-gray-500 mt-1">{change}</p>}
        </div>
        <div className={`w-12 h-12 ${color} rounded-lg flex items-center justify-center text-white text-2xl`}>
          {icon}
        </div>
      </div>
    </div>
  );
};

// AI Chat Component removed - now all AI communication happens through Telegram

// Smart Planning Component
const SmartPlanning = () => {
  const [routes, setRoutes] = useState(null);
  const [predictions, setPredictions] = useState([]);
  const [schedule, setSchedule] = useState(null);
  const [loading, setLoading] = useState(true);
  const [selectedCity, setSelectedCity] = useState('Калуга');

  useEffect(() => {
    fetchPlanningData();
  }, [selectedCity]);

  const fetchPlanningData = async () => {
    try {
      setLoading(true);
      
      const [routesRes, predictionsRes, scheduleRes] = await Promise.all([
        axios.get(`${API}/planning/routes/${selectedCity}`),
        axios.get(`${API}/planning/maintenance-predictions`),
        axios.get(`${API}/planning/weekly-schedule/${selectedCity}`)
      ]);
      
      setRoutes(routesRes.data);
      setPredictions(predictionsRes.data.predictions || []);
      setSchedule(scheduleRes.data);
      
    } catch (error) {
      console.error('Error fetching planning data:', error);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-96">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500"></div>
        <span className="ml-3 text-gray-600">Оптимизируем маршруты...</span>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <h2 className="text-2xl font-bold text-gray-900">🧠 Smart Планирование</h2>
        <div className="flex space-x-4">
          <select
            value={selectedCity}
            onChange={(e) => setSelectedCity(e.target.value)}
            className="border border-gray-300 rounded-lg px-4 py-2"
          >
            <option value="Калуга">Калуга</option>
            <option value="Кемерово">Кемерово</option>
          </select>
          <button
            onClick={fetchPlanningData}
            className="bg-blue-500 text-white px-4 py-2 rounded-lg hover:bg-blue-600"
          >
            🔄 Обновить
          </button>
        </div>
      </div>

      {/* Optimized Routes */}
      {routes && routes.success && (
        <div className="bg-white rounded-lg shadow-lg p-6">
          <h3 className="text-lg font-semibold mb-4">🚗 Оптимизированные маршруты - {selectedCity}</h3>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {routes.routes.map((route, index) => (
              <div key={index} className="border rounded-lg p-4 bg-gray-50">
                <h4 className="font-medium text-blue-600">{route.route_id}</h4>
                <p className="text-sm text-gray-600 mt-1">
                  Домов: {route.houses.length} | Время: {route.estimated_time}ч
                </p>
                <p className="text-sm text-gray-600">
                  Команда: {route.team_size} чел
                </p>
                <div className="mt-2">
                  <p className="text-xs text-gray-500">Первые дома:</p>
                  {route.houses.slice(0, 3).map((house, i) => (
                    <p key={i} className="text-xs text-gray-700 truncate">• {house}</p>
                  ))}
                </div>
              </div>
            ))}
          </div>
          <div className="mt-4 p-4 bg-blue-50 rounded-lg">
            <p className="text-sm">
              <strong>Итого:</strong> {routes.total_houses} домов, {routes.teams_needed} команд, 
              ~{routes.routes.reduce((sum, r) => sum + r.estimated_time, 0).toFixed(1)} часов работы
            </p>
          </div>
        </div>
      )}

      {/* Maintenance Predictions */}
      {predictions.length > 0 && (
        <div className="bg-white rounded-lg shadow-lg p-6">
          <h3 className="text-lg font-semibold mb-4">🔮 Предиктивное обслуживание</h3>
          <div className="space-y-3">
            {predictions.slice(0, 10).map((prediction, index) => (
              <div key={index} className={`p-3 rounded-lg border-l-4 ${
                prediction.priority === 'high' ? 'border-red-500 bg-red-50' :
                prediction.priority === 'medium' ? 'border-yellow-500 bg-yellow-50' :
                'border-green-500 bg-green-50'
              }`}>
                <div className="flex justify-between items-start">
                  <div>
                    <h4 className="font-medium">{prediction.house}</h4>
                    <p className="text-sm text-gray-600">{prediction.recommended_action}</p>
                  </div>
                  <div className="text-right">
                    <span className={`px-2 py-1 rounded-full text-xs ${
                      prediction.priority === 'high' ? 'bg-red-200 text-red-800' :
                      prediction.priority === 'medium' ? 'bg-yellow-200 text-yellow-800' :
                      'bg-green-200 text-green-800'
                    }`}>
                      {prediction.priority}
                    </span>
                    <p className="text-xs text-gray-500 mt-1">
                      {prediction.predicted_maintenance_date}
                    </p>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Weekly Schedule */}
      {schedule && schedule.success && (
        <div className="bg-white rounded-lg shadow-lg p-6">
          <h3 className="text-lg font-semibold mb-4">📅 Недельное расписание - {selectedCity}</h3>
          <div className="space-y-3">
            {Object.entries(schedule.schedule).map(([date, daySchedule]) => (
              <div key={date} className="border rounded-lg p-4">
                <div className="flex justify-between items-center mb-2">
                  <h4 className="font-medium">{daySchedule.date} ({daySchedule.day})</h4>
                  <span className="text-sm text-gray-500">
                    {daySchedule.total_estimated_time.toFixed(1)} часов
                  </span>
                </div>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div>
                    <p className="text-sm font-medium text-blue-600">Плановая уборка:</p>
                    <p className="text-sm">{daySchedule.route.houses.length} домов</p>
                    <p className="text-xs text-gray-600">
                      {daySchedule.route.houses.slice(0, 2).join(', ')}
                      {daySchedule.route.houses.length > 2 && '...'}
                    </p>
                  </div>
                  <div>
                    <p className="text-sm font-medium text-red-600">Срочные работы:</p>
                    <p className="text-sm">{daySchedule.urgent_maintenance.length} объектов</p>
                    {daySchedule.urgent_maintenance.length > 0 && (
                      <p className="text-xs text-gray-600">
                        {daySchedule.urgent_maintenance.slice(0, 1).join(', ')}
                      </p>
                    )}
                  </div>
                </div>
                <p className="text-xs text-gray-500 mt-2">
                  {daySchedule.weather_consideration}
                </p>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};

// Client Management Component
const ClientManagement = () => {
  const [satisfactionData, setSatisfactionData] = useState(null);
  const [houses, setHouses] = useState([]);
  const [loading, setLoading] = useState(true);
  const [selectedHouse, setSelectedHouse] = useState('');

  useEffect(() => {
    fetchClientData();
  }, []);

  const fetchClientData = async () => {
    try {
      setLoading(true);
      
      const [satisfactionRes, housesRes] = await Promise.all([
        axios.get(`${API}/clients/satisfaction-report`),
        axios.get(`${API}/bitrix24/cleaning-houses`)
      ]);
      
      setSatisfactionData(satisfactionRes.data);
      setHouses(housesRes.data.houses || []);
      
    } catch (error) {
      console.error('Error fetching client data:', error);
    } finally {
      setLoading(false);
    }
  };

  const sendNotification = async (notificationType) => {
    if (!selectedHouse) {
      alert('Выберите дом для отправки уведомления');
      return;
    }

    try {
      const response = await axios.post(`${API}/clients/send-notification`, {
        house_id: selectedHouse,
        notification_type: notificationType
      });

      if (response.data.success) {
        alert(`✅ Уведомление "${notificationType}" отправлено!`);
      } else {
        alert(`❌ Ошибка: ${response.data.error}`);
      }
    } catch (error) {
      alert('❌ Ошибка отправки уведомления');
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-96">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-green-500"></div>
        <span className="ml-3 text-gray-600">Загружаем данные клиентов...</span>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <h2 className="text-2xl font-bold text-gray-900">🤝 Управление клиентами</h2>

      {/* Client Satisfaction */}
      {satisfactionData && satisfactionData.success && (
        <div className="bg-white rounded-lg shadow-lg p-6">
          <h3 className="text-lg font-semibold mb-4">📊 Удовлетворенность клиентов</h3>
          
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
            <div className="text-center p-4 bg-blue-50 rounded-lg">
              <p className="text-2xl font-bold text-blue-600">
                {satisfactionData.satisfaction_data.average_rating.toFixed(1)}
              </p>
              <p className="text-sm text-gray-600">Средняя оценка</p>
            </div>
            <div className="text-center p-4 bg-green-50 rounded-lg">
              <p className="text-2xl font-bold text-green-600">
                {satisfactionData.satisfaction_data.nps_score}
              </p>
              <p className="text-sm text-gray-600">NPS Score</p>
            </div>
            <div className="text-center p-4 bg-purple-50 rounded-lg">
              <p className="text-2xl font-bold text-purple-600">
                {satisfactionData.satisfaction_data.total_surveys}
              </p>
              <p className="text-sm text-gray-600">Опросов</p>
            </div>
            <div className="text-center p-4 bg-orange-50 rounded-lg">
              <p className="text-2xl font-bold text-orange-600">
                {(satisfactionData.satisfaction_data.response_rate * 100).toFixed(0)}%
              </p>
              <p className="text-sm text-gray-600">Отклик</p>
            </div>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div>
              <h4 className="font-medium mb-3">Оценки по категориям:</h4>
              {Object.entries(satisfactionData.satisfaction_data.categories).map(([category, rating]) => (
                <div key={category} className="flex justify-between items-center mb-2">
                  <span className="text-sm capitalize">{category}</span>
                  <div className="flex items-center">
                    <div className="w-20 bg-gray-200 rounded-full h-2 mr-2">
                      <div 
                        className="bg-blue-500 h-2 rounded-full" 
                        style={{width: `${(rating/5)*100}%`}}
                      />
                    </div>
                    <span className="text-sm font-medium">{rating.toFixed(1)}</span>
                  </div>
                </div>
              ))}
            </div>
            
            <div>
              <h4 className="font-medium mb-3">Последние отзывы:</h4>
              <div className="space-y-2">
                {satisfactionData.satisfaction_data.recent_feedback.map((feedback, index) => (
                  <div key={index} className="p-3 bg-gray-50 rounded-lg">
                    <div className="flex justify-between items-start mb-1">
                      <div className="flex">
                        {[...Array(feedback.rating)].map((_, i) => (
                          <span key={i} className="text-yellow-400">⭐</span>
                        ))}
                      </div>
                      <span className="text-xs text-gray-500">{feedback.date}</span>
                    </div>
                    <p className="text-sm text-gray-700">{feedback.comment}</p>
                  </div>
                ))}
              </div>
            </div>
          </div>

          <div className="mt-6 p-4 bg-blue-50 rounded-lg">
            <h4 className="font-medium text-blue-800 mb-2">🤖 AI Рекомендации:</h4>
            <div className="text-sm text-blue-700 whitespace-pre-line">
              {satisfactionData.ai_insights}
            </div>
          </div>
        </div>
      )}

      {/* Client Notifications */}
      <div className="bg-white rounded-lg shadow-lg p-6">
        <h3 className="text-lg font-semibold mb-4">📬 Уведомления клиентам</h3>
        
        <div className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Выберите объект:
            </label>
            <select
              value={selectedHouse}
              onChange={(e) => setSelectedHouse(e.target.value)}
              className="w-full border border-gray-300 rounded-lg px-4 py-2"
            >
              <option value="">-- Выберите дом --</option>
              {houses.map((house) => (
                <option key={house.ID} value={house.ID}>
                  {house.TITLE}
                </option>
              ))}
            </select>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <button
              onClick={() => sendNotification('cleaning_scheduled')}
              disabled={!selectedHouse}
              className="bg-blue-500 text-white px-4 py-2 rounded-lg hover:bg-blue-600 disabled:opacity-50"
            >
              📅 Уборка запланирована
            </button>
            <button
              onClick={() => sendNotification('cleaning_completed')}
              disabled={!selectedHouse}
              className="bg-green-500 text-white px-4 py-2 rounded-lg hover:bg-green-600 disabled:opacity-50"
            >
              ✅ Уборка завершена
            </button>
            <button
              onClick={() => sendNotification('quality_check')}
              disabled={!selectedHouse}
              className="bg-purple-500 text-white px-4 py-2 rounded-lg hover:bg-purple-600 disabled:opacity-50"
            >
              ⭐ Оценить качество
            </button>
          </div>
        </div>

        <div className="mt-6 p-4 bg-gray-50 rounded-lg">
          <h4 className="font-medium mb-2">📱 Каналы уведомлений:</h4>
          <div className="grid grid-cols-3 gap-4 text-center">
            <div className="p-2">
              <span className="text-2xl">📧</span>
              <p className="text-xs">Email</p>
            </div>
            <div className="p-2">
              <span className="text-2xl">💬</span>
              <p className="text-xs">SMS</p>
            </div>
            <div className="p-2">
              <span className="text-2xl">📞</span>
              <p className="text-xs">Telegram</p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

// Telegram Bot Information Component
const TelegramInfo = () => {
  return (
    <div className="space-y-6">
      <h2 className="text-2xl font-bold text-gray-900">📱 Telegram Бот МАКС</h2>
      
      {/* Bot Information */}
      <div className="bg-gradient-to-br from-blue-50 to-indigo-50 rounded-lg shadow-lg p-6">
        <div className="flex items-center space-x-4 mb-4">
          <div className="bg-blue-500 text-white p-3 rounded-full">
            <span className="text-2xl">🤖</span>
          </div>
          <div>
            <h3 className="text-xl font-bold text-blue-800">AI-Директор МАКС</h3>
            <p className="text-blue-600">@aitest123432_bot</p>
          </div>
        </div>
        
        <div className="bg-white rounded-lg p-4 mb-4">
          <h4 className="font-semibold text-gray-800 mb-2">🎯 Основной интерфейс управления</h4>
          <p className="text-gray-700">
            Все общение с AI теперь происходит через Telegram. МАКС работает как ваш личный AI-директор:
            проактивно анализирует бизнес, предупреждает о проблемах и дает конкретные рекомендации.
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div className="bg-white rounded-lg p-4">
            <h4 className="font-medium text-gray-800 mb-2">👋 Знакомство</h4>
            <ul className="text-sm text-gray-600 space-y-1">
              <li>• Автоматическое знакомство при первом запуске</li>
              <li>• Персонализация под вашу роль и задачи</li>
              <li>• Настройка уведомлений и приоритетов</li>
            </ul>
          </div>
          
          <div className="bg-white rounded-lg p-4">
            <h4 className="font-medium text-gray-800 mb-2">📊 Проактивная аналитика</h4>
            <ul className="text-sm text-gray-600 space-y-1">
              <li>• Ежедневные сводки для руководства</li>
              <li>• Критические алерты по KPI</li>
              <li>• Рекомендации по оптимизации</li>
            </ul>
          </div>
          
          <div className="bg-white rounded-lg p-4">
            <h4 className="font-medium text-gray-800 mb-2">🧠 Память и контекст</h4>
            <ul className="text-sm text-gray-600 space-y-1">
              <li>• Помнит все разговоры и решения</li>
              <li>• Отслеживает выполнение задач</li>
              <li>• Персональные рекомендации</li>
            </ul>
          </div>
          
          <div className="bg-white rounded-lg p-4">
            <h4 className="font-medium text-gray-800 mb-2">🎯 Директорский стиль</h4>
            <ul className="text-sm text-gray-600 space-y-1">
              <li>• Четкие указания и рекомендации</li>
              <li>• Фокус на результат и цифры</li>
              <li>• Стратегическое мышление</li>
            </ul>
          </div>
        </div>
      </div>

      {/* How to Start */}
      <div className="bg-white rounded-lg shadow-lg p-6">
        <h3 className="text-lg font-semibold mb-4">🚀 Как начать работу</h3>
        
        <div className="space-y-4">
          <div className="flex items-start space-x-3">
            <span className="bg-blue-500 text-white rounded-full w-6 h-6 flex items-center justify-center text-sm font-bold">1</span>
            <div>
              <h4 className="font-medium">Откройте Telegram и найдите бота</h4>
              <p className="text-gray-600 text-sm">Перейдите по ссылке: <a href="https://t.me/aitest123432_bot" target="_blank" rel="noopener noreferrer" className="text-blue-500 underline">@aitest123432_bot</a></p>
            </div>
          </div>
          
          <div className="flex items-start space-x-3">
            <span className="bg-blue-500 text-white rounded-full w-6 h-6 flex items-center justify-center text-sm font-bold">2</span>
            <div>
              <h4 className="font-medium">Нажмите "START BOT"</h4>
              <p className="text-gray-600 text-sm">МАКС автоматически начнет знакомство и настройку под ваши задачи</p>
            </div>
          </div>
          
          <div className="flex items-start space-x-3">
            <span className="bg-blue-500 text-white rounded-full w-6 h-6 flex items-center justify-center text-sm font-bold">3</span>
            <div>
              <h4 className="font-medium">Ответьте на вопросы МАКС</h4>
              <p className="text-gray-600 text-sm">Расскажите о своей роли, опыте и приоритетах в работе</p>
            </div>
          </div>
          
          <div className="flex items-start space-x-3">
            <span className="bg-green-500 text-white rounded-full w-6 h-6 flex items-center justify-center text-sm font-bold">✓</span>
            <div>
              <h4 className="font-medium">Получите первый отчет</h4>
              <p className="text-gray-600 text-sm">МАКС проанализирует данные и даст персональные рекомендации</p>
            </div>
          </div>
        </div>
      </div>

      {/* Sample Conversation */}
      <div className="bg-gray-50 rounded-lg p-6">
        <h3 className="text-lg font-semibold mb-4">💬 Пример разговора с МАКС</h3>
        
        <div className="space-y-3">
          <div className="bg-blue-100 rounded-lg p-3">
            <p className="text-sm"><strong>🤖 МАКС:</strong> Добро пожаловать! Я МАКС - ваш AI-директор для управления ВасДом. Как к вам обращаться и какую должность занимаете?</p>
          </div>
          
          <div className="bg-white rounded-lg p-3 ml-6">
            <p className="text-sm"><strong>👤 Вы:</strong> Максим Маслов, генеральный директор</p>
          </div>
          
          <div className="bg-blue-100 rounded-lg p-3">
            <p className="text-sm"><strong>🤖 МАКС:</strong> Отлично, Максим! Готовлю управленческую сводку... По данным Bitrix24 у нас 15 активных сделок на 2.3 млн ₽. Конверсия в Кемерово упала на 12%. Рекомендую срочно провести планерку с командой. Нужна детализация?</p>
          </div>
        </div>
      </div>

      {/* Call to Action */}
      <div className="bg-gradient-to-r from-green-500 to-blue-500 text-white rounded-lg p-6 text-center">
        <h3 className="text-xl font-bold mb-2">🎯 Готовы к управлению с AI?</h3>
        <p className="mb-4">МАКС уже ждет вас в Telegram для первого знакомства и настройки</p>
        <a 
          href="https://t.me/aitest123432_bot" 
          target="_blank" 
          rel="noopener noreferrer"
          className="bg-white text-blue-600 px-6 py-3 rounded-lg font-semibold hover:bg-gray-100 transition-colors inline-block"
        >
          📱 Открыть бота в Telegram
        </a>
      </div>
    </div>
  );
};

// Smart Notifications Component  
const SmartNotifications = () => {
  const [notificationStats, setNotificationStats] = useState(null);
  const [loading, setLoading] = useState(true);
  const [telegramChatId, setTelegramChatId] = useState('');
  const [sendingDaily, setSendingDaily] = useState(false);

  useEffect(() => {
    fetchNotificationStats();
  }, []);

  const fetchNotificationStats = async () => {
    try {
      const response = await axios.get(`${API}/conversation/stats`);
      setNotificationStats(response.data);
    } catch (error) {
      console.error('Error fetching notification stats:', error);
    } finally {
      setLoading(false);
    }
  };

  const sendDailySummary = async () => {
    if (!telegramChatId.trim()) {
      alert('Введите Telegram Chat ID');
      return;
    }

    setSendingDaily(true);
    try {
      const response = await axios.post(`${API}/notifications/daily-summary?chat_id=${telegramChatId}`);
      if (response.data.success) {
        alert('✅ Ежедневная сводка отправлена в Telegram!');
      } else {
        alert('❌ Ошибка при отправке сводки');
      }
    } catch (error) {
      console.error('Error sending daily summary:', error);
      alert('❌ Ошибка при отправке сводки');
    } finally {
      setSendingDaily(false);
    }
  };

  const sendTestAlert = async () => {
    if (!telegramChatId.trim()) {
      alert('Введите Telegram Chat ID');
      return;
    }

    try {
      const response = await axios.post(`${API}/notifications/alert?chat_id=${telegramChatId}&alert_type=system_test`, {
        message: "Тестовое уведомление от AI-ассистента ВасДом"
      });
      if (response.data.success) {
        alert('✅ Тестовое уведомление отправлено!');
      } else {
        alert('❌ Ошибка при отправке уведомления');
      }
    } catch (error) {
      alert('❌ Ошибка при отправке уведомления');
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-32">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-500"></div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <h2 className="text-2xl font-bold text-gray-900">📢 Smart уведомления</h2>
      
      {/* Stats */}
      {notificationStats && (
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <div className="bg-white rounded-lg shadow p-4">
            <h3 className="font-medium text-gray-700">Всего сессий</h3>
            <p className="text-2xl font-bold text-blue-600">{notificationStats.total_sessions || 0}</p>
          </div>
          <div className="bg-white rounded-lg shadow p-4">
            <h3 className="font-medium text-gray-700">Активные сессии</h3>
            <p className="text-2xl font-bold text-green-600">{notificationStats.active_sessions || 0}</p>
          </div>
          <div className="bg-white rounded-lg shadow p-4">
            <h3 className="font-medium text-gray-700">Всего сообщений</h3>
            <p className="text-2xl font-bold text-purple-600">{notificationStats.total_messages || 0}</p>
          </div>
          <div className="bg-white rounded-lg shadow p-4">
            <h3 className="font-medium text-gray-700">За 24 часа</h3>
            <p className="text-2xl font-bold text-orange-600">{notificationStats.recent_messages_24h || 0}</p>
          </div>
        </div>
      )}

      {/* Notification Controls */}
      <div className="bg-white rounded-lg shadow-lg p-6">
        <h3 className="text-lg font-semibold mb-4">🔔 Управление уведомлениями</h3>
        
        <div className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Telegram Chat ID (для отправки уведомлений)
            </label>
            <input
              type="text"
              value={telegramChatId}
              onChange={(e) => setTelegramChatId(e.target.value)}
              placeholder="Введите ваш Telegram Chat ID"
              className="w-full border border-gray-300 rounded-lg px-4 py-2 focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            />
            <p className="text-xs text-gray-500 mt-1">
              💡 Чтобы узнать Chat ID, напишите боту @userinfobot в Telegram
            </p>
          </div>

          <div className="flex space-x-4">
            <button
              onClick={sendDailySummary}
              disabled={sendingDaily || !telegramChatId.trim()}
              className="bg-blue-500 text-white px-6 py-2 rounded-lg hover:bg-blue-600 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
            >
              {sendingDaily ? '⏳ Отправляю...' : '📊 Отправить ежедневную сводку'}
            </button>
            
            <button
              onClick={sendTestAlert}
              disabled={!telegramChatId.trim()}
              className="bg-green-500 text-white px-6 py-2 rounded-lg hover:bg-green-600 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
            >
              🧪 Тестовое уведомление
            </button>
          </div>
        </div>
      </div>

      {/* Notification Features */}
      <div className="bg-gradient-to-br from-purple-50 to-blue-50 rounded-lg p-6">
        <h3 className="text-lg font-semibold mb-4 text-purple-800">🚀 Возможности Smart уведомлений</h3>
        
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div>
            <h4 className="font-medium text-gray-800 mb-2">📅 Автоматические уведомления:</h4>
            <ul className="text-sm text-gray-600 space-y-1">
              <li>• Ежедневная сводка в 8:00 утра</li>
              <li>• Еженедельный отчет по понедельникам</li>
              <li>• Уведомления о крупных сделках</li>
              <li>• Предупреждения о падении конверсии</li>
              <li>• Напоминания о важных задачах</li>
            </ul>
          </div>
          
          <div>
            <h4 className="font-medium text-gray-800 mb-2">🤖 AI-функции:</h4>
            <ul className="text-sm text-gray-600 space-y-1">
              <li>• Персонализированные инсайты</li>
              <li>• Прогнозы и рекомендации</li>
              <li>• Анализ трендов бизнеса</li>
              <li>• Оптимизация процессов</li>
              <li>• Мониторинг KPI в реальном времени</li>
            </ul>
          </div>
        </div>

        <div className="mt-4 p-4 bg-white rounded-lg border-l-4 border-blue-500">
          <p className="text-sm text-gray-700">
            <strong>💡 Совет:</strong> Настройте автоматические уведомления для получения 
            ежедневных сводок и важных бизнес-алертов прямо в Telegram. 
            AI будет анализировать ваши данные и отправлять персональные рекомендации.
          </p>
        </div>
      </div>
    </div>
  );
};

// Main App Component
function App() {
  const [activeTab, setActiveTab] = useState('dashboard');
  const [userProfile, setUserProfile] = useState(null);
  const [showOnboarding, setShowOnboarding] = useState(false);

  // Check if user needs onboarding
  useEffect(() => {
    const savedProfile = localStorage.getItem('userProfile');
    if (savedProfile) {
      setUserProfile(JSON.parse(savedProfile));
    } else {
      // Show onboarding for new users
      const hasVisited = localStorage.getItem('hasVisited');
      if (!hasVisited) {
        setShowOnboarding(true);
        localStorage.setItem('hasVisited', 'true');
      }
    }
  }, []);

  const handleOnboardingComplete = (profile) => {
    setUserProfile(profile);
    localStorage.setItem('userProfile', JSON.stringify(profile));
    setShowOnboarding(false);
  };

  const renderContent = () => {
    switch (activeTab) {
      case 'dashboard':
        return <Dashboard />;
      case 'employees':
        return <Employees />;
      case 'analytics':
        return <Analytics />;
      case 'smart-planning':
        return <SmartPlanning />;
      case 'client-management':
        return <ClientManagement />;
      case 'live-voice':
        return <LiveVoiceChat />;
      case 'meetings':
        return <MeetingRecorder />;
      case 'notifications':
        return <SmartNotifications />;
      case 'telegram-info':
        return <TelegramInfo />;
      default:
        return <Dashboard />;
    }
  };

  // Show onboarding if needed
  if (showOnboarding) {
    return <OnboardingChat onComplete={handleOnboardingComplete} />;
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100">
      <div className="container mx-auto px-4 py-8">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-4xl font-bold text-gray-900 mb-2">
            📊 Панель управления ВасДom
            {userProfile && (
              <span className="text-2xl text-blue-600 ml-4">
                Привет, {userProfile.name}! 👋
              </span>
            )}
          </h1>
          <p className="text-gray-600">
            Аналитика, прогнозирование и управление. AI-ассистент МАКС работает в Telegram: @aitest123432_bot
          </p>
          {userProfile && (
            <div className="mt-2 flex space-x-4 text-sm text-gray-500">
              <span>💼 {userProfile.role}</span>
              <span>⭐ Опыт: {userProfile.experience}</span>
              <button 
                onClick={() => setShowOnboarding(true)}
                className="text-blue-500 hover:underline"
              >
                ⚙️ Настроить профиль
              </button>
            </div>
          )}
        </div>

        <Navigation activeTab={activeTab} setActiveTab={setActiveTab} />
        
        {renderContent()}
      </div>
    </div>
  );
}

export default App;