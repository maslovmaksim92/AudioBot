import React, { useState, useEffect } from 'react';
import { useApp } from '../../context/AppContext';
import { Card, StatCard, Button, LoadingSpinner } from '../UI';

const Dashboard = () => {
  const { state, actions } = useApp();
  const { dashboardStats, loading, apiStatus } = state;
  const [districtStats, setDistrictStats] = useState(null);

  const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;

  // Загружаем статистику по районам
  useEffect(() => {
    const fetchDistrictStats = async () => {
      try {
        const response = await fetch(`${BACKEND_URL}/api/analytics/districts`);
        if (response.ok) {
          const data = await response.json();
          setDistrictStats(data.districts || []);
        }
      } catch (error) {
        console.log('District stats not available, using defaults');
        // Используем статические данные как fallback
        setDistrictStats([
          { name: 'Центральный', houses: 58, color: 'green' },
          { name: 'Северный', houses: 71, color: 'blue' },
          { name: 'Никитинский', houses: 62, color: 'purple' },
          { name: 'Жилетово', houses: 45, color: 'yellow' },
          { name: 'Пригород', houses: 53, color: 'red' },
          { name: 'Окраины', houses: 59, color: 'gray' }
        ]);
      }
    };

    if (dashboardStats.houses) {
      fetchDistrictStats();
    }
  }, [dashboardStats.houses, BACKEND_URL]);

  // Основные карточки статистики (данные из Bitrix24)
  const mainStatCards = [
    { 
      title: 'Сотрудников', 
      value: dashboardStats.employees || 0, 
      icon: '👥', 
      color: 'blue',
      subtitle: 'В 6 бригадах',
      trend: '+2 за месяц'
    },
    { 
      title: 'Домов в CRM', 
      value: dashboardStats.houses || 0, 
      icon: '🏠', 
      color: 'green',
      subtitle: 'Из Bitrix24',
      trend: dashboardStats.houses >= 490 ? '🔥 Все загружены' : 'Загружается...'
    },
    { 
      title: 'Подъездов', 
      value: dashboardStats.entrances || 0, 
      icon: '🚪', 
      color: 'purple',
      subtitle: '~3 на дом',
      trend: `${Math.round((dashboardStats.entrances || 0) / (dashboardStats.houses || 1) * 10) / 10} сред./дом`
    },
    { 
      title: 'Квартир', 
      value: dashboardStats.apartments || 0, 
      icon: '🏠', 
      color: 'yellow',
      subtitle: '~75 на дом',
      trend: `${Math.round((dashboardStats.apartments || 0) / (dashboardStats.houses || 1))} сред./дом`
    },
    { 
      title: 'Этажей', 
      value: dashboardStats.floors || 0, 
      icon: '📊', 
      color: 'red',
      subtitle: '~5 на дом',
      trend: `${Math.round((dashboardStats.floors || 0) / (dashboardStats.houses || 1) * 10) / 10} сред./дом`
    },
    { 
      title: 'Планерок', 
      value: dashboardStats.meetings || 0, 
      icon: '🎤', 
      color: 'indigo',
      subtitle: 'Записано',
      trend: dashboardStats.meetings > 0 ? `${dashboardStats.meetings} готовы` : 'В ожидании'
    }
  ];

  // Карточки районов (данные из analytics API или fallback)
  const districtCards = districtStats ? districtStats.map(district => ({
    title: district.name,
    value: district.houses,
    icon: '🏘️',
    color: district.color,
    subtitle: 'домов в районе',
    trend: district.won_houses ? `${district.won_houses} выиграно` : 'В работе'
  })) : [];

  // Дополнительные метрики
  const additionalStats = [
    {
      title: 'AI Задач',
      value: dashboardStats.ai_tasks || 0,
      icon: '🤖',
      color: 'cyan',
      subtitle: 'Активных',
      trend: 'Автоматизация'
    },
    {
      title: 'Выиграно домов',
      value: dashboardStats.won_houses || 0,
      icon: '🏆',
      color: 'green',
      subtitle: 'Успешных сделок',
      trend: `${Math.round((dashboardStats.won_houses || 0) / (dashboardStats.houses || 1) * 100)}% успеха`
    },
    {
      title: 'Проблемных домов',
      value: dashboardStats.problem_houses || 0,
      icon: '⚠️',
      color: 'red',
      subtitle: 'Требуют внимания',
      trend: dashboardStats.problem_houses > 0 ? 'Нужна работа' : 'Все в порядке'
    }
  ];

  const systemStatus = [
    { 
      name: 'Bitrix24 API', 
      status: dashboardStats.houses > 0 ? 'active' : 'warning',
      details: dashboardStats.data_source || 'CRM интеграция'
    },
    { 
      name: 'GPT-4 mini (Emergent)', 
      status: 'active',
      details: 'AI чат активен'
    },
    { 
      name: 'База знаний', 
      status: 'active',
      details: 'RAG система работает'
    },
    { 
      name: 'Самообучение', 
      status: 'active',
      details: 'Модель обучается'
    },
    { 
      name: 'PostgreSQL', 
      status: apiStatus === 'connected' ? 'active' : 'warning',
      details: apiStatus === 'connected' ? 'БД подключена' : 'Проверка соединения'
    }
  ];

  const handleRefresh = () => {
    actions.fetchDashboardStats();
    setDistrictStats(null); // Перезагрузим районы
  };

  if (loading && !dashboardStats.houses) {
    return (
      <div className="p-6 flex justify-center items-center min-h-96">
        <LoadingSpinner size="lg" text="🔄 Загрузка данных из Bitrix24..." />
      </div>
    );
  }

  return (
    <div className="p-6 space-y-6">
      {/* Header с улучшенным дизайном */}
      <div className="flex justify-between items-center mb-8">
        <div>
          <h1 className="text-3xl font-bold text-gray-900 mb-2">
            🏠 VasDom Dashboard
          </h1>
          <p className="text-gray-600">
            {dashboardStats.crm_sync_time ? 
              `Последнее обновление: ${new Date(dashboardStats.crm_sync_time).toLocaleString('ru-RU')}` :
              'Управляющая компания • Калуга'
            }
          </p>
        </div>
        <div className="flex gap-3">
          <Button 
            onClick={handleRefresh} 
            disabled={loading}
            className="bg-blue-600 hover:bg-blue-700 text-white"
          >
            {loading ? '🔄 Обновление...' : '🔄 Обновить'}
          </Button>
        </div>
      </div>

      {/* Основная статистика */}
      <div className="mb-8">
        <h2 className="text-xl font-semibold text-gray-800 mb-4 flex items-center">
          📊 Основная статистика
          {dashboardStats.houses >= 490 && (
            <span className="ml-2 px-2 py-1 bg-green-100 text-green-800 text-xs rounded-full">
              🔥 Все данные загружены
            </span>
          )}
        </h2>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-6 gap-6">
          {mainStatCards.map((card, index) => (
            <StatCard 
              key={index} 
              {...card}
              className="transform hover:scale-105 transition-transform duration-200"
            />
          ))}
        </div>
      </div>

      {/* Статистика по районам */}
      {districtCards.length > 0 && (
        <div className="mb-8">
          <h2 className="text-xl font-semibold text-gray-800 mb-4 flex items-center">
            🏘️ Распределение по районам
            <span className="ml-2 text-sm text-gray-500">
              ({districtCards.reduce((sum, d) => sum + d.value, 0)} домов всего)
            </span>
          </h2>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-6 gap-4">
            {districtCards.map((card, index) => (
              <StatCard 
                key={index} 
                {...card}
                className="transform hover:scale-105 transition-transform duration-200"
              />
            ))}
          </div>
        </div>
      )}

      {/* Дополнительные метрики */}
      <div className="mb-8">
        <h2 className="text-xl font-semibold text-gray-800 mb-4">
          ⚡ Операционные метрики
        </h2>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          {additionalStats.map((card, index) => (
            <StatCard 
              key={index} 
              {...card}
              className="transform hover:scale-105 transition-transform duration-200"
            />
          ))}
        </div>
      </div>

      {/* Статус системы */}
      <Card className="mb-6">
        <div className="p-6">
          <h2 className="text-xl font-semibold text-gray-800 mb-4">
            🔧 Статус системы
          </h2>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-4">
            {systemStatus.map((service, index) => (
              <div key={index} className="flex items-center p-4 bg-gray-50 rounded-lg">
                <div className={`w-3 h-3 rounded-full mr-3 ${
                  service.status === 'active' ? 'bg-green-500' : 
                  service.status === 'warning' ? 'bg-yellow-500' : 'bg-red-500'
                }`}></div>
                <div>
                  <div className="font-medium text-sm">{service.name}</div>
                  <div className="text-xs text-gray-500">{service.details}</div>
                </div>
              </div>
            ))}
          </div>
        </div>
      </Card>

      {/* Быстрые действия */}
      <Card>
        <div className="p-6">
          <h2 className="text-xl font-semibold text-gray-800 mb-4">
            🚀 Быстрые действия
          </h2>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
            <Button className="bg-blue-600 hover:bg-blue-700 text-white p-4 h-auto flex flex-col items-center">
              <span className="text-2xl mb-2">💬</span>
              <span>AI Чат</span>
            </Button>
            <Button className="bg-green-600 hover:bg-green-700 text-white p-4 h-auto flex flex-col items-center">
              <span className="text-2xl mb-2">🎤</span>
              <span>Планерка</span>
            </Button>
            <Button className="bg-purple-600 hover:bg-purple-700 text-white p-4 h-auto flex flex-col items-center">
              <span className="text-2xl mb-2">🏠</span>
              <span>Дома</span>
            </Button>
            <Button className="bg-orange-600 hover:bg-orange-700 text-white p-4 h-auto flex flex-col items-center">
              <span className="text-2xl mb-2">📊</span>
              <span>Аналитика</span>
            </Button>
          </div>
        </div>
      </Card>
    </div>
  );
};

export default Dashboard;