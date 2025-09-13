import React, { useState, useEffect, useRef } from 'react';
import { useApp } from '../../context/AppContext';
import { Card, Button, LoadingSpinner } from '../UI';
import { apiService } from '../../services/apiService';

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
  
  // PRODUCTION: Динамические списки для фильтров
  const [availableCompanies, setAvailableCompanies] = useState([
    // FALLBACK список реальных УК на случай проблем с динамической загрузкой
    'ООО "Жилкомсервис"',
    'ООО "РЯДОМ-Плюс"', 
    'ООО "Мастер-УК"',
    'ООО "Стандарт-УК"',
    'ООО "СовершенствоУК"',
    'ООО "Управдом"',
    'ООО "РЯДОМ-Сервис"',
    'ООО "ГородУК"',
    'ООО "ДомУслуги"',
    'ООО "КомфортСервис"',
    'ООО "Элит-Сервис"',
    'ООО "РЯДОМ-Комфорт"',
    'ООО "ТехноДом"',
    'ООО "ЖЭК-Сервис"',
    'ООО "Премиум-УК"',
    'ООО "Домоуправление"',
    'ООО "УК Центр"',
    'ООО "УК Победа"',
    'ООО "УК Жилетово"',
    'ООО "НовоСтрой-УК"'
  ]);
  const [availableBrigades, setAvailableBrigades] = useState([]);
  
  // Progress state для UX улучшений
  const [loadingProgress, setLoadingProgress] = useState({
    stage: '',
    message: '',
    progress: 0
  });
  
  // UI/UX улучшения - Фаза 3
  const [currentPage, setCurrentPage] = useState(1);
  const [itemsPerPage, setItemsPerPage] = useState(12);
  const [isMobile, setIsMobile] = useState(false);
  const [viewDensity, setViewDensity] = useState('normal'); // compact, normal, spacious
  
  // Активные фильтры - РАСШИРЕННЫЕ
  const [activeFilters, setActiveFilters] = useState({
    search: '',
    brigade: '',
    management_company: '',
    status: '',
    apartments_min: '',
    apartments_max: '',
    month: 'september'
  });
  
  // Сортировка
  const [sortConfig, setSortConfig] = useState({
    field: 'address',
    direction: 'asc'
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
    
    // Детекция мобильных устройств и размера экрана
    const checkDeviceType = () => {
      setIsMobile(window.innerWidth < 768);
      // Автоматическая настройка элементов на страницу
      if (window.innerWidth < 768) {
        setItemsPerPage(6); // Меньше на мобильных
        setViewDensity('compact');
      } else if (window.innerWidth < 1200) {
        setItemsPerPage(9); // Средне на планшетах
      } else {
        setItemsPerPage(12); // Больше на десктопе
      }
    };
    
    checkDeviceType();
    window.addEventListener('resize', checkDeviceType);
    
    return () => window.removeEventListener('resize', checkDeviceType);
  }, []);

  // Эффект для применения фильтров и сортировки
  useEffect(() => {
    applyFiltersAndSort();
  }, [houses, activeFilters, sortConfig]);

  // API calls
  const fetchInitialData = async () => {
    setLoading(true);
    console.log('🔄 Starting initial data load...');
    try {
      // Выполняем последовательно для лучшего контроля ошибок
      await fetchFilters();
      await fetchDashboardStats();
      await fetchHouses(); // Самая важная операция последней
      console.log('✅ Initial data load completed');
    } catch (error) {
      console.error('❌ Error fetching initial data:', error);
    } finally {
      setLoading(false);
      console.log('🔄 Loading state set to false');
    }
  };

  const fetchFilters = async () => {
    try {
      const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
      const response = await fetch(`${BACKEND_URL}/api/cleaning/filters`);
      const data = await response.json();
      setFilters(data);
    } catch (error) {
      console.error('❌ Error fetching filters:', error);
    }
  };

  const fetchHouses = async () => {
    try {
      // Callback для прогресс-бара
      const onProgress = (progressData) => {
        setLoadingProgress(progressData);
        console.log(`🔄 Progress: ${progressData.stage} - ${progressData.message} (${progressData.progress}%)`);
      };
      
      console.log('🏠 Starting unified house loading (490 houses)...');
      
      // Используем унифицированный apiService с прогресс-баром
      const data = await apiService.getCleaningHouses(activeFilters, onProgress);
      
      console.log('🏠 API Response Summary:', {
        status: data?.status,
        total: data?.total,
        houses_count: data?.houses?.length || 0,
        error: data?.message || 'None'
      });
      
      // Простая и надежная логика извлечения данных
      if (data?.status === 'success' && data?.houses && Array.isArray(data.houses)) {
        const housesData = data.houses;
        console.log(`✅ Successfully received ${housesData.length} houses`);
        
        // PRODUCTION: Извлекаем уникальные УК и бригады для фильтров
        const companies = [...new Set(housesData.map(h => h.management_company).filter(Boolean))].sort();
        const brigades = [...new Set(housesData.map(h => h.brigade).filter(Boolean))].sort();
        
        console.log('🏢 ОКОНЧАТЕЛЬНАЯ ЗАГРУЗКА УК:');
        console.log('🏢 Total houses with companies:', housesData.filter(h => h.management_company).length);
        console.log('🏢 Unique companies extracted:', companies.length);
        console.log('🏢 Company sample:', companies.slice(0, 5));
        console.log('🏢 Full companies list:', companies);
        
        setAvailableCompanies(companies);
        setAvailableBrigades(brigades);
        setHouses(housesData);
        
        console.log(`📊 FINAL: ${companies.length} companies and ${brigades.length} brigades loaded`);
        
        // Принудительно показываем что загрузилось
        showNotification(`✅ УК загружено: ${companies.length}, бригад: ${brigades.length}`, 'info');
        
        // Анимация появления карточек (только для первых 50 для производительности)
        const newAnimated = new Set();
        const animationCount = Math.min(housesData.length, 50);
        for (let i = 0; i < animationCount; i++) {
          setTimeout(() => {
            newAnimated.add(i);
            setAnimatedCards(new Set(newAnimated));
          }, i * 30);
        }
        // Добавляем остальные карточки без анимации
        if (housesData.length > 50) {
          setTimeout(() => {
            const allAnimated = new Set();
            for (let i = 0; i < housesData.length; i++) {
              allAnimated.add(i);
            }
            setAnimatedCards(allAnimated);
          }, 1500);
        }
        
        showNotification(`✅ Загружено ${housesData.length} из 490 домов`, 'success');
        
      } else {
        // Обработка ошибок
        console.error('❌ Failed to load houses:', data?.message || 'Unknown error');
        showNotification(`❌ ${data?.message || 'Ошибка загрузки домов'}`, 'error');
        setHouses([]);
      }
      
    } catch (error) {
      console.error('❌ Exception during house loading:', error);
      showNotification('❌ Критическая ошибка загрузки', 'error');
      setHouses([]);
    } finally {
      // Сбрасываем прогресс
      setTimeout(() => {
        setLoadingProgress({ stage: '', message: '', progress: 0 });
      }, 1000);
    }
  };

  const fetchDashboardStats = async () => {
    try {
      const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
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
      const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
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

  // Функция применения фильтров и сортировки
  const applyFiltersAndSort = () => {
    let filtered = [...houses];
    
    // Применяем фильтры
    if (activeFilters.search) {
      const searchTerm = activeFilters.search.toLowerCase();
      filtered = filtered.filter(house =>
        house.address?.toLowerCase().includes(searchTerm) ||
        house.management_company?.toLowerCase().includes(searchTerm)
      );
    }
    
    if (activeFilters.brigade) {
      filtered = filtered.filter(house => house.brigade === activeFilters.brigade);
    }
    
    if (activeFilters.management_company) {
      filtered = filtered.filter(house => house.management_company === activeFilters.management_company);
    }
    
    if (activeFilters.status) {
      filtered = filtered.filter(house => house.status_text === activeFilters.status);
    }
    
    if (activeFilters.apartments_min) {
      filtered = filtered.filter(house => (house.apartments_count || 0) >= parseInt(activeFilters.apartments_min));
    }
    
    if (activeFilters.apartments_max) {
      filtered = filtered.filter(house => (house.apartments_count || 0) <= parseInt(activeFilters.apartments_max));
    }
    
    // Применяем сортировку
    filtered.sort((a, b) => {
      let aVal = a[sortConfig.field];
      let bVal = b[sortConfig.field];
      
      // Обработка разных типов данных
      if (sortConfig.field === 'apartments_count' || sortConfig.field === 'floors_count' || sortConfig.field === 'entrances_count') {
        aVal = aVal || 0;
        bVal = bVal || 0;
      } else if (typeof aVal === 'string') {
        aVal = aVal.toLowerCase();
        bVal = (bVal || '').toLowerCase();
      }
      
      if (aVal < bVal) return sortConfig.direction === 'asc' ? -1 : 1;
      if (aVal > bVal) return sortConfig.direction === 'asc' ? 1 : -1;
      return 0;
    });
    
    setFilteredHouses(filtered);
  };

  // Функция изменения сортировки
  const handleSort = (field) => {
    setSortConfig(prev => ({
      field,
      direction: prev.field === field && prev.direction === 'asc' ? 'desc' : 'asc'
    }));
  };

  // Сброс всех фильтров
  const resetFilters = () => {
    setActiveFilters({
      search: '',
      brigade: '',
      management_company: '',
      status: '',
      apartments_min: '',
      apartments_max: '',
      month: 'september'
    });
    setSortConfig({ field: 'address', direction: 'asc' });
    setShowSuggestions(false);
    setCurrentPage(1); // Сброс пагинации
  };

  // Пагинация
  const totalPages = Math.ceil(filteredHouses.length / itemsPerPage);
  const startIndex = (currentPage - 1) * itemsPerPage;
  const endIndex = startIndex + itemsPerPage;
  const paginatedHouses = filteredHouses.slice(startIndex, endIndex);

  // Функции пагинации
  const goToPage = (page) => {
    setCurrentPage(Math.max(1, Math.min(page, totalPages)));
    window.scrollTo({ top: 0, behavior: 'smooth' });
  };

  const nextPage = () => goToPage(currentPage + 1);
  const prevPage = () => goToPage(currentPage - 1);

  const exportToCSV = () => {
    const csvData = filteredHouses.map(house => ({
      'Адрес': house.address,
      'ID Сделки': house.deal_id,
      'Квартир': house.apartments_count || 0,
      'Этажей': house.floors_count || 0,
      'Подъездов': house.entrances_count || 0,
      'Бригада': house.brigade,
      'УК': house.management_company || '',
      'Статус': house.status_text,
      'График сентябрь': house.september_schedule?.cleaning_date_1?.join(', ') || 'Не назначен'
    }));

    const csv = [
      Object.keys(csvData[0]).join(','),
      ...csvData.map(row => Object.values(row).join(','))
    ].join('\n');

    const blob = new Blob([csv], { type: 'text/csv' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `houses_filtered_${filteredHouses.length}_${new Date().toISOString().split('T')[0]}.csv`;
    a.click();
    
    showNotification(`📤 Экспортировано ${filteredHouses.length} домов в CSV!`, 'success');
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

        {/* Переливающаяся кнопка создания дома */}
        <div className="relative">
          <div className="absolute -inset-0.5 bg-gradient-to-r from-green-400 via-emerald-500 to-green-600 rounded-xl blur opacity-70 animate-pulse"></div>
          <button
            onClick={() => setShowCreateModal(true)}
            className="relative px-6 py-3 bg-gray-900 text-white rounded-xl font-semibold hover:bg-gray-800 transition-all duration-200 flex items-center space-x-2"
          >
            <span>🏠</span>
            <span>Создать дом</span>
          </button>
        </div>
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
          <div key={index} className="group relative">
            <div className={`absolute -inset-0.5 bg-gradient-to-r ${card.gradient} via-${card.gradient.split('-')[1]}-500 rounded-2xl blur opacity-20 group-hover:opacity-50 transition duration-500 ${index === 0 ? 'animate-pulse' : ''}`}></div>
            <div className={`relative bg-gradient-to-br ${card.gradient} text-white p-6 rounded-2xl shadow-xl cursor-pointer`}>
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
          </div>
        ))}
      </div>
    );
  };

  const renderSmartFilters = () => (
    <Card title="🔍 Расширенные фильтры поиска" className="mb-8">
      <div className="space-y-6">
        {/* Умный поиск - улучшенный */}
        <div className="relative">
          <div className="flex items-center justify-between mb-2">
            <div className="flex items-center space-x-2">
              <span className="text-red-500">🔍</span>
              <label className="font-medium text-gray-700">Поиск по адресу или УК</label>
            </div>
            <div className="text-sm text-gray-500">
              Найдено: {filteredHouses.length} из {houses.length}
            </div>
          </div>
          <div className="relative">
            <input
              ref={searchRef}
              type="text"
              placeholder="Введите адрес дома или название УК..."
              className="w-full p-3 pl-10 border border-gray-300 rounded-xl focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all duration-200"
              value={activeFilters.search}
              onChange={(e) => {
                setActiveFilters(prev => ({ ...prev, search: e.target.value }));
                handleSmartSearch(e.target.value);
              }}
              onFocus={() => setShowSuggestions(searchSuggestions.length > 0)}
            />
            <div className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400">
              🔍
            </div>
            
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

        {/* Основные фильтры - адаптивные */}
        <div className={`grid gap-4 ${
          isMobile ? 'grid-cols-1' : 'grid-cols-2 md:grid-cols-4'
        }`}>
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
              <option value="">Все бригады ({availableBrigades.length})</option>
              {availableBrigades.map((brigade, index) => (
                <option key={index} value={brigade}>
                  {brigade}
                </option>
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
              <option value="">Все УК ({availableCompanies.length})</option>
              {availableCompanies.map((company, index) => (
                <option key={index} value={company}>
                  {company?.replace('ООО "', '').replace('"', '') || company}
                </option>
              ))}
            </select>
          </div>

          {/* Статус */}
          <div>
            <div className="flex items-center space-x-2 mb-2">
              <span className="text-purple-500">📊</span>
              <label className="font-medium text-gray-700">Статус</label>
            </div>
            <select
              className="w-full p-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500"
              value={activeFilters.status}
              onChange={(e) => setActiveFilters(prev => ({ ...prev, status: e.target.value }))}
            >
              <option value="">Все статусы</option>
              <option value="🏠 Активный">🏠 Активный</option>
              <option value="⚠️ Проблемный">⚠️ Проблемный</option>
              <option value="🔄 В работе">🔄 В работе</option>
            </select>
          </div>

          {/* Месяц графика */}
          <div>
            <div className="flex items-center space-x-2 mb-2">
              <span className="text-indigo-500">📅</span>
              <label className="font-medium text-gray-700">Месяц графика</label>
            </div>
            <select
              className="w-full p-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500"
              value={activeFilters.month}
              onChange={(e) => setActiveFilters(prev => ({ ...prev, month: e.target.value }))}
            >
              <option value="september">Сентябрь 2025</option>
              <option value="october">Октябрь 2025</option>
              <option value="november">Ноябрь 2025</option>
              <option value="december">Декабрь 2025</option>
            </select>
          </div>
        </div>

        {/* Дополнительные фильтры - адаптивные */}
        <div className="border-t pt-4">
          <h4 className="font-medium text-gray-700 mb-3">🏠 Фильтр по количеству квартир</h4>
          <div className={`grid gap-4 ${isMobile ? 'grid-cols-1' : 'grid-cols-2'}`}>
            <div>
              <label className="block text-sm text-gray-600 mb-1">От</label>
              <input
                type="number"
                placeholder="Мин. квартир"
                className="w-full p-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                value={activeFilters.apartments_min}
                onChange={(e) => setActiveFilters(prev => ({ ...prev, apartments_min: e.target.value }))}
              />
            </div>
            <div>
              <label className="block text-sm text-gray-600 mb-1">До</label>
              <input
                type="number"
                placeholder="Макс. квартир"
                className="w-full p-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                value={activeFilters.apartments_max}
                onChange={(e) => setActiveFilters(prev => ({ ...prev, apartments_max: e.target.value }))}
              />
            </div>
          </div>
        </div>

        {/* Панель сортировки - адаптивная */}
        <div className="border-t pt-4">
          <h4 className="font-medium text-gray-700 mb-3">📊 Сортировка</h4>
          <div className={`flex flex-wrap gap-2 ${isMobile ? 'justify-center' : 'justify-start'}`}>
            {[
              { field: 'address', label: '📍 По адресу' },
              { field: 'apartments_count', label: '🏠 По квартирам' },
              { field: 'brigade', label: '👥 По бригадам' },
              { field: 'management_company', label: '🏢 По УК' },
              { field: 'floors_count', label: '🏗️ По этажам' }
            ].map((sort) => (
              <button
                key={sort.field}
                onClick={() => handleSort(sort.field)}
                className={`px-3 py-2 rounded-lg text-sm font-medium transition-all ${
                  sortConfig.field === sort.field
                    ? 'bg-blue-500 text-white'
                    : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                }`}
              >
                {sort.label}
                {sortConfig.field === sort.field && (
                  <span className="ml-1">
                    {sortConfig.direction === 'asc' ? '↑' : '↓'}
                  </span>
                )}
              </button>
            ))}
          </div>
        </div>

        {/* Кнопки управления - обновленные */}
        <div className="flex justify-between items-center pt-4 border-t">
          <div className="flex space-x-2">
            <Button
              onClick={resetFilters}
              className="bg-gray-500 hover:bg-gray-600 text-white px-4 py-2 rounded-lg flex items-center space-x-2"
            >
              <span>🔄</span>
              <span>Сбросить всё</span>
            </Button>
            <Button
              onClick={fetchHouses}
              className="bg-green-500 hover:bg-green-600 text-white px-4 py-2 rounded-lg flex items-center space-x-2"
            >
              <span>🔄</span>
              <span>Обновить данные</span>
            </Button>
          </div>

          <div className="flex items-center space-x-4">
            {/* Статистика фильтрации */}
            <div className="text-sm text-gray-600 bg-gray-100 px-3 py-2 rounded-lg">
              📊 Показано: <span className="font-bold">{filteredHouses.length}</span> из <span className="font-bold">{houses.length}</span>
            </div>
            
            <Button
              onClick={() => setShowExportModal(true)}
              className="bg-orange-500 hover:bg-orange-600 text-white px-4 py-2 rounded-lg flex items-center space-x-2"
            >
              <span>📤</span>
              <span>Экспорт ({filteredHouses.length})</span>
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
      <div className={`${
        viewDensity === 'compact' ? 'p-4' : 
        viewDensity === 'spacious' ? 'p-8' : 'p-6'
      }`}>
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

        {/* PRODUCTION: Улучшенная информация */}
        <div className="space-y-3 mb-4">
          {/* Основная информация */}
          <div className="grid grid-cols-2 gap-3">
            <div className="bg-gray-50 p-2 rounded-lg">
              <div className="text-xs text-gray-600 mb-1">👥 Бригада</div>
              <div className="font-medium text-xs text-blue-800">
                {house.brigade?.split(' - ')[0]?.replace('бригада', 'бр.') || 'Не назначена'}
              </div>
            </div>
            <div className="bg-gray-50 p-2 rounded-lg">
              <div className="text-xs text-gray-600 mb-1">📋 Статус</div>
              <div className={`text-xs font-medium ${
                house.status_text?.includes('Активный') ? 'text-green-700' :
                house.status_text?.includes('Проблемный') ? 'text-red-700' :
                'text-gray-700'
              }`}>
                {house.status_text || '🏠 Активный'}
              </div>
            </div>
          </div>
          
          {/* УК информация */}
          <div className="bg-blue-50 p-3 rounded-lg border-l-2 border-blue-400">
            <div className="text-xs text-blue-700 font-semibold mb-1">🏢 Управляющая компания:</div>
            <div className="text-xs font-medium text-gray-900">
              {house.management_company?.replace('ООО "', '').replace('"', '') || 'Не указана'}
            </div>
          </div>
          
          {/* Дополнительные детали */}
          <div className="text-xs text-gray-500 bg-gray-50 p-2 rounded">
            <div className="flex justify-between items-center">
              <span>📍 ID сделки:</span>
              <span className="font-mono">{house.deal_id}</span>
            </div>
            {house.created_date && (
              <div className="flex justify-between items-center mt-1">
                <span>📅 Создано:</span>
                <span>{new Date(house.created_date).toLocaleDateString('ru-RU')}</span>
              </div>
            )}
          </div>
        </div>

        {/* PRODUCTION: Корректные графики уборки */}
        {house.september_schedule && house.september_schedule.has_schedule && (
          <div className="bg-gradient-to-r from-green-50 to-blue-50 p-4 rounded-xl mb-4 border border-green-200">
            <div className="text-sm font-bold text-green-800 mb-3 flex items-center space-x-2">
              <span>📅</span>
              <span>График уборки на сентябрь 2025</span>
            </div>
            
            {/* ИСПРАВЛЕНО: Уборка 1 - правильное соответствие типа и дат */}
            {house.september_schedule.cleaning_date_1 && 
             house.september_schedule.cleaning_date_1.length > 0 && (
              <div className="mb-3 p-3 bg-white rounded-lg border-l-4 border-green-500">
                <div className="text-xs font-semibold text-green-700 mb-1">
                  🗓️ Дата уборки 1 | Сентябрь 2025:
                </div>
                <div className="text-xs font-medium text-gray-900 mb-2">
                  {house.september_schedule.cleaning_date_1.map(date => 
                    new Date(date).toLocaleDateString('ru-RU', { 
                      day: '2-digit', 
                      month: '2-digit',
                      year: 'numeric'
                    })
                  ).join(' и ')}
                </div>
                <div className="text-xs font-semibold text-blue-700 mb-1">
                  🧹 Тип уборки 1 | Сентябрь 2025:
                </div>
                <div className="text-xs text-gray-700 leading-relaxed">
                  {house.september_schedule.cleaning_type_1 || 'Тип не указан'}
                </div>
              </div>
            )}
            
            {/* ИСПРАВЛЕНО: Уборка 2 - правильное соответствие типа и дат */}
            {house.september_schedule.cleaning_date_2 && 
             house.september_schedule.cleaning_date_2.length > 0 && (
              <div className="p-3 bg-white rounded-lg border-l-4 border-blue-500">
                <div className="text-xs font-semibold text-green-700 mb-1">
                  🗓️ Дата уборки 2 | Сентябрь 2025:
                </div>
                <div className="text-xs font-medium text-gray-900 mb-2">
                  {house.september_schedule.cleaning_date_2.map(date => 
                    new Date(date).toLocaleDateString('ru-RU', { 
                      day: '2-digit', 
                      month: '2-digit',
                      year: 'numeric'
                    })
                  ).join(' и ')}
                </div>
                <div className="text-xs font-semibold text-blue-700 mb-1">
                  🧹 Тип уборки 2 | Сентябрь 2025:
                </div>
                <div className="text-xs text-gray-700 leading-relaxed">
                  {house.september_schedule.cleaning_type_2 || 'Тип не указан'}
                </div>
              </div>
            )}
            
            {/* Индикатор статуса */}
            <div className="mt-3 flex items-center justify-between">
              <div className="flex items-center space-x-2">
                <div className="w-2 h-2 bg-green-500 rounded-full animate-pulse"></div>  
                <span className="text-xs font-medium text-green-700">
                  График активен
                </span>
              </div>
              <div className="text-xs text-gray-500">
                ID: {house.deal_id}
              </div>
            </div>
          </div>
        )}
        
        {/* Если нет графика */}
        {(!house.september_schedule || !house.september_schedule.has_schedule) && (
          <div className="bg-yellow-50 p-3 rounded-lg mb-4 border-l-4 border-yellow-400">
            <div className="text-sm font-medium text-yellow-800 mb-1">
              ⚠️ График уборки не назначен
            </div>
            <div className="text-xs text-yellow-700">
              Требуется создание графика в Bitrix24
            </div>
          </div>
        )}

        {/* Улучшенные кнопки действий */}
        <div className="grid grid-cols-2 gap-2">
          <Button
            onClick={() => {
              setSelectedHouse(house);
              setShowCalendar(true);
            }}
            className="bg-blue-500 hover:bg-blue-600 text-white px-3 py-2 rounded-lg text-sm flex items-center justify-center space-x-1 transition-all duration-200 hover:scale-105"
          >
            <span>📅</span>
            <span>График</span>
          </Button>
          <Button
            onClick={() => {
              setSelectedHouse(house);
              showNotification(`📊 Открываем детали для ${house.address}`, 'info');
            }}
            className="bg-indigo-500 hover:bg-indigo-600 text-white px-3 py-2 rounded-lg text-sm flex items-center justify-center space-x-1 transition-all duration-200 hover:scale-105"
          >
            <span>🔍</span>
            <span>Детали</span>
          </Button>
        </div>
        
        {/* Дополнительные кнопки для популярных действий */}
        <div className="grid grid-cols-3 gap-1 mt-2">
          <button
            onClick={() => openGoogleMaps(house.address)}
            className="text-xs text-gray-600 hover:text-blue-600 transition-colors p-1 rounded hover:bg-blue-50"
            title="Открыть на карте"
          >
            🗺️ Карта
          </button>
          <button
            onClick={() => showNotification(`📞 Контакты для ${house.address}`, 'info')}
            className="text-xs text-gray-600 hover:text-green-600 transition-colors p-1 rounded hover:bg-green-50"
            title="Контакты"
          >
            📞 Связь
          </button>
          <button
            onClick={() => showNotification(`📝 Заметки для ${house.address}`, 'info')}
            className="text-xs text-gray-600 hover:text-yellow-600 transition-colors p-1 rounded hover:bg-yellow-50"
            title="Заметки"
          >
            📝 Заметки
          </button>
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

  // Компонент skeleton для загрузки
  const renderSkeletonCards = () => (
    <div className={`grid gap-6 ${
      isMobile ? 'grid-cols-1' : 
      viewDensity === 'compact' ? 'grid-cols-1 sm:grid-cols-2 lg:grid-cols-4' :
      viewDensity === 'spacious' ? 'grid-cols-1 lg:grid-cols-2' :
      'grid-cols-1 md:grid-cols-2 lg:grid-cols-3'
    }`}>
      {[1, 2, 3, 4, 5, 6].map(i => (
        <div key={i} className={`bg-white rounded-2xl shadow-lg border-l-4 border-gray-300 animate-pulse ${
          viewDensity === 'compact' ? 'p-4' : viewDensity === 'spacious' ? 'p-8' : 'p-6'
        }`}>
          <div className="flex justify-between items-start mb-4">
            <div className="flex-1">
              <div className="h-5 bg-gray-300 rounded mb-2 w-3/4"></div>
              <div className="h-4 bg-gray-200 rounded w-1/2"></div>
            </div>
            <div className="h-4 bg-gray-200 rounded w-16"></div>
          </div>
          
          <div className={`grid gap-3 mb-4 ${isMobile ? 'grid-cols-2' : 'grid-cols-3'}`}>
            {[1, 2, 3].slice(0, isMobile ? 2 : 3).map(j => (
              <div key={j} className="bg-gray-100 p-3 rounded-lg">
                <div className="h-6 bg-gray-300 rounded mb-1"></div>
                <div className="h-3 bg-gray-200 rounded"></div>
              </div>
            ))}
          </div>
          
          <div className="space-y-2 mb-4">
            {[1, 2, 3].map(k => (
              <div key={k} className="flex justify-between">
                <div className="h-4 bg-gray-200 rounded w-1/3"></div>
                <div className="h-4 bg-gray-300 rounded w-1/2"></div>
              </div>
            ))}
          </div>
          
          <div className={`${isMobile ? 'space-y-2' : 'flex space-x-2'}`}>
            <div className="flex-1 h-8 bg-gray-300 rounded-lg"></div>
            <div className="flex-1 h-8 bg-gray-200 rounded-lg"></div>
          </div>
        </div>
      ))}
    </div>
  );

  // Показываем skeleton loading при загрузке
  const renderHousesSection = () => {
    if (loading && houses.length === 0) {
      return (
        <div className="mt-8">
          {renderSkeletonCards()}
        </div>
      );
    }

    if (houses.length === 0 && !loading) {
      return (
        <div className="mt-8 text-center py-12">
          <div className="text-6xl mb-4">🏠</div>
          <h3 className="text-xl font-bold text-gray-900 mb-2">Дома не найдены</h3>
          <p className="text-gray-500 mb-4">Попробуйте изменить фильтры поиска</p>
          <Button
            onClick={fetchHouses}
            className="bg-blue-500 hover:bg-blue-600 text-white px-6 py-3 rounded-lg"
          >
            🔄 Обновить список
          </Button>
        </div>
      );
    }

    return (
      <div className="mt-8">
        {/* Улучшенный счетчик домов */}
        <div className="flex items-center justify-between mb-6">
          <div className="flex items-center space-x-4">
            <h2 className="text-2xl font-bold text-gray-900">
              📋 Список домов ({filteredHouses.length} из {houses.length})
            </h2>
            <div className="flex space-x-2">
              {filteredHouses.length !== houses.length && (
                <div className="bg-blue-100 text-blue-800 px-3 py-1 rounded-full text-sm font-medium">
                  🔍 Применены фильтры
                </div>
              )}
              {houses.length < 490 && (
                <div className="bg-yellow-100 text-yellow-800 px-3 py-1 rounded-full text-sm font-medium">
                  ⚠️ Загружено {houses.length} из 490
                </div>
              )}
              {houses.length === 490 && (
                <div className="bg-green-100 text-green-800 px-3 py-1 rounded-full text-sm font-medium">
                  ✅ Все дома загружены
                </div>
              )}
            </div>
          </div>
          
          <Button
            onClick={fetchHouses}
            className="bg-green-500 hover:bg-green-600 text-white px-4 py-2 rounded-lg flex items-center space-x-2"
            disabled={loading}
          >
            <span>🔄</span>
            <span>{loading ? 'Загрузка...' : 'Обновить'}</span>
          </Button>
        </div>

        {viewMode === 'cards' ? (
          <div className={`grid gap-6 ${
            isMobile ? 'grid-cols-1' : 
            viewDensity === 'compact' ? 'grid-cols-1 sm:grid-cols-2 lg:grid-cols-4' :
            viewDensity === 'spacious' ? 'grid-cols-1 lg:grid-cols-2' :
            'grid-cols-1 md:grid-cols-2 lg:grid-cols-3'
          }`}>
            {paginatedHouses.map((house, index) => renderHouseCard(house, startIndex + index))}
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
                  {paginatedHouses.map((house, index) => (
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
    );
  };

  return (
    <div className="p-6 max-w-7xl mx-auto">
      {renderHeader()}
      {renderDashboardCards()}
      {renderSmartFilters()}
      
      {/* Прогресс-бар загрузки */}
      {loading && loadingProgress.stage && (
        <div className="bg-white rounded-2xl shadow-lg p-6 mb-8 border-l-4 border-blue-500">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-lg font-bold text-gray-900">🔄 Загрузка домов из Bitrix24</h3>
            <span className="text-sm text-gray-500">{loadingProgress.progress}%</span>
          </div>
          <div className="mb-3">
            <div className="flex justify-between items-center mb-2">
              <span className="text-sm font-medium text-gray-700">{loadingProgress.message}</span>
              <span className="text-sm text-gray-500">{loadingProgress.stage}</span>
            </div>
            <div className="w-full bg-gray-200 rounded-full h-2">
              <div 
                className="bg-blue-500 h-2 rounded-full transition-all duration-300 ease-out"
                style={{ width: `${loadingProgress.progress}%` }}
              ></div>
            </div>
          </div>
          <div className="text-xs text-gray-500">
            Загружаем данные из категории 34 (490 домов) - это может занять до 6 секунд
          </div>
        </div>
      )}
      
      {/* Панель управления отображением - Фаза 3 */}
      {!loading && houses.length > 0 && (
        <div className="flex flex-wrap items-center justify-between mb-6 p-4 bg-gray-50 rounded-2xl">
          <div className="flex items-center space-x-4 mb-2 sm:mb-0">
            <div className="flex items-center space-x-2">
              <span className="text-sm text-gray-600">Плотность:</span>
              <div className="flex bg-white rounded-lg border">
                {[
                  { value: 'compact', label: '📱', title: 'Компактно' },
                  { value: 'normal', label: '💻', title: 'Обычно' },
                  { value: 'spacious', label: '🖥️', title: 'Просторно' }
                ].map((density) => (
                  <button
                    key={density.value}
                    onClick={() => setViewDensity(density.value)}
                    className={`px-3 py-1 text-sm rounded ${
                      viewDensity === density.value
                        ? 'bg-blue-500 text-white'
                        : 'text-gray-600 hover:bg-gray-100'
                    }`}
                    title={density.title}
                  >
                    {density.label}
                  </button>
                ))}
              </div>
            </div>
            
            <div className="flex items-center space-x-2">
              <span className="text-sm text-gray-600">Устройство:</span>
              <span className="text-sm font-medium text-blue-600">
                {isMobile ? '📱 Мобильное' : '💻 Десктоп'}
              </span>
            </div>
          </div>
          
          <div className="flex items-center space-x-2">
            <div className="flex bg-gray-200 rounded-lg">
              <button
                onClick={() => setViewMode('cards')}
                className={`px-4 py-2 rounded-l-lg flex items-center space-x-1 ${
                  viewMode === 'cards' ? 'bg-blue-500 text-white' : 'bg-transparent text-gray-700'
                }`}
              >
                <span>📊</span>
                <span className={isMobile ? 'hidden' : 'inline'}>Карточки</span>
              </button>
              <button
                onClick={() => setViewMode('table')}
                className={`px-4 py-2 rounded-r-lg flex items-center space-x-1 ${
                  viewMode === 'table' ? 'bg-blue-500 text-white' : 'bg-transparent text-gray-700'
                }`}
              >
                <span>📋</span>
                <span className={isMobile ? 'hidden' : 'inline'}>Таблица</span>
              </button>
            </div>
          </div>
        </div>
      )}
      
      {/* Список домов с улучшенным UX */}
      {renderHousesSection()}
      
      {/* Пагинация - Фаза 3 */}
      {!loading && filteredHouses.length > itemsPerPage && (
        <div className="flex flex-col sm:flex-row items-center justify-between mt-8 p-4 bg-white rounded-2xl shadow-lg">
          {/* Информация о пагинации */}
          <div className="text-sm text-gray-600 mb-4 sm:mb-0">
            Показано <span className="font-bold">{startIndex + 1}</span> - <span className="font-bold">{Math.min(endIndex, filteredHouses.length)}</span> из <span className="font-bold">{filteredHouses.length}</span> домов
            <div className="text-xs text-gray-500 mt-1">
              Страница {currentPage} из {totalPages}
            </div>
          </div>
          
          {/* Элементы управления */}
          <div className="flex items-center space-x-2">
            {/* Размер страницы */}
            <div className="flex items-center space-x-2 mr-4">
              <span className="text-sm text-gray-600">На странице:</span>
              <select
                value={itemsPerPage}
                onChange={(e) => {
                  setItemsPerPage(Number(e.target.value));
                  setCurrentPage(1);
                }}
                className="text-sm border border-gray-300 rounded px-2 py-1"
              >
                <option value={6}>6</option>
                <option value={12}>12</option>
                <option value={24}>24</option>
                <option value={48}>48</option>
              </select>
            </div>
            
            {/* Кнопки навигации */}
            <button
              onClick={() => goToPage(1)}
              disabled={currentPage === 1}
              className="px-3 py-1 rounded bg-gray-100 text-gray-600 disabled:opacity-50 hover:bg-gray-200"
            >
              ⏮️
            </button>
            <button
              onClick={prevPage}
              disabled={currentPage === 1}
              className="px-3 py-1 rounded bg-gray-100 text-gray-600 disabled:opacity-50 hover:bg-gray-200"
            >
              ◀️
            </button>
            
            {/* Номера страниц */}
            <div className="flex space-x-1">
              {Array.from({ length: Math.min(5, totalPages) }, (_, i) => {
                const pageNum = Math.max(1, Math.min(totalPages - 4, currentPage - 2)) + i;
                if (pageNum > totalPages) return null;
                
                return (
                  <button
                    key={pageNum}
                    onClick={() => goToPage(pageNum)}
                    className={`px-3 py-1 rounded text-sm ${
                      pageNum === currentPage
                        ? 'bg-blue-500 text-white'
                        : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
                    }`}
                  >
                    {pageNum}
                  </button>
                );
              })}
            </div>
            
            <button
              onClick={nextPage}
              disabled={currentPage === totalPages}
              className="px-3 py-1 rounded bg-gray-100 text-gray-600 disabled:opacity-50 hover:bg-gray-200"
            >
              ▶️
            </button>
            <button
              onClick={() => goToPage(totalPages)}
              disabled={currentPage === totalPages}
              className="px-3 py-1 rounded bg-gray-100 text-gray-600 disabled:opacity-50 hover:bg-gray-200"
            >
              ⏭️
            </button>
          </div>
        </div>
      )}

      {/* Уведомления */}
      {notification && (
        <div className={`fixed top-4 right-4 ${
          notification.type === 'success' ? 'bg-green-500' :
          notification.type === 'error' ? 'bg-red-500' : 'bg-blue-500'
        } text-white px-6 py-3 rounded-lg shadow-lg z-50 transform transition-all duration-300`}>
          {notification.message}
        </div>
      )}
    </div>
  );
};

export default WorksEnhanced;