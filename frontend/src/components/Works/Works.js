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