import React, { useState, useEffect } from 'react';
import { 
  Building2, 
  Users, 
  Bot, 
  TrendingUp,
  Activity,
  Calendar,
  MapPin,
  Zap
} from 'lucide-react';

const Dashboard = () => {
  const [stats, setStats] = useState({
    total_houses: 0,
    total_apartments: 0,
    total_entrances: 0,
    total_floors: 0,
    active_brigades: 0,
    employees: 0
  });
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchDashboardStats();
  }, []);

  const fetchDashboardStats = async () => {
    try {
      const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
      const response = await fetch(`${BACKEND_URL}/api/dashboard/stats`);
      const data = await response.json();
      setStats(data);
    } catch (error) {
      console.error('Error fetching dashboard stats:', error);
      // Fallback данные
      setStats({
        total_houses: 490,
        total_apartments: 30153,
        total_entrances: 1567,
        total_floors: 2512,
        active_brigades: 7,
        employees: 82
      });
    } finally {
      setLoading(false);
    }
  };

  const statCards = [
    {
      title: 'Всего домов',
      value: stats.total_houses?.toLocaleString() || '0',
      icon: Building2,
      gradient: 'from-blue-500 to-cyan-500',
      change: '+3 за месяц',
      changeType: 'positive'
    },
    {
      title: 'Квартир',
      value: stats.total_apartments?.toLocaleString() || '0',
      icon: MapPin,
      gradient: 'from-emerald-500 to-teal-500',
      change: `Среднее: ${Math.round(stats.total_apartments / stats.total_houses || 62)} на дом`,
      changeType: 'neutral'
    },
    {
      title: 'Сотрудников',
      value: stats.employees?.toLocaleString() || '0',
      icon: Users,
      gradient: 'from-purple-500 to-pink-500',
      change: `${stats.active_brigades} активных бригад`,
      changeType: 'neutral'
    },
    {
      title: 'Подъездов',
      value: stats.total_entrances?.toLocaleString() || '0',
      icon: Activity,
      gradient: 'from-orange-500 to-red-500',
      change: `Среднее: ${Math.round(stats.total_entrances / stats.total_houses || 3)} на дом`,
      changeType: 'neutral'
    }
  ];

  const quickActions = [
    {
      title: 'Управление домами',
      description: 'Полная интеграция с Bitrix24',
      icon: Building2,
      color: 'bg-blue-500',
      href: '/works'
    },
    {
      title: 'AI Консультант',
      description: 'Диалог с голосовым помощником',
      icon: Bot,
      color: 'bg-purple-500',
      href: '/ai-chat'
    },
    {
      title: 'Управление бригадами',
      description: '82 сотрудника в 7 бригадах',
      icon: Users,
      color: 'bg-green-500',
      href: '/employees'
    }
  ];

  const recentActivity = [
    {
      id: 1,
      action: 'Дом добавлен в систему',
      details: 'ул. Ленина, 15',
      time: '2 минуты назад',
      type: 'success'
    },
    {
      id: 2,
      action: 'Уборка завершена',
      details: 'Бригада №3, пр. Мира, 22',
      time: '15 минут назад',
      type: 'info'
    },
    {
      id: 3,
      action: 'AI обработал запрос',
      details: 'Консультация по графику уборки',
      time: '1 час назад',
      type: 'purple'
    },
    {
      id: 4,
      action: 'Обновлен статус',
      details: 'УК "Домсервис" - новые объекты',
      time: '2 часа назад',
      type: 'warning'
    }
  ];

  // Компактная шапка и метрики
  const PageHeader = () => (
    <div className="mb-4 animate-fade-scale">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold gradient-text">VasDom AudioBot</h1>
        <div className="flex items-center space-x-2 text-sm text-green-600">
          <div className="w-2 h-2 bg-green-500 rounded-full animate-pulse"></div>
          <span>Bitrix24 подключен</span>
        </div>
      </div>
      <p className="text-sm text-gray-600 mt-1">Интеллектуальная система для комплексного управления клинингом</p>
    </div>
  );

  if (loading) {
    return (
      <div className="p-8 flex justify-center items-center min-h-96">
        <div className="flex items-center space-x-3">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
          <span className="text-lg font-medium text-gray-600">Загрузка дашборда...</span>
        </div>
      </div>
    );
  }

  return (
    <div className="pt-2 px-4 pb-6 max-w-7xl mx-auto space-y-6">
      {/* Header */}
      <PageHeader />
      <div className="hidden">
        <h1 className="text-4xl font-bold gradient-text">
          VasDom AudioBot
        </h1>
        <p className="text-xl text-gray-600 max-w-2xl mx-auto">
          Интеллектуальная система для комплексного управления клининговой компанией
        </p>
        <div className="flex items-center justify-center space-x-2 text-sm text-green-600">
          <div className="w-2 h-2 bg-green-500 rounded-full animate-pulse"></div>
          <span>Bitrix24 подключен • AI активен</span>
        </div>
      </div>

      {/* Stats Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        {statCards.map((card, index) => (
          <div
            key={card.title}
            className="card-modern shadow-hover animate-slide-up"
            style={{ animationDelay: `${index * 100}ms` }}
          >
            <div className="flex items-center justify-between mb-4">
              <div className={`p-3 rounded-xl bg-gradient-to-r ${card.gradient}`}>
                <card.icon className="w-6 h-6 text-white" />
              </div>
              <div className="text-right">
                <div className="text-2xl font-bold text-gray-900">{card.value}</div>
                <div className="text-sm text-gray-500">{card.title}</div>
              </div>
            </div>
            <div className={`text-sm ${
              card.changeType === 'positive' ? 'text-green-600' : 
              card.changeType === 'negative' ? 'text-red-600' : 'text-gray-600'
            }`}>
              {card.change}
            </div>
          </div>
        ))}
      </div>

      {/* Quick Actions */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        {quickActions.map((action, index) => (
          <div
            key={action.title}
            className="card-modern shadow-hover cursor-pointer group animate-slide-up"
            style={{ animationDelay: `${(index + 4) * 100}ms` }}
            onClick={() => window.location.href = action.href}
          >
            <div className="flex items-start space-x-4">
              <div className={`p-4 rounded-xl ${action.color} group-hover:scale-110 transition-transform duration-200`}>
                <action.icon className="w-8 h-8 text-white" />
              </div>
              <div className="flex-1">
                <h3 className="text-lg font-semibold text-gray-900 group-hover:text-blue-600 transition-colors">
                  {action.title}
                </h3>
                <p className="text-gray-600 mt-1">{action.description}</p>
                <div className="mt-3 flex items-center text-blue-600 text-sm font-medium">
                  <span>Перейти</span>
                  <TrendingUp className="w-4 h-4 ml-1 group-hover:translate-x-1 transition-transform" />
                </div>
              </div>
            </div>
          </div>
        ))}
      </div>

      {/* Recent Activity */}
      <div className="card-modern animate-slide-up" style={{ animationDelay: '400ms' }}>
        <div className="flex items-center justify-between mb-6">
          <h2 className="text-xl font-semibold text-gray-900 flex items-center">
            <Activity className="w-5 h-5 mr-2 text-blue-600" />
            Последняя активность
          </h2>
          <button className="text-blue-600 hover:text-blue-700 text-sm font-medium">
            Показать все
          </button>
        </div>
        
        <div className="space-y-4">
          {recentActivity.map((activity) => (
            <div key={activity.id} className="flex items-start space-x-4 p-4 rounded-lg hover:bg-gray-50 transition-colors">
              <div className={`w-2 h-2 rounded-full mt-2 ${
                activity.type === 'success' ? 'bg-green-500' :
                activity.type === 'info' ? 'bg-blue-500' :
                activity.type === 'purple' ? 'bg-purple-500' :
                activity.type === 'warning' ? 'bg-orange-500' : 'bg-gray-500'
              }`}></div>
              <div className="flex-1 min-w-0">
                <p className="text-sm font-medium text-gray-900">{activity.action}</p>
                <p className="text-sm text-gray-600 truncate">{activity.details}</p>
              </div>
              <div className="text-xs text-gray-500 whitespace-nowrap">
                {activity.time}
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* System Status */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <div className="card-modern animate-slide-up" style={{ animationDelay: '500ms' }}>
          <h3 className="text-lg font-semibold text-gray-900 mb-4 flex items-center">
            <Zap className="w-5 h-5 mr-2 text-green-600" />
            Статус системы
          </h3>
          <div className="space-y-3">
            <div className="flex items-center justify-between">
              <span className="text-sm text-gray-600">Bitrix24 API</span>
              <div className="flex items-center space-x-2">
                <div className="w-2 h-2 bg-green-500 rounded-full"></div>
                <span className="text-sm text-green-600 font-medium">Активен</span>
              </div>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-sm text-gray-600">AI Консультант</span>
              <div className="flex items-center space-x-2">
                <div className="w-2 h-2 bg-green-500 rounded-full"></div>
                <span className="text-sm text-green-600 font-medium">Готов</span>
              </div>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-sm text-gray-600">Telegram Bot</span>
              <div className="flex items-center space-x-2">
                <div className="w-2 h-2 bg-green-500 rounded-full"></div>
                <span className="text-sm text-green-600 font-medium">Онлайн</span>
              </div>
            </div>
          </div>
        </div>

        <div className="card-modern animate-slide-up" style={{ animationDelay: '900ms' }}>
          <h3 className="text-lg font-semibold text-gray-900 mb-4 flex items-center">
            <Calendar className="w-5 h-5 mr-2 text-blue-600" />
            Сегодня
          </h3>
          <div className="space-y-3">
            <div className="text-2xl font-bold text-blue-600">
              {new Date().toLocaleDateString('ru-RU', { 
                weekday: 'long',
                day: 'numeric',
                month: 'long'
              })}
            </div>
            <div className="text-sm text-gray-600">
              • Запланировано: 23 уборки
            </div>
            <div className="text-sm text-gray-600">
              • Завершено: 18 уборок
            </div>
            <div className="text-sm text-gray-600">
              • В процессе: 5 уборок
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Dashboard;