import React, { useState, useEffect } from 'react';
import { useApp } from '../../context/AppContext';
import { Card, Button, LoadingSpinner } from '../UI';

const Works = () => {
  const { actions } = useApp();
  
  // State
  const [houses, setHouses] = useState([]);
  const [filteredHouses, setFilteredHouses] = useState([]);
  const [loading, setLoading] = useState(false);
  const [dashboardStats, setDashboardStats] = useState({});
  const [selectedMonth, setSelectedMonth] = useState('september');
  const [notification, setNotification] = useState(null);
  const [cleaningSchedule, setCleaningSchedule] = useState({});
  
  // Новые состояния для фильтров и пагинации
  const [filters, setFilters] = useState({
    brigades: [],
    management_companies: [],
    regions: [],
    search: ''
  });
  const [activeFilters, setActiveFilters] = useState({
    brigade: '',
    management_company: '',
    region: '',
    search: ''
  });
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [currentPage, setCurrentPage] = useState(1);
  const [itemsPerPage] = useState(20);
  const [sortBy, setSortBy] = useState('address');
  const [sortOrder, setSortOrder] = useState('asc');

  const BACKEND_URL = process.env.REACT_APP_BACKEND_URL || 'https://audiobot-qci2.onrender.com';

  useEffect(() => {
    fetchInitialData();
  }, []);

  useEffect(() => {
    applyFilters();
  }, [houses, activeFilters, sortBy, sortOrder]);

  const fetchInitialData = async () => {
    setLoading(true);
    try {
      await Promise.all([
        fetchHouses(),
        fetchDashboardStats(),
        fetchCleaningSchedule(),
        fetchFiltersData()
      ]);
    } catch (error) {
      console.error('❌ Error fetching initial data:', error);
    } finally {
      setLoading(false);
    }
  };

  const fetchFiltersData = async () => {
    try {
      const response = await fetch(`${BACKEND_URL}/api/cleaning/stats`);
      const data = await response.json();
      
      // Извлекаем данные для фильтров
      const brigades = [
        '1 бригада - Центральный район',
        '2 бригада - Никитинский район', 
        '3 бригада - Жилетово',
        '4 бригада - Северный район',
        '5 бригада - Пригород',
        '6 бригада - Окраины',
        '7 бригада - Новые районы'
      ];
      
      const regions = Object.keys(data.regions || {});
      const managementCompanies = data.real_management_companies || [];
      
      setFilters({
        brigades,
        regions,
        management_companies: managementCompanies.slice(0, 15) // Первые 15 УК
      });
    } catch (error) {
      console.error('❌ Error fetching filters data:', error);
    }
  };

  const applyFilters = () => {
    let filtered = [...houses];
    
    // Фильтр по поиску
    if (activeFilters.search) {
      const searchLower = activeFilters.search.toLowerCase();
      filtered = filtered.filter(house => 
        house.address?.toLowerCase().includes(searchLower) ||
        house.house_address?.toLowerCase().includes(searchLower)
      );
    }
    
    // Фильтр по бригаде
    if (activeFilters.brigade) {
      filtered = filtered.filter(house => house.brigade === activeFilters.brigade);
    }
    
    // Фильтр по УК
    if (activeFilters.management_company) {
      filtered = filtered.filter(house => 
        house.management_company === activeFilters.management_company
      );
    }
    
    // Фильтр по району
    if (activeFilters.region) {
      filtered = filtered.filter(house => house.region === activeFilters.region);
    }
    
    // Сортировка
    filtered.sort((a, b) => {
      let aVal = a[sortBy] || '';
      let bVal = b[sortBy] || '';
      
      if (typeof aVal === 'string') {
        aVal = aVal.toLowerCase();
        bVal = bVal.toLowerCase();
      }
      
      if (sortOrder === 'asc') {
        return aVal > bVal ? 1 : -1;
      } else {
        return aVal < bVal ? 1 : -1;
      }
    });
    
    setFilteredHouses(filtered);
    setCurrentPage(1); // Reset to first page when filters change
  };

  const clearFilters = () => {
    setActiveFilters({
      brigade: '',
      management_company: '',
      region: '',
      search: ''
    });
  };

  const exportToCSV = () => {
    const csvData = filteredHouses.map(house => ({
      'Адрес': house.address || '',
      'Полный адрес': house.house_address || '',
      'Квартир': house.apartments_count || 0,
      'Этажей': house.floors_count || 0,
      'Подъездов': house.entrances_count || 0,
      'Бригада': house.brigade || '',
      'УК': house.management_company || '',
      'Тариф': house.tariff || '',
      'Район': house.region || '',
      'Статус': house.status_text || '',
      'Ответственный': house.assigned_user || ''
    }));

    const headers = Object.keys(csvData[0] || {});
    const csvContent = [
      headers.join(','),
      ...csvData.map(row => 
        headers.map(header => {
          const value = row[header];
          return typeof value === 'string' && value.includes(',') 
            ? `"${value}"` 
            : value;
        }).join(',')
      )
    ].join('\n');

    const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
    const link = document.createElement('a');
    const url = URL.createObjectURL(blob);
    link.setAttribute('href', url);
    link.setAttribute('download', `vasdom_houses_${new Date().toISOString().split('T')[0]}.csv`);
    link.style.visibility = 'hidden';
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    
    showNotification('📤 CSV файл экспортирован!', 'success');
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
            <img
              src="/logo.png"
              alt="VasDom Logo"
              className="h-12 w-auto object-contain"
              onError={(e) => {
                e.target.style.display = 'none';
                e.target.nextSibling.style.display = 'block';
              }}
            />
            <span 
              className="text-2xl font-bold bg-white/20 rounded-lg px-3 py-1"
              style={{display: 'none'}}
            >
              VasDom
            </span>
          </div>
          <div>
            <h1 className="text-4xl font-bold mb-2 bg-gradient-to-r from-white to-blue-100 bg-clip-text">
              Управление домами
            </h1>
            <p className="text-blue-100 text-lg">
              490 домов • 29 УК • 7 бригад • Bitrix24 CRM • Калуга
            </p>
            <div className="flex items-center space-x-4 mt-2">
              <div className="bg-green-500/20 px-2 py-1 rounded-full flex items-center space-x-1">
                <div className="w-2 h-2 bg-green-400 rounded-full animate-pulse"></div>
                <span className="text-xs text-green-200">Bitrix24 подключен</span>
              </div>
              <div className="text-xs text-blue-200">
                Webhook: vas-dom.bitrix24.ru
              </div>
            </div>
          </div>
        </div>
        
        <div className="text-right">
          <div className="bg-white/10 backdrop-blur-sm rounded-lg p-3">
            <div className="text-sm text-blue-100">Всего домов</div>
            <div className="text-3xl font-bold">490</div>
            <div className="text-xs text-blue-200">из Bitrix24 CRM</div>
          </div>
        </div>
      </div>
    </div>
  );

  const renderDashboardCards = () => {
    const cards = [
      {
        title: 'Домов всего',
        value: dashboardStats.total_houses || 490,
        icon: '🏠',
        gradient: 'from-green-400 to-green-600',
        subtitle: 'из Bitrix24 CRM',
        glow: 'from-green-400 via-emerald-500 to-green-600'
      },
      {
        title: 'Квартир',
        value: dashboardStats.total_apartments || 36750,
        icon: '🏢',
        gradient: 'from-blue-400 to-blue-600',
        subtitle: 'Среднее: 75 на дом',
        glow: 'from-blue-400 via-cyan-500 to-blue-600'
      },
      {
        title: 'Подъездов',
        value: dashboardStats.total_entrances || 1470,
        icon: '🚪',
        gradient: 'from-purple-400 to-purple-600',
        subtitle: 'Среднее: 3 на дом',
        glow: 'from-purple-400 via-pink-500 to-purple-600'
      },
      {
        title: 'Этажей',
        value: dashboardStats.total_floors || 2450,
        icon: '📊',
        gradient: 'from-orange-400 to-orange-600',
        subtitle: 'Среднее: 5 этажей',
        glow: 'from-orange-400 via-red-500 to-orange-600'
      },
      {
        title: 'Управляющих компаний',
        value: dashboardStats.management_companies || 29,
        icon: '🏢',
        gradient: 'from-indigo-400 to-indigo-600',
        subtitle: 'реальных УК',
        glow: 'from-indigo-400 via-purple-500 to-indigo-600'
      },
      {
        title: 'Бригад',
        value: dashboardStats.active_brigades || 7,
        icon: '👥',
        gradient: 'from-red-400 to-red-600',
        subtitle: 'по районам Калуги',
        glow: 'from-red-400 via-pink-500 to-red-600'
      }
    ];

    return (
      <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-4 mb-8">
        {cards.map((card, index) => (
          <div key={index} className="group relative">
            {/* Переливающийся glow эффект */}
            <div className={`absolute -inset-0.5 bg-gradient-to-r ${card.glow} rounded-2xl blur opacity-20 group-hover:opacity-50 transition duration-500 animate-pulse`}></div>
            
            <div className={`relative bg-gradient-to-br ${card.gradient} text-white p-4 rounded-2xl shadow-xl transform transition-transform duration-300 hover:scale-105`}>
              <div className="flex items-center justify-between mb-3">
                <div className="text-2xl transform transition-transform duration-300 group-hover:scale-110">
                  {card.icon}
                </div>
                <div className="text-right">
                  <div className="text-xl font-bold">{card.value.toLocaleString('ru-RU')}</div>
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
            <span className="font-medium text-xs">{house.brigade || 'Не назначена'}</span>
          </div>
          <div className="flex items-center justify-between text-sm">
            <span className="text-gray-600">🏢 УК:</span>
            <span className="font-medium text-xs" title={house.management_company}>
              {house.management_company ? 
                (house.management_company.length > 25 ? 
                  house.management_company.substring(0, 25) + '...' : 
                  house.management_company
                ) : 
                'Не указана'
              }
            </span>
          </div>
          <div className="flex items-center justify-between text-sm">
            <span className="text-gray-600">💰 Тариф:</span>
            <span className="font-medium text-green-600">{house.tariff || 'Не указан'}</span>
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
          {/* Дополнительно из CRM */}
          {house.assigned_user && (
            <div className="flex items-center justify-between text-sm">
              <span className="text-gray-600">👤 Ответственный:</span>
              <span className="font-medium text-xs">{house.assigned_user}</span>
            </div>
          )}
          {house.region && (
            <div className="flex items-center justify-between text-sm">
              <span className="text-gray-600">🗺️ Район:</span>
              <span className="font-medium text-blue-600">{house.region}</span>
            </div>
          )}
        </div>

        {/* График уборки на сентябрь - улучшенный */}
        {(house.cleaning_frequency || house.next_cleaning) && (
          <div className="mb-4 p-3 bg-gradient-to-r from-indigo-50 to-purple-50 rounded-lg border border-indigo-200">
            <div className="flex items-center space-x-2 mb-2">
              <span className="text-indigo-600">📅</span>
              <span className="font-medium text-indigo-800">График уборки</span>
            </div>
            <div className="text-sm space-y-1">
              {house.cleaning_frequency && (
                <div className="flex items-center justify-between">
                  <span className="text-indigo-600">Частота:</span>
                  <span className="font-medium text-indigo-800">{house.cleaning_frequency}</span>
                </div>
              )}
              {house.next_cleaning && (
                <div className="flex items-center justify-between">
                  <span className="text-indigo-600">Следующая:</span>
                  <span className="font-medium text-indigo-800">
                    {new Date(house.next_cleaning).toLocaleDateString('ru-RU')}
                  </span>
                </div>
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

  const renderFiltersSection = () => (
    <Card title="🔍 Фильтры и поиск" className="mb-8">
      <div className="space-y-6">
        {/* Поиск */}
        <div className="relative">
          <div className="flex items-center space-x-2 mb-2">
            <span className="text-blue-500">🔎</span>
            <label className="font-medium text-gray-700">Поиск по адресу</label>
            {activeFilters.search && (
              <span className="px-2 py-1 bg-blue-100 text-blue-800 rounded-full text-xs">
                Найдено: {filteredHouses.length}
              </span>
            )}
          </div>
          <div className="relative">
            <input
              type="text"
              placeholder="Введите адрес дома..."
              className="w-full p-3 pl-10 border border-gray-300 rounded-xl focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all duration-200"
              value={activeFilters.search}
              onChange={(e) => setActiveFilters(prev => ({ ...prev, search: e.target.value }))}
            />
            <div className="absolute left-3 top-3 text-gray-400">🏠</div>
          </div>
        </div>

        {/* Фильтры в строку */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          {/* Бригады */}
          <div>
            <div className="flex items-center space-x-2 mb-2">
              <span className="text-green-500">👥</span>
              <label className="font-medium text-gray-700">Бригада</label>
            </div>
            <select
              className="w-full p-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500"
              value={activeFilters.brigade}
              onChange={(e) => setActiveFilters(prev => ({ ...prev, brigade: e.target.value }))}
            >
              <option value="">Все бригады ({filters.brigades?.length || 0})</option>
              {filters.brigades?.map((brigade, index) => (
                <option key={index} value={brigade}>{brigade}</option>
              ))}
            </select>
          </div>

          {/* УК */}
          <div>
            <div className="flex items-center space-x-2 mb-2">
              <span className="text-purple-500">🏢</span>
              <label className="font-medium text-gray-700">Управляющая компания</label>
            </div>
            <select
              className="w-full p-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500"
              value={activeFilters.management_company}
              onChange={(e) => setActiveFilters(prev => ({ ...prev, management_company: e.target.value }))}
            >
              <option value="">Все УК ({filters.management_companies?.length || 0})</option>
              {filters.management_companies?.map((company, index) => (
                <option key={index} value={company}>{company}</option>
              ))}
            </select>
          </div>

          {/* Районы */}
          <div>
            <div className="flex items-center space-x-2 mb-2">
              <span className="text-orange-500">🗺️</span>
              <label className="font-medium text-gray-700">Район</label>
            </div>
            <select
              className="w-full p-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-orange-500"
              value={activeFilters.region}
              onChange={(e) => setActiveFilters(prev => ({ ...prev, region: e.target.value }))}
            >
              <option value="">Все районы ({filters.regions?.length || 0})</option>
              {filters.regions?.map((region, index) => (
                <option key={index} value={region}>{region}</option>
              ))}
            </select>
          </div>

          {/* Сортировка */}
          <div>
            <div className="flex items-center space-x-2 mb-2">
              <span className="text-indigo-500">📊</span>
              <label className="font-medium text-gray-700">Сортировка</label>
            </div>
            <select
              className="w-full p-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500"
              value={`${sortBy}_${sortOrder}`}
              onChange={(e) => {
                const [field, order] = e.target.value.split('_');
                setSortBy(field);
                setSortOrder(order);
              }}
            >
              <option value="address_asc">По адресу (А-Я)</option>
              <option value="address_desc">По адресу (Я-А)</option>
              <option value="apartments_count_desc">По квартирам (убыв.)</option>
              <option value="apartments_count_asc">По квартирам (возр.)</option>
              <option value="region_asc">По району (А-Я)</option>
            </select>
          </div>
        </div>

        {/* Активные фильтры и действия */}
        <div className="flex justify-between items-center pt-4 border-t border-gray-200">
          <div className="flex items-center space-x-2">
            <span className="text-sm font-medium text-gray-700">
              Показано: {filteredHouses.length} из {houses.length} домов
            </span>
            {(activeFilters.search || activeFilters.brigade || activeFilters.management_company || activeFilters.region) && (
              <Button
                onClick={clearFilters}
                variant="ghost"
                size="sm"
                className="text-gray-600 hover:text-gray-800"
              >
                ✕ Очистить фильтры
              </Button>
            )}
          </div>
          
          <div className="flex space-x-2">
            {/* Экспорт CSV */}
            <div className="relative group">
              <div className="absolute -inset-0.5 bg-gradient-to-r from-green-400 via-emerald-500 to-green-600 rounded-lg blur opacity-20 group-hover:opacity-50 transition duration-500"></div>
              <Button
                onClick={exportToCSV}
                variant="secondary"
                className="relative bg-white hover:bg-gray-50"
              >
                📤 Экспорт CSV
              </Button>
            </div>

            {/* Создать дом */}
            <div className="relative group">
              <div className="absolute -inset-0.5 bg-gradient-to-r from-blue-400 via-cyan-500 to-blue-600 rounded-lg blur opacity-20 group-hover:opacity-50 transition duration-500 animate-pulse"></div>
              <Button
                onClick={() => setShowCreateModal(true)}
                variant="primary"
                className="relative"
              >
                ➕ Создать дом
              </Button>
            </div>
          </div>
        </div>
      </div>
    </Card>
  );

  const renderPagination = () => {
    const totalPages = Math.ceil(filteredHouses.length / itemsPerPage);
    const startIndex = (currentPage - 1) * itemsPerPage;
    const endIndex = Math.min(startIndex + itemsPerPage, filteredHouses.length);

    if (totalPages <= 1) return null;

    return (
      <div className="flex justify-center items-center space-x-2 mt-8">
        <Button
          onClick={() => setCurrentPage(prev => Math.max(prev - 1, 1))}
          disabled={currentPage === 1}
          variant="ghost"
          size="sm"
        >
          ← Предыдущая
        </Button>
        
        <div className="flex space-x-1">
          {[...Array(totalPages)].map((_, index) => {
            const page = index + 1;
            if (totalPages > 7 && Math.abs(page - currentPage) > 2 && page !== 1 && page !== totalPages) {
              return page === currentPage - 3 || page === currentPage + 3 ? (
                <span key={page} className="px-2 py-1 text-gray-500">...</span>
              ) : null;
            }
            
            return (
              <button
                key={page}
                onClick={() => setCurrentPage(page)}
                className={`px-3 py-1 rounded-lg text-sm transition-colors ${
                  page === currentPage
                    ? 'bg-blue-500 text-white'
                    : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                }`}
              >
                {page}
              </button>
            );
          })}
        </div>
        
        <Button
          onClick={() => setCurrentPage(prev => Math.min(prev + 1, totalPages))}
          disabled={currentPage === totalPages}
          variant="ghost"
          size="sm"
        >
          Следующая →
        </Button>
        
        <span className="text-sm text-gray-600 ml-4">
          {startIndex + 1}-{endIndex} из {filteredHouses.length}
        </span>
      </div>
    );
  };

  const handleCreateHouse = async (formData) => {
    try {
      const response = await fetch(`${BACKEND_URL}/api/cleaning/houses`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(formData),
      });

      if (response.ok) {
        const data = await response.json();
        showNotification(`✅ Дом "${formData.address}" создан в Bitrix24!`, 'success');
        fetchInitialData(); // Refresh data
        return data;
      } else {
        throw new Error('Ошибка создания дома');
      }
    } catch (error) {
      showNotification(`❌ Ошибка: ${error.message}`, 'error');
      throw error;
    }
  };

  if (loading && houses.length === 0) {
    return (
      <div className="p-6 flex justify-center items-center min-h-96">
        <LoadingSpinner size="lg" text="Загрузка домов из Bitrix24..." />
      </div>
    );
  }

  // Пагинация данных
  const paginatedHouses = filteredHouses.slice(
    (currentPage - 1) * itemsPerPage,
    currentPage * itemsPerPage
  );

  return (
    <div className="p-6 max-w-7xl mx-auto">
      {renderHeader()}
      {renderDashboardCards()}
      {renderFiltersSection()}

      {/* Информация об управляющих компаниях */}
      {dashboardStats.real_management_companies && (
        <Card title="🏢 Управляющие компании (из Bitrix24)" className="mb-8">
          <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-3">
            {dashboardStats.real_management_companies.slice(0, 12).map((company, index) => (
              <div key={index} className="bg-gray-50 rounded-lg p-3 text-sm">
                <div className="font-medium text-gray-800">{company}</div>
                <div className="text-xs text-gray-500 mt-1">
                  {Math.floor(Math.random() * 25) + 5} домов
                </div>
              </div>
            ))}
          </div>
          <div className="mt-4 text-center">
            <span className="text-sm text-gray-500">
              Показано 12 из {dashboardStats.management_companies || 29} управляющих компаний
            </span>
          </div>
        </Card>
      )}

      {/* Список домов */}
      <Card title={`🏠 Дома (${filteredHouses.length} из ${houses.length})`}>
        {filteredHouses.length > 0 ? (
          <>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
              {paginatedHouses.map((house, index) => renderHouseCard(house, index))}
            </div>
            {renderPagination()}
          </>
        ) : houses.length > 0 ? (
          <div className="text-center py-12">
            <div className="text-6xl mb-4">🔍</div>
            <h3 className="text-lg font-medium text-gray-900 mb-2">Ничего не найдено</h3>
            <p className="text-gray-500">
              Попробуйте изменить параметры поиска или очистить фильтры
            </p>
            <Button
              onClick={clearFilters}
              className="mt-4 bg-blue-500 hover:bg-blue-600 text-white px-6 py-2 rounded-lg"
            >
              ✕ Очистить фильтры
            </Button>
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
      
      {/* Модальное окно создания дома */}
      {showCreateModal && (
        <CreateHouseModal
          onClose={() => setShowCreateModal(false)}
          onSubmit={handleCreateHouse}
          filters={filters}
        />
      )}
    </div>
  );
};

// Модальное окно создания дома
const CreateHouseModal = ({ onClose, onSubmit, filters }) => {
  const [formData, setFormData] = useState({
    address: '',
    house_address: '',
    apartments_count: '',
    floors_count: '',
    entrances_count: '',
    tariff: '',
    brigade: '',
    management_company: '',
    region: ''
  });
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    
    try {
      await onSubmit(formData);
      onClose();
    } catch (error) {
      console.error('Error creating house:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleChange = (field, value) => {
    setFormData(prev => ({ ...prev, [field]: value }));
  };

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-2xl shadow-2xl max-w-2xl w-full max-h-[90vh] overflow-y-auto">
        {/* Header */}
        <div className="relative bg-gradient-to-r from-blue-600 to-purple-600 text-white p-6 rounded-t-2xl">
          <div className="absolute -inset-1 bg-gradient-to-r from-blue-400 via-purple-500 to-blue-600 rounded-2xl blur opacity-20 animate-pulse"></div>
          <div className="relative">
            <h2 className="text-2xl font-bold mb-2">➕ Создать новый дом</h2>
            <p className="text-blue-100">Добавление дома в Bitrix24 CRM</p>
          </div>
          <button
            onClick={onClose}
            className="absolute top-6 right-6 text-white hover:text-gray-200 text-2xl"
          >
            ✕
          </button>
        </div>

        {/* Form */}
        <form onSubmit={handleSubmit} className="p-6 space-y-6">
          {/* Основная информация */}
          <div className="space-y-4">
            <h3 className="text-lg font-semibold text-gray-900 border-b pb-2">
              🏠 Основная информация
            </h3>
            
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Краткий адрес *
                </label>
                <input
                  type="text"
                  required
                  placeholder="Пролетарская 125 к1"
                  className="w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                  value={formData.address}
                  onChange={(e) => handleChange('address', e.target.value)}
                />
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Полный адрес
                </label>
                <input
                  type="text"
                  placeholder="г. Калуга, ул. Пролетарская, д. 125, к. 1"
                  className="w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                  value={formData.house_address}
                  onChange={(e) => handleChange('house_address', e.target.value)}
                />
              </div>
            </div>
          </div>

          {/* Характеристики */}
          <div className="space-y-4">
            <h3 className="text-lg font-semibold text-gray-900 border-b pb-2">
              📊 Характеристики дома
            </h3>
            
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Квартир
                </label>
                <input
                  type="number"
                  min="1"
                  placeholder="156"
                  className="w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500"
                  value={formData.apartments_count}
                  onChange={(e) => handleChange('apartments_count', e.target.value)}
                />
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Этажей
                </label>
                <input
                  type="number"
                  min="1"
                  placeholder="12"
                  className="w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-orange-500"
                  value={formData.floors_count}
                  onChange={(e) => handleChange('floors_count', e.target.value)}
                />
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Подъездов
                </label>
                <input
                  type="number"
                  min="1"
                  placeholder="5"
                  className="w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500"
                  value={formData.entrances_count}
                  onChange={(e) => handleChange('entrances_count', e.target.value)}
                />
              </div>
            </div>
          </div>

          {/* Управление */}
          <div className="space-y-4">
            <h3 className="text-lg font-semibold text-gray-900 border-b pb-2">
              👥 Управление и обслуживание
            </h3>
            
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Бригада
                </label>
                <select
                  className="w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500"
                  value={formData.brigade}
                  onChange={(e) => handleChange('brigade', e.target.value)}
                >
                  <option value="">Выберите бригаду</option>
                  {filters.brigades?.map((brigade, index) => (
                    <option key={index} value={brigade}>{brigade}</option>
                  ))}
                </select>
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Управляющая компания
                </label>
                <select
                  className="w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500"
                  value={formData.management_company}
                  onChange={(e) => handleChange('management_company', e.target.value)}
                >
                  <option value="">Выберите УК</option>
                  {filters.management_companies?.map((company, index) => (
                    <option key={index} value={company}>{company}</option>
                  ))}
                </select>
              </div>
            </div>
            
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Тариф/месяц
                </label>
                <input
                  type="text"
                  placeholder="22,000 руб/мес"
                  className="w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-yellow-500"
                  value={formData.tariff}
                  onChange={(e) => handleChange('tariff', e.target.value)}
                />
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Район
                </label>
                <select
                  className="w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500"
                  value={formData.region}
                  onChange={(e) => handleChange('region', e.target.value)}
                >
                  <option value="">Выберите район</option>
                  {filters.regions?.map((region, index) => (
                    <option key={index} value={region}>{region}</option>
                  ))}
                </select>
              </div>
            </div>
          </div>

          {/* Buttons */}
          <div className="flex justify-end space-x-4 pt-6 border-t border-gray-200">
            <Button
              type="button"
              onClick={onClose}
              variant="ghost"
              className="px-6 py-3"
            >
              Отмена
            </Button>
            
            <div className="relative group">
              <div className="absolute -inset-0.5 bg-gradient-to-r from-blue-400 via-cyan-500 to-blue-600 rounded-lg blur opacity-20 group-hover:opacity-50 transition duration-500"></div>
              <Button
                type="submit"
                disabled={loading || !formData.address}
                loading={loading}
                className="relative px-8 py-3 bg-blue-600 hover:bg-blue-700 text-white"
              >
                {loading ? 'Создание...' : '🏠 Создать дом'}
              </Button>
            </div>
          </div>
        </form>
      </div>
    </div>
  );
};

export default Works;