import React from 'react';
import { useApp } from '../../context/AppContext';
import { Card, StatCard, Button, LoadingSpinner } from '../UI';

const Dashboard = () => {
  const { state, actions } = useApp();
  const { dashboardStats, loading, apiStatus } = state;

  const BACKEND_URL = process.env.REACT_APP_BACKEND_URL || 'http://localhost:8001';

  const statCards = [
    { 
      title: 'Сотрудников', 
      value: dashboardStats.employees || 0, 
      icon: '👥', 
      color: 'blue',
      subtitle: 'В 6 бригадах'
    },
    { 
      title: 'Домов в CRM', 
      value: dashboardStats.houses || 0, 
      icon: '🏠', 
      color: 'green',
      subtitle: 'Из Bitrix24'
    },
    { 
      title: 'Подъездов', 
      value: dashboardStats.entrances || 0, 
      icon: '🚪', 
      color: 'purple',
      subtitle: '~3 на дом'
    },
    { 
      title: 'Квартир', 
      value: dashboardStats.apartments || 0, 
      icon: '🏠', 
      color: 'yellow',
      subtitle: '~75 на дом'
    },
    { 
      title: 'Этажей', 
      value: dashboardStats.floors || 0, 
      icon: '📊', 
      color: 'red',
      subtitle: '~5 на дом'
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
      &lt;div className="p-6 flex justify-center items-center min-h-96"&gt;
        &lt;LoadingSpinner size="lg" text="Загрузка данных дашборда..." /&gt;
      &lt;/div&gt;
    );
  }

  return (
    &lt;div className="p-6"&gt;
      {/* Header */}
      &lt;div className="flex justify-between items-center mb-6"&gt;
        &lt;div&gt;
          &lt;h1 className="text-3xl font-bold text-gray-900"&gt;Общий обзор&lt;/h1&gt;
          &lt;p className="text-gray-600"&gt;VasDom AI - Система управления клинингом&lt;/p&gt;
          &lt;p className="text-sm text-gray-500"&gt;
            Обновлено: {new Date().toLocaleString('ru-RU')}
          &lt;/p&gt;
        &lt;/div&gt;
        &lt;Button
          onClick={handleRefresh}
          disabled={loading}
          loading={loading}
          variant="primary"
        &gt;
          {loading ? 'Обновление...' : '🔄 Обновить'}
        &lt;/Button&gt;
      &lt;/div&gt;

      {/* Stats Grid */}
      &lt;div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 mb-8"&gt;
        {statCards.map((card, index) => (
          &lt;StatCard
            key={index}
            title={card.title}
            value={card.value}
            icon={&lt;span className="text-2xl"&gt;{card.icon}&lt;/span&gt;}
            color={card.color}
            subtitle={card.subtitle}
          /&gt;
        ))}
      &lt;/div&gt;

      {/* System Status */}
      &lt;Card title="🔥 Статус системы" className="mb-6"&gt;
        &lt;div className="grid grid-cols-2 md:grid-cols-5 gap-4"&gt;
          {systemStatus.map((system, index) => (
            &lt;div key={index} className="flex items-center"&gt;
              &lt;div 
                className={`w-3 h-3 rounded-full mr-2 ${
                  system.status === 'active' 
                    ? 'bg-green-500 animate-pulse' 
                    : system.status === 'warning'
                    ? 'bg-yellow-500'
                    : 'bg-red-500'
                }`}
              &gt;&lt;/div&gt;
              &lt;span className="text-sm"&gt;{system.name}&lt;/span&gt;
            &lt;/div&gt;
          ))}
        &lt;/div&gt;
        
        &lt;div className="mt-4 p-3 bg-blue-50 rounded-lg"&gt;
          &lt;p className="text-sm text-blue-800"&gt;
            🔗 &lt;strong&gt;Backend:&lt;/strong&gt; {BACKEND_URL}
          &lt;/p&gt;
          &lt;p className="text-sm text-blue-600"&gt;
            📅 &lt;strong&gt;Система активна:&lt;/strong&gt; {new Date().toLocaleString('ru-RU')}
          &lt;/p&gt;
        &lt;/div&gt;
      &lt;/Card&gt;

      {/* Quick Actions */}
      &lt;Card title="🚀 Быстрые действия"&gt;
        &lt;div className="grid grid-cols-2 md:grid-cols-4 gap-4"&gt;
          &lt;Button 
            variant="secondary" 
            className="flex flex-col items-center p-4 h-20"
            onClick={() => actions.setCurrentSection('voice')}
          &gt;
            &lt;span className="text-xl mb-1"&gt;🎤&lt;/span&gt;
            &lt;span className="text-xs"&gt;AI Чат&lt;/span&gt;
          &lt;/Button&gt;
          
          &lt;Button 
            variant="secondary" 
            className="flex flex-col items-center p-4 h-20"
            onClick={() => actions.setCurrentSection('meetings')}
          &gt;
            &lt;span className="text-xl mb-1"&gt;📝&lt;/span&gt;
            &lt;span className="text-xs"&gt;Планерки&lt;/span&gt;
          &lt;/Button&gt;
          
          &lt;Button 
            variant="secondary" 
            className="flex flex-col items-center p-4 h-20"
            onClick={() => actions.setCurrentSection('works')}
          &gt;
            &lt;span className="text-xl mb-1"&gt;🏠&lt;/span&gt;
            &lt;span className="text-xs"&gt;Дома&lt;/span&gt;
          &lt;/Button&gt;
          
          &lt;Button 
            variant="secondary" 
            className="flex flex-col items-center p-4 h-20"
            onClick={() => actions.setCurrentSection('employees')}
          &gt;
            &lt;span className="text-xl mb-1"&gt;👥&lt;/span&gt;
            &lt;span className="text-xs"&gt;Сотрудники&lt;/span&gt;
          &lt;/Button&gt;
        &lt;/div&gt;
      &lt;/Card&gt;
    &lt;/div&gt;
  );
};

export default Dashboard;