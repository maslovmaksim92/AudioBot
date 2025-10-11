import React, { useState, useEffect } from 'react';
import { 
  Home, 
  Users, 
  TrendingUp, 
  CheckCircle,
  Clock,
  AlertCircle,
  Building2,
  Calendar,
  DollarSign,
  Activity,
  Zap,
  Target,
  BarChart3
} from 'lucide-react';
import { CleaningLineChart, TaskProgressBar } from './DashboardCharts';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL || import.meta?.env?.REACT_APP_BACKEND_URL;

const Dashboard = () => {
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(true);
  const [recentActivities, setRecentActivities] = useState([]);

  useEffect(() => {
    loadDashboardData();
    // Обновление каждые 30 секунд
    const interval = setInterval(loadDashboardData, 30000);
    return () => clearInterval(interval);
  }, []);

  const loadDashboardData = async () => {
    try {
      const response = await fetch(`${BACKEND_URL}/api/dashboard/stats`);
      const data = await response.json();
      
      // Загружаем данные для графиков
      const cleaningResponse = await fetch(`${BACKEND_URL}/api/dashboard/cleaning-stats-monthly`).catch(() => ({ json: () => ({}) }));
      const cleaningData = await cleaningResponse.json();
      
      // Преобразуем данные из backend в формат для отображения
      setStats({
        houses: data.total_houses || 0,
        employees: data.employees || 0,
        brigades: data.active_brigades || 0,
        tasks_today: data.active_tasks || 0,
        tasks_completed: data.completed_tasks || 0,
        tasks_pending: data.active_tasks || 0,
        apartments: data.total_apartments || 0,
        entrances: data.total_entrances || 0,
        floors: data.total_floors || 0,
        companies: data.total_companies || 0,
        recent_logs: data.recent_logs || 0,
        last_sync: data.last_sync,
        cleaningData: cleaningData
      });
      
      // Загружаем недавние активности из API
      try {
        const activityResponse = await fetch(`${BACKEND_URL}/api/dashboard/recent-activity?limit=10`);
        const activities = await activityResponse.json();
        
        if (activities && activities.length > 0) {
          setRecentActivities(activities.map((act, idx) => ({
            id: idx,
            type: act.category,
            message: act.message,
            time: new Date(act.created_at).toLocaleString('ru-RU'),
            icon: act.level === 'error' ? AlertCircle : Activity,
            color: act.level === 'error' ? 'text-red-600 bg-red-50' : 'text-blue-600 bg-blue-50'
          })));
        }
      } catch (err) {
        console.log('Activities not loaded:', err);
      }
      
      setLoading(false);
    } catch (error) {
      console.error('Error loading dashboard:', error);
      // Fallback данные только при ошибке
      setStats({
        houses: 0,
        employees: 0,
        brigades: 0,
        tasks_today: 0,
        tasks_completed: 0,
        tasks_pending: 0,
        apartments: 0,
        entrances: 0,
        floors: 0,
        companies: 0,
        cleaningData: {}
      });
      setLoading(false);
    }
  };

  const mainStats = stats ? [
    {
      label: 'Всего домов',
      value: stats.houses || 0,
      change: `${stats.apartments || 0} квартир`,
      icon: Building2,
      color: 'blue',
      gradient: 'from-blue-500 to-blue-600'
    },
    {
      label: 'Сотрудников',
      value: stats.employees || 0,
      change: `${stats.brigades || 0} бригад`,
      icon: Users,
      color: 'green',
      gradient: 'from-green-500 to-green-600'
    },
    {
      label: 'Активных задач',
      value: stats.tasks_today || 0,
      change: `${stats.tasks_completed || 0} выполнено`,
      icon: CheckCircle,
      color: 'purple',
      gradient: 'from-purple-500 to-purple-600'
    },
    {
      label: 'Управляющих компаний',
      value: stats.companies || 0,
      change: `${stats.entrances || 0} подъездов`,
      icon: Building2,
      color: 'emerald',
      gradient: 'from-emerald-500 to-emerald-600'
    }
  ] : [];

  const performanceStats = stats ? [
    {
      label: 'Задачи',
      completed: stats.tasks_completed || 0,
      total: stats.tasks_today || 0,
      percentage: stats.tasks_today ? Math.round((stats.tasks_completed / stats.tasks_today) * 100) : 0,
      icon: CheckCircle,
      color: 'green'
    },
    {
      label: 'Уборки',
      completed: stats.cleaning_completed || 0,
      total: stats.cleaning_today || 0,
      percentage: stats.cleaning_today ? Math.round((stats.cleaning_completed / stats.cleaning_today) * 100) : 0,
      icon: Home,
      color: 'blue'
    },
    {
      label: 'В процессе',
      completed: stats.cleaning_in_progress || 0,
      total: stats.cleaning_today || 0,
      percentage: stats.cleaning_today ? Math.round((stats.cleaning_in_progress / stats.cleaning_today) * 100) : 0,
      icon: Clock,
      color: 'yellow'
    }
  ] : [];

  // Loading не блокирует рендер - показываем данные сразу

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 via-white to-indigo-50">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="mb-8">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-4xl font-bold text-gray-900 mb-2 flex items-center gap-3">
                <Home className="w-10 h-10 text-blue-600" />
                Обзор VasDom
              </h1>
              <p className="text-gray-600">
                {new Date().toLocaleDateString('ru-RU', { 
                  weekday: 'long', 
                  year: 'numeric', 
                  month: 'long', 
                  day: 'numeric' 
                })}
              </p>
            </div>
            
            {/* Real-time status */}
            <div className="flex items-center gap-4">
              <div className="flex items-center gap-2 px-4 py-2 bg-green-100 text-green-700 rounded-xl">
                <div className="w-3 h-3 bg-green-500 rounded-full animate-pulse" />
                <span className="font-semibold">Система активна</span>
              </div>
              <div className="flex items-center gap-2 px-4 py-2 bg-purple-100 text-purple-700 rounded-xl">
                <Zap className="w-4 h-4" />
                <span className="font-semibold">AI готов</span>
              </div>
            </div>
          </div>
        </div>

        {/* Main Stats */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
          {mainStats.map((stat, index) => (
            <div 
              key={index} 
              className="bg-white rounded-2xl shadow-lg border border-gray-100 overflow-hidden hover:shadow-xl transition-all cursor-pointer group"
            >
              <div className={`h-2 bg-gradient-to-r ${stat.gradient}`} />
              <div className="p-6">
                <div className="flex items-center justify-between mb-4">
                  <div className={`w-14 h-14 rounded-xl bg-${stat.color}-100 flex items-center justify-center group-hover:scale-110 transition-transform`}>
                    <stat.icon className={`w-7 h-7 text-${stat.color}-600`} />
                  </div>
                  <div className={`text-xs font-semibold px-3 py-1 rounded-full bg-${stat.color}-50 text-${stat.color}-700`}>
                    {stat.change}
                  </div>
                </div>
                <p className="text-sm text-gray-600 mb-2">{stat.label}</p>
                <p className="text-3xl font-bold text-gray-900">{stat.value}</p>
              </div>
            </div>
          ))}
        </div>

        {/* Analytics Chart - Cleaning Stats */}
        <div className="bg-white rounded-2xl shadow-lg p-6 border border-gray-100 mb-8">
          <h2 className="text-xl font-bold text-gray-900 mb-4 flex items-center gap-2">
            <TrendingUp className="w-6 h-6 text-green-600" />
            Уборки по месяцам
          </h2>
          <CleaningLineChart data={stats?.cleaningData || {}} />
        </div>

        {/* Performance & Activities */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8">
          {/* Performance */}
          <div className="bg-white rounded-2xl shadow-lg p-6 border border-gray-100">
            <div className="flex items-center justify-between mb-6">
              <h2 className="text-2xl font-bold text-gray-900 flex items-center gap-2">
                <BarChart3 className="w-7 h-7 text-blue-600" />
                Производительность
              </h2>
              <button className="text-sm text-blue-600 hover:text-blue-700 font-medium">
                Подробнее →
              </button>
            </div>

            <div className="space-y-4">
              {performanceStats.map((stat, index) => (
                <div key={index}>
                  <div className="flex items-center justify-between mb-2">
                    <div className="flex items-center gap-2">
                      <stat.icon className={`w-5 h-5 text-${stat.color}-600`} />
                      <span className="font-medium text-gray-700">{stat.label}</span>
                    </div>
                    <span className="text-sm font-semibold text-gray-600">
                      {stat.completed}/{stat.total} ({stat.percentage}%)
                    </span>
                  </div>
                  <div className="w-full bg-gray-200 rounded-full h-3">
                    <div 
                      className={`bg-${stat.color}-500 h-3 rounded-full transition-all duration-500`}
                      style={{ width: `${stat.percentage}%` }}
                    />
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Recent Activities */}
          <div className="bg-white rounded-2xl shadow-lg p-6 border border-gray-100">
            <div className="flex items-center justify-between mb-6">
              <h2 className="text-2xl font-bold text-gray-900 flex items-center gap-2">
                <Activity className="w-7 h-7 text-purple-600" />
                Последние события
              </h2>
              <button className="text-sm text-purple-600 hover:text-purple-700 font-medium">
                Все события →
              </button>
            </div>

            <div className="space-y-3">
              {recentActivities.map((activity) => (
                <div 
                  key={activity.id}
                  className="flex items-start gap-3 p-3 rounded-xl hover:bg-gray-50 transition-all cursor-pointer"
                >
                  <div className={`w-10 h-10 rounded-lg ${activity.color} flex items-center justify-center flex-shrink-0`}>
                    <activity.icon className="w-5 h-5" />
                  </div>
                  <div className="flex-1">
                    <p className="text-sm font-medium text-gray-900">{activity.message}</p>
                    <p className="text-xs text-gray-500 mt-1">{activity.time}</p>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* Quick Actions */}
        <div className="bg-gradient-to-r from-blue-600 to-indigo-600 rounded-2xl shadow-2xl p-8 text-white">
          <h2 className="text-2xl font-bold mb-6 flex items-center gap-2">
            <Target className="w-7 h-7" />
            Быстрые действия
          </h2>
          
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <button className="bg-white bg-opacity-20 hover:bg-opacity-30 rounded-xl p-4 text-left transition-all group">
              <Calendar className="w-8 h-8 mb-3 group-hover:scale-110 transition-transform" />
              <h3 className="font-semibold mb-1">Планёрка 8:30</h3>
              <p className="text-sm text-blue-100">Начать планёрку сегодня</p>
            </button>

            <button className="bg-white bg-opacity-20 hover:bg-opacity-30 rounded-xl p-4 text-left transition-all group">
              <TrendingUp className="w-8 h-8 mb-3 group-hover:scale-110 transition-transform" />
              <h3 className="font-semibold mb-1">Отчётность</h3>
              <p className="text-sm text-blue-100">Сформировать отчёт</p>
            </button>

            <button className="bg-white bg-opacity-20 hover:bg-opacity-30 rounded-xl p-4 text-left transition-all group">
              <Zap className="w-8 h-8 mb-3 group-hover:scale-110 transition-transform" />
              <h3 className="font-semibold mb-1">AI Задача</h3>
              <p className="text-sm text-blue-100">Создать новую автоматизацию</p>
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Dashboard;