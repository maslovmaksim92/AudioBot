import React, { useState, useEffect } from 'react';
import { useApp } from '../../context/AppContext';
import { apiService } from '../../services/apiService';
import { Card, Button, LoadingSpinner } from '../UI';

const Works = () => {
  const { actions } = useApp();
  const [houses, setHouses] = useState([]);
  const [loading, setLoading] = useState(false);
  const [filterStatus, setFilterStatus] = useState('all');
  const [searchTerm, setSearchTerm] = useState('');

  useEffect(() => {
    fetchHouses();
  }, []);

  const fetchHouses = async () => {
    setLoading(true);
    try {
      const response = await apiService.getHouses();
      if (response.status === 'success') {
        setHouses(response.houses || []);
        actions.addNotification({
          type: 'success',
          message: `Загружено ${response.houses?.length || 0} домов`
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

  const filteredHouses = houses.filter(house => {
    const matchesStatus = filterStatus === 'all' || house.stage === filterStatus;
    const matchesSearch = house.address?.toLowerCase().includes(searchTerm.toLowerCase()) ||
                         house.deal_id?.toLowerCase().includes(searchTerm.toLowerCase());
    return matchesStatus && matchesSearch;
  });

  const getStatusColor = (stage) => {
    switch (stage) {
      case 'C2:NEW': return 'bg-blue-100 text-blue-800';
      case 'C2:PREPARATION': return 'bg-yellow-100 text-yellow-800';
      case 'C2:CLIENT': return 'bg-purple-100 text-purple-800';
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
    &lt;div className="p-6"&gt;
      &lt;div className="flex justify-between items-center mb-6"&gt;
        &lt;div&gt;
          &lt;h1 className="text-3xl font-bold text-gray-900"&gt;Дома в управлении&lt;/h1&gt;
          &lt;p className="text-gray-600"&gt;Всего домов: {houses.length} из Bitrix24 CRM&lt;/p&gt;
        &lt;/div&gt;
        &lt;Button onClick={fetchHouses} loading={loading}&gt;
          🔄 Обновить
        &lt;/Button&gt;
      &lt;/div&gt;

      {/* Filters and Search */}
      &lt;Card className="mb-6"&gt;
        &lt;div className="flex flex-col md:flex-row md:items-center md:justify-between space-y-4 md:space-y-0"&gt;
          &lt;div className="flex flex-wrap gap-2"&gt;
            &lt;Button
              variant={filterStatus === 'all' ? 'primary' : 'secondary'}
              size="sm"
              onClick={() => setFilterStatus('all')}
            &gt;
              Все ({houses.length})
            &lt;/Button&gt;
            {Object.entries(statusCounts).map(([status, count]) => (
              &lt;Button
                key={status}
                variant={filterStatus === status ? 'primary' : 'secondary'}
                size="sm"
                onClick={() => setFilterStatus(status)}
              &gt;
                {getStatusText(status)} ({count})
              &lt;/Button&gt;
            ))}
          &lt;/div&gt;
          
          &lt;div className="flex items-center space-x-2"&gt;
            &lt;input
              type="text"
              placeholder="Поиск по адресу или ID..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
            /&gt;
          &lt;/div&gt;
        &lt;/div&gt;
      &lt;/Card&gt;

      {/* Houses Grid */}
      {loading ? (
        &lt;div className="flex justify-center py-12"&gt;
          &lt;LoadingSpinner size="lg" text="Загрузка домов..." /&gt;
        &lt;/div&gt;
      ) : filteredHouses.length > 0 ? (
        &lt;div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6"&gt;
          {filteredHouses.map((house, index) => (
            &lt;Card key={house.deal_id || index} className="hover:shadow-lg transition-shadow"&gt;
              &lt;div className="space-y-3"&gt;
                &lt;div className="flex justify-between items-start"&gt;
                  &lt;h3 className="font-semibold text-gray-900 text-sm leading-tight"&gt;
                    {house.address || 'Адрес не указан'}
                  &lt;/h3&gt;
                  &lt;span className={`px-2 py-1 rounded-full text-xs font-medium ${getStatusColor(house.stage)}`}&gt;
                    {getStatusText(house.stage)}
                  &lt;/span&gt;
                &lt;/div&gt;
                
                &lt;div className="space-y-2 text-sm text-gray-600"&gt;
                  &lt;div className="flex justify-between"&gt;
                    &lt;span&gt;ID сделки:&lt;/span&gt;
                    &lt;span className="font-mono text-xs"&gt;{house.deal_id}&lt;/span&gt;
                  &lt;/div&gt;
                  
                  {house.brigade && (
                    &lt;div className="flex justify-between"&gt;
                      &lt;span&gt;Бригада:&lt;/span&gt;
                      &lt;span&gt;{house.brigade}&lt;/span&gt;
                    &lt;/div&gt;
                  )}
                  
                  {house.opportunity && (
                    &lt;div className="flex justify-between"&gt;
                      &lt;span&gt;Сумма:&lt;/span&gt;
                      &lt;span className="font-semibold"&gt;{house.opportunity} ₽&lt;/span&gt;
                    &lt;/div&gt;
                  )}
                  
                  {house.created_date && (
                    &lt;div className="flex justify-between"&gt;
                      &lt;span&gt;Создан:&lt;/span&gt;
                      &lt;span&gt;{new Date(house.created_date).toLocaleDateString('ru-RU')}&lt;/span&gt;
                    &lt;/div&gt;
                  )}
                &lt;/div&gt;
                
                &lt;div className="pt-3 border-t border-gray-100"&gt;
                  &lt;div className="flex justify-between items-center"&gt;
                    &lt;span className="text-xs text-gray-500"&gt;
                      Обновлено: {house.last_sync ? new Date(house.last_sync).toLocaleTimeString('ru-RU') : 'Неизвестно'}
                    &lt;/span&gt;
                    {house.status_text && (
                      &lt;span className="text-xs px-2 py-1 bg-gray-100 rounded"&gt;
                        {house.status_text}
                      &lt;/span&gt;
                    )}
                  &lt;/div&gt;
                &lt;/div&gt;
              &lt;/div&gt;
            &lt;/Card&gt;
          ))}
        &lt;/div&gt;
      ) : (
        &lt;Card&gt;
          &lt;div className="text-center py-12"&gt;
            &lt;div className="text-6xl mb-4"&gt;🏠&lt;/div&gt;
            &lt;h3 className="text-lg font-medium text-gray-900 mb-2"&gt;
              {searchTerm || filterStatus !== 'all' ? 'Нет результатов' : 'Нет домов'}
            &lt;/h3&gt;
            &lt;p className="text-gray-600"&gt;
              {searchTerm || filterStatus !== 'all' 
                ? 'Попробуйте изменить фильтры или поисковый запрос'
                : 'Дома появятся после загрузки из Bitrix24'
              }
            &lt;/p&gt;
          &lt;/div&gt;
        &lt;/Card&gt;
      )}
    &lt;/div&gt;
  );
};

export default Works;