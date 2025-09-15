import React, { useState, useEffect, useRef } from 'react';
import { 
  Building2, 
  Search, 
  Filter, 
  MapPin, 
  Users, 
  Calendar,
  BarChart3,
  RefreshCw,
  Download,
  Plus,
  Home,
  Layers,
  DoorOpen
} from 'lucide-react';

const Works = () => {
  // State
  const [houses, setHouses] = useState([]);
  const [filters, setFilters] = useState({
    brigades: [],
    management_companies: [],
    statuses: []
  });
  const [loading, setLoading] = useState(false);
  
  // Активные фильтры
  const [activeFilters, setActiveFilters] = useState({
    brigade: '',
    management_company: '',
    status: '',
    search: ''
  });
  
  // UI состояние
  const [viewMode, setViewMode] = useState('cards');
  const [searchSuggestions, setSearchSuggestions] = useState([]);
  const [showSuggestions, setShowSuggestions] = useState(false);
  const [notification, setNotification] = useState(null);
  const [animatedCards, setAnimatedCards] = useState(new Set());
  
  const searchRef = useRef(null);

  useEffect(() => {
    fetchInitialData();
  }, []);

  useEffect(() => {
    fetchHouses();
  }, [activeFilters]);

  // API calls
  const fetchInitialData = async () => {
    setLoading(true);
    try {
      await Promise.all([
        fetchFilters(),
        fetchHouses()
      ]);
    } catch (error) {
      console.error('❌ Error fetching initial data:', error);
      showNotification('❌ Ошибка загрузки данных', 'error');
    } finally {
      setLoading(false);
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
      const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
      const queryParams = new URLSearchParams();
      
      Object.entries(activeFilters).forEach(([key, value]) => {
        if (value) queryParams.append(key, value);
      });

      const url = `${BACKEND_URL}/api/cleaning/houses${queryParams.toString() ? '?' + queryParams.toString() : ''}`;
      console.log('🏠 Fetching houses from:', url);

      const response = await fetch(url);
      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }

      const data = await response.json();
      console.log('🏠 Houses data received:', data);

      const housesData = data.houses || data || [];
      setHouses(housesData);

      // Анимация появления карточек
      const newAnimated = new Set();
      housesData.forEach((_, index) => {
        setTimeout(() => {
          newAnimated.add(index);
          setAnimatedCards(new Set(newAnimated));
        }, index * 50);
      });

      console.log(`✅ Loaded ${housesData.length} houses`);
      showNotification(`✅ Загружено ${housesData.length} домов из Bitrix24`, 'success');
      
    } catch (error) {
      console.error('❌ Error fetching houses:', error);
      showNotification('❌ Ошибка загрузки домов из Bitrix24', 'error');
      setHouses([]);
    }
  };

  // Smart search
  const handleSmartSearch = (searchTerm) => {
    setActiveFilters(prev => ({ ...prev, search: searchTerm }));
    
    if (searchTerm.length > 1) {
      const suggestions = houses
        .filter(house =>
          house.address?.toLowerCase().includes(searchTerm.toLowerCase()) ||
          house.title?.toLowerCase().includes(searchTerm.toLowerCase())
        )
        .slice(0, 5)
        .map(house => ({
          text: house.address || house.title,
          address: house.title
        }));
      
      setSearchSuggestions(suggestions);
      setShowSuggestions(true);
    } else {
      setShowSuggestions(false);
    }
  };

  const showNotification = (message, type = 'info') => {
    setNotification({ message, type });
    setTimeout(() => setNotification(null), 3000);
  };

  // Render функции
  const renderHeader = () => (
    <div className="mb-8 animate-fade-scale">
      <div className="text-center space-y-4">
        <h1 className="text-3xl font-bold gradient-text flex items-center justify-center">
          <Building2 className="w-8 h-8 mr-3 text-blue-600" />
          Управление домами
        </h1>
        <p className="text-lg text-gray-600">
          Полная интеграция с Bitrix24 • {houses.length} домов в системе
        </p>
      </div>

      {/* Статистика */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mt-8">
        <div className="bg-gradient-to-br from-blue-500 to-blue-600 text-white p-6 rounded-xl shadow-elegant">
          <div className="flex items-center justify-between">
            <div>
              <div className="text-2xl font-bold">{houses.length}</div>
              <div className="text-blue-100 text-sm">Домов загружено</div>
            </div>
            <Building2 className="w-8 h-8 text-blue-200" />
          </div>
        </div>
        
        <div className="bg-gradient-to-br from-green-500 to-green-600 text-white p-6 rounded-xl shadow-elegant">
          <div className="flex items-center justify-between">
            <div>
              <div className="text-2xl font-bold">
                {houses.reduce((sum, house) => sum + (house.apartments || 0), 0).toLocaleString()}
              </div>
              <div className="text-green-100 text-sm">Квартир</div>
            </div>
            <Home className="w-8 h-8 text-green-200" />
          </div>
        </div>
        
        <div className="bg-gradient-to-br from-purple-500 to-purple-600 text-white p-6 rounded-xl shadow-elegant">
          <div className="flex items-center justify-between">
            <div>
              <div className="text-2xl font-bold">{filters.management_companies?.length || 0}</div>
              <div className="text-purple-100 text-sm">УК в системе</div>
            </div>
            <Users className="w-8 h-8 text-purple-200" />
          </div>
        </div>
        
        <div className="bg-gradient-to-br from-orange-500 to-orange-600 text-white p-6 rounded-xl shadow-elegant">
          <div className="flex items-center justify-between">
            <div>
              <div className="text-2xl font-bold">{filters.brigades?.length || 0}</div>
              <div className="text-orange-100 text-sm">Бригад</div>
            </div>
            <BarChart3 className="w-8 h-8 text-orange-200" />
          </div>
        </div>
      </div>
    </div>
  );

  const renderSmartFilters = () => (
    <div className="card-modern mb-8 animate-slide-up">
      <div className="flex items-center justify-between mb-6">
        <h2 className="text-xl font-semibold text-gray-900 flex items-center">
          <Filter className="w-5 h-5 mr-2 text-blue-600" />
          Умные фильтры домов
        </h2>
        
        <div className="flex items-center space-x-3">
          <button
            onClick={fetchHouses}
            disabled={loading}
            className="btn-primary flex items-center space-x-2"
          >
            <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
            <span>{loading ? 'Обновление...' : 'Обновить'}</span>
          </button>
          
          <button className="px-4 py-2 bg-green-500 hover:bg-green-600 text-white rounded-lg flex items-center space-x-2 transition-colors">
            <Download className="w-4 h-4" />
            <span>Экспорт</span>
          </button>
        </div>
      </div>

      {/* Умный поиск */}
      <div className="relative mb-6">
        <div className="flex items-center space-x-2 mb-2">
          <Search className="w-5 h-5 text-blue-500" />
          <label className="font-medium text-gray-700">Поиск по адресу</label>
          {searchSuggestions.length > 0 && (
            <span className="text-xs bg-blue-100 text-blue-800 px-2 py-1 rounded-full">
              {searchSuggestions.length} предложений
            </span>
          )}
        </div>
        
        <div className="relative">
          <input
            ref={searchRef}
            type="text"
            placeholder="Начните вводить адрес..."
            className="w-full p-3 pl-10 border border-gray-300 rounded-xl focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all duration-200"
            value={activeFilters.search}
            onChange={(e) => handleSmartSearch(e.target.value)}
            onFocus={() => setShowSuggestions(searchSuggestions.length > 0)}
          />
          <Search className="absolute left-3 top-3 w-5 h-5 text-gray-400" />
          
          {/* Suggestions dropdown */}
          {showSuggestions && searchSuggestions.length > 0 && (
            <div className="absolute top-full left-0 right-0 bg-white border border-gray-200 rounded-xl shadow-lg z-10 mt-1 max-h-60 overflow-y-auto">
              {searchSuggestions.map((suggestion, index) => (
                <div
                  key={index}
                  className="p-3 hover:bg-blue-50 cursor-pointer border-b last:border-b-0 flex items-center space-x-2"
                  onClick={() => {
                    setActiveFilters(prev => ({ ...prev, search: suggestion.text }));
                    setShowSuggestions(false);
                  }}
                >
                  <MapPin className="w-4 h-4 text-blue-500" />
                  <div className="flex-1">
                    <div className="font-medium">{suggestion.text}</div>
                    <div className="text-sm text-gray-500">{suggestion.address}</div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>

      {/* Фильтры */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2 flex items-center">
            <Users className="w-4 h-4 mr-1 text-blue-500" />
            Бригады
            <span className="ml-2 text-xs bg-blue-100 text-blue-800 px-2 py-1 rounded-full">
              {filters.brigades?.length || 0}
            </span>
          </label>
          <select
            className="w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 bg-white"
            value={activeFilters.brigade}
            onChange={(e) => setActiveFilters(prev => ({ ...prev, brigade: e.target.value }))}
          >
            <option value="">Все бригады</option>
            {filters.brigades?.map((brigade, index) => (
              <option key={index} value={brigade}>{brigade}</option>
            ))}
          </select>
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2 flex items-center">
            <Building2 className="w-4 h-4 mr-1 text-green-500" />
            Управляющие компании
            <span className="ml-2 text-xs bg-green-100 text-green-800 px-2 py-1 rounded-full">
              {filters.management_companies?.length || 0}
            </span>
          </label>
          <select
            className="w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500 bg-white"
            value={activeFilters.management_company}
            onChange={(e) => setActiveFilters(prev => ({ ...prev, management_company: e.target.value }))}
          >
            <option value="">Все УК</option>
            {filters.management_companies?.map((company, index) => (
              <option key={index} value={company}>{company}</option>
            ))}
          </select>
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2 flex items-center">
            <BarChart3 className="w-4 h-4 mr-1 text-purple-500" />
            Статус
            <span className="ml-2 text-xs bg-purple-100 text-purple-800 px-2 py-1 rounded-full">
              {filters.statuses?.length || 0}
            </span>
          </label>
          <select
            className="w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 bg-white"
            value={activeFilters.status}
            onChange={(e) => setActiveFilters(prev => ({ ...prev, status: e.target.value }))}
          >
            <option value="">Все статусы</option>
            {filters.statuses?.map((status, index) => (
              <option key={index} value={status}>{status}</option>
            ))}
          </select>
        </div>
      </div>

      {/* Reset button */}
      <div className="mt-6 flex justify-between items-center">
        <button
          onClick={() => {
            setActiveFilters({
              brigade: '',
              management_company: '',
              status: '',
              search: ''
            });
            setShowSuggestions(false);
          }}
          className="px-4 py-2 bg-gray-500 hover:bg-gray-600 text-white rounded-lg transition-colors"
        >
          ↻ Сбросить фильтры
        </button>
        
        <div className="text-sm text-gray-600">
          Найдено: <span className="font-semibold">{houses.length}</span> домов
        </div>
      </div>
    </div>
  );

  const renderHouseCard = (house, index) => (
    <div
      key={house.id || index}
      className={`card-modern shadow-hover transition-all duration-300 ${
        animatedCards.has(index) ? 'animate-fade-scale' : 'opacity-0'
      }`}
      style={{ animationDelay: `${index * 50}ms` }}
    >
      {/* Header */}
      <div className="flex items-start justify-between mb-4">
        <div className="flex items-center space-x-3">
          <div className="w-12 h-12 bg-gradient-to-br from-blue-500 to-purple-600 rounded-xl flex items-center justify-center">
            <Building2 className="w-6 h-6 text-white" />
          </div>
          <div>
            <h3 className="text-lg font-semibold text-gray-900">
              {house.title || house.address || 'Без названия'}
            </h3>
            <p className="text-sm text-gray-500">ID: {house.id || 'N/A'}</p>
          </div>
        </div>
        <div className="text-xs bg-green-100 text-green-800 px-2 py-1 rounded-full">
          Активный
        </div>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-3 gap-3 mb-4">
        <div className="bg-gradient-to-r from-emerald-500 to-emerald-600 text-white p-3 rounded-lg text-center">
          <div className="text-lg font-bold">{house.apartments || 0}</div>
          <div className="text-xs text-emerald-100">Квартир</div>
        </div>
        <div className="bg-gradient-to-r from-blue-500 to-blue-600 text-white p-3 rounded-lg text-center">
          <div className="text-lg font-bold">{house.entrances || 0}</div>
          <div className="text-xs text-blue-100">Подъездов</div>
        </div>
        <div className="bg-gradient-to-r from-orange-500 to-orange-600 text-white p-3 rounded-lg text-center">
          <div className="text-lg font-bold">{house.floors || 0}</div>
          <div className="text-xs text-orange-100">Этажей</div>
        </div>
      </div>

      {/* Info */}
      <div className="space-y-3 mb-4">
        <div className="flex items-center space-x-2 text-sm">
          <Building2 className="w-4 h-4 text-blue-600" />
          <span className="font-medium">УК:</span>
          <span className="text-gray-700">{house.management_company || 'Не указана'}</span>
        </div>
        
        <div className="flex items-center space-x-2 text-sm">
          <Users className="w-4 h-4 text-green-600" />
          <span className="font-medium">Бригада:</span>
          <span className="text-gray-700">{house.brigade || 'Не назначена'}</span>
        </div>
        
        <div className="flex items-center space-x-2 text-sm">
          <Calendar className="w-4 h-4 text-purple-600" />
          <span className="font-medium">График:</span>
          <span className="text-gray-700">
            {Object.keys(house.cleaning_dates || {}).length > 0 ? 'Настроен' : 'Не указан'}
          </span>
        </div>
      </div>

      {/* Actions */}
      <div className="grid grid-cols-2 gap-2">
        <button className="bg-blue-500 hover:bg-blue-600 text-white px-4 py-2 rounded-lg text-sm font-medium flex items-center justify-center space-x-1 transition-colors">
          <Calendar className="w-4 h-4" />
          <span>График</span>
        </button>
        <button className="bg-green-500 hover:bg-green-600 text-white px-4 py-2 rounded-lg text-sm font-medium flex items-center justify-center space-x-1 transition-colors">
          <MapPin className="w-4 h-4" />
          <span>Детали</span>
        </button>
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
      <div className="p-8 flex justify-center items-center min-h-96">
        <div className="flex items-center space-x-3">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
          <span className="text-lg font-medium text-gray-600">Загрузка домов из Bitrix24...</span>
        </div>
      </div>
    );
  }

  return (
    <div className="p-8 max-w-7xl mx-auto">
      {renderHeader()}
      {renderSmartFilters()}
      
      {/* Houses Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {houses.map((house, index) => renderHouseCard(house, index))}
      </div>

      {/* Empty State */}
      {houses.length === 0 && !loading && (
        <div className="text-center py-12 animate-fade-scale">
          <div className="text-6xl mb-4">🏠</div>
          <h2 className="text-2xl font-bold text-gray-900 mb-2">Дома не найдены</h2>
          <p className="text-gray-600 mb-6">Проверьте подключение к Bitrix24 или измените фильтры</p>
          <button
            onClick={fetchHouses}
            className="btn-primary flex items-center space-x-2 mx-auto"
          >
            <RefreshCw className="w-4 h-4" />
            <span>Попробовать снова</span>
          </button>
        </div>
      )}

      <NotificationBar />
    </div>
  );
};

export default Works;