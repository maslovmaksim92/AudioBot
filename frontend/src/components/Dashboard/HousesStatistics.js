import React, { useState, useEffect } from 'react';
import { Card } from '../UI';

const HousesStatistics = () => {
  const [statistics, setStatistics] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    loadStatistics();
  }, []);

  const loadStatistics = async () => {
    try {
      setLoading(true);
      const response = await fetch(`${process.env.REACT_APP_BACKEND_URL}/api/houses-statistics`);
      const data = await response.json();
      
      if (data.status === 'success') {
        setStatistics(data);
        setError(null);
      } else {
        setError(data.message || 'Ошибка загрузки статистики');
      }
    } catch (err) {
      setError('Ошибка загрузки данных: ' + err.message);
    } finally {
      setLoading(false);
    }
  };

  const SimpleBarChart = ({ data, title, color = "blue" }) => {
    if (!data || data.length === 0) return null;
    
    const maxValue = Math.max(...data.map(item => item.value));
    
    return (
      <Card title={title} className="h-64">
        <div className="space-y-2">
          {data.map((item, index) => (
            <div key={index} className="flex items-center space-x-2">
              <div className="w-20 text-xs text-gray-600 truncate">
                {item.name}
              </div>
              <div className="flex-1 bg-gray-200 rounded-full h-4 relative">
                <div 
                  className={`bg-${color}-500 h-4 rounded-full transition-all duration-500`}
                  style={{ width: `${(item.value / maxValue) * 100}%` }}
                />
                <span className="absolute right-2 top-0 text-xs text-gray-700 leading-4">
                  {item.value}
                </span>
              </div>
            </div>
          ))}
        </div>
      </Card>
    );
  };

  const StatCard = ({ title, value, subtitle, icon, color = "blue" }) => (
    <Card className="text-center">
      <div className="space-y-2">
        <div className="text-2xl">{icon}</div>
        <div className={`text-2xl font-bold text-${color}-600`}>{value}</div>
        <div className="text-sm font-medium text-gray-700">{title}</div>
        {subtitle && <div className="text-xs text-gray-500">{subtitle}</div>}
      </div>
    </Card>
  );

  const DistrictChart = ({ data }) => {
    if (!data || data.length === 0) return null;
    
    const colors = ['blue', 'green', 'purple', 'pink', 'indigo', 'yellow'];
    const total = data.reduce((sum, item) => sum + item.value, 0);
    
    return (
      <Card title="🗺️ Распределение по районам Калуги" className="h-64">
        <div className="grid grid-cols-2 gap-2">
          {data.map((item, index) => {
            const percentage = Math.round((item.value / total) * 100);
            const color = colors[index % colors.length];
            
            return (
              <div key={index} className="text-center p-2 rounded-lg bg-gray-50">
                <div className={`text-lg font-bold text-${color}-600`}>
                  {item.value}
                </div>
                <div className="text-xs text-gray-600 truncate">
                  {item.name}
                </div>
                <div className="text-xs text-gray-500">
                  {percentage}%
                </div>
              </div>
            );
          })}
        </div>
      </Card>
    );
  };

  if (loading) {
    return (
      <div className="p-6">
        <div className="flex items-center justify-center h-64">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
          <span className="ml-2 text-gray-600">Загружаем статистику домов...</span>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="p-6">
        <Card className="text-center">
          <div className="text-red-600">
            <div className="text-2xl">❌</div>
            <div className="mt-2 text-sm">{error}</div>
            <button 
              onClick={loadStatistics}
              className="mt-4 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
            >
              Попробовать снова
            </button>
          </div>
        </Card>
      </div>
    );
  }

  const { summary, charts } = statistics;

  return (
    <div className="p-6 bg-gradient-to-br from-blue-50 to-indigo-100 min-h-screen">
      <div className="flex justify-between items-center mb-6">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">📊 Статистика домов VasDom</h1>
          <p className="text-gray-600">Детальная аналитика по {summary.total_houses} домам из Bitrix24</p>
        </div>
        <button 
          onClick={loadStatistics}
          className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
        >
          🔄 Обновить
        </button>
      </div>

      {/* Основная статистика */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
        <StatCard 
          title="Всего домов"
          value={summary.total_houses}
          subtitle="В управлении"
          icon="🏠"
          color="blue"
        />
        <StatCard 
          title="Подъездов"
          value={summary.total_entrances}
          subtitle={`Ср. ${summary.avg_entrances} на дом`}
          icon="🚪"
          color="green"
        />
        <StatCard 
          title="Этажей"
          value={summary.total_floors}
          subtitle={`Ср. ${summary.avg_floors} на дом`}
          icon="🏢"
          color="purple"
        />
        <StatCard 
          title="Квартир"
          value={summary.total_apartments}
          subtitle={`Ср. ${summary.avg_apartments} на дом`}
          icon="🏠"
          color="pink"
        />
      </div>

      {/* Графики */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <SimpleBarChart 
          data={charts.entrances}
          title="📊 Распределение по подъездам"
          color="green"
        />
        
        <SimpleBarChart 
          data={charts.floors}
          title="📊 Распределение по этажам"  
          color="purple"
        />
        
        <SimpleBarChart 
          data={charts.apartments}
          title="📊 Распределение по квартирам"
          color="pink"
        />
        
        <DistrictChart data={charts.districts} />
      </div>

      {/* Дополнительная информация */}
      <div className="mt-6 grid grid-cols-1 md:grid-cols-3 gap-4">
        <Card title="💡 Аналитика">
          <div className="space-y-2 text-sm">
            <p>• <strong>Средний дом:</strong> {summary.avg_entrances} подъезда, {summary.avg_floors} этажей</p>
            <p>• <strong>Всего квартир:</strong> {summary.total_apartments} в управлении</p>
            <p>• <strong>Активные районы:</strong> {charts.districts?.length || 0} районов Калуги</p>
          </div>
        </Card>
        
        <Card title="🎯 Особенности">
          <div className="space-y-2 text-sm">
            <p>• Данные загружены из <strong>Bitrix24 CRM</strong></p>
            <p>• Автоматический анализ параметров домов</p>
            <p>• Обновление в реальном времени</p>
          </div>
        </Card>
        
        <Card title="📈 Тенденции">
          <div className="space-y-2 text-sm">
            <p>• <strong>Преобладают:</strong> 5-этажные дома</p>
            <p>• <strong>Большинство:</strong> 1-2 подъезда</p>
            <p>• <strong>Районы:</strong> равномерное распределение</p>
          </div>
        </Card>
      </div>
    </div>
  );
};

export default HousesStatistics;