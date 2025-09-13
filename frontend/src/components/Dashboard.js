import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from './ui/card';
import { Badge } from './ui/badge';
import { Separator } from './ui/separator';
import { Tabs, TabsContent, TabsList, TabsTrigger } from './ui/tabs';
import { Button } from './ui/button';
import { Progress } from './ui/progress';
import { DropdownMenu, DropdownMenuContent, DropdownMenuItem, DropdownMenuSeparator, DropdownMenuTrigger } from './ui/dropdown-menu';
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
  MoreVertical,
  ClipboardCheck,
  Trash2,
  FileText,
  Star,
  Construction,
  Shield
} from 'lucide-react';
import axios from 'axios';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

export default function Dashboard() {
  const [statistics, setStatistics] = useState(null);
  const [houses, setHouses] = useState([]);
  const [employees, setEmployees] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [lastUpdated, setLastUpdated] = useState(null);

  const fetchData = async () => {
    try {
      setLoading(true);
      setError(null);

      // Параллельно загружаем все данные
      const [statsResponse, housesResponse, employeesResponse] = await Promise.all([
        axios.get(`${API}/dashboard/statistics`),
        axios.get(`${API}/cleaning/houses?limit=50`),
        axios.get(`${API}/dashboard/employees`)
      ]);

      setStatistics(statsResponse.data.statistics);
      setHouses(housesResponse.data.houses);
      setEmployees(employeesResponse.data.employees);
      setLastUpdated(new Date().toLocaleString());
    } catch (err) {
      console.error('Ошибка загрузки данных:', err);
      setError('Ошибка подключения к Bitrix24. Проверьте настройки интеграции.');
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
        <Card className="w-full max-w-md">
          <CardContent className="pt-6">
            <div className="text-center">
              <AlertCircle className="h-12 w-12 text-red-500 mx-auto mb-4" />
              <h3 className="text-lg font-semibold mb-2">Ошибка загрузки</h3>
              <p className="text-gray-600 mb-4">{error}</p>
              <Button onClick={fetchData} className="w-full">
                <RefreshCw className="h-4 w-4 mr-2" />
                Попробовать снова
              </Button>
            </div>
          </CardContent>
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
                <h1 className="text-2xl font-bold text-gray-900">AudioBot Dashboard</h1>
                <p className="text-sm text-gray-500">Система управления домами</p>
              </div>
            </div>
            <div className="flex items-center space-x-4">
              <Badge variant="outline" className="text-green-600 border-green-600">
                <CheckCircle className="h-3 w-3 mr-1" />
                Bitrix24 подключен
              </Badge>
              <Button onClick={fetchData} variant="outline" size="sm">
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
            <Card>
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm font-medium">Всего домов</CardTitle>
                <Home className="h-4 w-4 text-muted-foreground" />
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">{statistics.houses.total}</div>
                <p className="text-xs text-muted-foreground">
                  {statistics.houses.total_apartments} квартир, {statistics.houses.with_schedule} с графиками
                </p>
              </CardContent>
            </Card>

            <Card>
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm font-medium">Сотрудники</CardTitle>
                <Users className="h-4 w-4 text-muted-foreground" />
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">{statistics.employees.total}</div>
                <p className="text-xs text-muted-foreground">
                  {statistics.employees.brigades} бригад
                </p>
              </CardContent>
            </Card>

            <Card>
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm font-medium">Управляющие компании</CardTitle>
                <Building2 className="h-4 w-4 text-muted-foreground" />
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">{statistics.management_companies.total}</div>
                <p className="text-xs text-muted-foreground">
                  Активные партнеры
                </p>
              </CardContent>
            </Card>

            <Card>
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm font-medium">Объекты обслуживания</CardTitle>
                <BarChart3 className="h-4 w-4 text-muted-foreground" />
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">{statistics.houses.total_entrances}</div>
                <p className="text-xs text-muted-foreground">
                  Подъездов в управлении
                </p>
              </CardContent>
            </Card>
          </div>
        )}

        {/* Tabs */}
        <Tabs defaultValue="houses" className="space-y-6">
          <TabsList className="grid w-full grid-cols-3">
            <TabsTrigger value="houses">Дома</TabsTrigger>
            <TabsTrigger value="brigades">Бригады</TabsTrigger>
            <TabsTrigger value="companies">Управляющие компании</TabsTrigger>
          </TabsList>

          {/* Houses Tab */}
          <TabsContent value="houses" className="space-y-6">
            <Card>
              <CardHeader>
                <div className="flex items-center justify-between">
                  <div className="flex items-center">
                    <FileText className="h-6 w-6 text-gray-600 mr-3" />
                    <div>
                      <CardTitle className="text-xl font-bold">
                        Список домов ({houses.length} из {houses.length})
                      </CardTitle>
                      <div className="flex items-center mt-1">
                        <CheckCircle className="h-4 w-4 text-green-500 mr-2" />
                        <span className="text-sm text-green-600 font-medium">
                          Все дома загружены
                        </span>
                      </div>
                    </div>
                  </div>
                  <Button className="bg-green-600 hover:bg-green-700 text-white">
                    <RefreshCw className="h-4 w-4 mr-2" />
                    Обновить
                  </Button>
                </div>
              </CardHeader>
              <CardContent>
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                  {houses.map((house) => (
                    <Card key={house.id} className="border border-gray-200 shadow-sm hover:shadow-md transition-shadow duration-200">
                      <CardContent className="p-0">
                        {/* Blue Left Border */}
                        <div className="border-l-4 border-blue-500 p-6">
                          
                          {/* House Title */}
                          <div className="mb-4">
                            <h3 className="text-xl font-bold text-gray-900 mb-1">
                              {house.address.replace('ул. ', '').replace('пр. ', '')}
                            </h3>
                            <div className="flex items-center text-sm text-blue-500">
                              <MapPin className="h-4 w-4 mr-1" />
                              {house.address}
                            </div>
                            <div className="text-xs text-gray-400 mt-1">
                              ID: {house.id}
                            </div>
                          </div>

                          {/* Правильные данные Section */}
                          <div className="mb-4">
                            <h4 className="text-sm font-medium text-gray-600 mb-3 text-right">
                              Правильные данные
                            </h4>
                            <div className="grid grid-cols-3 gap-3">
                              {/* Квартиры - Green */}
                              <div className="bg-green-100 rounded-lg p-3 text-center">
                                <div className="text-2xl font-bold text-green-600 mb-1">
                                  {house.apartments}
                                </div>
                                <div className="text-xs font-medium text-green-700">
                                  Квартир
                                </div>
                              </div>
                              
                              {/* Подъезды - Blue */}
                              <div className="bg-blue-100 rounded-lg p-3 text-center">
                                <div className="text-2xl font-bold text-blue-600 mb-1">
                                  {house.entrances}
                                </div>
                                <div className="text-xs font-medium text-blue-700">
                                  Подъездов
                                </div>
                              </div>
                              
                              {/* Этажи - Orange */}
                              <div className="bg-orange-100 rounded-lg p-3 text-center">
                                <div className="text-2xl font-bold text-orange-600 mb-1">
                                  {house.floors}
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
                              <span>1 бр.</span>
                            </div>
                            <div className="flex items-center">
                              <span className="text-gray-500 mr-2">Статус</span>
                              <CheckCircle className="h-4 w-4 text-green-500" />
                              <span className="text-green-600 ml-1">Активный</span>
                            </div>
                          </div>

                          {/* Управляющая компания */}
                          <div className="mb-4 bg-blue-50 rounded-lg p-3">
                            <div className="flex items-center text-sm mb-1">
                              <Building2 className="h-4 w-4 text-blue-600 mr-2" />
                              <span className="text-blue-700 font-medium">Управляющая компания:</span>
                            </div>
                            <div className="text-sm text-gray-800 font-medium pl-6">
                              {house.management_company}
                            </div>
                          </div>

                          {/* ID Сделки */}
                          <div className="mb-4 text-xs text-gray-500 flex justify-between">
                            <span>ID сделки:</span>
                            <span>{house.id}</span>
                          </div>

                          {/* График уборки */}
                          <div className="mb-6 bg-green-50 rounded-lg p-4 border border-green-200">
                            <div className="flex items-center mb-3">
                              <Calendar className="h-4 w-4 text-green-600 mr-2" />
                              <span className="font-medium text-green-800">
                                График уборки на сентябрь 2025
                              </span>
                            </div>
                            
                            {house.september_schedule && house.september_schedule !== 'Не указан' ? (
                              <div className="space-y-3">
                                {(() => {
                                  // Парсим новый формат: дата|описание|дата|описание
                                  const scheduleParts = house.september_schedule.split('|');
                                  const scheduleItems = [];
                                  
                                  for (let i = 0; i < scheduleParts.length; i += 2) {
                                    if (scheduleParts[i] && scheduleParts[i + 1]) {
                                      scheduleItems.push({
                                        date: scheduleParts[i].trim(),
                                        type: scheduleParts[i + 1].trim()
                                      });
                                    }
                                  }
                                  
                                  return scheduleItems.map((item, index) => (
                                    <div key={index} className="bg-white rounded-lg p-3 border border-green-200">
                                      <div className="flex items-center text-sm mb-2">
                                        <Calendar className="h-3 w-3 text-red-500 mr-2" />
                                        <span className="font-medium text-gray-700">
                                          Дата {index + 1}: {item.date}
                                        </span>
                                      </div>
                                      <div className="flex items-start text-xs">
                                        <Edit className="h-3 w-3 text-orange-500 mr-2 mt-0.5 flex-shrink-0" />
                                        <span className="text-gray-600 leading-relaxed">
                                          Тип {index + 1}: {item.type}
                                        </span>
                                      </div>
                                    </div>
                                  ));
                                })()}
                              </div>
                            ) : (
                              <div className="text-sm text-gray-500 italic">
                                График не установлен
                              </div>
                            )}

                            {/* График активен */}
                            <div className="flex items-center mt-3 text-xs">
                              <div className="w-2 h-2 bg-green-500 rounded-full mr-2"></div>
                              <span className="text-green-700">График активен</span>
                              <span className="ml-auto text-gray-400">ID: {house.id}</span>
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
                      </CardContent>
                    </Card>
                  ))}
                </div>

                {/* Summary Card */}
                <Card className="mt-6 bg-gradient-to-r from-blue-50 to-purple-50 border-blue-200">
                  <CardContent className="p-6">
                    <div className="flex items-center justify-between">
                      <div>
                        <h4 className="text-lg font-semibold text-gray-900 mb-2">Сводка по домам</h4>
                        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
                          <div>
                            <span className="text-gray-600">Всего домов:</span>
                            <span className="font-bold text-blue-600 ml-2">{houses.length}</span>
                          </div>
                          <div>
                            <span className="text-gray-600">Всего квартир:</span>
                            <span className="font-bold text-green-600 ml-2">
                              {houses.reduce((sum, house) => sum + house.apartments, 0)}
                            </span>
                          </div>
                          <div>
                            <span className="text-gray-600">Всего подъездов:</span>
                            <span className="font-bold text-purple-600 ml-2">
                              {houses.reduce((sum, house) => sum + house.entrances, 0)}
                            </span>
                          </div>
                          <div>
                            <span className="text-gray-600">Средняя этажность:</span>
                            <span className="font-bold text-orange-600 ml-2">
                              {Math.round(houses.reduce((sum, house) => sum + house.floors, 0) / houses.length)}
                            </span>
                          </div>
                        </div>
                      </div>
                      <div className="hidden md:block">
                        <div className="bg-white p-4 rounded-lg shadow-sm">
                          <BarChart3 className="h-8 w-8 text-blue-600" />
                        </div>
                      </div>
                    </div>
                  </CardContent>
                </Card>
              </CardContent>
            </Card>
          </TabsContent>

          {/* Brigades Tab */}
          <TabsContent value="brigades" className="space-y-6">
            <Card>
              <CardHeader>
                <CardTitle>Рабочие бригады</CardTitle>
                <CardDescription>
                  Организационная структура и сотрудники
                </CardDescription>
              </CardHeader>
              <CardContent>
                {statistics && (
                  <div className="grid gap-6">
                    {statistics.employees.by_brigade.map((brigade) => (
                      <Card key={brigade.id} className="p-4">
                        <div className="flex items-center justify-between mb-4">
                          <h3 className="text-lg font-semibold">{brigade.name}</h3>
                          <Badge variant="outline">
                            {brigade.employees.length} сотрудников
                          </Badge>
                        </div>
                        <div className="grid gap-3">
                          {brigade.employees.map((employee) => (
                            <div key={employee.id} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                              <div>
                                <p className="font-medium">{employee.name}</p>
                                <p className="text-sm text-gray-600">{employee.position}</p>
                              </div>
                              <div className="text-right text-sm text-gray-500">
                                {employee.email && (
                                  <div className="flex items-center">
                                    <Mail className="h-3 w-3 mr-1" />
                                    {employee.email}
                                  </div>
                                )}
                              </div>
                            </div>
                          ))}
                        </div>
                      </Card>
                    ))}
                  </div>
                )}
              </CardContent>
            </Card>
          </TabsContent>

          {/* Companies Tab */}
          <TabsContent value="companies" className="space-y-6">
            <Card>
              <CardHeader>
                <CardTitle>Управляющие компании</CardTitle>
                <CardDescription>
                  Партнеры и контрагенты
                </CardDescription>
              </CardHeader>
              <CardContent>
                {statistics && (
                  <div className="grid gap-4">
                    {statistics.management_companies.list.map((company, index) => (
                      <Card key={index} className="p-4">
                        <div className="flex items-center justify-between">
                          <div className="flex items-center">
                            <Building2 className="h-5 w-5 text-blue-600 mr-3" />
                            <div>
                              <h3 className="font-semibold">{company}</h3>
                              <p className="text-sm text-gray-600">Управляющая компания</p>
                            </div>
                          </div>
                          <Badge variant="secondary">Активная</Badge>
                        </div>
                      </Card>
                    ))}
                  </div>
                )}
              </CardContent>
            </Card>
          </TabsContent>
        </Tabs>

        {/* Footer */}
        {lastUpdated && (
          <div className="mt-8 text-center text-sm text-gray-500">
            Последнее обновление: {lastUpdated}
          </div>
        )}
      </main>
    </div>
  );
}