import React, { useState, useEffect, useRef } from 'react';
import { useApp } from '../../context/AppContext';
import { Card, Button, LoadingSpinner } from '../UI';

const WorksEnhanced = () => {
  const { actions } = useApp();
  
  // State
  const [houses, setHouses] = useState([]);
  const [filteredHouses, setFilteredHouses] = useState([]);
  const [filters, setFilters] = useState({
    brigades: [],
    cleaning_weeks: [],
    management_companies: [],
    months: []
  });
  const [dashboardStats, setDashboardStats] = useState({});
  const [loading, setLoading] = useState(false);
  
  // Активные фильтры
  const [activeFilters, setActiveFilters] = useState({
    brigade: '',
    cleaning_week: '',
    month: '',
    management_company: '',
    search: ''
  });

  // UI состояние - ВАУ функции
  const [viewMode, setViewMode] = useState('cards');
  const [selectedMonth, setSelectedMonth] = useState('september'); 
  const [showCalendar, setShowCalendar] = useState(false);
  const [selectedHouse, setSelectedHouse] = useState(null);
  const [showExportModal, setShowExportModal] = useState(false);
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [sortBy, setSortBy] = useState('address');
  const [sortOrder, setSortOrder] = useState('asc');
  const [animatedCards, setAnimatedCards] = useState(new Set());
  const [searchSuggestions, setSearchSuggestions] = useState([]);
  const [showSuggestions, setShowSuggestions] = useState(false);
  const [hoveredCard, setHoveredCard] = useState(null);
  const [notification, setNotification] = useState(null);
  
  // Refs для анимаций
  const searchRef = useRef(null);
  const cardRefs = useRef({});

  useEffect(() => {
    fetchInitialData();
  }, []);

  // API calls
  const fetchInitialData = async () => {
    setLoading(true);
    try {
      await Promise.all([
        fetchFilters(),
        fetchHouses(),
        fetchDashboardStats()
      ]);
    } catch (error) {
      console.error('❌ Error fetching initial data:', error);
    } finally {
      setLoading(false);
    }
  };

  const fetchFilters = async () => {
    try {
      const BACKEND_URL = process.env.REACT_APP_BACKEND_URL || 'http://localhost:8001';
      const response = await fetch(`${BACKEND_URL}/api/cleaning/filters`);
      const data = await response.json();
      setFilters(data);
    } catch (error) {
      console.error('❌ Error fetching filters:', error);
    }
  };

  const fetchHouses = async () => {
    try {
      const BACKEND_URL = process.env.REACT_APP_BACKEND_URL || 'http://localhost:8001';
      const queryParams = new URLSearchParams();
      
      Object.entries(activeFilters).forEach(([key, value]) => {
        if (value) queryParams.append(key, value);
      });
      
      const url = `${BACKEND_URL}/api/cleaning/houses${queryParams.toString() ? '?' + queryParams.toString() : ''}`;
      const response = await fetch(url);
      const data = await response.json();
      
      setHouses(data.houses || []);
      
      // Анимация появления карточек
      const newAnimated = new Set();
      (data.houses || []).forEach((_, index) => {
        setTimeout(() => {
          newAnimated.add(index);
          setAnimatedCards(new Set(newAnimated));
        }, index * 50);
      });
    } catch (error) {
      console.error('❌ Error fetching houses:', error);
    }
  };

  const fetchDashboardStats = async () => {
    try {
      const BACKEND_URL = process.env.REACT_APP_BACKEND_URL || 'http://localhost:8001';
      const response = await fetch(`${BACKEND_URL}/api/cleaning/stats`);
      const data = await response.json();
      setDashboardStats(data);
    } catch (error) {
      console.error('❌ Error fetching stats:', error);
    }
  };

  // ВАУ функции
  const handleSmartSearch = (searchTerm) => {
    setActiveFilters(prev => ({ ...prev, search: searchTerm }));
    
    if (searchTerm.length > 1) {
      const suggestions = houses
        .filter(house => 
          house.address?.toLowerCase().includes(searchTerm.toLowerCase()) ||
          house.house_address?.toLowerCase().includes(searchTerm.toLowerCase())
        )
        .slice(0, 5)
        .map(house => ({
          text: house.address,
          address: house.house_address
        }));
      
      setSearchSuggestions(suggestions);
      setShowSuggestions(true);
    } else {
      setShowSuggestions(false);
    }
  };

  const openGoogleMaps = (address) => {
    if (address) {
      const mapsUrl = `https://www.google.com/maps/search/?api=1&query=${encodeURIComponent(address)}`;
      window.open(mapsUrl, '_blank');
      showNotification('🗺️ Открываем Google Maps...', 'success');
    }
  };

  const handleCreateHouse = async (houseData) => {
    try {
      const BACKEND_URL = process.env.REACT_APP_BACKEND_URL || 'http://localhost:8001';
      const response = await fetch(`${BACKEND_URL}/api/cleaning/houses`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(houseData)
      });
      
      const result = await response.json();
      
      if (response.ok) {
        showNotification(`✅ ${result.message}`, 'success');
        setShowCreateModal(false);
        fetchHouses(); // Обновляем список
      } else {
        showNotification(`❌ ${result.detail}`, 'error');
      }
    } catch (error) {
      console.error('❌ Error creating house:', error);
      showNotification('❌ Ошибка при создании дома', 'error');
    }
  };

  const showNotification = (message, type = 'info') => {
    setNotification({ message, type });
    setTimeout(() => setNotification(null), 3000);
  };

  const exportToCSV = () => {
    const csvData = houses.map(house => ({
      'Адрес': house.address,
      'Реальный адрес': house.house_address || '',
      'Квартир': house.apartments_count || 0,
      'Этажей': house.floors_count || 0,
      'Подъездов': house.entrances_count || 0,
      'Бригада': house.brigade,
      'УК': house.management_company || '',
      'Статус': house.status_text
    }));

    const csv = [
      Object.keys(csvData[0]).join(','),
      ...csvData.map(row => Object.values(row).join(','))
    ].join('\n');

    const blob = new Blob([csv], { type: 'text/csv' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `houses_export_${new Date().toISOString().split('T')[0]}.csv`;
    a.click();
    
    showNotification('📤 CSV файл скачан!', 'success');
    setShowExportModal(false);
  };

  // Рендер функции
  const renderHeader = () => (
    <div className="relative bg-gradient-to-r from-blue-600 via-purple-600 to-indigo-700 text-white p-8 rounded-2xl mb-8 shadow-2xl overflow-hidden">
      {/* Анимированный фон */}
      <div className="absolute inset-0 bg-gradient-to-r from-blue-400/20 via-purple-400/20 to-indigo-400/20 animate-pulse"></div>
      
      {/* Логотип и заголовок */}
      <div className="relative flex items-center justify-between">
        <div className="flex items-center space-x-4">
          <div className="bg-white/10 backdrop-blur-sm rounded-2xl p-4 border border-white/20">
            <img 
              src="/logo.png" 
              alt="Логотип" 
              className="h-12 w-auto object-contain"
              onError={(e) => {
                e.target.style.display = 'none';
                e.target.nextSibling.style.display = 'block';
              }}
            />
            <div 
              className="text-2xl font-bold bg-white/20 rounded-lg px-3 py-1" 
              style={{display: 'none'}}
            >
              РЯДОМ
            </div>
          </div>
          
          <div>
            <h1 className="text-4xl font-bold mb-2 bg-gradient-to-r from-white to-blue-100 bg-clip-text">
              🏠 Управление домами
            </h1>
            <p className="text-blue-100 text-lg">
              Полный контроль над клининговыми объектами
            </p>
          </div>
        </div>

        {/* Кнопка создания */}
        <Button
          onClick={() => setShowCreateModal(true)}
          className="bg-green-500 hover:bg-green-600 text-white px-6 py-3 rounded-xl shadow-lg transform hover:scale-105 transition-all duration-200 flex items-center space-x-2"
        >
          <span className="text-xl">➕</span>
          <span>Создать дом</span>
        </Button>
      </div>
    </div>
  );

  const renderDashboardCards = () => {
    const cards = [
      { 
        title: 'Всего домов', 
        value: dashboardStats.total_houses || 490, 
        icon: '🏠', 
        gradient: 'from-green-400 to-green-600',
        subtitle: '+3 за месяц'
      },
      { 
        title: 'Квартир', 
        value: dashboardStats.total_apartments || 30153, 
        icon: '🏢', 
        gradient: 'from-blue-400 to-blue-600',
        subtitle: 'Среднее: 62 на дом'
      },
      { 
        title: 'Подъездов', 
        value: dashboardStats.total_entrances || 1567, 
        icon: '🚪', 
        gradient: 'from-purple-400 to-purple-600',
        subtitle: 'Среднее: 3 на дом'
      },
      { 
        title: 'Этажей', 
        value: dashboardStats.total_floors || 2512, 
        icon: '📊', 
        gradient: 'from-orange-400 to-orange-600',
        subtitle: 'Среднее: 5 этажей'
      }
    ];

    return (
      <div className="grid grid-cols-2 md:grid-cols-4 gap-6 mb-8">
        {cards.map((card, index) => (
          <div
            key={index}
            className={`bg-gradient-to-br ${card.gradient} text-white p-6 rounded-2xl shadow-xl transform hover:scale-105 transition-all duration-300 hover:shadow-2xl cursor-pointer`}
            onMouseEnter={() => setHoveredCard(index)}
            onMouseLeave={() => setHoveredCard(null)}
          >
            <div className="flex items-center justify-between mb-4">
              <div className={`text-3xl transform transition-transform duration-300 ${hoveredCard === index ? 'scale-110' : ''}`}>
                {card.icon}
              </div>
              <div className="text-right">
                <div className="text-2xl font-bold">{card.value.toLocaleString()}</div>
                <div className="text-xs opacity-80">{card.title}</div>
              </div>
            </div>
            <div className="text-xs opacity-90">{card.subtitle}</div>
          </div>
        ))}
      </div>
    );
  };

  const renderSmartFilters = () => (
    <Card title="🔍 Фильтры поиска" className="mb-8">
      <div className="space-y-4">
        {/* Умный поиск */}
        <div className="relative">
          <div className="flex items-center space-x-2">
            <span className="text-red-500">📍</span>
            <label className="font-medium text-gray-700">Поиск по адресу</label>
          </div>
          <div className="relative mt-2">
            <input
              ref={searchRef}
              type="text"
              placeholder="Введите адрес для поиска..."
              className="w-full p-3 border border-gray-300 rounded-xl focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all duration-200"
              value={activeFilters.search}
              onChange={(e) => handleSmartSearch(e.target.value)}
              onFocus={() => setShowSuggestions(searchSuggestions.length > 0)}
            />
            
            {/* Умные подсказки */}
            {showSuggestions && searchSuggestions.length > 0 && (
              <div className="absolute top-full left-0 right-0 bg-white border border-gray-200 rounded-xl shadow-lg z-10 mt-1">
                {searchSuggestions.map((suggestion, index) => (
                  <div
                    key={index}
                    className="p-3 hover:bg-gray-50 cursor-pointer border-b last:border-b-0"
                    onClick={() => {
                      setActiveFilters(prev => ({ ...prev, search: suggestion.text }));
                      setShowSuggestions(false);
                    }}
                  >
                    <div className="font-medium">{suggestion.text}</div>
                    <div className="text-sm text-gray-500">{suggestion.address}</div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>

        {/* Остальные фильтры */}
        <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
          {/* Бригады */}
          <div>
            <div className="flex items-center space-x-2 mb-2">
              <span className="text-blue-500">👥</span>
              <label className="font-medium text-gray-700">Бригада</label>
            </div>
            <select
              className="w-full p-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
              value={activeFilters.brigade}
              onChange={(e) => setActiveFilters(prev => ({ ...prev, brigade: e.target.value }))}
            >
              <option value="">Все бригады (0)</option>
              {filters.brigades?.map((brigade, index) => (
                <option key={index} value={brigade}>{brigade}</option>
              ))}
            </select>
          </div>

          {/* Недели уборки */}
          <div>
            <div className="flex items-center space-x-2 mb-2">
              <span className="text-orange-500">📅</span>
              <label className="font-medium text-gray-700">Неделя уборки</label>
            </div>
            <select
              className="w-full p-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-orange-500"
              value={activeFilters.cleaning_week}
              onChange={(e) => setActiveFilters(prev => ({ ...prev, cleaning_week: e.target.value }))}
            >
              <option value="">Все недели</option>
              {filters.cleaning_weeks?.map((week, index) => (
                <option key={index} value={week}>Неделя {week}</option>
              ))}
            </select>
          </div>

          {/* Месяцы */}
          <div>
            <div className="flex items-center space-x-2 mb-2">
              <span className="text-purple-500">🗓️</span>
              <label className="font-medium text-gray-700">Месяц</label>
            </div>
            <select
              className="w-full p-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500"
              value={activeFilters.month}
              onChange={(e) => setActiveFilters(prev => ({ ...prev, month: e.target.value }))}
            >
              <option value="">Все месяцы</option>
              {filters.months?.map((month, index) => (
                <option key={index} value={month}>{month}</option>
              ))}
            </select>
          </div>

          {/* УК */}
          <div>
            <div className="flex items-center space-x-2 mb-2">
              <span className="text-green-500">🏢</span>
              <label className="font-medium text-gray-700">УК</label>
            </div>
            <select
              className="w-full p-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500"
              value={activeFilters.management_company}
              onChange={(e) => setActiveFilters(prev => ({ ...prev, management_company: e.target.value }))}
            >
              <option value="">Все УК (0)</option>
              {filters.management_companies?.map((company, index) => (
                <option key={index} value={company}>{company}</option>
              ))}
            </select>
          </div>

          {/* Показать график */}
          <div>
            <div className="flex items-center space-x-2 mb-2">
              <span className="text-indigo-500">📊</span>
              <label className="font-medium text-gray-700">Показать график</label>
            </div>
            <select
              className="w-full p-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500"
              value={selectedMonth}
              onChange={(e) => setSelectedMonth(e.target.value)}
            >
              <option value="september">Сентябрь</option>
              <option value="october">Октябрь</option>
              <option value="november">Ноябрь</option>
              <option value="december">Декабрь</option>
            </select>
          </div>
        </div>

        {/* Кнопки управления */}
        <div className="flex justify-between items-center pt-4 border-t">
          <div className="flex space-x-2">
            <Button
              onClick={fetchHouses}
              className="bg-blue-500 hover:bg-blue-600 text-white px-4 py-2 rounded-lg"
            >
              Применить
            </Button>
            <Button
              onClick={() => {
                setActiveFilters({
                  brigade: '',
                  cleaning_week: '',
                  month: '',
                  management_company: '',
                  search: ''
                });
                setShowSuggestions(false);
              }}
              className="bg-gray-500 hover:bg-gray-600 text-white px-4 py-2 rounded-lg"
            >
              Сбросить
            </Button>
          </div>

          <div className="flex space-x-2">
            <Button
              onClick={() => setShowExportModal(true)}
              className="bg-orange-500 hover:bg-orange-600 text-white px-4 py-2 rounded-lg flex items-center space-x-2"
            >
              <span>📤</span>
              <span>Экспорт</span>
            </Button>
            
            <div className="flex bg-gray-200 rounded-lg">
              <Button
                onClick={() => setViewMode('cards')}
                className={`px-4 py-2 rounded-l-lg ${viewMode === 'cards' ? 'bg-blue-500 text-white' : 'bg-transparent text-gray-700'}`}
              >
                📊 Карточки
              </Button>
              <Button
                onClick={() => setViewMode('table')}
                className={`px-4 py-2 rounded-r-lg ${viewMode === 'table' ? 'bg-blue-500 text-white' : 'bg-transparent text-gray-700'}`}
              >
                📋 Таблица
              </Button>
            </div>
          </div>
        </div>
      </div>
    </Card>
  );

  const renderHouseCard = (house, index) => (
    <div
      key={house.deal_id}
      ref={el => cardRefs.current[index] = el}
      className={`bg-white rounded-2xl shadow-lg hover:shadow-2xl transition-all duration-300 transform hover:scale-105 ${
        animatedCards.has(index) ? 'opacity-100 translate-y-0' : 'opacity-0 translate-y-4'
      } border-l-4 border-blue-500`}
      onMouseEnter={() => setHoveredCard(index)}
      onMouseLeave={() => setHoveredCard(null)}
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
            <span className="text-xs text-gray-500">ID: {house.deal_id}</span>
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
            <span className="font-medium">{house.brigade}</span>
          </div>
          <div className="flex items-center justify-between text-sm">
            <span className="text-gray-600">🏢 УК:</span>
            <span className="font-medium text-xs">{house.management_company || 'Не указана'}</span>
          </div>
          <div className="flex items-center justify-between text-sm">
            <span className="text-gray-600">📋 Статус:</span>
            <span className={`px-2 py-1 rounded text-xs font-medium ${
              house.status_color === 'green' ? 'bg-green-100 text-green-800' :
              house.status_color === 'yellow' ? 'bg-yellow-100 text-yellow-800' :
              'bg-gray-100 text-gray-800'
            }`}>
              {house.status_text}
            </span>
          </div>
        </div>

        {/* Кнопки действий */}
        <div className="flex space-x-2">
          <Button
            onClick={() => {
              setSelectedHouse(house);
              setShowCalendar(true);
            }}
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

  // Модальные окна
  const CreateHouseModal = () => {
    const [formData, setFormData] = useState({
      address: '',
      apartments_count: '',
      floors_count: '',
      entrances_count: '',
      tariff: '',
      management_company: ''
    });

    const handleSubmit = (e) => {
      e.preventDefault();
      const dataToSend = {
        ...formData,
        apartments_count: formData.apartments_count ? parseInt(formData.apartments_count) : null,
        floors_count: formData.floors_count ? parseInt(formData.floors_count) : null,
        entrances_count: formData.entrances_count ? parseInt(formData.entrances_count) : null,
      };
      handleCreateHouse(dataToSend);
    };

    if (!showCreateModal) return null;

    return (
      <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
        <div className="bg-white rounded-2xl p-8 max-w-md w-full mx-4 shadow-2xl">
          <h2 className="text-2xl font-bold mb-6 flex items-center space-x-2">
            <span>🏠</span>
            <span>Создать новый дом</span>
          </h2>
          
          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Адрес дома *
              </label>
              <input
                type="text"
                required
                className="w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                placeholder="Введите адрес дома"
                value={formData.address}
                onChange={(e) => setFormData(prev => ({ ...prev, address: e.target.value }))}
              />
            </div>
            
            <div className="grid grid-cols-3 gap-3">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">Квартир</label>
                <input
                  type="number" 
                  className="w-full p-2 border border-gray-300 rounded-lg"
                  value={formData.apartments_count}
                  onChange={(e) => setFormData(prev => ({ ...prev, apartments_count: e.target.value }))}
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">Этажей</label>
                <input
                  type="number"
                  className="w-full p-2 border border-gray-300 rounded-lg"
                  value={formData.floors_count}
                  onChange={(e) => setFormData(prev => ({ ...prev, floors_count: e.target.value }))}
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">Подъездов</label>
                <input
                  type="number"
                  className="w-full p-2 border border-gray-300 rounded-lg"
                  value={formData.entrances_count}
                  onChange={(e) => setFormData(prev => ({ ...prev, entrances_count: e.target.value }))}
                />
              </div>
            </div>
            
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">Тариф</label>
              <input
                type="text"
                className="w-full p-3 border border-gray-300 rounded-lg"
                placeholder="Тариф уборки"
                value={formData.tariff}
                onChange={(e) => setFormData(prev => ({ ...prev, tariff: e.target.value }))}
              />
            </div>
            
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">Управляющая компания</label>
              <input
                type="text"
                className="w-full p-3 border border-gray-300 rounded-lg"
                placeholder="Название УК"
                value={formData.management_company}
                onChange={(e) => setFormData(prev => ({ ...prev, management_company: e.target.value }))}
              />
            </div>
            
            <div className="flex space-x-3 pt-4">
              <Button
                type="submit"
                className="flex-1 bg-green-500 hover:bg-green-600 text-white py-3 rounded-lg"
              >
                ✅ Создать в Bitrix24
              </Button>
              <Button
                type="button"
                onClick={() => setShowCreateModal(false)}
                className="flex-1 bg-gray-500 hover:bg-gray-600 text-white py-3 rounded-lg"
              >
                ❌ Отмена
              </Button>
            </div>
          </form>
        </div>
      </div>
    );
  };

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
        <LoadingSpinner size="lg" text="Загрузка домов..." />
      </div>
    );
  }

  return (
    <div className="p-6 max-w-7xl mx-auto">
      {renderHeader()}
      {renderDashboardCards()}
      {renderSmartFilters()}
      
      {/* Список домов */}
      <div className="mt-8">
        {viewMode === 'cards' ? (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {houses.map((house, index) => renderHouseCard(house, index))}
          </div>
        ) : (
          <Card title="📋 Таблица домов">
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead>
                  <tr className="border-b">
                    <th className="text-left p-3">Адрес</th>
                    <th className="text-left p-3">Квартир</th>
                    <th className="text-left p-3">Этажей</th>
                    <th className="text-left p-3">Подъездов</th>
                    <th className="text-left p-3">Бригада</th>
                    <th className="text-left p-3">УК</th>
                    <th className="text-left p-3">Статус</th>
                  </tr>
                </thead>
                <tbody>
                  {houses.map((house, index) => (
                    <tr key={house.deal_id} className="border-b hover:bg-gray-50">
                      <td className="p-3">
                        <div>
                          <div className="font-medium">{house.address}</div>
                          {house.house_address && (
                            <button
                              onClick={() => openGoogleMaps(house.house_address)}
                              className="text-blue-600 hover:text-blue-800 underline text-xs"
                            >
                              📍 {house.house_address}
                            </button>
                          )}
                        </div>
                      </td>
                      <td className="p-3">{house.apartments_count || 0}</td>
                      <td className="p-3">{house.floors_count || 0}</td>
                      <td className="p-3">{house.entrances_count || 0}</td>
                      <td className="p-3">{house.brigade}</td>
                      <td className="p-3 text-xs">{house.management_company || '-'}</td>
                      <td className="p-3">
                        <span className={`px-2 py-1 rounded text-xs ${
                          house.status_color === 'green' ? 'bg-green-100 text-green-800' :
                          house.status_color === 'yellow' ? 'bg-yellow-100 text-yellow-800' :
                          'bg-gray-100 text-gray-800'
                        }`}>
                          {house.status_text}
                        </span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </Card>
        )}
      </div>

      <CreateHouseModal />
      <NotificationBar />
    </div>
  );
};

export default WorksEnhanced;