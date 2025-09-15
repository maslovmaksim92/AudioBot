import React, { useState, useEffect } from 'react';
import { useApp } from '../../context/AppContext';
import { Card, Button, LoadingSpinner } from '../UI';

const Works = () => {
  const { state, actions } = useApp();
  const [houses, setHouses] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [statistics, setStatistics] = useState(null);

  const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;

  const fetchHousesData = async () => {
    try {
      setLoading(true);
      setError(null);

      // Используем исправленный endpoint
      const response = await fetch(`${BACKEND_URL}/api/cleaning/houses-fixed`);
      const data = await response.json();
      
      if (data.houses) {
        setHouses(data.houses);
        
        // Вычисляем статистику из РЕАЛЬНЫХ данных CRM (без fallback)
        const stats = {
          total: data.houses.length,
          total_apartments: data.houses.reduce((sum, house) => {
            const apartments = house.apartments_count || house.apartment_count || 0;
            return sum + apartments;
          }, 0),
          total_entrances: data.houses.reduce((sum, house) => {
            const entrances = house.entrances_count || house.entrance_count || 0;
            return sum + entrances;
          }, 0),
          management_companies: [...new Set(data.houses.map(house => house.management_company).filter(Boolean))].length,
          with_schedule: data.houses.filter(house => house.september_schedule?.has_schedule).length // Только реальные графики
        };
        
        setStatistics(stats);
        console.log('✅ Houses data loaded:', stats);
      }
    } catch (err) {
      console.error('❌ Error loading houses:', err);
      setError('Ошибка загрузки данных домов');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchHousesData();
  }, []);

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
          <p className="text-gray-600">Загрузка данных домов из Bitrix24...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="text-center p-8">
        <div className="text-red-500 text-6xl mb-4">❌</div>
        <h2 className="text-xl font-semibold mb-2">Ошибка загрузки</h2>
        <p className="text-gray-600 mb-4">{error}</p>
        <Button onClick={fetchHousesData} className="bg-blue-600 hover:bg-blue-700 text-white">
          Попробовать снова
        </Button>
      </div>
    );
  }

  return (
    <div className="p-6">
      {/* Header */}
      <div className="mb-8">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold text-gray-900 mb-2">
              🏠 Управление домами
            </h1>
            <p className="text-gray-600">Полный контроль над клининговыми объектами</p>
          </div>
          <div className="flex items-center space-x-4">
            <div className="bg-green-100 text-green-600 px-3 py-1 rounded-full text-sm">
              ✅ Bitrix24 подключен
            </div>
            <Button onClick={fetchHousesData} className="bg-blue-600 hover:bg-blue-700 text-white">
              🔄 Обновить
            </Button>
          </div>
        </div>
      </div>

      {/* Statistics */}
      {statistics && (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
          <Card className="p-6 bg-blue-50 border-blue-200">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-blue-600">Всего домов</p>
                <p className="text-2xl font-bold text-blue-900">{statistics.total}</p>
              </div>
              <div className="text-blue-400 text-3xl">🏠</div>
            </div>
          </Card>

          <Card className="p-6 bg-green-50 border-green-200">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-green-600">Квартиры</p>
                <p className="text-2xl font-bold text-green-900">{statistics.total_apartments}</p>
              </div>
              <div className="text-green-400 text-3xl">🏢</div>
            </div>
          </Card>

          <Card className="p-6 bg-purple-50 border-purple-200">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-purple-600">Подъезды</p>
                <p className="text-2xl font-bold text-purple-900">{statistics.total_entrances}</p>
              </div>
              <div className="text-purple-400 text-3xl">🚪</div>
            </div>
          </Card>

          <Card className="p-6 bg-orange-50 border-orange-200">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-orange-600">УК</p>
                <p className="text-2xl font-bold text-orange-900">{statistics.management_companies}</p>
              </div>
              <div className="text-orange-400 text-3xl">🏢</div>
            </div>
          </Card>
        </div>
      )}

      {/* Houses Grid */}
      <Card className="p-6">
        <div className="flex items-center justify-between mb-6">
          <h2 className="text-xl font-bold text-gray-900">
            📋 Список домов ({houses.length})
          </h2>
          <div className="text-sm text-green-600">
            ✅ Данные из CRM загружены
          </div>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {houses.slice(0, 12).map((house) => (
            <Card key={house.deal_id} className="border-l-4 border-blue-500 hover:shadow-lg transition-shadow">
              <div className="p-6">
                {/* House Title */}
                <div className="mb-4">
                  <h3 className="text-lg font-bold text-gray-900 mb-1">
                    {house.house_address || house.address}
                  </h3>
                  <div className="text-sm text-blue-600 flex items-center">
                    📍 {house.address}
                  </div>
                  <div className="text-xs text-gray-400 mt-1">
                    ID: {house.deal_id}
                  </div>
                </div>

                {/* House Data */}
                <div className="mb-4">
                  <h4 className="text-sm font-medium text-gray-600 mb-3">Данные дома</h4>
                  <div className="grid grid-cols-3 gap-2">
                    <div className="bg-green-100 rounded p-2 text-center">
                      <div className="text-lg font-bold text-green-600">
                        {house.apartments_count || 0}
                      </div>
                      <div className="text-xs text-green-700">Квартир</div>
                    </div>
                    <div className="bg-blue-100 rounded p-2 text-center">
                      <div className="text-lg font-bold text-blue-600">
                        {house.entrances_count || 0}
                      </div>
                      <div className="text-xs text-blue-700">Подъездов</div>
                    </div>
                    <div className="bg-orange-100 rounded p-2 text-center">
                      <div className="text-lg font-bold text-orange-600">
                        {house.floors_count || 0}
                      </div>
                      <div className="text-xs text-orange-700">Этажей</div>
                    </div>
                  </div>
                </div>

                {/* Brigade and Status */}
                <div className="mb-4 flex justify-between text-sm">
                  <div>
                    👥 {house.brigade || 'Не назначена'}
                  </div>
                  <div className={`flex items-center ${house.status_color === 'error' ? 'text-red-600' : 'text-green-600'}`}>
                    {house.status_color === 'error' ? '❌' : '✅'} {house.status_text || 'Активный'}
                  </div>
                </div>

                {/* Management Company */}
                <div className="mb-4 bg-blue-50 rounded p-3">
                  <div className="text-sm text-blue-700 font-medium mb-1">
                    🏢 Управляющая компания:
                  </div>
                  <div className="text-sm text-gray-800">
                    {house.management_company || 'Не указана'}
                  </div>
                </div>

                {/* Cleaning Schedule */}
                <div className="mb-4 bg-green-50 rounded p-3 border border-green-200">
                  <div className="flex items-center mb-2">
                    <span className="text-green-600 text-sm font-medium">
                      📅 График уборки (сентябрь 2025)
                    </span>
                  </div>
                  
                  {house.september_schedule ? (
                    <div className="text-xs text-gray-700 bg-white rounded p-2">
                      {house.september_schedule.length > 100 
                        ? `${house.september_schedule.substring(0, 100)}...` 
                        : house.september_schedule
                      }
                    </div>
                  ) : (
                    <div className="text-xs text-gray-500 italic">
                      График не установлен
                    </div>
                  )}

                  <div className="flex items-center mt-2 text-xs">
                    <div className={`w-2 h-2 rounded-full mr-2 ${house.september_schedule ? 'bg-green-500' : 'bg-gray-400'}`}></div>
                    <span className={house.september_schedule ? 'text-green-700' : 'text-gray-500'}>
                      График {house.september_schedule ? 'активен' : 'не установлен'}
                    </span>
                  </div>
                </div>

                {/* Action Buttons */}
                <div className="flex gap-2">
                  <Button className="flex-1 bg-blue-600 hover:bg-blue-700 text-white text-sm">
                    📅 График
                  </Button>
                  <Button className="flex-1 bg-green-600 hover:bg-green-700 text-white text-sm">
                    👁️ Детали
                  </Button>
                </div>
              </div>
            </Card>
          ))}
        </div>

        {/* Load More */}
        {houses.length > 12 && (
          <div className="text-center mt-6">
            <Button className="bg-gray-600 hover:bg-gray-700 text-white">
              Показать еще ({houses.length - 12} домов)
            </Button>
          </div>
        )}

        {/* Summary */}
        {statistics && (
          <Card className="mt-6 bg-gradient-to-r from-blue-50 to-purple-50 border-blue-200 p-6">
            <div className="flex items-center justify-between">
              <div>
                <h4 className="text-lg font-semibold text-gray-900 mb-2">📊 Сводка по домам</h4>
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
                  <div>
                    <span className="text-gray-600">Всего домов:</span>
                    <span className="font-bold text-blue-600 ml-2">{statistics.total}</span>
                  </div>
                  <div>
                    <span className="text-gray-600">Всего квартир:</span>
                    <span className="font-bold text-green-600 ml-2">{statistics.total_apartments}</span>
                  </div>
                  <div>
                    <span className="text-gray-600">Всего подъездов:</span>
                    <span className="font-bold text-purple-600 ml-2">{statistics.total_entrances}</span>
                  </div>
                  <div>
                    <span className="text-gray-600">УК-партнеров:</span>
                    <span className="font-bold text-orange-600 ml-2">{statistics.management_companies}</span>
                  </div>
                </div>
              </div>
              <div className="text-6xl">📈</div>
            </div>
          </Card>
        )}
      </Card>
    </div>
  );
};

export default Works;