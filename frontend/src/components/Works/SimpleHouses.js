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
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
          {houses.slice(0, 12).map((house, index) => (
            <div key={house.deal_id || index} className="bg-white rounded-lg shadow border p-4">
              {/* Адрес */}
              <h3 className="font-semibold text-gray-900 mb-2">
                {house.address || 'Адрес не указан'}
              </h3>
              
              {/* Статистика */}
              <div className="grid grid-cols-3 gap-2 mb-3 text-center">
                <div className="bg-green-50 p-2 rounded">
                  <div className="font-bold text-green-600">{house.apartments_count || 0}</div>
                  <div className="text-xs text-green-700">Квартир</div>
                </div>
                <div className="bg-blue-50 p-2 rounded">
                  <div className="font-bold text-blue-600">{house.entrances_count || 0}</div>
                  <div className="text-xs text-blue-700">Подъездов</div>
                </div>
                <div className="bg-orange-50 p-2 rounded">
                  <div className="font-bold text-orange-600">{house.floors_count || 0}</div>
                  <div className="text-xs text-orange-700">Этажей</div>
                </div>
              </div>

              {/* УК */}
              <div className="bg-gray-50 p-2 rounded mb-3">
                <div className="text-xs text-gray-600 mb-1">🏢 УК:</div>
                <div className="text-sm font-medium">
                  {house.management_company || 'Не указана'}
                </div>
              </div>

              {/* График уборки */}
              {house.september_schedule?.has_schedule && (
                <div className="bg-green-50 p-2 rounded">
                  <div className="text-xs text-green-700 mb-1">📅 График:</div>
                  {house.september_schedule.cleaning_date_1 && (
                    <div className="text-xs">
                      <strong>Дата 1:</strong> {house.september_schedule.cleaning_date_1.map(d => 
                        new Date(d).toLocaleDateString()
                      ).join(', ')}
                    </div>
                  )}
                  {house.september_schedule.cleaning_type_1 && (
                    <div className="text-xs">
                      <strong>Тип 1:</strong> {house.september_schedule.cleaning_type_1}
                    </div>
                  )}
                </div>
              )}
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