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
import DatePicker from 'react-datepicker';
import { ru } from 'date-fns/locale';
import 'react-datepicker/dist/react-datepicker.css';

const Works = () => {
  // State
  const [houses, setHouses] = useState([]);
  const [pagination, setPagination] = useState({
    total: 0,
    page: 1,
    limit: 50,
    pages: 0
  });
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
    cleaning_date: '',
    search: ''
  });
  
  // UI состояние
  const [searchSuggestions, setSearchSuggestions] = useState([]);
  const [showSuggestions, setShowSuggestions] = useState(false);
  const [notification, setNotification] = useState(null);
  const [animatedCards, setAnimatedCards] = useState(new Set());
  const [showScheduleModal, setShowScheduleModal] = useState(false);
  const [selectedHouse, setSelectedHouse] = useState(null);
  const [showDetailsModal, setShowDetailsModal] = useState(false);
  const [houseDetails, setHouseDetails] = useState(null);
  const [detailsLoading, setDetailsLoading] = useState(false);
  
  const searchRef = useRef(null);

  useEffect(() => {
    fetchInitialData();
  }, []);

  useEffect(() => {
    fetchHouses();
  }, [activeFilters, pagination.page, pagination.limit]);

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
      
      queryParams.append('page', pagination.page.toString());
      queryParams.append('limit', pagination.limit.toString());

      const url = `${BACKEND_URL}/api/cleaning/houses?${queryParams.toString()}`;
      const response = await fetch(url);
      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }

      const data = await response.json();
      const housesData = data.houses || [];
      setHouses(housesData);
      setPagination({
        total: data.total || 0,
        page: data.page || 1,
        limit: data.limit || 50,
        pages: data.pages || 0
      });

      const newAnimated = new Set();
      housesData.forEach((_, index) => {
        setTimeout(() => {
          newAnimated.add(index);
          setAnimatedCards(new Set(newAnimated));
        }, index * 50);
      });

      showNotification(`✅ Загружено ${housesData.length} домов из ${data.total}`, 'success');
      
    } catch (error) {
      console.error('❌ Error fetching houses:', error);
      showNotification('❌ Ошибка загрузки домов из Bitrix24', 'error');
      setHouses([]);
    }
  };

  const showNotification = (message, type = 'info') => {
    setNotification({ message, type });
    setTimeout(() => setNotification(null), 3000);
  };

  const handlePageChange = (newPage) => {
    setPagination(prev => ({ ...prev, page: newPage }));
    setAnimatedCards(new Set());
  };

  const handleLimitChange = (newLimit) => {
    setPagination(prev => ({ 
      ...prev, 
      limit: parseInt(newLimit), 
      page: 1
    }));
    setAnimatedCards(new Set());
  };

  const fetchHouseDetails = async (houseId) => {
    setDetailsLoading(true);
    try {
      const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
      const response = await fetch(`${BACKEND_URL}/api/cleaning/house/${houseId}/details`);
      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }
      const data = await response.json();
      setHouseDetails(data);
      setShowDetailsModal(true);
    } catch (error) {
      console.error('❌ Error fetching house details:', error);
      showNotification('❌ Ошибка загрузки деталей дома', 'error');
    } finally {
      setDetailsLoading(false);
    }
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
    <div className="pt-2 px-6 pb-8 max-w-7xl mx-auto">
      {/* Header */}
      <div className="mb-4 animate-fade-scale">
        <h1 className="text-2xl font-bold gradient-text flex items-center">
          <Building2 className="w-7 h-7 mr-3 text-blue-600" />
          Управление домами
        </h1>
        <p className="text-sm text-gray-600 mt-1">
          Полная интеграция с Bitrix24 • {pagination.total.toLocaleString()} домов в системе
        </p>
      </div>

      {/* Filters */}
      <div className="card-modern mb-8 animate-slide-up">
        <div className="flex items-center justify-between mb-6">
          <h2 className="text-xl font-semibold text-gray-900">Фильтры домов</h2>
          <button
            onClick={fetchHouses}
            disabled={loading}
            className="btn-primary"
          >
            <RefreshCw className={`w-4 h-4 mr-2 ${loading ? 'animate-spin' : ''}`} />
            Обновить
          </button>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-2">
          <select
            className="w-full p-3 border border-gray-300 rounded-lg bg-white"
            value={activeFilters.brigade}
            onChange={(e) => { setActiveFilters(prev => ({ ...prev, brigade: e.target.value })); setPagination(prev => ({...prev, page: 1})); }}
          >
            <option value="">Все бригады</option>
            {filters.brigades?.map((brigade, index) => (
              <option key={index} value={brigade}>{brigade}</option>
            ))}
          </select>

          <select
            className="w-full p-3 border border-gray-300 rounded-lg bg-white"
            value={activeFilters.management_company}
            onChange={(e) => { setActiveFilters(prev => ({ ...prev, management_company: e.target.value })); setPagination(prev => ({...prev, page: 1})); }}
          >
            <option value="">Все УК</option>
            {filters.management_companies?.map((company, index) => (
              <option key={index} value={company}>{company}</option>
            ))}
          </select>

          {/* Фильтр по дате уборки */}
          <DatePicker
            selected={activeFilters.cleaning_date ? new Date(activeFilters.cleaning_date) : null}
            onChange={(date) => {
              const val = date ? date.toISOString().slice(0,10) : '';
              setActiveFilters(prev => ({ ...prev, cleaning_date: val }));
              setPagination(prev => ({...prev, page: 1}));
            }}
            placeholderText="Дата уборки"
            dateFormat="yyyy-MM-dd"
            className="w-full p-3 border border-gray-300 rounded-lg bg-white"
            locale={ru}
            isClearable
          />



        </div>
      </div>
      
      {/* Houses Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {houses.map((house, index) => (
          <div
            key={house.id || index}
            className={`card-modern shadow-hover transition-all duration-300 ${
              animatedCards.has(index) ? 'animate-fade-scale' : 'opacity-0'
            }`}
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
                  <p className="text-sm text-gray-500">ID: {house.id}</p>
                </div>
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
                <Layers className="w-4 h-4 text-indigo-600" />
                <span className="font-medium">Периодичность:</span>
                <span className="text-gray-700">{house.periodicity || 'индивидуальная'}</span>
              </div>
              
              <div className="flex items-center space-x-2 text-sm">
                <Users className="w-4 h-4 text-green-600" />
                <span className="font-medium">Бригада №:</span>
                <span className="text-gray-700">{house.brigade || 'Не назначена'}</span>
              </div>
            </div>

            {/* График уборки сентябрь */}
            {house.cleaning_dates && (house.cleaning_dates.september_1 || house.cleaning_dates.september_2) && (
              <div className="mb-4 p-4 bg-purple-50 rounded-lg border border-purple-200">
                <h4 className="text-sm font-semibold text-purple-800 mb-3">🗓️ График уборки 2025</h4>
                
                <div className="bg-white p-3 rounded-lg border border-purple-100">
                  <div className="text-xs font-medium text-purple-700 mb-3">🍂 Сентябрь</div>
                  <div className="space-y-3">
                    {house.cleaning_dates.september_1 && house.cleaning_dates.september_1.dates && house.cleaning_dates.september_1.dates.length > 0 && (
                      <div className="space-y-2">
                        <div className="flex items-start space-x-2">
                          <span className="w-5 h-5 bg-purple-500 text-white rounded-full flex items-center justify-center text-xs font-bold">1</span>
                          <div className="flex-1">
                            <div className="flex flex-wrap gap-1 mb-2">
                              {house.cleaning_dates.september_1.dates.map((date, idx) => (
                                <span key={idx} className="bg-purple-100 text-purple-800 px-2 py-1 rounded text-xs font-medium border border-purple-200">
                                  {date}
                                </span>
                              ))}
                            </div>
                            <div className="text-purple-600 text-xs leading-relaxed">
                              {house.cleaning_dates.september_1.type}
                            </div>
                          </div>
                        </div>
                      </div>
                    )}
                    
                    {house.cleaning_dates.september_2 && house.cleaning_dates.september_2.dates && house.cleaning_dates.september_2.dates.length > 0 && (
                      <div className="space-y-2">
                        <div className="flex items-start space-x-2">
                          <span className="w-5 h-5 bg-purple-500 text-white rounded-full flex items-center justify-center text-xs font-bold">2</span>
                          <div className="flex-1">
                            <div className="flex flex-wrap gap-1 mb-2">
                              {house.cleaning_dates.september_2.dates.map((date, idx) => (
                                <span key={idx} className="bg-purple-100 text-purple-800 px-2 py-1 rounded text-xs font-medium border border-purple-200">
                                  {date}
                                </span>
                              ))}
                            </div>
                            <div className="text-purple-600 text-xs leading-relaxed">
                              {house.cleaning_dates.september_2.type}
                            </div>
                          </div>
                        </div>
                      </div>
                    )}
                  </div>
                </div>

      {/* Pagination */}
      <div className="flex items-center justify-center mt-6 space-x-2">
        <button
          onClick={() => handlePageChange(Math.max(1, pagination.page - 1))}
          disabled={pagination.page <= 1}
          className="px-3 py-2 bg-white border rounded-lg text-sm disabled:opacity-50"
        >
          ← Предыдущая
        </button>
        {Array.from({ length: pagination.pages || 0 }, (_, i) => i + 1).slice(Math.max(0, pagination.page - 3), Math.max(3, pagination.page + 2)).map(p => (
          <button
            key={p}
            onClick={() => handlePageChange(p)}
            className={`px-3 py-2 border rounded-lg text-sm ${p === pagination.page ? 'bg-blue-600 text-white border-blue-600' : 'bg-white'}`}
          >
            {p}
          </button>
        ))}
        <button
          onClick={() => handlePageChange(Math.min(pagination.pages, pagination.page + 1))}
          disabled={pagination.page >= pagination.pages}
          className="px-3 py-2 bg-white border rounded-lg text-sm disabled:opacity-50"
        >
          Следующая →
        </button>
      </div>

              </div>
            )}

            {/* Actions */}
            <div className="grid grid-cols-2 gap-2">
              <button 
                onClick={() => {
                  setSelectedHouse(house);
                  setShowScheduleModal(true);
                }}
                className="bg-blue-500 hover:bg-blue-600 text-white px-4 py-2 rounded-lg text-sm font-medium flex items-center justify-center space-x-1 transition-colors"
              >
                <Calendar className="w-4 h-4" />
                <span>График</span>
              </button>
              <button 
                onClick={() => fetchHouseDetails(house.id)}
                disabled={detailsLoading}
                className="bg-green-500 hover:bg-green-600 text-white px-4 py-2 rounded-lg text-sm font-medium flex items-center justify-center space-x-1 transition-colors disabled:opacity-50"
              >
                <MapPin className="w-4 h-4" />
                <span>{detailsLoading ? 'Загрузка...' : 'Детали'}</span>
              </button>
            </div>
          </div>
        ))}
      </div>

      {/* Модальное окно */}
      {showScheduleModal && selectedHouse && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-xl max-w-2xl w-full max-h-[80vh] overflow-y-auto">
            <div className="p-6">
              <div className="flex items-center justify-between mb-6">
                <h2 className="text-xl font-semibold text-gray-900">
                  График уборки: {selectedHouse.title}
                </h2>
                <button
                  onClick={() => setShowScheduleModal(false)}
                  className="p-2 hover:bg-gray-100 rounded-lg"
                >
                  ✕
                </button>
              </div>

              <div className="space-y-4">
                {/* Все месяцы в модальном окне */}
                {Object.entries(selectedHouse.cleaning_dates || {}).map(([key, cleaning]) => {
                  if (!cleaning.dates || cleaning.dates.length === 0) return null;
                  
                  let monthName = '';
                  let bgColor = '';
                  let textColor = '';
                  
                  if (key.includes('september')) {
                    monthName = '🍂 Сентябрь 2025';
                    bgColor = 'bg-purple-50';
                    textColor = 'text-purple-700';
                  } else if (key.includes('october')) {
                    monthName = '🍁 Октябрь 2025';
                    bgColor = 'bg-orange-50';
                    textColor = 'text-orange-700';
                  } else if (key.includes('november')) {
                    monthName = '❄️ Ноябрь 2025';
                    bgColor = 'bg-yellow-50';
                    textColor = 'text-yellow-700';
                  } else if (key.includes('december')) {
                    monthName = '⛄ Декабрь 2025';
                    bgColor = 'bg-blue-50';
                    textColor = 'text-blue-700';
                  }
                  
                  return (
                    <div key={key} className={`${bgColor} p-4 rounded-lg`}>
                      <div className={`text-sm font-medium ${textColor} mb-3`}>{monthName}</div>
                      <div className="bg-white p-3 rounded-lg">
                        <div className="flex flex-wrap gap-2 mb-2">
                          {cleaning.dates.map((date, idx) => (
                            <span key={idx} className="bg-gray-100 px-3 py-1 rounded text-sm">
                              {date}
                            </span>
                          ))}
                        </div>
                        <div className="text-gray-700 text-sm">{cleaning.type}</div>
                      </div>
                    </div>
                  );
                })}
              </div>

              <div className="mt-6 flex justify-end">
                <button
                  onClick={() => setShowScheduleModal(false)}
                  className="px-6 py-2 bg-gray-500 hover:bg-gray-600 text-white rounded-lg"
                >
                  Закрыть
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Модальное окно деталей */}
      {showDetailsModal && houseDetails && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-xl max-w-3xl w-full max-h-[90vh] overflow-y-auto">
            <div className="p-6">
              <div className="flex items-center justify-between mb-6">
                <h2 className="text-2xl font-semibold text-gray-900">
                  Детали дома: {houseDetails.house.title}
                </h2>
                <button
                  onClick={() => setShowDetailsModal(false)}
                  className="p-2 hover:bg-gray-100 rounded-lg transition-colors"
                >
                  ✕
                </button>
              </div>

              <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                {/* Информация о доме */}
                <div className="bg-blue-50 p-6 rounded-lg border border-blue-200">
                  <h3 className="text-lg font-semibold text-blue-800 mb-4 flex items-center">
                    <Building2 className="w-5 h-5 mr-2" />
                    Информация о доме
                  </h3>
                  
                  <div className="space-y-3">
                    <div>
                      <span className="text-sm font-medium text-gray-600">Адрес:</span>
                      <p className="text-gray-900">{houseDetails.house.address || 'Не указан'}</p>
                    </div>
                    
                    <div className="grid grid-cols-3 gap-4">
                      <div className="text-center bg-white p-3 rounded-lg">
                        <div className="text-xl font-bold text-blue-600">{houseDetails.house.apartments}</div>
                        <div className="text-xs text-gray-500">Квартир</div>
                      </div>
                      <div className="text-center bg-white p-3 rounded-lg">
                        <div className="text-xl font-bold text-green-600">{houseDetails.house.entrances}</div>
                        <div className="text-xs text-gray-500">Подъездов</div>
                      </div>
                      <div className="text-center bg-white p-3 rounded-lg">
                        <div className="text-xl font-bold text-orange-600">{houseDetails.house.floors}</div>
                        <div className="text-xs text-gray-500">Этажей</div>
                      </div>
                    </div>
                    
                    <div>
                      <span className="text-sm font-medium text-gray-600">Бригада:</span>
                      <p className="text-gray-900">{houseDetails.house.brigade || 'Не назначена'}</p>
                    </div>
                    
                    <div>
                      <span className="text-sm font-medium text-gray-600">Статус:</span>
                      <p className="text-gray-900">{houseDetails.house.status || 'Не указан'}</p>
                    </div>
                  </div>
                </div>

                {/* Управляющая компания */}
                <div className="bg-green-50 p-6 rounded-lg border border-green-200">
                  <h3 className="text-lg font-semibold text-green-800 mb-4 flex items-center">
                    <Building2 className="w-5 h-5 mr-2" />
                    Управляющая компания
                  </h3>
                  
                  <div className="space-y-3">
                    <div>
                      <span className="text-sm font-medium text-gray-600">Название:</span>
                      <p className="text-gray-900 font-medium">{houseDetails.management_company.title || 'Не указана'}</p>
                    </div>
                    
                    {houseDetails.management_company.phone && (
                      <div>
                        <span className="text-sm font-medium text-gray-600">Телефон:</span>
                        <p className="text-gray-900">
                          <a href={`tel:${houseDetails.management_company.phone}`} className="text-blue-600 hover:underline">
                            {houseDetails.management_company.phone}
                          </a>
                        </p>
                      </div>
                    )}
                    
                    {houseDetails.management_company.email && (
                      <div>
                        <span className="text-sm font-medium text-gray-600">Email:</span>
                        <p className="text-gray-900">
                          <a href={`mailto:${houseDetails.management_company.email}`} className="text-blue-600 hover:underline">
                            {houseDetails.management_company.email}
                          </a>
                        </p>
                      </div>
                    )}
                    
                    {houseDetails.management_company.address && (
                      <div>
                        <span className="text-sm font-medium text-gray-600">Адрес:</span>
                        <p className="text-gray-900">{houseDetails.management_company.address}</p>
                      </div>
                    )}
                    
                    {houseDetails.management_company.web && (
                      <div>
                        <span className="text-sm font-medium text-gray-600">Сайт:</span>
                        <p className="text-gray-900">
                          <a href={houseDetails.management_company.web} target="_blank" rel="noopener noreferrer" className="text-blue-600 hover:underline">
                            {houseDetails.management_company.web}
                          </a>
                        </p>
                      </div>
                    )}
                    
                    {houseDetails.management_company.comments && (
                      <div>
                        <span className="text-sm font-medium text-gray-600">Комментарии:</span>
                        <p className="text-gray-900 text-sm bg-white p-3 rounded-lg">{houseDetails.management_company.comments}</p>
                      </div>
                    )}
                  </div>
                </div>
              </div>

              {/* Старший дома */}
              {houseDetails.senior_resident.full_name && (
                <div className="mt-6 bg-purple-50 p-6 rounded-lg border border-purple-200">
                  <h3 className="text-lg font-semibold text-purple-800 mb-4 flex items-center">
                    <Users className="w-5 h-5 mr-2" />
                    Старший дома (контактное лицо)
                  </h3>
                  
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div>
                      <span className="text-sm font-medium text-gray-600">ФИО:</span>
                      <p className="text-gray-900 font-medium">{houseDetails.senior_resident.full_name}</p>
                    </div>
                    
                    {houseDetails.senior_resident.phone && (
                      <div>
                        <span className="text-sm font-medium text-gray-600">Телефон:</span>
                        <p className="text-gray-900">
                          <a href={`tel:${houseDetails.senior_resident.phone}`} className="text-blue-600 hover:underline">
                            {houseDetails.senior_resident.phone}
                          </a>
                        </p>
                      </div>
                    )}
                    
                    {houseDetails.senior_resident.email && (
                      <div>
                        <span className="text-sm font-medium text-gray-600">Email:</span>
                        <p className="text-gray-900">
                          <a href={`mailto:${houseDetails.senior_resident.email}`} className="text-blue-600 hover:underline">
                            {houseDetails.senior_resident.email}
                          </a>
                        </p>
                      </div>
                    )}
                  </div>
                  
                  {houseDetails.senior_resident.comments && (
                    <div className="mt-4">
                      <span className="text-sm font-medium text-gray-600">Комментарии:</span>
                      <p className="text-gray-900 text-sm bg-white p-3 rounded-lg mt-1">{houseDetails.senior_resident.comments}</p>
                    </div>
                  )}
                </div>
              )}

              <div className="mt-6 flex justify-end space-x-3">
                <button
                  onClick={() => setShowDetailsModal(false)}
                  className="px-6 py-2 bg-gray-500 hover:bg-gray-600 text-white rounded-lg transition-colors"
                >
                  Закрыть
                </button>
                <button
                  onClick={() => {
                    setShowDetailsModal(false);
                    setSelectedHouse(houseDetails.house);
                    setShowScheduleModal(true);
                  }}
                  className="px-6 py-2 bg-blue-500 hover:bg-blue-600 text-white rounded-lg transition-colors flex items-center space-x-2"
                >
                  <Calendar className="w-4 h-4" />
                  <span>Посмотреть график</span>
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Notification */}
      {notification && (
        <div className={`fixed top-4 right-4 px-6 py-3 rounded-lg shadow-lg z-50 text-white ${
          notification.type === 'success' ? 'bg-green-500' :
          notification.type === 'error' ? 'bg-red-500' : 'bg-blue-500'
        }`}>
          {notification.message}
        </div>
      )}
    </div>
  );
};

export default Works;