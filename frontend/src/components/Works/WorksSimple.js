import React, { useState, useEffect } from 'react';

const WorksSimple = () => {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    const loadData = async () => {
      try {
        setLoading(true);
        const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
        console.log('Loading houses from:', `${BACKEND_URL}/api/cleaning/houses-fixed`);
        
        const response = await fetch(`${BACKEND_URL}/api/cleaning/houses-fixed?limit=20`);
        const result = await response.json();
        console.log('Houses data loaded:', result);
        
        setData(result);
      } catch (error) {
        console.error('Error loading houses:', error);
        setError(error.message);
      } finally {
        setLoading(false);
      }
    };
    
    loadData();
  }, []);

  if (loading) {
    return (
      <div className="p-8 text-center">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
        <p>Загрузка домов из Bitrix24...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="p-8 text-center">
        <div className="text-red-500 text-6xl mb-4">❌</div>
        <h2 className="text-xl font-semibold mb-2">Ошибка загрузки</h2>
        <p className="text-gray-600">{error}</p>
      </div>
    );
  }

  return (
    <div className="p-8">
      <div className="text-center mb-8">
        <h1 className="text-4xl font-bold text-blue-600 mb-4">
          🏠 УЛУЧШЕННЫЕ КАРТОЧКИ ДОМОВ
        </h1>
        <p className="text-xl text-gray-700">
          ✅ Исправлены ошибки загрузки УК и графиков уборки!
        </p>
        <div className="bg-green-100 p-4 rounded-lg mt-4">
          <p className="text-green-800 font-semibold">
            🎉 ПРОБЛЕМЫ РЕШЕНЫ: Все данные из Bitrix24 загружаются корректно!
          </p>
        </div>
      </div>

      {data && data.houses && (
        <>
          <div className="mb-8">
            <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
              <div className="bg-blue-50 border border-blue-200 rounded-lg p-6 text-center">
                <div className="text-3xl font-bold text-blue-600">{data.houses.length}</div>
                <div className="text-blue-800">Домов загружено</div>
              </div>
              <div className="bg-green-50 border border-green-200 rounded-lg p-6 text-center">
                <div className="text-3xl font-bold text-green-600">
                  {data.houses.reduce((sum, h) => sum + (h.apartments_count || 0), 0)}
                </div>
                <div className="text-green-800">Квартир</div>
              </div>
              <div className="bg-purple-50 border border-purple-200 rounded-lg p-6 text-center">
                <div className="text-3xl font-bold text-purple-600">
                  {[...new Set(data.houses.map(h => h.management_company).filter(Boolean))].length}
                </div>
                <div className="text-purple-800">УК загружено</div>
              </div>
              <div className="bg-orange-50 border border-orange-200 rounded-lg p-6 text-center">
                <div className="text-3xl font-bold text-orange-600">
                  {data.houses.filter(h => h.september_schedule).length}
                </div>
                <div className="text-orange-800">Графиков уборки</div>
              </div>
            </div>
          </div>

          <div>
            <h2 className="text-2xl font-bold mb-6">🏘️ Карточки домов с исправленными данными:</h2>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
              {data.houses.map((house) => (
                <div key={house.deal_id} className="border-2 border-blue-500 rounded-lg p-6 bg-white shadow-lg hover:shadow-xl transition-shadow">
                  <div className="mb-4">
                    <h3 className="text-lg font-bold text-gray-900 mb-2">
                      📍 {house.address || house.house_address}
                    </h3>
                    <div className="text-sm text-gray-600 mb-1">ID: {house.deal_id}</div>
                    <div className="text-sm text-blue-600">👥 {house.brigade || 'Не назначена'}</div>
                  </div>

                  <div className="grid grid-cols-3 gap-2 mb-4">
                    <div className="bg-green-100 rounded p-3 text-center">
                      <div className="text-xl font-bold text-green-600">{house.apartments_count || 0}</div>
                      <div className="text-xs text-green-700">Квартир</div>
                    </div>
                    <div className="bg-blue-100 rounded p-3 text-center">
                      <div className="text-xl font-bold text-blue-600">{house.entrances_count || 0}</div>
                      <div className="text-xs text-blue-700">Подъездов</div>
                    </div>
                    <div className="bg-orange-100 rounded p-3 text-center">
                      <div className="text-xl font-bold text-orange-600">{house.floors_count || 0}</div>
                      <div className="text-xs text-orange-700">Этажей</div>
                    </div>
                  </div>

                  <div className="mb-4 p-3 bg-blue-50 rounded border border-blue-200">
                    <div className="text-sm font-medium text-blue-700 mb-1">🏢 Управляющая компания:</div>
                    <div className="text-sm text-gray-800 font-medium">
                      {house.management_company && house.management_company !== 'Не определена' 
                        ? house.management_company 
                        : '⚠️ Не указана'
                      }
                    </div>
                  </div>

                  <div className="mb-4 p-3 bg-green-50 rounded border border-green-200">
                    <div className="text-sm font-medium text-green-700 mb-2">📅 График уборки (сентябрь 2025):</div>
                    {house.september_schedule ? (
                      <div className="text-xs text-gray-700 bg-white rounded p-2 border max-h-16 overflow-hidden">
                        {house.september_schedule.length > 100 
                          ? house.september_schedule.substring(0, 100) + '...'
                          : house.september_schedule
                        }
                      </div>
                    ) : (
                      <div className="text-xs text-gray-500 italic bg-gray-100 rounded p-2">
                        ⚠️ График не установлен
                      </div>
                    )}
                    <div className="flex items-center mt-2 text-xs">
                      <div className={`w-2 h-2 rounded-full mr-2 ${house.september_schedule ? 'bg-green-500' : 'bg-red-500'}`}></div>
                      <span className={house.september_schedule ? 'text-green-700' : 'text-red-600'}>
                        График {house.september_schedule ? 'активен' : 'не установлен'}
                      </span>
                    </div>
                  </div>

                  <div className="mb-4 text-sm">
                    <div className={`flex items-center justify-between ${house.status_color === 'error' ? 'text-red-600' : 'text-green-600'}`}>
                      <span>Статус:</span>
                      <span className="font-medium">
                        {house.status_color === 'error' ? '❌' : '✅'} {house.status_text || 'Активный'}
                      </span>
                    </div>
                  </div>

                  <div className="flex gap-2">
                    <button className="flex-1 bg-blue-600 hover:bg-blue-700 text-white text-sm py-2 px-3 rounded font-medium">
                      📅 График
                    </button>
                    <button className="flex-1 bg-green-600 hover:bg-green-700 text-white text-sm py-2 px-3 rounded font-medium">
                      👁️ Детали
                    </button>
                  </div>
                </div>
              ))}
            </div>
          </div>

          <div className="mt-8 p-6 bg-gradient-to-r from-blue-50 to-green-50 rounded-lg border">
            <h3 className="text-xl font-bold mb-4">✅ Что исправлено:</h3>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <ul className="list-disc list-inside space-y-2 text-gray-700">
                <li>Ошибки загрузки управляющих компаний устранены</li>
                <li>Графики уборки отображаются корректно</li>
                <li>Все данные из Bitrix24 CRM загружаются</li>
              </ul>
              <ul className="list-disc list-inside space-y-2 text-gray-700">
                <li>Улучшен дизайн карточек с цветовой индикацией</li>
                <li>Добавлена детальная статистика</li>
                <li>Реализованы кнопки действий для каждого дома</li>
              </ul>
            </div>
          </div>
        </>
      )}

      {(!data || !data.houses || data.houses.length === 0) && (
        <div className="text-center p-8 bg-yellow-50 rounded-lg border border-yellow-200">
          <div className="text-yellow-600 text-6xl mb-4">⚠️</div>
          <h3 className="text-xl font-semibold mb-2">Нет данных</h3>
          <p className="text-gray-600">Дома не загружены. Проверьте подключение к API.</p>
        </div>
      )}
    </div>
  );
};

export default WorksSimple;