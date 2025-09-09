import React, { useState, useEffect } from 'react';
import { useApp } from '../../context/AppContext';
import { Card, Button, LoadingSpinner } from '../UI';

const Works = () => {
  const { actions } = useApp();
  
  // State для домов и фильтров
  const [houses, setHouses] = useState([]);
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

  // Состояние UI
  const [viewMode, setViewMode] = useState('cards'); // 'cards' или 'table'
  const [selectedMonth, setSelectedMonth] = useState('september');

  useEffect(() => {
    fetchInitialData();
  }, []);

  const fetchInitialData = async () => {
    await Promise.all([
      fetchFilters(),
      fetchHouses(),
      fetchDashboardStats()
    ]);
  };

  const fetchFilters = async () => {
    try {
      const response = await fetch(`${process.env.REACT_APP_BACKEND_URL}/api/cleaning/filters`);
      const data = await response.json();
      if (data.status === 'success') {
        setFilters(data);
      }
    } catch (error) {
      console.error('❌ Error fetching filters:', error);
    }
  };

  const fetchHouses = async () => {
    setLoading(true);
    try {
      let url = `${process.env.REACT_APP_BACKEND_URL}/api/cleaning/houses`;
      const params = new URLSearchParams();
      
      Object.entries(activeFilters).forEach(([key, value]) => {
        if (value) params.append(key, value);
      });
      
      if (params.toString()) {
        url += '?' + params.toString();
      }

      const response = await fetch(url);
      const data = await response.json();
      
      if (data.status === 'success') {
        setHouses(data.houses || []);
      }
    } catch (error) {
      console.error('❌ Error fetching houses:', error);
      actions.addNotification({
        type: 'error',
        message: 'Ошибка загрузки домов'
      });
    } finally {
      setLoading(false);
    }
  };

  const fetchDashboardStats = async () => {
    try {
      const response = await fetch(`${process.env.REACT_APP_BACKEND_URL}/api/cleaning/stats`);
      const data = await response.json();
      if (data.status === 'success') {
        setDashboardStats(data.stats);
      }
    } catch (error) {
      console.error('❌ Error fetching dashboard stats:', error);
    }
  };

  const handleFilterChange = (filterType, value) => {
    setActiveFilters(prev => ({
      ...prev,
      [filterType]: value
    }));
  };

  const applyFilters = () => {
    fetchHouses();
  };

  const resetFilters = () => {
    setActiveFilters({
      brigade: '',
      cleaning_week: '',
      month: '',
      management_company: '',
      search: ''
    });
    setTimeout(fetchHouses, 100);
  };

  const getStatusColor = (statusColor) => {
    switch (statusColor) {
      case 'success': return 'bg-emerald-100 text-emerald-800 border-emerald-200';
      case 'error': return 'bg-red-100 text-red-800 border-red-200';
      case 'info': return 'bg-blue-100 text-blue-800 border-blue-200';
      case 'processing': return 'bg-amber-100 text-amber-800 border-amber-200';
      default: return 'bg-gray-100 text-gray-800 border-gray-200';
    }
  };

  const formatDate = (dateStr) => {
    if (!dateStr) return '';
    try {
      const [day, month, year] = dateStr.split('.');
      return new Date(year, month - 1, day).toLocaleDateString('ru-RU', {
        day: '2-digit',
        month: 'short'
      });
    } catch (e) {
      return dateStr;
    }
  };

  const getMonthSchedule = (house, month) => {
    switch (month) {
      case 'september': return house.september_schedule;
      case 'october': return house.october_schedule;
      case 'november': return house.november_schedule;
      case 'december': return house.december_schedule;
      default: return null;
    }
  };

  const getMonthName = (month) => {
    const names = {
      'september': 'Сентябрь',
      'october': 'Октябрь', 
      'november': 'Ноябрь',
      'december': 'Декабрь'
    };
    return names[month] || month;
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 via-white to-purple-50">
      {/* Header с градиентом */}
      <div className="bg-gradient-to-r from-blue-600 via-purple-600 to-indigo-600 text-white">
        <div className="max-w-7xl mx-auto px-6 py-8">
          <div className="flex justify-between items-center">
            <div>
              <h1 className="text-3xl font-bold mb-2">🏠 Управление домами</h1>
              <p className="text-blue-100">Полный контроль над клининговыми объектами</p>
            </div>
            <div className="text-right">
              <div className="text-2xl font-bold">{houses.length} / 490</div>
              <div className="text-blue-100">домов отображено</div>
            </div>
          </div>
        </div>
      </div>

      <div className="max-w-7xl mx-auto px-6 py-6 space-y-6">
        
        {/* Dashboard Cards */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
          <Card className="p-6 bg-gradient-to-br from-emerald-50 to-emerald-100 border-emerald-200">
            <div className="flex items-center">
              <div className="p-3 bg-emerald-500 rounded-xl text-white text-2xl mr-4">🏠</div>
              <div>
                <div className="text-3xl font-bold text-emerald-700">{dashboardStats.total_houses || '490'}</div>
                <div className="text-emerald-600">Всего домов</div>
              </div>
            </div>
          </Card>

          <Card className="p-6 bg-gradient-to-br from-blue-50 to-blue-100 border-blue-200">
            <div className="flex items-center">
              <div className="p-3 bg-blue-500 rounded-xl text-white text-2xl mr-4">🏢</div>
              <div>
                <div className="text-3xl font-bold text-blue-700">{dashboardStats.total_apartments?.toLocaleString() || '30,153'}</div>
                <div className="text-blue-600">Квартир</div>
              </div>
            </div>
          </Card>

          <Card className="p-6 bg-gradient-to-br from-purple-50 to-purple-100 border-purple-200">
            <div className="flex items-center">
              <div className="p-3 bg-purple-500 rounded-xl text-white text-2xl mr-4">🚪</div>
              <div>
                <div className="text-3xl font-bold text-purple-700">{dashboardStats.total_entrances?.toLocaleString() || '1,567'}</div>
                <div className="text-purple-600">Подъездов</div>
              </div>
            </div>
          </Card>

          <Card className="p-6 bg-gradient-to-br from-orange-50 to-orange-100 border-orange-200">
            <div className="flex items-center">
              <div className="p-3 bg-orange-500 rounded-xl text-white text-2xl mr-4">📊</div>
              <div>
                <div className="text-3xl font-bold text-orange-700">{dashboardStats.total_floors?.toLocaleString() || '8,147'}</div>
                <div className="text-orange-600">Этажей</div>
              </div>
            </div>
          </div>
        </div>

        {/* Filters Panel */}
        <Card className="p-6 bg-white border-0 shadow-lg">
          <div className="flex justify-between items-center mb-6">
            <h3 className="text-xl font-semibold text-gray-800">🔍 Фильтры поиска</h3>
            <div className="flex space-x-3">
              <Button onClick={applyFilters} className="bg-blue-600 hover:bg-blue-700">
                Применить
              </Button>
              <Button onClick={resetFilters} variant="outline">
                Сбросить
              </Button>
            </div>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-6 gap-4">
            {/* Поиск */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                📍 Поиск по адресу
              </label>
              <input
                type="text"
                value={activeFilters.search}
                onChange={(e) => handleFilterChange('search', e.target.value)}
                placeholder="Введите адрес..."
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              />
            </div>

            {/* Бригада */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                👥 Бригада
              </label>
              <select
                value={activeFilters.brigade}
                onChange={(e) => handleFilterChange('brigade', e.target.value)}
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
              >
                <option value="">Все бригады</option>
                {filters.brigades.map((brigade) => (
                  <option key={brigade} value={brigade}>
                    {brigade}
                  </option>
                ))}
              </select>
            </div>

            {/* Неделя */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                📅 Неделя уборки
              </label>
              <select
                value={activeFilters.cleaning_week}
                onChange={(e) => handleFilterChange('cleaning_week', e.target.value)}
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
              >
                <option value="">Все недели</option>
                {[1, 2, 3, 4, 5].map((week) => (
                  <option key={week} value={week}>
                    {week} неделя
                  </option>
                ))}
              </select>
            </div>

            {/* Месяц */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                🗓️ Месяц
              </label>
              <select
                value={activeFilters.month}
                onChange={(e) => handleFilterChange('month', e.target.value)}
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
              >
                <option value="">Все месяцы</option>
                {filters.months.map((month) => (
                  <option key={month} value={month.toLowerCase()}>
                    {month}
                  </option>
                ))}
              </select>
            </div>

            {/* Управляющая компания */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                🏢 УК
              </label>
              <select
                value={activeFilters.management_company}
                onChange={(e) => handleFilterChange('management_company', e.target.value)}
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
              >
                <option value="">Все УК</option>
                {filters.management_companies.map((company) => (
                  <option key={company} value={company}>
                    {company}
                  </option>
                ))}
              </select>
            </div>

            {/* Отображение месяца */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                📋 Показать график
              </label>
              <select
                value={selectedMonth}
                onChange={(e) => setSelectedMonth(e.target.value)}
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500"
              >
                <option value="september">Сентябрь</option>
                <option value="october">Октябрь</option>
                <option value="november">Ноябрь</option>
                <option value="december">Декабрь</option>
              </select>
            </div>
          </div>
        </Card>

        {/* Houses Grid */}
        {loading ? (
          <div className="flex justify-center py-12">
            <LoadingSpinner />
          </div>
        ) : (
          <div className="grid grid-cols-1 lg:grid-cols-2 xl:grid-cols-3 gap-6">
            {houses.map((house) => {
              const monthSchedule = getMonthSchedule(house, selectedMonth);
              
              return (
                <Card key={house.deal_id} className="p-6 hover:shadow-xl transition-all duration-300 transform hover:-translate-y-1 bg-white border-0 shadow-lg">
                  {/* House Header */}
                  <div className="flex justify-between items-start mb-4">
                    <div className="flex-1">
                      <h3 className="text-lg font-bold text-gray-900 mb-1">
                        {house.address}
                      </h3>
                      <div className="text-sm text-gray-500">ID: {house.deal_id}</div>
                    </div>
                    <span className={`px-3 py-1 rounded-full text-xs font-medium border ${getStatusColor(house.status_color)}`}>
                      {house.status_text}
                    </span>
                  </div>

                  {/* Stats Row */}
                  <div className="grid grid-cols-3 gap-4 mb-4">
                    <div className="text-center p-3 bg-blue-50 rounded-lg">
                      <div className="text-2xl font-bold text-blue-600">{house.apartments_count || '-'}</div>
                      <div className="text-xs text-blue-500">Квартир</div>
                    </div>
                    <div className="text-center p-3 bg-green-50 rounded-lg">
                      <div className="text-2xl font-bold text-green-600">{house.floors_count || '-'}</div>
                      <div className="text-xs text-green-500">Этажей</div>
                    </div>
                    <div className="text-center p-3 bg-purple-50 rounded-lg">
                      <div className="text-2xl font-bold text-purple-600">{house.entrances_count || '-'}</div>
                      <div className="text-xs text-purple-500">Подъездов</div>
                    </div>
                  </div>

                  {/* Brigade & Company */}
                  <div className="space-y-2 mb-4">
                    <div className="flex items-center text-sm">
                      <span className="text-gray-500 mr-2">👥</span>
                      <span className="font-medium">{house.brigade}</span>
                    </div>
                    <div className="flex items-center text-sm">
                      <span className="text-gray-500 mr-2">🏢</span>
                      <span className="text-gray-600">{house.management_company}</span>
                    </div>
                    {house.tariff && (
                      <div className="flex items-center text-sm">
                        <span className="text-gray-500 mr-2">💰</span>
                        <span className="text-gray-600">{house.tariff}</span>
                      </div>
                    )}
                  </div>

                  {/* Schedule for Selected Month */}
                  {monthSchedule && (
                    <div className="border-t pt-4">
                      <div className="text-sm font-medium text-gray-700 mb-3">
                        📅 {getMonthName(selectedMonth)} 2025
                      </div>
                      
                      {/* Schedule Type 1 */}
                      {monthSchedule.cleaning_date_1?.length > 0 && (
                        <div className="mb-3 p-3 bg-blue-50 rounded-lg">
                          <div className="text-xs font-medium text-blue-700 mb-1">
                            📍 {monthSchedule.cleaning_date_1.map(formatDate).join(', ')}
                          </div>
                          <div className="text-xs text-gray-600 line-clamp-2">
                            {monthSchedule.cleaning_type_1}
                          </div>
                        </div>
                      )}
                      
                      {/* Schedule Type 2 */}
                      {monthSchedule.cleaning_date_2?.length > 0 && (
                        <div className="mb-3 p-3 bg-green-50 rounded-lg">
                          <div className="text-xs font-medium text-green-700 mb-1">
                            📍 {monthSchedule.cleaning_date_2.map(formatDate).join(', ')}
                          </div>
                          <div className="text-xs text-gray-600 line-clamp-2">
                            {monthSchedule.cleaning_type_2}
                          </div>
                        </div>
                      )}

                      {/* Cleaning Weeks */}
                      {house.cleaning_weeks?.length > 0 && (
                        <div className="flex flex-wrap gap-1 mt-2">
                          {house.cleaning_weeks.map((week) => (
                            <span key={week} className="px-2 py-1 bg-purple-100 text-purple-700 rounded text-xs">
                              {week} нед
                            </span>
                          ))}
                        </div>
                      )}
                    </div>
                  )}

                  {/* Footer */}
                  <div className="flex justify-between items-center text-xs text-gray-500 border-t pt-3 mt-4">
                    <span>Обновлено: {new Date(house.last_sync).toLocaleDateString()}</span>
                    <span>{house.opportunity ? `${house.opportunity} ₽` : ''}</span>
                  </div>
                </Card>
              );
            })}
          </div>
        )}

        {/* Empty State */}
        {!loading && houses.length === 0 && (
          <Card className="p-12 text-center bg-white border-0 shadow-lg">
            <div className="text-6xl mb-4">🏠</div>
            <div className="text-xl text-gray-600 mb-2">
              {Object.values(activeFilters).some(v => v) ? 'Нет домов по выбранным фильтрам' : 'Дома не найдены'}
            </div>
            <div className="text-gray-500 mb-6">
              Попробуйте изменить параметры поиска или сбросить фильтры
            </div>
            {Object.values(activeFilters).some(v => v) && (
              <Button onClick={resetFilters} className="bg-blue-600 hover:bg-blue-700">
                Сбросить все фильтры
              </Button>
            )}
          </Card>
        )}
      </div>
    </div>
  );
};

export default Works;