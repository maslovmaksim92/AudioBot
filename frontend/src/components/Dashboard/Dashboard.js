import React from 'react';
import { useApp } from '../../context/AppContext';
import { Card, StatCard, Button, LoadingSpinner } from '../UI';

const Dashboard = () => {
  const { state, actions } = useApp();
  const { dashboardStats, loading, apiStatus } = state;

  const BACKEND_URL = process.env.REACT_APP_BACKEND_URL || 'https://audiobot-qci2.onrender.com';

  const statCards = [
    {
      title: 'Сотрудников',
      value: dashboardStats.employees || 0,
      icon: '👥',
      color: 'blue',
      subtitle: 'В 6 бригадах'
    },
    {
      title: 'Центральный',
      value: 58,
      icon: '🏘️',
      color: 'green',
      subtitle: 'домов в районе'
    },
    {
      title: 'Никитинский',
      value: 62,
      icon: '🏘️',
      color: 'purple',
      subtitle: 'домов в районе'
    },
    {
      title: 'Жилетово',
      value: 45,
      icon: '🏘️',
      color: 'yellow',
      subtitle: 'домов в районе'
    },
    {
      title: 'Северный',
      value: 71,
      icon: '🏘️',
      color: 'red',
      subtitle: 'домов в районе'
    },
    {
      title: 'Планерок',
      value: dashboardStats.meetings || 0,
      icon: '🎤',
      color: 'gray',
      subtitle: 'Записано'
    }
  ];

  const systemStatus = [
    { name: 'Bitrix24 API', status: 'active' },
    { name: 'GPT-4 mini (Emergent)', status: 'active' },
    { name: 'База знаний', status: 'active' },
    { name: 'Самообучение', status: 'active' },
    { name: 'PostgreSQL', status: apiStatus === 'connected' ? 'active' : 'warning' }
  ];

  const handleRefresh = () => {
    actions.fetchDashboardStats();
  };

  if (loading && !dashboardStats.houses) {
    return (
      <div className="p-6 flex justify-center items-center min-h-96">
        <LoadingSpinner size="lg" text="Загрузка данных дашборда..." />
      </div>
    );
  }

  return (
    <div className="p-6">
      {/* Header */}
      <div className="flex justify-between items-center mb-6">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Общий обзор</h1>
          <p className="text-gray-600">VasDom AI - Система управления клинингом</p>
          <p className="text-sm text-gray-500">
            Обновлено: {new Date().toLocaleString('ru-RU')}
          </p>
        </div>
        <Button
          onClick={handleRefresh}
          disabled={loading}
          loading={loading}
          variant="primary"
        >
          {loading ? 'Обновление...' : '🔄 Обновить'}
        </Button>
      </div>

      {/* Stats Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 mb-8">
        {statCards.map((card, index) => (
          <StatCard
            key={index}
            title={card.title}
            value={card.value}
            icon={<span className="text-2xl">{card.icon}</span>}
            color={card.color}
            subtitle={card.subtitle}
          />
        ))}
      </div>

      {/* System Status */}
      <Card title="🔥 Статус системы" className="mb-6">
        <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
          {systemStatus.map((system, index) => (
            <div key={index} className="flex items-center">
              <div
                className={`w-3 h-3 rounded-full mr-2 ${
                  system.status === 'active'
                    ? 'bg-green-500 animate-pulse'
                    : system.status === 'warning'
                    ? 'bg-yellow-500'
                    : 'bg-red-500'
                }`}
              ></div>
              <span className="text-sm">{system.name}</span>
            </div>
          ))}
        </div>
        <div className="mt-4 p-3 bg-blue-50 rounded-lg">
          <p className="text-sm text-blue-800">
            🔗 <strong>Backend:</strong> {BACKEND_URL}
          </p>
          <p className="text-sm text-blue-600">
            📅 <strong>Система активна:</strong> {new Date().toLocaleString('ru-RU')}
          </p>
        </div>
      </Card>

      {/* Quick Actions */}
      <Card title="🚀 Быстрые действия">
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <Button
            variant="secondary"
            className="flex flex-col items-center p-4 h-20"
            onClick={() => actions.setCurrentSection('voice')}
          >
            <span className="text-xl mb-1">🎤</span>
            <span className="text-xs">AI Чат</span>
          </Button>
          <Button
            variant="secondary"
            className="flex flex-col items-center p-4 h-20"
            onClick={() => actions.setCurrentSection('meetings')}
          >
            <span className="text-xl mb-1">📝</span>
            <span className="text-xs">Планерки</span>
          </Button>
          <Button
            variant="secondary"
            className="flex flex-col items-center p-4 h-20"
            onClick={() => actions.setCurrentSection('works')}
          >
            <span className="text-xl mb-1">🏠</span>
            <span className="text-xs">Дома</span>
          </Button>
          <Button
            variant="secondary"
            className="flex flex-col items-center p-4 h-20"
            onClick={() => actions.setCurrentSection('tasks')}
          >
            <span className="text-xl mb-1">📋</span>
            <span className="text-xs">Задачи</span>
          </Button>
          <Button
            variant="secondary"
            className="flex flex-col items-center p-4 h-20"
            onClick={() => actions.setCurrentSection('employees')}
          >
            <span className="text-xl mb-1">👥</span>
            <span className="text-xs">Сотрудники</span>
          </Button>
        </div>
      </Card>
    </div>
  );
};

export default Dashboard;