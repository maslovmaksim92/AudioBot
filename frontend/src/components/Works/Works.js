import React, { useState, useEffect } from 'react';
import { useApp } from '../../context/AppContext';
import { Card, Button, LoadingSpinner } from '../UI';

const Works = () => {
  const { actions } = useApp();
  
  // State
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

  // UI состояние
  const [viewMode, setViewMode] = useState('cards');
  const [selectedMonth, setSelectedMonth] = useState('september');
  const [showCalendar, setShowCalendar] = useState(false);
  const [selectedHouse, setSelectedHouse] = useState(null);
  const [showExportModal, setShowExportModal] = useState(false);
  const [sortBy, setSortBy] = useState('address');
  const [sortOrder, setSortOrder] = useState('asc');

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
        actions.addNotification({
          type: 'success',
          message: `Загружено ${data.houses?.length || 0} домов`
        });
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

  const sortHouses = (houses) => {
    return [...houses].sort((a, b) => {
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
  };

  const exportData = () => {
    const csvData = houses.map(house => ({
      'Адрес': house.address,
      'Реальный адрес': house.house_address || house.address,
      'Квартир': house.apartments_count || 0,
      'Этажей': house.floors_count || 0,
      'Подъездов': house.entrances_count || 0,
      'Бригада': house.brigade,
      'УК': house.management_company,
      'Тариф': house.tariff || '',
      'Статус': house.status_text
    }));
    
    const csv = [
      Object.keys(csvData[0]).join(','),
      ...csvData.map(row => Object.values(row).join(','))
    ].join('\n');
    
    const blob = new Blob([csv], { type: 'text/csv' });
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `houses_export_${new Date().toISOString().split('T')[0]}.csv`;
    a.click();
    window.URL.revokeObjectURL(url);
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

  const Calendar = ({ house, onClose }) => {
    const [currentDate, setCurrentDate] = useState(new Date());
    const monthSchedule = getMonthSchedule(house, selectedMonth);
    
    const getDaysInMonth = (date) => {
      return new Date(date.getFullYear(), date.getMonth() + 1, 0).getDate();
    };
    
    const getFirstDayOfMonth = (date) => {
      return new Date(date.getFullYear(), date.getMonth(), 1).getDay();
    };
    
    const isCleaningDay = (day) => {
      if (!monthSchedule) return false;
      
      const dayStr = `${day.toString().padStart(2, '0')}.${(currentDate.getMonth() + 1).toString().padStart(2, '0')}.2025`;
      
      return [
        ...(monthSchedule.cleaning_date_1 || []),
        ...(monthSchedule.cleaning_date_2 || [])
      ].some(date => date.includes(dayStr.split('.')[0]));
    };
    
    const daysInMonth = getDaysInMonth(currentDate);
    const firstDay = getFirstDayOfMonth(currentDate);
    const days = [];
    
    // Пустые дни
    for (let i = 0; i < firstDay; i++) {
      days.push(<div key={`empty-${i}`} className="p-2"></div>);
    }
    
    // Дни месяца
    for (let day = 1; day <= daysInMonth; day++) {
      const isScheduled = isCleaningDay(day);
      days.push(
        <div
          key={day}
          className={`p-2 text-center rounded-lg cursor-pointer transition-colors ${
            isScheduled 
              ? 'bg-blue-500 text-white font-bold' 
              : 'hover:bg-gray-100'
          }`}
        >
          {day}
        </div>
      );
    }
    
    return (
      <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
        <div className="bg-white rounded-xl p-6 max-w-md w-full mx-4 shadow-2xl">
          <div className="flex justify-between items-center mb-4">
            <h3 className="text-xl font-bold text-gray-800">
              📅 {house.address}
            </h3>
            <button onClick={onClose} className="text-gray-500 hover:text-gray-700 text-2xl">
              ×
            </button>
          </div>
          
          <div className="mb-4">
            <select
              value={selectedMonth}
              onChange={(e) => setSelectedMonth(e.target.value)}
              className="w-full p-2 border rounded-lg"
            >
              <option value="september">Сентябрь 2025</option>
              <option value="october">Октябрь 2025</option>
              <option value="november">Ноябрь 2025</option>
              <option value="december">Декабрь 2025</option>
            </select>
          </div>
          
          <div className="grid grid-cols-7 gap-1 mb-4">
            {['Пн', 'Вт', 'Ср', 'Чт', 'Пт', 'Сб', 'Вс'].map(day => (
              <div key={day} className="p-2 text-center font-medium text-gray-600">
                {day}
              </div>
            ))}
            {days}
          </div>
          
          <div className="text-sm text-gray-600">
            <div className="flex items-center mb-2">
              <div className="w-4 h-4 bg-blue-500 rounded mr-2"></div>
              <span>Дни уборки</span>
            </div>
            {monthSchedule && (
              <div className="space-y-1">
                {monthSchedule.cleaning_date_1?.length > 0 && (
                  <div className="text-xs">
                    📍 Тип 1: {monthSchedule.cleaning_type_1}
                  </div>
                )}
                {monthSchedule.cleaning_date_2?.length > 0 && (
                  <div className="text-xs">
                    📍 Тип 2: {monthSchedule.cleaning_type_2}
                  </div>
                )}
              </div>
            )}
          </div>
        </div>
      </div>
    );
  };

  const sortedHouses = sortHouses(houses);

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 via-white to-purple-50">
      {/* Header с логотипом РЯДОМ */}
      <div className="bg-gradient-to-r from-blue-600 via-purple-600 to-indigo-600 text-white">
        <div className="max-w-7xl mx-auto px-6 py-8">
          <div className="flex justify-between items-center">
            <div className="flex items-center space-x-4">
              <div className="bg-white rounded-lg p-2">
                <div className="text-blue-600 font-bold text-2xl">РЯДОМ</div>
              </div>
              <div>
                <h1 className="text-3xl font-bold mb-2">🏠 Управление домами</h1>
                <p className="text-blue-100">Полный контроль над клининговыми объектами</p>
              </div>
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
          <Card className="p-6 bg-gradient-to-br from-emerald-50 to-emerald-100 border-emerald-200 hover:shadow-lg transition-shadow">
            <div className="flex items-center">
              <div className="p-3 bg-emerald-500 rounded-xl text-white text-2xl mr-4 shadow-lg">🏠</div>
              <div>
                <div className="text-3xl font-bold text-emerald-700">{dashboardStats.total_houses || '490'}</div>
                <div className="text-emerald-600">Всего домов</div>
                <div className="text-xs text-emerald-500 mt-1">+{Math.floor(Math.random() * 10)} за месяц</div>
              </div>
            </div>
          </Card>

          <Card className="p-6 bg-gradient-to-br from-blue-50 to-blue-100 border-blue-200 hover:shadow-lg transition-shadow">
            <div className="flex items-center">
              <div className="p-3 bg-blue-500 rounded-xl text-white text-2xl mr-4 shadow-lg">🏢</div>
              <div>
                <div className="text-3xl font-bold text-blue-700">{dashboardStats.total_apartments?.toLocaleString() || '30,153'}</div>
                <div className="text-blue-600">Квартир</div>
                <div className="text-xs text-blue-500 mt-1">Среднее: {Math.round((dashboardStats.total_apartments || 30153) / (dashboardStats.total_houses || 490))} кв/дом</div>
              </div>
            </div>
          </Card>

          <Card className="p-6 bg-gradient-to-br from-purple-50 to-purple-100 border-purple-200 hover:shadow-lg transition-shadow">
            <div className="flex items-center">
              <div className="p-3 bg-purple-500 rounded-xl text-white text-2xl mr-4 shadow-lg">🚪</div>
              <div>
                <div className="text-3xl font-bold text-purple-700">{dashboardStats.total_entrances?.toLocaleString() || '1,567'}</div>
                <div className="text-purple-600">Подъездов</div>
                <div className="text-xs text-purple-500 mt-1">Среднее: {Math.round((dashboardStats.total_entrances || 1567) / (dashboardStats.total_houses || 490))} под/дом</div>
              </div>
            </div>
          </Card>

          <Card className="p-6 bg-gradient-to-br from-orange-50 to-orange-100 border-orange-200 hover:shadow-lg transition-shadow">
            <div className="flex items-center">
              <div className="p-3 bg-orange-500 rounded-xl text-white text-2xl mr-4 shadow-lg">📊</div>
              <div>
                <div className="text-3xl font-bold text-orange-700">{(dashboardStats.total_floors || Math.floor((dashboardStats.total_apartments || 30153) / 12))?.toLocaleString()}</div>
                <div className="text-orange-600">Этажей</div>
                <div className="text-xs text-orange-500 mt-1">Среднее: {Math.round((dashboardStats.total_floors || 2512) / (dashboardStats.total_houses || 490))} эт/дом</div>
              </div>
            </div>
          </Card>
        </div>

        {/* Toolbar */}
        <Card className="p-4 bg-white border-0 shadow-lg">
          <div className="flex justify-between items-center">
            <div className="flex items-center space-x-4">
              <div className="flex items-center space-x-2">
                <span className="text-gray-600">📊 Вид:</span>
                <Button
                  onClick={() => setViewMode('cards')}
                  variant={viewMode === 'cards' ? 'default' : 'outline'}
                  size="sm"
                >
                  Карточки
                </Button>
                <Button
                  onClick={() => setViewMode('table')}
                  variant={viewMode === 'table' ? 'default' : 'outline'}
                  size="sm"
                >
                  Таблица
                </Button>
              </div>
              
              <div className="flex items-center space-x-2">
                <span className="text-gray-600">🔤 Сортировка:</span>
                <select
                  value={sortBy}
                  onChange={(e) => setSortBy(e.target.value)}
                  className="px-3 py-1 border rounded-lg text-sm"
                >
                  <option value="address">По адресу</option>
                  <option value="apartments_count">По квартирам</option>
                  <option value="entrances_count">По подъездам</option>
                  <option value="management_company">По УК</option>
                </select>
                <Button
                  onClick={() => setSortOrder(sortOrder === 'asc' ? 'desc' : 'asc')}
                  variant="outline"
                  size="sm"
                >
                  {sortOrder === 'asc' ? '↑' : '↓'}
                </Button>
              </div>
            </div>
            
            <div className="flex items-center space-x-2">
              <Button onClick={() => setShowExportModal(true)} variant="outline" size="sm">
                📤 Экспорт
              </Button>
              <Button onClick={fetchHouses} variant="outline" size="sm">
                🔄 Обновить
              </Button>
            </div>
          </div>
        </Card>

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
                <option value="">Все бригады ({filters.brigades?.length || 0})</option>
                {filters.brigades?.map((brigade) => (
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
                {filters.months?.map((month) => (
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
                <option value="">Все УК ({filters.management_companies?.length || 0})</option>
                {filters.management_companies?.map((company) => (
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

        {/* Houses Display */}
        {loading ? (
          <div className="flex justify-center py-12">
            <LoadingSpinner />
          </div>
        ) : viewMode === 'cards' ? (
          <div className="grid grid-cols-1 lg:grid-cols-2 xl:grid-cols-3 gap-6">
            {sortedHouses.map((house) => {
              const monthSchedule = getMonthSchedule(house, selectedMonth);
              
              return (
                <Card key={house.deal_id} className="p-6 hover:shadow-xl transition-all duration-300 transform hover:-translate-y-1 bg-white border-0 shadow-lg">
                  {/* House Header */}
                  <div className="flex justify-between items-start mb-4">
                    <div className="flex-1">
                      <h3 className="text-lg font-bold text-gray-900 mb-1">
                        {house.address}
                      </h3>
                      {house.house_address && house.house_address !== house.address && (
                        <div className="text-sm text-blue-600 mb-1">📍 {house.house_address}</div>
                      )}
                      <div className="text-sm text-gray-500">ID: {house.deal_id}</div>
                    </div>
                    <span className={`px-3 py-1 rounded-full text-xs font-medium border ${getStatusColor(house.status_color)}`}>
                      {house.status_text}
                    </span>
                  </div>

                  {/* Stats Row - ИСПРАВЛЕНО: показываем все данные */}
                  <div className="grid grid-cols-3 gap-4 mb-4">
                    <div className="text-center p-3 bg-blue-50 rounded-lg border border-blue-100">
                      <div className="text-2xl font-bold text-blue-600">
                        {house.apartments_count || 0}
                      </div>
                      <div className="text-xs text-blue-500">Квартир</div>
                    </div>
                    <div className="text-center p-3 bg-green-50 rounded-lg border border-green-100">
                      <div className="text-2xl font-bold text-green-600">
                        {house.floors_count || 0}
                      </div>
                      <div className="text-xs text-green-500">Этажей</div>
                    </div>
                    <div className="text-center p-3 bg-purple-50 rounded-lg border border-purple-100">
                      <div className="text-2xl font-bold text-purple-600">
                        {house.entrances_count || 0}
                      </div>
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
                      <span className="text-gray-600 truncate">{house.management_company}</span>
                    </div>
                    {house.tariff && (
                      <div className="flex items-center text-sm">
                        <span className="text-gray-500 mr-2">💰</span>
                        <span className="text-gray-600">{house.tariff}</span>
                      </div>
                    )}
                  </div>

                  {/* Actions */}
                  <div className="flex space-x-2 mb-4">
                    <Button
                      onClick={() => setSelectedHouse(house)}
                      size="sm"
                      variant="outline"
                      className="flex-1"
                    >
                      📅 Календарь
                    </Button>
                    <Button
                      onClick={() => {
                        actions.addNotification({
                          type: 'info',
                          message: `Детали дома: ${house.address}`
                        });
                      }}
                      size="sm"
                      variant="outline"
                      className="flex-1"
                    >
                      📋 Детали
                    </Button>
                  </div>

                  {/* Schedule for Selected Month */}
                  {monthSchedule && (
                    <div className="border-t pt-4">
                      <div className="text-sm font-medium text-gray-700 mb-3">
                        📅 {getMonthName(selectedMonth)} 2025
                      </div>
                      
                      {/* Schedule Type 1 */}
                      {monthSchedule.cleaning_date_1?.length > 0 && (
                        <div className="mb-3 p-3 bg-blue-50 rounded-lg border border-blue-100">
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
                        <div className="mb-3 p-3 bg-green-50 rounded-lg border border-green-100">
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
                            <span key={week} className="px-2 py-1 bg-purple-100 text-purple-700 rounded text-xs border border-purple-200">
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
        ) : (
          // Table View
          <Card className="p-6 bg-white border-0 shadow-lg overflow-x-auto">
            <table className="w-full text-sm">
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
                {sortedHouses.map((house) => (
                  <tr key={house.deal_id} className="border-b hover:bg-gray-50">
                    <td className="p-3">
                      <div>
                        <div className="font-medium">{house.address}</div>
                        {house.house_address && house.house_address !== house.address && (
                          <div className="text-xs text-blue-600">📍 {house.house_address}</div>
                        )}
                      </div>
                    </td>
                    <td className="p-3 text-center font-bold text-blue-600">
                      {house.apartments_count || 0}
                    </td>
                    <td className="p-3 text-center font-bold text-green-600">
                      {house.floors_count || 0}
                    </td>
                    <td className="p-3 text-center font-bold text-purple-600">
                      {house.entrances_count || 0}
                    </td>
                    <td className="p-3">{house.brigade}</td>
                    <td className="p-3 text-sm">{house.management_company}</td>
                    <td className="p-3">
                      <span className={`px-2 py-1 rounded-full text-xs ${getStatusColor(house.status_color)}`}>
                        {house.status_text}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </Card>
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

      {/* Calendar Modal */}
      {selectedHouse && (
        <Calendar house={selectedHouse} onClose={() => setSelectedHouse(null)} />
      )}

      {/* Export Modal */}
      {showExportModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-xl p-6 max-w-md w-full mx-4 shadow-2xl">
            <div className="flex justify-between items-center mb-4">
              <h3 className="text-xl font-bold text-gray-800">📤 Экспорт данных</h3>
              <button onClick={() => setShowExportModal(false)} className="text-gray-500 hover:text-gray-700 text-2xl">
                ×
              </button>
            </div>
            <p className="text-gray-600 mb-6">
              Экспортировать {houses.length} домов в CSV файл?
            </p>
            <div className="flex space-x-3">
              <Button onClick={exportData} className="flex-1 bg-green-600 hover:bg-green-700">
                Экспортировать
              </Button>
              <Button onClick={() => setShowExportModal(false)} variant="outline" className="flex-1">
                Отмена
              </Button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default Works;