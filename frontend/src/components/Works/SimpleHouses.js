import React, { useState, useEffect } from 'react';

const SimpleHouses = () => {
  const [houses, setHouses] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    loadHouses();
  }, []);

  const loadHouses = async () => {
    try {
      setLoading(true);
      setError(null);
      
      const BACKEND_URL = process.env.REACT_APP_BACKEND_URL || import.meta.env.REACT_APP_BACKEND_URL;
      console.log('🔗 Loading houses from:', `${BACKEND_URL}/api/cleaning/houses-490`);
      
      const response = await fetch(`${BACKEND_URL}/api/cleaning/houses-490`);
      console.log('📡 Response status:', response.status);
      
      if (!response.ok) {
        throw new Error(`HTTP ${response.status}`);
      }
      
      const data = await response.json();
      console.log('📊 API Data:', {
        status: data?.status,
        total: data?.total,
        houses_count: data?.houses?.length || 0
      });
      
      if (data?.status === 'success' && Array.isArray(data.houses)) {
        setHouses(data.houses);
        console.log('✅ Houses loaded:', data.houses.length);
      } else {
        throw new Error('Invalid data format');
      }
      
    } catch (err) {
      console.error('❌ Error loading houses:', err);
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="p-8 text-center">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-500 mx-auto mb-4"></div>
        <p>Загрузка домов...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="p-8 text-center">
        <div className="text-red-500 mb-4">❌ Ошибка: {error}</div>
        <button 
          onClick={loadHouses}
          className="bg-blue-500 text-white px-4 py-2 rounded hover:bg-blue-600"
        >
          🔄 Повторить
        </button>
      </div>
    );
  }

  return (
    <div className="p-6">
      <div className="mb-6">
        <h1 className="text-2xl font-bold mb-2">🏠 Простой список домов</h1>
        <p className="text-gray-600">Загружено: <strong>{houses.length}</strong> домов</p>
      </div>

      {houses.length === 0 ? (
        <div className="text-center py-12">
          <p className="text-gray-500 mb-4">Дома не загружены</p>
          <button 
            onClick={loadHouses}
            className="bg-blue-500 text-white px-4 py-2 rounded hover:bg-blue-600"
          >
            🔄 Загрузить заново
          </button>
        </div>
      ) : (
        <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
          {houses.slice(0, 12).map((house, index) => (
            <div key={house.deal_id || index} className="bg-white rounded-xl shadow-xl hover:shadow-2xl transition-all duration-300 border-l-4 border-blue-500 overflow-hidden transform hover:-translate-y-1">
              {/* Заголовок с градиентом */}
              <div className="bg-gradient-to-r from-blue-500 to-purple-600 p-4 text-white">
                <h3 className="font-bold text-lg mb-1">
                  🏠 {house.address || 'Адрес не указан'}
                </h3>
                {house.house_address && house.house_address !== house.address && (
                  <p className="text-blue-100 text-sm">📍 {house.house_address}</p>
                )}
              </div>

              <div className="p-4">
                {/* Статистика с иконками */}
                <div className="grid grid-cols-3 gap-3 mb-4">
                  <div className="bg-gradient-to-br from-green-50 to-green-100 p-3 rounded-lg text-center border border-green-200">
                    <div className="text-2xl font-bold text-green-600">{house.apartments_count || 0}</div>
                    <div className="text-xs text-green-700 font-medium">🚪 Квартир</div>
                  </div>
                  <div className="bg-gradient-to-br from-blue-50 to-blue-100 p-3 rounded-lg text-center border border-blue-200">
                    <div className="text-2xl font-bold text-blue-600">{house.entrances_count || 0}</div>
                    <div className="text-xs text-blue-700 font-medium">🚶 Подъездов</div>
                  </div>
                  <div className="bg-gradient-to-br from-orange-50 to-orange-100 p-3 rounded-lg text-center border border-orange-200">
                    <div className="text-2xl font-bold text-orange-600">{house.floors_count || 0}</div>
                    <div className="text-xs text-orange-700 font-medium">🏢 Этажей</div>
                  </div>
                </div>

                {/* УК с улучшенным дизайном */}
                <div className="bg-gradient-to-r from-indigo-50 to-purple-50 p-3 rounded-lg mb-4 border border-indigo-200">
                  <div className="flex items-center mb-2">
                    <span className="text-indigo-600 font-semibold text-sm">🏢 Управляющая компания</span>
                  </div>
                  <div className="text-sm font-bold text-gray-800 break-words">
                    {house.management_company || 'Не указана'}
                  </div>
                  {house.brigade && (
                    <div className="text-xs text-indigo-600 mt-1">
                      👥 Бригада: {house.brigade}
                    </div>
                  )}
                </div>

                {/* График уборки с улучшенным отображением */}
                {house.september_schedule?.has_schedule ? (
                  <div className="bg-gradient-to-r from-green-50 to-emerald-50 p-3 rounded-lg mb-4 border border-green-200">
                    <div className="flex items-center justify-between mb-2">
                      <span className="text-green-700 font-semibold text-sm">📅 График уборки</span>
                      <span className="bg-green-200 text-green-800 px-2 py-1 rounded-full text-xs font-bold">Активен</span>
                    </div>
                    
                    <div className="space-y-2">
                      {house.september_schedule.cleaning_date_1 && (
                        <div className="bg-white p-2 rounded border-l-4 border-green-400">
                          <div className="flex justify-between items-center">
                            <div>
                              <div className="text-xs font-bold text-green-700">ДАТА 1:</div>
                              <div className="text-xs text-gray-700">
                                {house.september_schedule.cleaning_date_1.map(d => 
                                  new Date(d).toLocaleDateString('ru-RU', { day: '2-digit', month: '2-digit' })
                                ).join(', ')}
                              </div>
                            </div>
                            {house.september_schedule.cleaning_type_1 && (
                              <div className="bg-green-100 px-2 py-1 rounded text-xs font-medium text-green-800">
                                {house.september_schedule.cleaning_type_1}
                              </div>
                            )}
                          </div>
                        </div>
                      )}
                      
                      {house.september_schedule.cleaning_date_2 && (
                        <div className="bg-white p-2 rounded border-l-4 border-blue-400">
                          <div className="flex justify-between items-center">
                            <div>
                              <div className="text-xs font-bold text-blue-700">ДАТА 2:</div>
                              <div className="text-xs text-gray-700">
                                {house.september_schedule.cleaning_date_2.map(d => 
                                  new Date(d).toLocaleDateString('ru-RU', { day: '2-digit', month: '2-digit' })
                                ).join(', ')}
                              </div>
                            </div>
                            {house.september_schedule.cleaning_type_2 && (
                              <div className="bg-blue-100 px-2 py-1 rounded text-xs font-medium text-blue-800">
                                {house.september_schedule.cleaning_type_2}
                              </div>
                            )}
                          </div>
                        </div>
                      )}
                    </div>
                  </div>
                ) : (
                  <div className="bg-gradient-to-r from-gray-50 to-gray-100 p-3 rounded-lg mb-4 border border-gray-200">
                    <div className="text-center text-gray-500">
                      <div className="text-sm">📅 График уборки</div>
                      <div className="text-xs mt-1">Не настроен</div>
                    </div>
                  </div>
                )}

                {/* Кнопки действий */}
                <div className="grid grid-cols-2 gap-3 mt-4">
                  <button className="bg-gradient-to-r from-blue-500 to-blue-600 hover:from-blue-600 hover:to-blue-700 text-white px-4 py-2 rounded-lg text-sm font-medium transition-all duration-200 transform hover:scale-105 shadow-md hover:shadow-lg">
                    📅 График
                  </button>
                  <button 
                    onClick={() => house.house_address && openGoogleMaps(house.house_address)}
                    className="bg-gradient-to-r from-green-500 to-green-600 hover:from-green-600 hover:to-green-700 text-white px-4 py-2 rounded-lg text-sm font-medium transition-all duration-200 transform hover:scale-105 shadow-md hover:shadow-lg"
                  >
                    🗺️ Карта
                  </button>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}

      {houses.length > 12 && (
        <div className="text-center mt-6 p-4 bg-blue-50 rounded">
          <p className="text-blue-800">
            Показано 12 из {houses.length} домов. Полный список в основном компоненте.
          </p>
        </div>
      )}
    </div>
  );
};

export default SimpleHouses;