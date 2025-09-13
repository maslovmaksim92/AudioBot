import React, { useState, useEffect } from 'react';
import { useApp } from '../../context/AppContext';
import { Card, Button, LoadingSpinner } from '../UI';
import { 
  Home, 
  Users, 
  Building2, 
  Calendar,
  BarChart3,
  RefreshCw,
  AlertCircle,
  CheckCircle,
  MapPin,
  Phone,
  Mail,
  Clock,
  Eye,
  Edit,
  FileText
} from 'lucide-react';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const Works = () => {
  const { actions } = useApp();
  
  // State
  const [houses, setHouses] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [statistics, setStatistics] = useState(null);
  const [lastUpdated, setLastUpdated] = useState(null);

  const fetchData = async () => {
    try {
      setLoading(true);
      setError(null);

      // Загружаем данные домов с исправленного endpoint
      const response = await fetch(`${API}/cleaning/houses-fixed`);
      const data = await response.json();
      
      if (data.houses) {
        setHouses(data.houses);
        
        // Вычисляем статистику из загруженных домов
        const stats = {
          houses: {
            total: data.houses.length,
            total_apartments: data.houses.reduce((sum, house) => sum + (house.apartments_count || 0), 0),
            total_entrances: data.houses.reduce((sum, house) => sum + (house.entrances_count || 0), 0),
            total_floors: data.houses.reduce((sum, house) => sum + (house.floors_count || 0), 0),
            with_schedule: data.houses.filter(house => house.september_schedule).length
          },
          management_companies: {
            total: [...new Set(data.houses.map(house => house.management_company).filter(Boolean))].length,
            list: [...new Set(data.houses.map(house => house.management_company).filter(Boolean))]
          }
        };
        
        setStatistics(stats);
        setLastUpdated(new Date().toLocaleString());
      }
    } catch (err) {
      console.error('Ошибка загрузки данных:', err);
      setError('Ошибка подключения к API. Проверьте настройки.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, []);

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="text-center">
          <RefreshCw className="h-8 w-8 animate-spin mx-auto mb-4 text-blue-600" />
          <p className="text-lg font-medium">Загрузка данных из Bitrix24...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <Card className="w-full max-w-md p-6">
          <div className="text-center">
            <AlertCircle className="h-12 w-12 text-red-500 mx-auto mb-4" />
            <h3 className="text-lg font-semibold mb-2">Ошибка загрузки</h3>
            <p className="text-gray-600 mb-4">{error}</p>
            <Button onClick={fetchData} className="w-full">
              <RefreshCw className="h-4 w-4 mr-2" />
              Попробовать снова
            </Button>
          </div>
        </Card>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white shadow-sm">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center py-6">
            <div className="flex items-center">
              <Building2 className="h-8 w-8 text-blue-600 mr-3" />
              <div>
                <h1 className="text-2xl font-bold text-gray-900">Управление домами</h1>
                <p className="text-sm text-gray-500">Полный контроль над клининговыми объектами</p>
              </div>
            </div>
            <div className="flex items-center space-x-4">
              <div className="bg-green-100 text-green-600 px-3 py-1 rounded-full text-sm flex items-center">
                <CheckCircle className="h-3 w-3 mr-1" />
                Bitrix24 подключен
              </div>
              <Button onClick={fetchData} className="bg-blue-600 hover:bg-blue-700 text-white">
                <RefreshCw className="h-4 w-4 mr-2" />
                Обновить
              </Button>
            </div>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Statistics Cards */}
        {statistics && (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
            <Card className="p-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm font-medium text-gray-600">Всего домов</p>
                  <p className="text-2xl font-bold text-gray-900">{statistics.houses.total}</p>
                  <p className="text-xs text-gray-500">{statistics.houses.with_schedule} с графиками</p>
                </div>
                <Home className="h-8 w-8 text-gray-400" />
              </div>
            </Card>

            <Card className="p-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm font-medium text-gray-600">Квартиры</p>
                  <p className="text-2xl font-bold text-gray-900">{statistics.houses.total_apartments}</p>
                  <p className="text-xs text-gray-500">Всего в управлении</p>
                </div>
                <Building2 className="h-8 w-8 text-gray-400" />
              </div>
            </Card>

            <Card className="p-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm font-medium text-gray-600">Подъезды</p>
                  <p className="text-2xl font-bold text-gray-900">{statistics.houses.total_entrances}</p>
                  <p className="text-xs text-gray-500">Объекты обслуживания</p>
                </div>
                <BarChart3 className="h-8 w-8 text-gray-400" />
              </div>
            </Card>

            <Card className="p-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm font-medium text-gray-600">Управляющие компании</p>
                  <p className="text-2xl font-bold text-gray-900">{statistics.management_companies.total}</p>
                  <p className="text-xs text-gray-500">Активные партнеры</p>
                </div>
                <Users className="h-8 w-8 text-gray-400" />
              </div>
            </Card>
          </div>
        )}

        {/* Houses Grid */}
        <Card className="p-6">
          <div className="flex items-center justify-between mb-6">
            <div className="flex items-center">
              <FileText className="h-6 w-6 text-gray-600 mr-3" />
              <div>
                <h3 className="text-xl font-bold">Список домов ({houses.length})</h3>
                <div className="flex items-center mt-1">
                  <CheckCircle className="h-4 w-4 text-green-500 mr-2" />
                  <span className="text-sm text-green-600 font-medium">Все дома загружены</span>
                </div>
              </div>
            </div>
            <Button onClick={fetchData} className="bg-green-600 hover:bg-green-700 text-white">
              <RefreshCw className="h-4 w-4 mr-2" />
              Обновить
            </Button>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {houses.map((house) => (
              <Card key={house.deal_id} className="border border-gray-200 shadow-sm hover:shadow-md transition-shadow duration-200">
                <div className="p-0">
                  {/* Blue Left Border */}
                  <div className="border-l-4 border-blue-500 p-6">
                    
                    {/* House Title */}
                    <div className="mb-4">
                      <h3 className="text-xl font-bold text-gray-900 mb-1">
                        {house.house_address || house.address}
                      </h3>
                      <div className="flex items-center text-sm text-blue-500">
                        <MapPin className="h-4 w-4 mr-1" />
                        {house.address}
                      </div>
                      <div className="text-xs text-gray-400 mt-1">
                        ID: {house.deal_id}
                      </div>
                    </div>

                    {/* Данные дома */}
                    <div className="mb-4">
                      <h4 className="text-sm font-medium text-gray-600 mb-3 text-right">
                        Данные дома
                      </h4>
                      <div className="grid grid-cols-3 gap-3">
                        {/* Квартиры */}
                        <div className="bg-green-100 rounded-lg p-3 text-center">
                          <div className="text-2xl font-bold text-green-600 mb-1">
                            {house.apartments_count || 0}
                          </div>
                          <div className="text-xs font-medium text-green-700">
                            Квартир
                          </div>
                        </div>
                        
                        {/* Подъезды */}
                        <div className="bg-blue-100 rounded-lg p-3 text-center">
                          <div className="text-2xl font-bold text-blue-600 mb-1">
                            {house.entrances_count || 0}
                          </div>
                          <div className="text-xs font-medium text-blue-700">
                            Подъездов
                          </div>
                        </div>
                        
                        {/* Этажи */}
                        <div className="bg-orange-100 rounded-lg p-3 text-center">
                          <div className="text-2xl font-bold text-orange-600 mb-1">
                            {house.floors_count || 0}
                          </div>
                          <div className="text-xs font-medium text-orange-700">
                            Этажей
                          </div>
                        </div>
                      </div>
                    </div>

                    {/* Бригада и Статус */}
                    <div className="mb-4 flex justify-between text-sm">
                      <div className="flex items-center">
                        <Users className="h-4 w-4 mr-1" />
                        <span>{house.brigade || 'Не назначена'}</span>
                      </div>
                      <div className="flex items-center">
                        <span className="text-gray-500 mr-2">Статус:</span>
                        {house.status_color === 'error' ? (
                          <AlertCircle className="h-4 w-4 text-red-500" />
                        ) : (
                          <CheckCircle className="h-4 w-4 text-green-500" />
                        )}
                        <span className={`ml-1 ${house.status_color === 'error' ? 'text-red-600' : 'text-green-600'}`}>
                          {house.status_text || 'Активный'}
                        </span>
                      </div>
                    </div>

                    {/* Управляющая компания */}
                    <div className="mb-4 bg-blue-50 rounded-lg p-3">
                      <div className="flex items-center text-sm mb-1">
                        <Building2 className="h-4 w-4 text-blue-600 mr-2" />
                        <span className="text-blue-700 font-medium">Управляющая компания:</span>
                      </div>
                      <div className="text-sm text-gray-800 font-medium pl-6">
                        {house.management_company || 'Не указана'}
                      </div>
                    </div>

                    {/* График уборки */}
                    <div className="mb-6 bg-green-50 rounded-lg p-4 border border-green-200">
                      <div className="flex items-center mb-3">
                        <Calendar className="h-4 w-4 text-green-600 mr-2" />
                        <span className="font-medium text-green-800">
                          График уборки на сентябрь 2025
                        </span>
                      </div>
                      
                      {house.september_schedule ? (
                        <div className="text-sm text-gray-700 bg-white rounded p-2 border">
                          {house.september_schedule}
                        </div>
                      ) : (
                        <div className="text-sm text-gray-500 italic">
                          График не установлен
                        </div>
                      )}

                      {/* График активен */}
                      <div className="flex items-center mt-3 text-xs">
                        <div className="w-2 h-2 bg-green-500 rounded-full mr-2"></div>
                        <span className="text-green-700">
                          График {house.september_schedule ? 'активен' : 'не установлен'}
                        </span>
                        <span className="ml-auto text-gray-400">ID: {house.deal_id}</span>
                      </div>
                    </div>

                    {/* Action Buttons */}
                    <div className="flex gap-3">
                      <Button className="flex-1 bg-blue-600 hover:bg-blue-700 text-white">
                        <Calendar className="h-4 w-4 mr-2" />
                        График
                      </Button>
                      <Button className="flex-1 bg-green-600 hover:bg-green-700 text-white">
                        <Eye className="h-4 w-4 mr-2" />
                        Детали
                      </Button>
                    </div>

                    {/* Bottom Icons */}
                    <div className="flex justify-between items-center mt-4 pt-4 border-t border-gray-200">
                      <div className="flex items-center text-xs text-gray-500">
                        <MapPin className="h-3 w-3 mr-1" />
                        <span>Карта</span>
                      </div>
                      <div className="flex items-center text-xs text-gray-500">
                        <Phone className="h-3 w-3 mr-1" />
                        <span>Связь</span>
                      </div>
                      <div className="flex items-center text-xs text-gray-500">
                        <FileText className="h-3 w-3 mr-1" />
                        <span>Заметки</span>
                      </div>
                    </div>
                  </div>
                </div>
              </Card>
            ))}
          </div>

          {/* Summary Card */}
          {statistics && (
            <Card className="mt-6 bg-gradient-to-r from-blue-50 to-purple-50 border-blue-200 p-6">
              <div className="flex items-center justify-between">
                <div>
                  <h4 className="text-lg font-semibold text-gray-900 mb-2">Сводка по домам</h4>
                  <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
                    <div>
                      <span className="text-gray-600">Всего домов:</span>
                      <span className="font-bold text-blue-600 ml-2">{statistics.houses.total}</span>
                    </div>
                    <div>
                      <span className="text-gray-600">Всего квартир:</span>
                      <span className="font-bold text-green-600 ml-2">{statistics.houses.total_apartments}</span>
                    </div>
                    <div>
                      <span className="text-gray-600">Всего подъездов:</span>
                      <span className="font-bold text-purple-600 ml-2">{statistics.houses.total_entrances}</span>
                    </div>
                    <div>
                      <span className="text-gray-600">УК-партнеров:</span>
                      <span className="font-bold text-orange-600 ml-2">{statistics.management_companies.total}</span>
                    </div>
                  </div>
                </div>
                <div className="hidden md:block">
                  <div className="bg-white p-4 rounded-lg shadow-sm">
                    <BarChart3 className="h-8 w-8 text-blue-600" />
                  </div>
                </div>
              </div>
            </Card>
          )}
        </Card>

        {/* Footer */}
        {lastUpdated && (
          <div className="mt-8 text-center text-sm text-gray-500">
            Последнее обновление: {lastUpdated}
          </div>
        )}
      </main>
    </div>
  );
};

export default Works;