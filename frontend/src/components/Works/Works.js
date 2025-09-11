import React, { useState, useEffect } from 'react';
import { useApp } from '../../context/AppContext';
import { Card, Button, LoadingSpinner } from '../UI';

const Works = () => {
  const { actions } = useApp();
  
  // State
  const [houses, setHouses] = useState([]);
  const [loading, setLoading] = useState(false);
  const [dashboardStats, setDashboardStats] = useState({});
  const [selectedMonth, setSelectedMonth] = useState('september');
  const [notification, setNotification] = useState(null);
  const [cleaningSchedule, setCleaningSchedule] = useState({});

  const BACKEND_URL = process.env.REACT_APP_BACKEND_URL || 'https://audiobot-qci2.onrender.com';

  useEffect(() => {
    fetchInitialData();
  }, []);

  const fetchInitialData = async () => {
    setLoading(true);
    try {
      await Promise.all([
        fetchHouses(),
        fetchDashboardStats(),
        fetchCleaningSchedule()
      ]);
    } catch (error) {
      console.error('❌ Error fetching initial data:', error);
    } finally {
      setLoading(false);
    }
  };

  const fetchHouses = async () => {
    try {
      const response = await fetch(`${BACKEND_URL}/api/cleaning/houses`);
      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }
      const data = await response.json();
      console.log('🏠 Houses data received:', data);
      
      const housesData = data.houses || data || [];
      setHouses(housesData);
      console.log(`✅ Loaded ${housesData.length} houses`);
    } catch (error) {
      console.error('❌ Error fetching houses:', error);
      showNotification('❌ Ошибка загрузки домов из Bitrix24', 'error');
    }
  };

  const fetchDashboardStats = async () => {
    try {
      const response = await fetch(`${BACKEND_URL}/api/cleaning/stats`);
      const data = await response.json();
      setDashboardStats(data);
    } catch (error) {
      console.error('❌ Error fetching stats:', error);
    }
  };

  const fetchCleaningSchedule = async () => {
    try {
      const response = await fetch(`${BACKEND_URL}/api/cleaning/schedule/${selectedMonth}`);
      const data = await response.json();
      setCleaningSchedule(data);
    } catch (error) {
      console.error('❌ Error fetching cleaning schedule:', error);
    }
  };

  const showNotification = (message, type = 'info') => {
    setNotification({ message, type });
    setTimeout(() => setNotification(null), 4000);
  };

  const openGoogleMaps = (address) => {
    if (address) {
      const mapsUrl = `https://www.google.com/maps/search/?api=1&query=${encodeURIComponent(address)}`;
      window.open(mapsUrl, '_blank');
      showNotification('🗺️ Открываем Google Maps...', 'success');
    }
  };

  const renderHeader = () => (
    <div className="relative bg-gradient-to-r from-blue-600 via-purple-600 to-indigo-700 text-white p-8 rounded-2xl mb-8 shadow-2xl overflow-hidden">
      <div className="absolute inset-0 bg-gradient-to-r from-blue-400/20 via-purple-400/20 to-indigo-400/20 animate-pulse"></div>
      
      <div className="relative flex items-center justify-between">
        <div className="flex items-center space-x-4">
          <div className="bg-white/10 backdrop-blur-sm rounded-2xl p-4 border border-white/20">
            <span className="text-2xl font-bold bg-white/20 rounded-lg px-3 py-1">
              🏠 VasDom
            </span>
          </div>
          <div>
            <h1 className="text-4xl font-bold mb-2 bg-gradient-to-r from-white to-blue-100 bg-clip-text">
              Управление домами
            </h1>
            <p className="text-blue-100 text-lg">
              Интеграция с Bitrix24 CRM • График уборки • Калуга
            </p>
          </div>
        </div>
        
        <div className="text-right">
          <div className="bg-white/10 backdrop-blur-sm rounded-lg p-3">
            <div className="text-sm text-blue-100">Подключено к</div>
            <div className="text-lg font-bold">Bitrix24 CRM</div>
            <div className="text-xs text-blue-200">🟢 Активно</div>
          </div>
        </div>
      </div>
    </div>
  );

  const renderDashboardCards = () => {
    const cards = [
      {
        title: 'Всего домов',
        value: dashboardStats.total_houses || 450,
        icon: '🏠',
        gradient: 'from-green-400 to-green-600',
        subtitle: 'из Bitrix24'
      },
      {
        title: 'Квартир',
        value: dashboardStats.total_apartments || 43308,
        icon: '🏢',
        gradient: 'from-blue-400 to-blue-600',
        subtitle: 'Среднее: 96 на дом'
      },
      {
        title: 'Подъездов',
        value: dashboardStats.total_entrances || 1123,
        icon: '🚪',
        gradient: 'from-purple-400 to-purple-600',
        subtitle: 'Среднее: 2.5 на дом'
      },
      {
        title: 'Этажей',
        value: dashboardStats.total_floors || 3372,
        icon: '📊',
        gradient: 'from-orange-400 to-orange-600',
        subtitle: 'Среднее: 7.5 этажей'
      }
    ];

    return (
      <div className="grid grid-cols-2 md:grid-cols-4 gap-6 mb-8">
        {cards.map((card, index) => (
          <div key={index} className="group relative">
            <div className={`absolute -inset-0.5 bg-gradient-to-r ${card.gradient} rounded-2xl blur opacity-20 group-hover:opacity-50 transition duration-500`}></div>
            <div className={`relative bg-gradient-to-br ${card.gradient} text-white p-6 rounded-2xl shadow-xl`}>
              <div className="flex items-center justify-between mb-4">
                <div className="text-3xl">{card.icon}</div>
                <div className="text-right">
                  <div className="text-2xl font-bold">{card.value.toLocaleString('ru-RU')}</div>
                  <div className="text-xs opacity-80">{card.title}</div>
                </div>
              </div>
              <div className="text-xs opacity-90">{card.subtitle}</div>
            </div>
          </div>
        ))}
      </div>
    );
  };

  const renderHouseCard = (house, index) => (
    <div
      key={house.deal_id || index}
      className="bg-white rounded-2xl shadow-lg hover:shadow-2xl transition-all duration-300 transform hover:scale-105 border-l-4 border-blue-500"
    >
      <div className="p-6">
        {/* Заголовок карточки */}
        <div className="flex justify-between items-start mb-4">
          <div className="flex-1">
            <h3 className="text-lg font-bold text-gray-900 mb-1">{house.address}</h3>
            <div className="flex items-center space-x-2">
              <span className="text-gray-500">📍</span>
              {house.house_address ? (
                <button
                  onClick={() => openGoogleMaps(house.house_address)}
                  className="text-blue-600 hover:text-blue-800 underline text-sm transition-colors"
                >
                  {house.house_address}
                </button>
              ) : (
                <span className="text-gray-400 text-sm">{house.address}</span>
              )}
            </div>
          </div>
          <div className="text-right">
            <span className="text-xs text-gray-500">ID: {house.deal_id || `house_${index}`}</span>
          </div>
        </div>

        {/* Статистика дома */}
        <div className="grid grid-cols-3 gap-3 mb-4">
          <div className="bg-green-50 p-3 rounded-lg text-center">
            <div className="text-2xl font-bold text-green-600">{house.apartments_count || 0}</div>
            <div className="text-xs text-green-700">Квартир</div>
          </div>
          <div className="bg-blue-50 p-3 rounded-lg text-center">
            <div className="text-2xl font-bold text-blue-600">{house.entrances_count || 0}</div>
            <div className="text-xs text-blue-700">Подъездов</div>
          </div>
          <div className="bg-orange-50 p-3 rounded-lg text-center">
            <div className="text-2xl font-bold text-orange-600">{house.floors_count || 0}</div>
            <div className="text-xs text-orange-700">Этажей</div>
          </div>
        </div>

        {/* Дополнительная информация */}
        <div className="space-y-2 mb-4">
          <div className="flex items-center justify-between text-sm">
            <span className="text-gray-600">👥 Бригада:</span>
            <span className="font-medium">{house.brigade || 'Не назначена'}</span>
          </div>
          <div className="flex items-center justify-between text-sm">
            <span className="text-gray-600">🏢 УК:</span>
            <span className="font-medium text-xs">{house.management_company || 'Не указана'}</span>
          </div>
          <div className="flex items-center justify-between text-sm">
            <span className="text-gray-600">💰 Цена:</span>
            <span className="font-medium">{house.tariff || 'Не указана'}</span>
          </div>
          <div className="flex items-center justify-between text-sm">
            <span className="text-gray-600">📋 Статус:</span>
            <span className={`px-2 py-1 rounded text-xs font-medium ${
              house.status_color === 'green' ? 'bg-green-100 text-green-800' :
              house.status_color === 'yellow' ? 'bg-yellow-100 text-yellow-800' :
              'bg-gray-100 text-gray-800'
            }`}>
              {house.status_text || 'В работе'}
            </span>
          </div>
        </div>

        {/* График уборки на сентябрь */}
        {cleaningSchedule[house.deal_id] && (
          <div className="mb-4 p-3 bg-indigo-50 rounded-lg">
            <div className="flex items-center space-x-2 mb-2">
              <span className="text-indigo-600">📅</span>
              <span className="font-medium text-indigo-800">График уборки (сентябрь)</span>
            </div>
            <div className="text-sm text-indigo-700">
              {cleaningSchedule[house.deal_id].schedule ? (
                <div className="grid grid-cols-7 gap-1">
                  {cleaningSchedule[house.deal_id].schedule.map((day, dayIndex) => (
                    <div 
                      key={dayIndex} 
                      className={`text-center py-1 rounded ${
                        day.cleaning ? 'bg-indigo-200 text-indigo-900 font-bold' : 'bg-gray-100'
                      }`}
                    >
                      {day.date}
                    </div>
                  ))}
                </div>
              ) : (
                <span>Расписание: {cleaningSchedule[house.deal_id].frequency}</span>
              )}
            </div>
          </div>
        )}

        {/* Кнопки действий */}
        <div className="flex space-x-2">
          <Button
            onClick={() => showNotification(`📅 Календарь для ${house.address}`, 'info')}
            className="flex-1 bg-blue-500 hover:bg-blue-600 text-white px-3 py-2 rounded-lg text-sm flex items-center justify-center space-x-1"
          >
            <span>📅</span>
            <span>Календарь</span>
          </Button>
          <Button
            onClick={() => showNotification(`📊 Подробности для ${house.address}`, 'info')}
            className="flex-1 bg-gray-500 hover:bg-gray-600 text-white px-3 py-2 rounded-lg text-sm flex items-center justify-center space-x-1"
          >
            <span>📊</span>
            <span>Детали</span>
          </Button>
        </div>
      </div>
    </div>
  );

  const NotificationBar = () => {
    if (!notification) return null;

    const bgColor = notification.type === 'success' ? 'bg-green-500' :
                    notification.type === 'error' ? 'bg-red-500' : 'bg-blue-500';

    return (
      <div className={`fixed top-4 right-4 ${bgColor} text-white px-6 py-3 rounded-lg shadow-lg z-50 transform transition-all duration-300`}>
        {notification.message}
      </div>
    );
  };

  if (loading && houses.length === 0) {
    return (
      <div className="p-6 flex justify-center items-center min-h-96">
        <LoadingSpinner size="lg" text="Загрузка домов из Bitrix24..." />
      </div>
    );
  }

  return (
    <div className="p-6 max-w-7xl mx-auto">
      {renderHeader()}
      {renderDashboardCards()}

      {/* Фильтр по месяцам */}
      <Card title="📅 График уборки" className="mb-8">
        <div className="flex items-center space-x-4">
          <label className="font-medium text-gray-700">Месяц:</label>
          <select
            className="p-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
            value={selectedMonth}
            onChange={(e) => {
              setSelectedMonth(e.target.value);
              fetchCleaningSchedule();
            }}
          >
            <option value="september">Сентябрь 2025</option>
            <option value="october">Октябрь 2025</option>
            <option value="november">Ноябрь 2025</option>
            <option value="december">Декабрь 2025</option>
          </select>
          <Button
            onClick={fetchInitialData}
            className="bg-blue-500 hover:bg-blue-600 text-white px-4 py-2 rounded-lg"
          >
            🔄 Обновить данные
          </Button>
        </div>
      </Card>

      {/* Список домов */}
      <Card title={`🏠 Дома (${houses.length})`}>
        {houses.length > 0 ? (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {houses.map((house, index) => renderHouseCard(house, index))}
          </div>
        ) : (
          <div className="text-center py-12">
            <div className="text-6xl mb-4">🏠</div>
            <h3 className="text-lg font-medium text-gray-900 mb-2">Загружаем дома из Bitrix24</h3>
            <p className="text-gray-500">
              Подождите, загружаем данные о домах, квартирах и графике уборки...
            </p>
            <Button
              onClick={fetchInitialData}
              className="mt-4 bg-blue-500 hover:bg-blue-600 text-white px-6 py-2 rounded-lg"
            >
              🔄 Попробовать снова
            </Button>
          </div>
        )}
      </Card>

      <NotificationBar />
    </div>
  );
};

export default Works;