import React, { useState, useEffect } from 'react';
import { useApp } from '../../context/AppContext';
import { apiService } from '../../services/apiService';
import { Card, Button, LoadingSpinner } from '../UI';

const Works = () => {
  const { actions } = useApp();
  const [houses, setHouses] = useState([]);
  const [filters, setFilters] = useState({ brigades: [], cleaning_days: [] });
  const [loading, setLoading] = useState(false);
  const [selectedBrigade, setSelectedBrigade] = useState('');
  const [selectedDay, setSelectedDay] = useState('');
  const [searchTerm, setSearchTerm] = useState('');

  useEffect(() => {
    fetchFilters();
    fetchHouses();
  }, []);

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

  const fetchHouses = async (brigade = '', cleaningDay = '') => {
    setLoading(true);
    try {
      let url = `${process.env.REACT_APP_BACKEND_URL}/api/cleaning/houses`;
      const params = new URLSearchParams();
      
      if (brigade) params.append('brigade', brigade);
      if (cleaningDay) params.append('cleaning_day', cleaningDay);
      
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

  const handleFilterChange = (type, value) => {
    if (type === 'brigade') {
      setSelectedBrigade(value);
      fetchHouses(value, selectedDay);
    } else if (type === 'day') {
      setSelectedDay(value);
      fetchHouses(selectedBrigade, value);
    }
  };

  const resetFilters = () => {
    setSelectedBrigade('');
    setSelectedDay('');
    setSearchTerm('');
    fetchHouses();
  };

  const filteredHouses = houses.filter(house => {
    const matchesSearch = house.address?.toLowerCase().includes(searchTerm.toLowerCase()) ||
                         house.deal_id?.toLowerCase().includes(searchTerm.toLowerCase());
    return matchesSearch;
  });

  const getStatusColor = (statusColor) => {
    switch (statusColor) {
      case 'success': return 'bg-green-100 text-green-800';
      case 'error': return 'bg-red-100 text-red-800';
      case 'info': return 'bg-blue-100 text-blue-800';
      case 'processing': return 'bg-yellow-100 text-yellow-800';
      default: return 'bg-gray-100 text-gray-800';
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

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <h2 className="text-2xl font-bold text-gray-900">Управление домами</h2>
        <div className="text-sm text-gray-500">
          Всего домов: {filteredHouses.length}
        </div>
      </div>

      {/* Фильтры */}
      <Card className="p-6">
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-4">
          {/* Поиск */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Поиск по адресу
            </label>
            <input
              type="text"
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              placeholder="Введите адрес..."
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>

          {/* Фильтр по бригаде */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Бригада
            </label>
            <select
              value={selectedBrigade}
              onChange={(e) => handleFilterChange('brigade', e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              <option value="">Все бригады</option>
              {filters.brigades.map((brigade) => (
                <option key={brigade} value={brigade}>
                  {brigade}
                </option>
              ))}
            </select>
          </div>

          {/* Фильтр по дню недели */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              День уборки
            </label>
            <select
              value={selectedDay}
              onChange={(e) => handleFilterChange('day', e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              <option value="">Все дни</option>
              {filters.cleaning_days.map((day) => (
                <option key={day} value={day}>
                  {day}
                </option>
              ))}
            </select>
          </div>

          {/* Кнопка сброса */}
          <div className="flex items-end">
            <Button
              onClick={resetFilters}
              variant="outline"
              className="w-full"
            >
              Сбросить
            </Button>
          </div>
        </div>
      </Card>

      {/* Список домов */}
      {loading ? (
        <div className="flex justify-center py-8">
          <LoadingSpinner />
        </div>
      ) : (
        <div className="grid grid-cols-1 lg:grid-cols-2 xl:grid-cols-3 gap-6">
          {filteredHouses.map((house) => (
            <Card key={house.deal_id} className="p-6 hover:shadow-lg transition-shadow">
              {/* Заголовок дома */}
              <div className="flex justify-between items-start mb-4">
                <h3 className="text-lg font-semibold text-gray-900 flex-1">
                  {house.address}
                </h3>
                <span className={`px-2 py-1 rounded-full text-xs font-medium ${getStatusColor(house.status_color)}`}>
                  {house.status_text}
                </span>
              </div>

              {/* Информация о доме */}
              <div className="grid grid-cols-3 gap-4 mb-4 text-sm">
                <div className="text-center">
                  <div className="text-2xl font-bold text-blue-600">{house.apartments_count || '-'}</div>
                  <div className="text-gray-500">Квартир</div>
                </div>
                <div className="text-center">
                  <div className="text-2xl font-bold text-green-600">{house.floors_count || '-'}</div>
                  <div className="text-gray-500">Этажей</div>
                </div>
                <div className="text-center">
                  <div className="text-2xl font-bold text-purple-600">{house.entrances_count || '-'}</div>
                  <div className="text-gray-500">Подъездов</div>
                </div>
              </div>

              {/* Бригада */}
              <div className="mb-4">
                <div className="text-sm text-gray-600 mb-1">Бригада:</div>
                <div className="text-sm font-medium text-gray-900">{house.brigade}</div>
              </div>

              {/* График уборки на сентябрь */}
              {house.september_schedule && (
                <div className="mb-4">
                  <div className="text-sm text-gray-600 mb-2">График уборки (Сентябрь 2025):</div>
                  
                  {/* Тип уборки 1 */}
                  {house.september_schedule.cleaning_date_1?.length > 0 && (
                    <div className="mb-2">
                      <div className="text-xs text-blue-600 font-medium">
                        Даты: {house.september_schedule.cleaning_date_1.map(formatDate).join(', ')}
                      </div>
                      <div className="text-xs text-gray-500 truncate">
                        {house.september_schedule.cleaning_type_1}
                      </div>
                    </div>
                  )}
                  
                  {/* Тип уборки 2 */}
                  {house.september_schedule.cleaning_date_2?.length > 0 && (
                    <div className="mb-2">
                      <div className="text-xs text-green-600 font-medium">
                        Даты: {house.september_schedule.cleaning_date_2.map(formatDate).join(', ')}
                      </div>
                      <div className="text-xs text-gray-500 truncate">
                        {house.september_schedule.cleaning_type_2}
                      </div>
                    </div>
                  )}

                  {/* Периодичность */}
                  {house.tariff && (
                    <div className="text-xs text-gray-600">
                      Периодичность: {house.tariff}
                    </div>
                  )}
                </div>
              )}

              {/* Дни недели уборки */}
              {house.cleaning_days?.length > 0 && (
                <div className="mb-4">
                  <div className="text-sm text-gray-600 mb-1">Дни уборки:</div>
                  <div className="flex flex-wrap gap-1">
                    {house.cleaning_days.map((day) => (
                      <span key={day} className="px-2 py-1 bg-gray-100 text-gray-700 rounded text-xs">
                        {day}
                      </span>
                    ))}
                  </div>
                </div>
              )}

              {/* Дополнительная информация */}
              <div className="flex justify-between items-center text-xs text-gray-500 border-t pt-3">
                <span>ID: {house.deal_id}</span>
                <span>{house.opportunity ? `${house.opportunity} ₽` : ''}</span>
              </div>
            </Card>
          ))}
        </div>
      )}

      {/* Сообщение если нет домов */}
      {!loading && filteredHouses.length === 0 && (
        <Card className="p-8 text-center">
          <div className="text-gray-500 text-lg">
            {houses.length === 0 ? 'Дома не найдены' : 'Нет домов по выбранным фильтрам'}
          </div>
          {(selectedBrigade || selectedDay || searchTerm) && (
            <Button onClick={resetFilters} className="mt-4">
              Сбросить фильтры
            </Button>
          )}
        </Card>
      )}
    </div>
  );
};

export default Works;
      case 'C2:EXECUTING': return 'bg-green-100 text-green-800';
      case 'C2:FINAL_INVOICE': return 'bg-orange-100 text-orange-800';
      case 'C2:WON': return 'bg-green-200 text-green-900';
      case 'C2:APOLOGY': return 'bg-red-100 text-red-800';
      default: return 'bg-gray-100 text-gray-800';
    }
  };

  const getStatusText = (stage) => {
    const statusMap = {
      'C2:NEW': 'Новый',
      'C2:PREPARATION': 'Подготовка',
      'C2:CLIENT': 'С клиентом',
      'C2:EXECUTING': 'Выполняется',
      'C2:FINAL_INVOICE': 'Счет',
      'C2:WON': 'Выполнен',
      'C2:APOLOGY': 'Отказ'
    };
    return statusMap[stage] || stage;
  };

  const statusCounts = houses.reduce((acc, house) => {
    acc[house.stage] = (acc[house.stage] || 0) + 1;
    return acc;
  }, {});

  return (
    <div className="p-6">
      <div className="flex justify-between items-center mb-6">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Дома в управлении</h1>
          <p className="text-gray-600">Всего домов: {houses.length} из Bitrix24 CRM</p>
        </div>
        <Button onClick={fetchHouses} loading={loading}>
          🔄 Обновить
        </Button>
      </div>

      {/* Filters and Search */}
      <Card className="mb-6">
        <div className="flex flex-col md:flex-row md:items-center md:justify-between space-y-4 md:space-y-0">
          <div className="flex flex-wrap gap-2">
            <Button
              variant={filterStatus === 'all' ? 'primary' : 'secondary'}
              size="sm"
              onClick={() => setFilterStatus('all')}
            >
              Все ({houses.length})
            </Button>
            {Object.entries(statusCounts).map(([status, count]) => (
              <Button
                key={status}
                variant={filterStatus === status ? 'primary' : 'secondary'}
                size="sm"
                onClick={() => setFilterStatus(status)}
              >
                {getStatusText(status)} ({count})
              </Button>
            ))}
          </div>
          
          <div className="flex items-center space-x-2">
            <input
              type="text"
              placeholder="Поиск по адресу или ID..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>
        </div>
      </Card>

      {/* Houses Grid */}
      {loading ? (
        <div className="flex justify-center py-12">
          <LoadingSpinner size="lg" text="Загрузка домов..." />
        </div>
      ) : filteredHouses.length > 0 ? (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {filteredHouses.map((house, index) => (
            <Card key={house.deal_id || index} className="hover:shadow-lg transition-shadow">
              <div className="space-y-3">
                <div className="flex justify-between items-start">
                  <h3 className="font-semibold text-gray-900 text-sm leading-tight">
                    {house.address || 'Адрес не указан'}
                  </h3>
                  <span className={`px-2 py-1 rounded-full text-xs font-medium ${getStatusColor(house.stage)}`}>
                    {getStatusText(house.stage)}
                  </span>
                </div>
                
                <div className="space-y-2 text-sm text-gray-600">
                  <div className="flex justify-between">
                    <span>ID сделки:</span>
                    <span className="font-mono text-xs">{house.deal_id}</span>
                  </div>
                  
                  {house.brigade && (
                    <div className="flex justify-between">
                      <span>Бригада:</span>
                      <span>{house.brigade}</span>
                    </div>
                  )}
                  
                  {house.opportunity && (
                    <div className="flex justify-between">
                      <span>Сумма:</span>
                      <span className="font-semibold">{house.opportunity} ₽</span>
                    </div>
                  )}
                  
                  {house.created_date && (
                    <div className="flex justify-between">
                      <span>Создан:</span>
                      <span>{new Date(house.created_date).toLocaleDateString('ru-RU')}</span>
                    </div>
                  )}
                </div>
                
                <div className="pt-3 border-t border-gray-100">
                  <div className="flex justify-between items-center">
                    <span className="text-xs text-gray-500">
                      Обновлено: {house.last_sync ? new Date(house.last_sync).toLocaleTimeString('ru-RU') : 'Неизвестно'}
                    </span>
                    {house.status_text && (
                      <span className="text-xs px-2 py-1 bg-gray-100 rounded">
                        {house.status_text}
                      </span>
                    )}
                  </div>
                </div>
              </div>
            </Card>
          ))}
        </div>
      ) : (
        <Card>
          <div className="text-center py-12">
            <div className="text-6xl mb-4">🏠</div>
            <h3 className="text-lg font-medium text-gray-900 mb-2">
              {searchTerm || filterStatus !== 'all' ? 'Нет результатов' : 'Нет домов'}
            </h3>
            <p className="text-gray-600">
              {searchTerm || filterStatus !== 'all' 
                ? 'Попробуйте изменить фильтры или поисковый запрос'
                : 'Дома появятся после загрузки из Bitrix24'
              }
            </p>
          </div>
        </Card>
      )}
    </div>
  );
};

export default Works;